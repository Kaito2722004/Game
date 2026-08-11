"""Tournament creation, execution, results and statistics."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError
from app.models.tournament import (
    Tournament,
    TournamentMatch,
    TournamentResult,
    TournamentRound,
    TournamentStatus,
)
from app.models.user import User
from app.repositories.tournament import TournamentRepository
from app.schemas.simulation import (
    RoundResultResponse,
    TournamentCreateRequest,
    TournamentMatchDetailResponse,
    TournamentMatchSummaryResponse,
    TournamentRankingResponse,
    TournamentResponse,
    TournamentResultsResponse,
)
from app.schemas.statistics import (
    CooperationByRound,
    DescriptiveStatisticsResponse,
    HeadToHeadEntry,
    TournamentStatisticsResponse,
)
from app.services.payoff_matrix_service import PayoffMatrixService
from app.simulation.tournament import TournamentResult as DomainTournamentResult
from app.simulation.tournament import run_tournament
from app.statistics.analysis import tournament_statistics
from app.strategies.registry import strategy_registry


class TournamentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = TournamentRepository(db)
        self.matrices = PayoffMatrixService(db)

    # ------------------------------------------------------------ creation --
    def create(
        self, payload: TournamentCreateRequest, actor: User | None = None
    ) -> TournamentResponse:
        """Register a tournament. Simulation happens later, on /run."""
        for strategy_id in payload.strategy_ids:
            strategy_registry.get(strategy_id)

        _, stored_matrix = self.matrices.resolve_domain_matrix(
            payload.matrix, payload.payoff_matrix_id
        )
        if stored_matrix is None:
            # An inline matrix still has to be stored, because results must
            # remain reproducible from what the database holds.
            stored_matrix = self._store_inline_matrix(payload, actor)

        tournament = Tournament(
            name=payload.name,
            description=payload.description,
            status=TournamentStatus.PENDING,
            strategy_codes=payload.strategy_ids,
            rounds_per_match=payload.rounds_per_match,
            repetitions=payload.repetitions,
            seed=payload.seed,
            continuation_probability=payload.continuation_probability,
            include_self_play=payload.include_self_play,
            payoff_matrix_id=stored_matrix.id,
            created_by_id=actor.id if actor else None,
        )
        self.repository.add(tournament)
        self.db.commit()
        self.db.refresh(tournament)
        return self.to_response(tournament)

    def _store_inline_matrix(
        self, payload: TournamentCreateRequest, actor: User | None
    ):
        from app.models.payoff_matrix import PayoffMatrix

        matrix = PayoffMatrix(
            name=f"Matrix for tournament '{payload.name}' {uuid.uuid4().hex[:8]}",
            description="Created automatically from an inline tournament matrix.",
            is_default=False,
            created_by_id=actor.id if actor else None,
        )
        matrix.apply_domain(payload.matrix.to_domain())
        self.db.add(matrix)
        self.db.flush()
        return matrix

    # ----------------------------------------------------------- retrieval --
    def get_model(self, tournament_id: uuid.UUID) -> Tournament:
        tournament = self.repository.get(tournament_id)
        if tournament is None:
            raise NotFoundError(f"Tournament {tournament_id} was not found")
        return tournament

    def get(self, tournament_id: uuid.UUID) -> TournamentResponse:
        return self.to_response(self.get_model(tournament_id))

    def list(self, limit: int = 100, offset: int = 0) -> list[TournamentResponse]:
        return [
            self.to_response(row)
            for row in self.repository.list(limit=limit, offset=offset)
        ]

    def to_response(self, tournament: Tournament) -> TournamentResponse:
        return TournamentResponse(
            id=tournament.id,
            name=tournament.name,
            description=tournament.description,
            status=tournament.status,
            strategy_codes=list(tournament.strategy_codes),
            rounds_per_match=tournament.rounds_per_match,
            repetitions=tournament.repetitions,
            seed=tournament.seed,
            continuation_probability=tournament.continuation_probability,
            include_self_play=tournament.include_self_play,
            payoff_matrix_id=tournament.payoff_matrix_id,
            matches_played=self.repository.count_matches(tournament.id),
            started_at=tournament.started_at,
            completed_at=tournament.completed_at,
            error_message=tournament.error_message,
            created_at=tournament.created_at,
        )

    # ----------------------------------------------------------- execution --
    def run(self, tournament_id: uuid.UUID) -> TournamentResultsResponse:
        """Simulate every match and store the results.

        A COMPLETED tournament is not re-run: its stored results are the
        evidence for a report and must not change underneath it. A RUNNING one
        is refused as well, so two concurrent requests cannot both simulate it.
        """
        tournament = self.get_model(tournament_id)

        if tournament.status is TournamentStatus.COMPLETED:
            raise ConflictError(
                "This tournament has already been run. Create a new tournament "
                "to run the simulation again."
            )
        if tournament.status is TournamentStatus.RUNNING:
            raise ConflictError("This tournament is already running")

        self.repository.clear_previous_run(tournament)
        tournament.status = TournamentStatus.RUNNING
        tournament.started_at = datetime.now(timezone.utc)
        tournament.error_message = None
        self.db.commit()

        try:
            result = run_tournament(
                strategy_ids=list(tournament.strategy_codes),
                rounds_per_match=tournament.rounds_per_match,
                matrix=tournament.payoff_matrix.to_domain(),
                repetitions=tournament.repetitions,
                seed=tournament.seed,
                continuation_probability=tournament.continuation_probability,
                include_self_play=tournament.include_self_play,
            )
        except Exception as exc:
            tournament.status = TournamentStatus.FAILED
            tournament.error_message = str(exc)[:1000]
            self.db.commit()
            raise

        self._persist_result(tournament, result)
        tournament.status = TournamentStatus.COMPLETED
        tournament.completed_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(tournament)
        return self.results(tournament.id)

    def _persist_result(
        self, tournament: Tournament, result: DomainTournamentResult
    ) -> None:
        matches_per_repetition = (
            len(result.matches) // result.repetitions if result.repetitions else 0
        )

        for index, match_result in enumerate(result.matches):
            repetition = (
                index // matches_per_repetition + 1 if matches_per_repetition else 1
            )
            match = TournamentMatch(
                tournament_id=tournament.id,
                sequence=index + 1,
                repetition=repetition,
                strategy_a_code=match_result.strategy_a_id,
                strategy_b_code=match_result.strategy_b_id,
                rounds_played=match_result.rounds_played,
                player_a_score=match_result.player_a.total_payoff,
                player_b_score=match_result.player_b.total_payoff,
                player_a_cooperation_count=match_result.player_a.cooperation_count,
                player_b_cooperation_count=match_result.player_b.cooperation_count,
                winner_code=match_result.winner,
            )
            self.db.add(match)
            self.db.flush()

            self.db.bulk_save_objects(
                [
                    TournamentRound(
                        match_id=match.id,
                        round_number=row.round_number,
                        player_a_action=row.player_a_action,
                        player_b_action=row.player_b_action,
                        player_a_payoff=row.player_a_payoff,
                        player_b_payoff=row.player_b_payoff,
                    )
                    for row in match_result.rounds
                ]
            )

        for ranking in result.rankings:
            self.db.add(
                TournamentResult(
                    tournament_id=tournament.id,
                    strategy_code=ranking.strategy_id,
                    rank=ranking.rank,
                    total_score=ranking.total_score,
                    average_score=ranking.average_score,
                    matches_played=ranking.matches_played,
                    rounds_played=ranking.rounds_played,
                    wins=ranking.wins,
                    draws=ranking.draws,
                    losses=ranking.losses,
                    cooperation_count=ranking.cooperation_count,
                    defection_count=ranking.defection_count,
                    cooperation_rate=ranking.cooperation_rate,
                    defection_rate=ranking.defection_rate,
                )
            )
        self.db.flush()

    # ------------------------------------------------------------- results --
    def results(self, tournament_id: uuid.UUID) -> TournamentResultsResponse:
        tournament = self.get_model(tournament_id)
        rows = self.repository.list_results(tournament_id)
        if not rows and tournament.status is not TournamentStatus.COMPLETED:
            raise ConflictError(
                "This tournament has no results yet. Run it with "
                f"POST /tournaments/{tournament_id}/run first."
            )

        rankings = [
            TournamentRankingResponse(
                rank=row.rank,
                strategy_id=row.strategy_code,
                strategy_name=_strategy_name(row.strategy_code),
                total_score=row.total_score,
                average_score=row.average_score,
                matches_played=row.matches_played,
                rounds_played=row.rounds_played,
                wins=row.wins,
                draws=row.draws,
                losses=row.losses,
                cooperation_count=row.cooperation_count,
                defection_count=row.defection_count,
                cooperation_rate=row.cooperation_rate,
                defection_rate=row.defection_rate,
            )
            for row in rows
        ]

        return TournamentResultsResponse(
            tournament_id=tournament.id,
            status=tournament.status,
            winner_strategy_id=rankings[0].strategy_id if rankings else None,
            rankings=rankings,
            matches_played=self.repository.count_matches(tournament.id),
            rounds_per_match=tournament.rounds_per_match,
            repetitions=tournament.repetitions,
            seed=tournament.seed,
        )

    def matches(self, tournament_id: uuid.UUID) -> list[TournamentMatchSummaryResponse]:
        self.get_model(tournament_id)
        return [
            TournamentMatchSummaryResponse(
                id=match.id,
                sequence=match.sequence,
                repetition=match.repetition,
                strategy_a_id=match.strategy_a_code,
                strategy_b_id=match.strategy_b_code,
                rounds_played=match.rounds_played,
                player_a_score=match.player_a_score,
                player_b_score=match.player_b_score,
                player_a_cooperation_count=match.player_a_cooperation_count,
                player_b_cooperation_count=match.player_b_cooperation_count,
                winner=match.winner_code,
            )
            for match in self.repository.list_matches(tournament_id)
        ]

    def match_detail(
        self, tournament_id: uuid.UUID, match_id: uuid.UUID
    ) -> TournamentMatchDetailResponse:
        self.get_model(tournament_id)
        match = self.repository.get_match(tournament_id, match_id)
        if match is None:
            raise NotFoundError(
                f"Match {match_id} was not found in tournament {tournament_id}"
            )

        from app.game_theory.actions import Outcome

        return TournamentMatchDetailResponse(
            id=match.id,
            sequence=match.sequence,
            repetition=match.repetition,
            strategy_a_id=match.strategy_a_code,
            strategy_b_id=match.strategy_b_code,
            rounds_played=match.rounds_played,
            player_a_score=match.player_a_score,
            player_b_score=match.player_b_score,
            player_a_cooperation_count=match.player_a_cooperation_count,
            player_b_cooperation_count=match.player_b_cooperation_count,
            winner=match.winner_code,
            rounds=[
                RoundResultResponse(
                    round_number=row.round_number,
                    player_a_action=row.player_a_action,
                    player_b_action=row.player_b_action,
                    player_a_payoff=row.player_a_payoff,
                    player_b_payoff=row.player_b_payoff,
                    outcome=Outcome.from_actions(row.player_a_action, row.player_b_action),
                )
                for row in match.rounds
            ],
        )

    # ---------------------------------------------------------- statistics --
    def statistics(self, tournament_id: uuid.UUID) -> TournamentStatisticsResponse:
        """Statistics recomputed from the stored rounds.

        Re-simulating would be faster, but reading the stored rows means the
        numbers reported always match the data the tournament actually saved.
        """
        tournament = self.get_model(tournament_id)
        matches = self.repository.list_matches(tournament_id)
        if not matches:
            raise ConflictError("This tournament has no matches yet. Run it first.")

        rebuilt = _rebuild_domain_result(tournament, matches)
        payload = tournament_statistics(rebuilt)

        return TournamentStatisticsResponse(
            tournament_id=tournament.id,
            matches_played=payload["matches_played"],
            rounds_per_match=payload["rounds_per_match"],
            repetitions=payload["repetitions"],
            score_statistics=DescriptiveStatisticsResponse.model_validate(
                payload["score_statistics"]
            ),
            cooperation_rate_statistics=DescriptiveStatisticsResponse.model_validate(
                payload["cooperation_rate_statistics"]
            ),
            outcome_frequency=payload["outcome_frequency"],
            outcome_rates=payload["outcome_rates"],
            cooperation_by_round=[
                CooperationByRound(**row) for row in payload["cooperation_by_round"]
            ],
            head_to_head=[HeadToHeadEntry(**row) for row in payload["head_to_head"]],
        )


def _strategy_name(code: str) -> str:
    try:
        return strategy_registry.metadata(code).name
    except KeyError:
        return code


def _rebuild_domain_result(
    tournament: Tournament, matches
) -> DomainTournamentResult:
    """Rebuild the in-memory result object from stored rows."""
    from app.simulation.game import RoundResult
    from app.simulation.match import MatchResult, PlayerMatchStatistics
    from app.simulation.tournament import RankedStrategy

    rebuilt_matches: list[MatchResult] = []
    for match in matches:
        rounds = [
            RoundResult(
                round_number=row.round_number,
                player_a_action=row.player_a_action,
                player_b_action=row.player_b_action,
                player_a_payoff=row.player_a_payoff,
                player_b_payoff=row.player_b_payoff,
            )
            for row in match.rounds
        ]
        played = match.rounds_played or 1
        outcome_counts: dict = {}
        for row in rounds:
            outcome_counts[row.outcome] = outcome_counts.get(row.outcome, 0) + 1

        rebuilt_matches.append(
            MatchResult(
                strategy_a_id=match.strategy_a_code,
                strategy_b_id=match.strategy_b_code,
                rounds_played=match.rounds_played,
                rounds_requested=tournament.rounds_per_match,
                continuation_probability=tournament.continuation_probability,
                seed=tournament.seed,
                rounds=rounds,
                player_a=PlayerMatchStatistics(
                    strategy_id=match.strategy_a_code,
                    total_payoff=match.player_a_score,
                    average_payoff=match.player_a_score / played,
                    cooperation_count=match.player_a_cooperation_count,
                    defection_count=match.rounds_played - match.player_a_cooperation_count,
                    cooperation_rate=match.player_a_cooperation_count / played,
                    defection_rate=1 - match.player_a_cooperation_count / played,
                ),
                player_b=PlayerMatchStatistics(
                    strategy_id=match.strategy_b_code,
                    total_payoff=match.player_b_score,
                    average_payoff=match.player_b_score / played,
                    cooperation_count=match.player_b_cooperation_count,
                    defection_count=match.rounds_played - match.player_b_cooperation_count,
                    cooperation_rate=match.player_b_cooperation_count / played,
                    defection_rate=1 - match.player_b_cooperation_count / played,
                ),
                winner=match.winner_code,
                outcome_counts=outcome_counts,
            )
        )

    rankings = [
        RankedStrategy(
            rank=row.rank,
            strategy_id=row.strategy_code,
            total_score=row.total_score,
            average_score=row.average_score,
            matches_played=row.matches_played,
            rounds_played=row.rounds_played,
            wins=row.wins,
            draws=row.draws,
            losses=row.losses,
            cooperation_count=row.cooperation_count,
            defection_count=row.defection_count,
            cooperation_rate=row.cooperation_rate,
            defection_rate=row.defection_rate,
        )
        for row in tournament.results
    ]

    return DomainTournamentResult(
        strategy_ids=list(tournament.strategy_codes),
        rounds_per_match=tournament.rounds_per_match,
        repetitions=tournament.repetitions,
        seed=tournament.seed,
        continuation_probability=tournament.continuation_probability,
        include_self_play=tournament.include_self_play,
        matches=rebuilt_matches,
        rankings=rankings,
        matrix=tournament.payoff_matrix.to_domain(),
    )

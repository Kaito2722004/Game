"""Single-match simulation, with optional persistence."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.models.tournament import (
    Tournament,
    TournamentMatch,
    TournamentRound,
    TournamentStatus,
)
from app.models.user import User
from app.repositories.tournament import TournamentRepository
from app.schemas.payoff_matrix import PayoffMatrixInput
from app.schemas.simulation import (
    MatchResultResponse,
    MatchSimulationRequest,
    PlayerMatchStatisticsResponse,
    RoundResultResponse,
)
from app.services.payoff_matrix_service import PayoffMatrixService
from app.simulation.match import MatchResult, simulate_match
from app.statistics.analysis import cumulative_scores
from app.strategies.registry import strategy_registry

STANDALONE_TOURNAMENT_NAME = "Ad hoc match simulations"


class MatchService:
    """Runs one match between two strategies.

    A persisted ad hoc match is stored against a hidden container tournament,
    so that a single set of match/round tables serves both this endpoint and
    the tournament engine.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.matrices = PayoffMatrixService(db)
        self.tournaments = TournamentRepository(db)

    def simulate(
        self, payload: MatchSimulationRequest, actor: User | None = None
    ) -> MatchResultResponse:
        strategy_registry.get(payload.strategy_a_id)
        strategy_registry.get(payload.strategy_b_id)

        matrix, stored_matrix = self.matrices.resolve_domain_matrix(
            payload.matrix, payload.payoff_matrix_id
        )

        result = simulate_match(
            strategy_a_id=payload.strategy_a_id,
            strategy_b_id=payload.strategy_b_id,
            rounds=payload.rounds,
            matrix=matrix,
            seed=payload.seed,
            continuation_probability=payload.continuation_probability,
        )

        match_id: uuid.UUID | None = None
        if payload.persist:
            match_id = self._persist(result, stored_matrix, actor)

        return self.to_response(result, matrix, match_id)

    def get(self, match_id: uuid.UUID) -> MatchResultResponse:
        """Fetch a stored match, whether ad hoc or part of a tournament."""
        match = self.db.get(TournamentMatch, match_id)
        if match is None:
            raise NotFoundError(f"Match {match_id} was not found")

        matrix = match.tournament.payoff_matrix.to_domain()
        rounds = [
            RoundResultResponse(
                round_number=row.round_number,
                player_a_action=row.player_a_action,
                player_b_action=row.player_b_action,
                player_a_payoff=row.player_a_payoff,
                player_b_payoff=row.player_b_payoff,
                outcome=_outcome_value(row.player_a_action, row.player_b_action),
            )
            for row in match.rounds
        ]

        rounds_played = match.rounds_played or 1
        cumulative_a = 0.0
        cumulative_b = 0.0
        cumulative: list[dict[str, float]] = []
        for row in rounds:
            cumulative_a += row.player_a_payoff
            cumulative_b += row.player_b_payoff
            cumulative.append(
                {
                    "round_number": row.round_number,
                    "player_a_cumulative": cumulative_a,
                    "player_b_cumulative": cumulative_b,
                }
            )

        outcome_counts = {"CC": 0, "CD": 0, "DC": 0, "DD": 0}
        for row in rounds:
            outcome_counts[row.outcome.value] += 1

        return MatchResultResponse(
            id=match.id,
            strategy_a_id=match.strategy_a_code,
            strategy_b_id=match.strategy_b_code,
            rounds_played=match.rounds_played,
            rounds_requested=match.tournament.rounds_per_match,
            continuation_probability=match.tournament.continuation_probability,
            seed=match.tournament.seed,
            player_a=PlayerMatchStatisticsResponse(
                strategy_id=match.strategy_a_code,
                total_payoff=match.player_a_score,
                average_payoff=match.player_a_score / rounds_played,
                cooperation_count=match.player_a_cooperation_count,
                defection_count=match.rounds_played - match.player_a_cooperation_count,
                cooperation_rate=match.player_a_cooperation_count / rounds_played,
                defection_rate=1 - match.player_a_cooperation_count / rounds_played,
            ),
            player_b=PlayerMatchStatisticsResponse(
                strategy_id=match.strategy_b_code,
                total_payoff=match.player_b_score,
                average_payoff=match.player_b_score / rounds_played,
                cooperation_count=match.player_b_cooperation_count,
                defection_count=match.rounds_played - match.player_b_cooperation_count,
                cooperation_rate=match.player_b_cooperation_count / rounds_played,
                defection_rate=1 - match.player_b_cooperation_count / rounds_played,
            ),
            winner=match.winner_code,
            is_draw=match.winner_code is None,
            outcome_counts=outcome_counts,
            rounds=rounds,
            cumulative_scores=cumulative,
            matrix=PayoffMatrixInput.from_domain(matrix),
        )

    @staticmethod
    def to_response(
        result: MatchResult, matrix, match_id: uuid.UUID | None = None
    ) -> MatchResultResponse:
        return MatchResultResponse(
            id=match_id,
            strategy_a_id=result.strategy_a_id,
            strategy_b_id=result.strategy_b_id,
            rounds_played=result.rounds_played,
            rounds_requested=result.rounds_requested,
            continuation_probability=result.continuation_probability,
            seed=result.seed,
            player_a=PlayerMatchStatisticsResponse(**vars(result.player_a)),
            player_b=PlayerMatchStatisticsResponse(**vars(result.player_b)),
            winner=result.winner,
            is_draw=result.is_draw,
            outcome_counts={
                outcome.value: count for outcome, count in result.outcome_counts.items()
            },
            rounds=[
                RoundResultResponse(
                    round_number=row.round_number,
                    player_a_action=row.player_a_action,
                    player_b_action=row.player_b_action,
                    player_a_payoff=row.player_a_payoff,
                    player_b_payoff=row.player_b_payoff,
                    outcome=row.outcome,
                )
                for row in result.rounds
            ],
            cumulative_scores=cumulative_scores(result),
            matrix=PayoffMatrixInput.from_domain(matrix),
        )

    def _persist(
        self, result: MatchResult, stored_matrix, actor: User | None
    ) -> uuid.UUID:
        container = self._standalone_container(stored_matrix, actor)
        sequence = self.tournaments.count_matches(container.id) + 1

        match = TournamentMatch(
            tournament_id=container.id,
            sequence=sequence,
            repetition=1,
            strategy_a_code=result.strategy_a_id,
            strategy_b_code=result.strategy_b_id,
            rounds_played=result.rounds_played,
            player_a_score=result.player_a.total_payoff,
            player_b_score=result.player_b.total_payoff,
            player_a_cooperation_count=result.player_a.cooperation_count,
            player_b_cooperation_count=result.player_b.cooperation_count,
            winner_code=result.winner,
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
                for row in result.rounds
            ]
        )
        self.db.commit()
        return match.id

    def _standalone_container(self, stored_matrix, actor: User | None) -> Tournament:
        """The hidden tournament that holds ad hoc persisted matches."""
        matrix = stored_matrix or self.matrices.get_default_model()
        container = (
            self.db.query(Tournament)
            .filter(
                Tournament.name == STANDALONE_TOURNAMENT_NAME,
                Tournament.payoff_matrix_id == matrix.id,
            )
            .first()
        )
        if container is not None:
            return container

        container = Tournament(
            name=STANDALONE_TOURNAMENT_NAME,
            description=(
                "Container for matches simulated through /matches/simulate with "
                "persist enabled. Not a real tournament."
            ),
            status=TournamentStatus.COMPLETED,
            strategy_codes=[],
            rounds_per_match=0,
            repetitions=1,
            payoff_matrix_id=matrix.id,
            created_by_id=actor.id if actor else None,
        )
        self.db.add(container)
        self.db.flush()
        return container


def _outcome_value(action_a, action_b):
    from app.game_theory.actions import Outcome

    return Outcome.from_actions(action_a, action_b)

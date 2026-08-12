"""Builds the combined activity history.

Tournaments, classroom experiments and kept one-off simulations are stored in
different tables because they mean different things. This service is the one
place that flattens them into a single time-ordered list, so the client does
not have to stitch three endpoints together and guess at the ordering.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.game_theory.actions import Action
from app.models.experiment import Experiment, HumanMatch, HumanRound, TrustSurvey
from app.models.tournament import (
    Tournament,
    TournamentMatch,
    TournamentResult,
    TournamentRound,
)
from app.schemas.history import (
    HistoryEntry,
    HistoryKind,
    HistoryResponse,
    HistoryTotals,
)
from app.services.match_service import STANDALONE_TOURNAMENT_NAME
from app.strategies.registry import strategy_registry


def _strategy_name(code: str) -> str:
    try:
        return strategy_registry.metadata(code).name
    except KeyError:
        return code


class HistoryService:
    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------ helpers --
    def _container_ids(self) -> list:
        """Ids of the hidden containers that hold ad hoc simulated matches.

        These are Tournament rows only as a storage detail, so they are
        reported as individual matches rather than as tournaments.
        """
        return list(
            self.db.execute(
                select(Tournament.id).where(Tournament.name == STANDALONE_TOURNAMENT_NAME)
            )
            .scalars()
            .all()
        )

    # ---------------------------------------------------------- assemblers --
    def _tournament_entries(self, container_ids: list) -> list[HistoryEntry]:
        statement = select(Tournament).order_by(Tournament.created_at.desc())
        if container_ids:
            statement = statement.where(Tournament.id.not_in(container_ids))

        entries: list[HistoryEntry] = []
        for tournament in self.db.execute(statement).scalars().all():
            counts = self.db.execute(
                select(
                    func.count(TournamentMatch.id),
                    func.coalesce(func.sum(TournamentMatch.rounds_played), 0),
                ).where(TournamentMatch.tournament_id == tournament.id)
            ).one()
            match_count, round_count = int(counts[0]), int(counts[1])

            totals = self.db.execute(
                select(
                    func.coalesce(func.sum(TournamentResult.cooperation_count), 0),
                    func.coalesce(func.sum(TournamentResult.defection_count), 0),
                ).where(TournamentResult.tournament_id == tournament.id)
            ).one()
            cooperations, defections = int(totals[0]), int(totals[1])
            moves = cooperations + defections

            winner = self.db.execute(
                select(TournamentResult.strategy_code)
                .where(TournamentResult.tournament_id == tournament.id)
                .order_by(TournamentResult.rank)
                .limit(1)
            ).scalar_one_or_none()

            entries.append(
                HistoryEntry(
                    id=tournament.id,
                    kind=HistoryKind.TOURNAMENT,
                    title=tournament.name,
                    subtitle="{} strategies · {} rounds per match".format(
                        len(tournament.strategy_codes), tournament.rounds_per_match
                    ),
                    status=tournament.status.value,
                    occurred_at=tournament.completed_at or tournament.created_at,
                    matches=match_count,
                    rounds=round_count,
                    cooperation_rate=cooperations / moves if moves else None,
                    headline=f"Winner: {_strategy_name(winner)}" if winner else None,
                )
            )
        return entries

    def _experiment_entries(self) -> list[HistoryEntry]:
        entries: list[HistoryEntry] = []
        experiments = (
            self.db.execute(select(Experiment).order_by(Experiment.created_at.desc()))
            .scalars()
            .all()
        )

        for experiment in experiments:
            pair_count = int(
                self.db.execute(
                    select(func.count(HumanMatch.id)).where(
                        HumanMatch.experiment_id == experiment.id
                    )
                ).scalar_one()
            )

            rows = self.db.execute(
                select(HumanRound.player_a_action, HumanRound.player_b_action).where(
                    HumanRound.experiment_id == experiment.id
                )
            ).all()

            moves = len(rows) * 2
            cooperations = sum(
                (1 if a is Action.COOPERATE else 0) + (1 if b is Action.COOPERATE else 0)
                for a, b in rows
            )

            entries.append(
                HistoryEntry(
                    id=experiment.id,
                    kind=HistoryKind.EXPERIMENT,
                    title=experiment.name,
                    subtitle="{} participants · {} pairs · {} rounds each".format(
                        len(experiment.participants), pair_count, experiment.rounds
                    ),
                    status=experiment.status.value,
                    occurred_at=experiment.completed_at
                    or experiment.started_at
                    or experiment.created_at,
                    matches=pair_count,
                    rounds=len(rows),
                    cooperation_rate=cooperations / moves if moves else None,
                    headline=(
                        "{} of {} rounds recorded".format(
                            len(rows), pair_count * experiment.rounds
                        )
                        if pair_count
                        else None
                    ),
                )
            )
        return entries

    def _simulated_match_entries(self, container_ids: list) -> list[HistoryEntry]:
        if not container_ids:
            return []

        matches = (
            self.db.execute(
                select(TournamentMatch)
                .where(TournamentMatch.tournament_id.in_(container_ids))
                .order_by(TournamentMatch.created_at.desc())
            )
            .scalars()
            .all()
        )

        entries: list[HistoryEntry] = []
        for match in matches:
            moves = match.rounds_played * 2
            cooperations = (
                match.player_a_cooperation_count + match.player_b_cooperation_count
            )
            if match.winner_code:
                headline = f"{_strategy_name(match.winner_code)} scored higher"
            else:
                headline = "Drawn"

            entries.append(
                HistoryEntry(
                    id=match.id,
                    kind=HistoryKind.SIMULATED_MATCH,
                    title="{} vs {}".format(
                        _strategy_name(match.strategy_a_code),
                        _strategy_name(match.strategy_b_code),
                    ),
                    subtitle="{:g} – {:g} over {} rounds".format(
                        match.player_a_score, match.player_b_score, match.rounds_played
                    ),
                    status="COMPLETED",
                    occurred_at=match.created_at,
                    matches=1,
                    rounds=match.rounds_played,
                    cooperation_rate=cooperations / moves if moves else None,
                    headline=headline,
                    parent_id=match.tournament_id,
                )
            )
        return entries

    # -------------------------------------------------------------- totals --
    def _totals(self, container_ids: list) -> HistoryTotals:
        def count(model, *where) -> int:
            statement = select(func.count()).select_from(model)
            for clause in where:
                statement = statement.where(clause)
            return int(self.db.execute(statement).scalar_one())

        tournaments = count(
            Tournament,
            *( [Tournament.id.not_in(container_ids)] if container_ids else [] ),
        )
        simulated = (
            count(TournamentMatch, TournamentMatch.tournament_id.in_(container_ids))
            if container_ids
            else 0
        )

        real_match_filter = (
            [TournamentMatch.tournament_id.not_in(container_ids)] if container_ids else []
        )
        tournament_matches = count(TournamentMatch, *real_match_filter)

        rounds_statement = select(func.count()).select_from(TournamentRound)
        if container_ids:
            rounds_statement = rounds_statement.where(
                TournamentRound.match_id.in_(
                    select(TournamentMatch.id).where(
                        TournamentMatch.tournament_id.not_in(container_ids)
                    )
                )
            )
        tournament_rounds = int(self.db.execute(rounds_statement).scalar_one())

        simulated_rounds = 0
        if container_ids:
            simulated_rounds = int(
                self.db.execute(
                    select(func.coalesce(func.sum(TournamentMatch.rounds_played), 0)).where(
                        TournamentMatch.tournament_id.in_(container_ids)
                    )
                ).scalar_one()
            )

        human_rounds = count(HumanRound)

        return HistoryTotals(
            tournaments=tournaments,
            tournament_matches=tournament_matches,
            tournament_rounds=tournament_rounds,
            experiments=count(Experiment),
            human_pairs=count(HumanMatch),
            human_rounds=human_rounds,
            simulated_matches=simulated,
            survey_responses=count(TrustSurvey),
            total_rounds_played=tournament_rounds + simulated_rounds + human_rounds,
        )

    # ---------------------------------------------------------------- api --
    def build(self, kind: HistoryKind | None = None, limit: int = 200) -> HistoryResponse:
        """Everything played, newest first.

        `kind` narrows to one category; the totals always describe the whole
        record so the summary does not change as you filter.
        """
        container_ids = self._container_ids()

        entries: list[HistoryEntry] = []
        if kind in (None, HistoryKind.TOURNAMENT):
            entries += self._tournament_entries(container_ids)
        if kind in (None, HistoryKind.EXPERIMENT):
            entries += self._experiment_entries()
        if kind in (None, HistoryKind.SIMULATED_MATCH):
            entries += self._simulated_match_entries(container_ids)

        entries.sort(key=lambda entry: entry.occurred_at, reverse=True)

        return HistoryResponse(totals=self._totals(container_ids), entries=entries[:limit])

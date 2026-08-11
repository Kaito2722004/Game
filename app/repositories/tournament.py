"""Tournament data access."""

from __future__ import annotations

import uuid
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.tournament import (
    Tournament,
    TournamentMatch,
    TournamentResult,
    TournamentRound,
)
from app.repositories.base import BaseRepository


class TournamentRepository(BaseRepository[Tournament]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Tournament)

    def list_matches(self, tournament_id: uuid.UUID) -> Sequence[TournamentMatch]:
        statement = (
            select(TournamentMatch)
            .where(TournamentMatch.tournament_id == tournament_id)
            .order_by(TournamentMatch.sequence)
        )
        return self.db.execute(statement).scalars().all()

    def get_match(
        self, tournament_id: uuid.UUID, match_id: uuid.UUID
    ) -> TournamentMatch | None:
        statement = (
            select(TournamentMatch)
            .where(
                TournamentMatch.tournament_id == tournament_id,
                TournamentMatch.id == match_id,
            )
            .options(selectinload(TournamentMatch.rounds))
        )
        return self.db.execute(statement).scalar_one_or_none()

    def count_matches(self, tournament_id: uuid.UUID) -> int:
        statement = (
            select(func.count())
            .select_from(TournamentMatch)
            .where(TournamentMatch.tournament_id == tournament_id)
        )
        return int(self.db.execute(statement).scalar_one())

    def list_results(self, tournament_id: uuid.UUID) -> Sequence[TournamentResult]:
        statement = (
            select(TournamentResult)
            .where(TournamentResult.tournament_id == tournament_id)
            .order_by(TournamentResult.rank, TournamentResult.strategy_code)
        )
        return self.db.execute(statement).scalars().all()

    def list_rounds_for_tournament(
        self, tournament_id: uuid.UUID
    ) -> Sequence[TournamentRound]:
        statement = (
            select(TournamentRound)
            .join(TournamentMatch, TournamentRound.match_id == TournamentMatch.id)
            .where(TournamentMatch.tournament_id == tournament_id)
            .order_by(TournamentMatch.sequence, TournamentRound.round_number)
        )
        return self.db.execute(statement).scalars().all()

    def clear_previous_run(self, tournament: Tournament) -> None:
        """Remove matches and results from an earlier attempt.

        Used when re-running a tournament that previously FAILED, so a retry
        does not accumulate duplicate rows.
        """
        for match in list(tournament.matches):
            self.db.delete(match)
        for result in list(tournament.results):
            self.db.delete(result)
        self.db.flush()

"""Payoff matrix data access."""

from __future__ import annotations

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.payoff_matrix import PayoffMatrix
from app.repositories.base import BaseRepository


class PayoffMatrixRepository(BaseRepository[PayoffMatrix]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, PayoffMatrix)

    def get_by_name(self, name: str) -> PayoffMatrix | None:
        statement = select(PayoffMatrix).where(PayoffMatrix.name == name)
        return self.db.execute(statement).scalar_one_or_none()

    def get_default(self) -> PayoffMatrix | None:
        statement = select(PayoffMatrix).where(PayoffMatrix.is_default.is_(True))
        return self.db.execute(statement).scalars().first()

    def clear_default(self, except_id=None) -> None:
        """Unset is_default everywhere else, so at most one default exists."""
        statement = update(PayoffMatrix).where(PayoffMatrix.is_default.is_(True))
        if except_id is not None:
            statement = statement.where(PayoffMatrix.id != except_id)
        self.db.execute(statement.values(is_default=False))

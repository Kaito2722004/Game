"""Generic repository over a single ORM model."""

from __future__ import annotations

import uuid
from typing import Generic, Sequence, Type, TypeVar

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Data access for one model.

    Repositories own queries and flushes. Committing is left to the service
    layer so that a single request can span several repositories atomically.
    """

    def __init__(self, db: Session, model: Type[ModelType]) -> None:
        self.db = db
        self.model = model

    def get(self, entity_id: uuid.UUID) -> ModelType | None:
        return self.db.get(self.model, entity_id)

    def list(self, limit: int = 100, offset: int = 0) -> Sequence[ModelType]:
        statement = (
            select(self.model)
            .order_by(self.model.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return self.db.execute(statement).scalars().all()

    def count(self) -> int:
        return int(self.db.execute(select(func.count()).select_from(self.model)).scalar_one())

    def add(self, entity: ModelType) -> ModelType:
        self.db.add(entity)
        self.db.flush()
        return entity

    def delete(self, entity: ModelType) -> None:
        self.db.delete(entity)
        self.db.flush()

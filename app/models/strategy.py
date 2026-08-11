"""Strategy catalogue table.

The behaviour of a strategy lives in code, in `app/strategies/`. This table
stores only its catalogue entry, so that tournaments can reference strategies
by row and the seed script can record which strategies a deployment knows
about.
"""

from __future__ import annotations

from sqlalchemy import JSON, Boolean, Enum as SAEnum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.game_theory.actions import StrategyCategory


class Strategy(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "strategies"

    code: Mapped[str] = mapped_column(String(60), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=False)
    rules: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    category: Mapped[StrategyCategory] = mapped_column(
        SAEnum(StrategyCategory, name="strategy_category"), nullable=False
    )
    is_deterministic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

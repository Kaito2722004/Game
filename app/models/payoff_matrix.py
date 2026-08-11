"""Stored payoff matrices."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Float, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.game_theory.payoff import PayoffMatrix as DomainPayoffMatrix


class PayoffMatrix(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A 2x2 payoff matrix that simulations and experiments can reference.

    The stored numbers are not assumed to form a Prisoner's Dilemma; that is
    determined by the analysis engine whenever it is asked.
    """

    __tablename__ = "payoff_matrices"

    name: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    cc_player_a: Mapped[float] = mapped_column(Float, nullable=False)
    cc_player_b: Mapped[float] = mapped_column(Float, nullable=False)
    cd_player_a: Mapped[float] = mapped_column(Float, nullable=False)
    cd_player_b: Mapped[float] = mapped_column(Float, nullable=False)
    dc_player_a: Mapped[float] = mapped_column(Float, nullable=False)
    dc_player_b: Mapped[float] = mapped_column(Float, nullable=False)
    dd_player_a: Mapped[float] = mapped_column(Float, nullable=False)
    dd_player_b: Mapped[float] = mapped_column(Float, nullable=False)

    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    created_by = relationship("User", lazy="joined")

    def to_domain(self) -> DomainPayoffMatrix:
        """Convert the row into the immutable domain value object."""
        return DomainPayoffMatrix.from_tuples(
            cc=(self.cc_player_a, self.cc_player_b),
            cd=(self.cd_player_a, self.cd_player_b),
            dc=(self.dc_player_a, self.dc_player_b),
            dd=(self.dd_player_a, self.dd_player_b),
        )

    def apply_domain(self, matrix: DomainPayoffMatrix) -> None:
        """Copy values from a domain matrix onto this row."""
        self.cc_player_a, self.cc_player_b = matrix.cc.as_tuple()
        self.cd_player_a, self.cd_player_b = matrix.cd.as_tuple()
        self.dc_player_a, self.dc_player_b = matrix.dc.as_tuple()
        self.dd_player_a, self.dd_player_b = matrix.dd.as_tuple()

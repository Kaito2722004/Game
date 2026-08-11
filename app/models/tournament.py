"""Tournament, match, round and result tables."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.game_theory.actions import Action


class TournamentStatus(str, Enum):
    """Lifecycle of a tournament.

    A tournament is created as PENDING, moves to RUNNING while its matches are
    simulated, and ends COMPLETED or FAILED. Only PENDING and FAILED
    tournaments can be run.
    """

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Tournament(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tournaments"

    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    status: Mapped[TournamentStatus] = mapped_column(
        SAEnum(TournamentStatus, name="tournament_status"),
        nullable=False,
        default=TournamentStatus.PENDING,
        index=True,
    )

    strategy_codes: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    rounds_per_match: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    repetitions: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    seed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    continuation_probability: Mapped[float | None] = mapped_column(Float, nullable=True)
    include_self_play: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    payoff_matrix_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("payoff_matrices.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    payoff_matrix = relationship("PayoffMatrix", lazy="joined")
    created_by = relationship("User", lazy="joined")
    matches = relationship(
        "TournamentMatch",
        back_populates="tournament",
        cascade="all, delete-orphan",
        order_by="TournamentMatch.sequence",
    )
    results = relationship(
        "TournamentResult",
        back_populates="tournament",
        cascade="all, delete-orphan",
        order_by="TournamentResult.rank",
    )


class TournamentMatch(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tournament_matches"
    __table_args__ = (
        Index("ix_tournament_matches_tournament_sequence", "tournament_id", "sequence"),
    )

    tournament_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("tournaments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    repetition: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    strategy_a_code: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    strategy_b_code: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    rounds_played: Mapped[int] = mapped_column(Integer, nullable=False)

    player_a_score: Mapped[float] = mapped_column(Float, nullable=False)
    player_b_score: Mapped[float] = mapped_column(Float, nullable=False)
    player_a_cooperation_count: Mapped[int] = mapped_column(Integer, nullable=False)
    player_b_cooperation_count: Mapped[int] = mapped_column(Integer, nullable=False)
    winner_code: Mapped[str | None] = mapped_column(String(60), nullable=True)

    tournament = relationship("Tournament", back_populates="matches")
    rounds = relationship(
        "TournamentRound",
        back_populates="match",
        cascade="all, delete-orphan",
        order_by="TournamentRound.round_number",
    )


class TournamentRound(UUIDPrimaryKeyMixin, Base):
    """One round of one tournament match.

    No timestamp mixin: these rows are written in bulk and their creation time
    is the parent match's.
    """

    __tablename__ = "tournament_rounds"
    __table_args__ = (
        Index("ix_tournament_rounds_match_round", "match_id", "round_number", unique=True),
    )

    match_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("tournament_matches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)
    player_a_action: Mapped[Action] = mapped_column(
        SAEnum(Action, name="action"), nullable=False
    )
    player_b_action: Mapped[Action] = mapped_column(
        SAEnum(Action, name="action"), nullable=False
    )
    player_a_payoff: Mapped[float] = mapped_column(Float, nullable=False)
    player_b_payoff: Mapped[float] = mapped_column(Float, nullable=False)

    match = relationship("TournamentMatch", back_populates="rounds")


class TournamentResult(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One strategy's final placing in a completed tournament."""

    __tablename__ = "tournament_results"
    __table_args__ = (
        Index(
            "ix_tournament_results_tournament_strategy",
            "tournament_id",
            "strategy_code",
            unique=True,
        ),
    )

    tournament_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("tournaments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    strategy_code: Mapped[str] = mapped_column(String(60), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    total_score: Mapped[float] = mapped_column(Float, nullable=False)
    average_score: Mapped[float] = mapped_column(Float, nullable=False)
    matches_played: Mapped[int] = mapped_column(Integer, nullable=False)
    rounds_played: Mapped[int] = mapped_column(Integer, nullable=False)
    wins: Mapped[int] = mapped_column(Integer, nullable=False)
    draws: Mapped[int] = mapped_column(Integer, nullable=False)
    losses: Mapped[int] = mapped_column(Integer, nullable=False)
    cooperation_count: Mapped[int] = mapped_column(Integer, nullable=False)
    defection_count: Mapped[int] = mapped_column(Integer, nullable=False)
    cooperation_rate: Mapped[float] = mapped_column(Float, nullable=False)
    defection_rate: Mapped[float] = mapped_column(Float, nullable=False)

    tournament = relationship("Tournament", back_populates="results")

"""Human classroom experiment tables."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.game_theory.actions import Action


class ExperimentStatus(str, Enum):
    """Lifecycle of a classroom experiment.

    Participants may be added while DRAFT. Starting the experiment pairs them
    and moves it to RUNNING, which is the only state in which rounds may be
    submitted. COMPLETED experiments are read-only.
    """

    DRAFT = "DRAFT"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"


class SurveyQuestionType(str, Enum):
    """The two questions in the classroom trust survey.

    EXPECTED_COOPERATION is asked before play ("how likely do you think your
    opponent is to cooperate?"), TRUST_AFTER afterwards ("how much did you
    trust your opponent?"). Both are answered on a 1-5 scale.

    This is a short project-specific survey inspired by the textbook's
    discussion of trust and suspicion. It is not a published psychometric
    instrument and must not be reported as one.
    """

    EXPECTED_COOPERATION = "EXPECTED_COOPERATION"
    TRUST_AFTER = "TRUST_AFTER"


class Experiment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "experiments"

    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    status: Mapped[ExperimentStatus] = mapped_column(
        SAEnum(ExperimentStatus, name="experiment_status"),
        nullable=False,
        default=ExperimentStatus.DRAFT,
        index=True,
    )

    rounds: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    anonymous_mode: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    trust_survey_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )

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

    payoff_matrix = relationship("PayoffMatrix", lazy="joined")
    created_by = relationship("User", lazy="joined")
    participants = relationship(
        "ExperimentParticipant",
        back_populates="experiment",
        cascade="all, delete-orphan",
        order_by="ExperimentParticipant.created_at",
    )
    matches = relationship(
        "HumanMatch",
        back_populates="experiment",
        cascade="all, delete-orphan",
    )
    surveys = relationship(
        "TrustSurvey", back_populates="experiment", cascade="all, delete-orphan"
    )


class ExperimentParticipant(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "experiment_participants"
    __table_args__ = (
        UniqueConstraint("experiment_id", "code", name="uq_participant_code_per_experiment"),
    )

    experiment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(60), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    experiment = relationship("Experiment", back_populates="participants")

    def public_label(self, anonymous: bool) -> str:
        """The name to expose: the code alone when the experiment is anonymous."""
        if anonymous or not self.display_name:
            return self.code
        return self.display_name


class HumanMatch(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A pairing of two participants for the duration of an experiment."""

    __tablename__ = "human_matches"

    experiment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    pair_number: Mapped[int] = mapped_column(Integer, nullable=False)
    participant_a_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("experiment_participants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    participant_b_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("experiment_participants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    player_a_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    player_b_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    is_complete: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    experiment = relationship("Experiment", back_populates="matches")
    participant_a = relationship("ExperimentParticipant", foreign_keys=[participant_a_id])
    participant_b = relationship("ExperimentParticipant", foreign_keys=[participant_b_id])
    rounds = relationship(
        "HumanRound",
        back_populates="match",
        cascade="all, delete-orphan",
        order_by="HumanRound.round_number",
    )


class HumanRound(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One recorded round of human play.

    Payoffs are always computed by the backend from the two actions and the
    experiment's payoff matrix. Nothing the client sends is treated as
    authoritative for scoring.
    """

    __tablename__ = "human_rounds"
    __table_args__ = (
        UniqueConstraint("match_id", "round_number", name="uq_human_round_per_match"),
        Index("ix_human_rounds_experiment_round", "experiment_id", "round_number"),
    )

    experiment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    match_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("human_matches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)

    player_a_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("experiment_participants.id", ondelete="CASCADE"),
        nullable=False,
    )
    player_b_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("experiment_participants.id", ondelete="CASCADE"),
        nullable=False,
    )
    player_a_action: Mapped[Action] = mapped_column(
        SAEnum(Action, name="action"), nullable=False
    )
    player_b_action: Mapped[Action] = mapped_column(
        SAEnum(Action, name="action"), nullable=False
    )
    player_a_payoff: Mapped[float] = mapped_column(Float, nullable=False)
    player_b_payoff: Mapped[float] = mapped_column(Float, nullable=False)

    match = relationship("HumanMatch", back_populates="rounds")


class TrustSurvey(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One answer to one trust-survey question by one participant."""

    __tablename__ = "trust_surveys"
    __table_args__ = (
        UniqueConstraint(
            "experiment_id",
            "participant_id",
            "question_type",
            name="uq_survey_answer_per_participant",
        ),
    )

    experiment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    participant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("experiment_participants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_type: Mapped[SurveyQuestionType] = mapped_column(
        SAEnum(SurveyQuestionType, name="survey_question_type"), nullable=False
    )
    score: Mapped[int] = mapped_column(Integer, nullable=False)

    experiment = relationship("Experiment", back_populates="surveys")
    participant = relationship("ExperimentParticipant", lazy="joined")

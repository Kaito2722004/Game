"""Experiment, participant, human match/round and survey data access."""

from __future__ import annotations

import uuid
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.experiment import (
    Experiment,
    ExperimentParticipant,
    HumanMatch,
    HumanRound,
    SurveyQuestionType,
    TrustSurvey,
)
from app.repositories.base import BaseRepository


class ExperimentRepository(BaseRepository[Experiment]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Experiment)

    # --- participants ------------------------------------------------------
    def list_participants(
        self, experiment_id: uuid.UUID
    ) -> Sequence[ExperimentParticipant]:
        statement = (
            select(ExperimentParticipant)
            .where(ExperimentParticipant.experiment_id == experiment_id)
            .order_by(ExperimentParticipant.created_at, ExperimentParticipant.code)
        )
        return self.db.execute(statement).scalars().all()

    def get_participant(
        self, experiment_id: uuid.UUID, participant_id: uuid.UUID
    ) -> ExperimentParticipant | None:
        statement = select(ExperimentParticipant).where(
            ExperimentParticipant.experiment_id == experiment_id,
            ExperimentParticipant.id == participant_id,
        )
        return self.db.execute(statement).scalar_one_or_none()

    def get_participant_by_code(
        self, experiment_id: uuid.UUID, code: str
    ) -> ExperimentParticipant | None:
        statement = select(ExperimentParticipant).where(
            ExperimentParticipant.experiment_id == experiment_id,
            ExperimentParticipant.code == code,
        )
        return self.db.execute(statement).scalar_one_or_none()

    def count_participants(self, experiment_id: uuid.UUID) -> int:
        statement = (
            select(func.count())
            .select_from(ExperimentParticipant)
            .where(ExperimentParticipant.experiment_id == experiment_id)
        )
        return int(self.db.execute(statement).scalar_one())

    # --- matches -----------------------------------------------------------
    def list_matches(self, experiment_id: uuid.UUID) -> Sequence[HumanMatch]:
        statement = (
            select(HumanMatch)
            .where(HumanMatch.experiment_id == experiment_id)
            .order_by(HumanMatch.pair_number)
        )
        return self.db.execute(statement).scalars().all()

    def get_match(
        self, experiment_id: uuid.UUID, match_id: uuid.UUID
    ) -> HumanMatch | None:
        statement = select(HumanMatch).where(
            HumanMatch.experiment_id == experiment_id, HumanMatch.id == match_id
        )
        return self.db.execute(statement).scalar_one_or_none()

    def count_matches(self, experiment_id: uuid.UUID) -> int:
        statement = (
            select(func.count())
            .select_from(HumanMatch)
            .where(HumanMatch.experiment_id == experiment_id)
        )
        return int(self.db.execute(statement).scalar_one())

    # --- rounds ------------------------------------------------------------
    def list_rounds(self, experiment_id: uuid.UUID) -> Sequence[HumanRound]:
        statement = (
            select(HumanRound)
            .where(HumanRound.experiment_id == experiment_id)
            .order_by(HumanRound.match_id, HumanRound.round_number)
        )
        return self.db.execute(statement).scalars().all()

    def get_round(self, match_id: uuid.UUID, round_number: int) -> HumanRound | None:
        statement = select(HumanRound).where(
            HumanRound.match_id == match_id, HumanRound.round_number == round_number
        )
        return self.db.execute(statement).scalar_one_or_none()

    def count_rounds_for_match(self, match_id: uuid.UUID) -> int:
        statement = (
            select(func.count())
            .select_from(HumanRound)
            .where(HumanRound.match_id == match_id)
        )
        return int(self.db.execute(statement).scalar_one())

    # --- surveys -----------------------------------------------------------
    def list_surveys(self, experiment_id: uuid.UUID) -> Sequence[TrustSurvey]:
        statement = (
            select(TrustSurvey)
            .where(TrustSurvey.experiment_id == experiment_id)
            .order_by(TrustSurvey.created_at)
        )
        return self.db.execute(statement).scalars().all()

    def get_survey(
        self,
        experiment_id: uuid.UUID,
        participant_id: uuid.UUID,
        question_type: SurveyQuestionType,
    ) -> TrustSurvey | None:
        statement = select(TrustSurvey).where(
            TrustSurvey.experiment_id == experiment_id,
            TrustSurvey.participant_id == participant_id,
            TrustSurvey.question_type == question_type,
        )
        return self.db.execute(statement).scalar_one_or_none()

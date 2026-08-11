"""Classroom trust survey.

A short project-specific survey: one question before play and one after, each
answered from 1 to 5. It is inspired by the textbook's discussion of trust and
suspicion in experimental settings, and is not a standardised psychological
instrument. Results are descriptive and never support a causal claim.
"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.models.experiment import TrustSurvey
from app.repositories.experiment import ExperimentRepository
from app.schemas.experiment import (
    TrustSurveyRequest,
    TrustSurveyResponse,
    TrustSurveyStatisticsResponse,
)
from app.schemas.statistics import DescriptiveStatisticsResponse
from app.services.experiment_service import ExperimentService
from app.statistics.experiment_analysis import (
    TrustSurveyRecord,
    trust_survey_statistics,
)


class SurveyService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = ExperimentRepository(db)
        self.experiments = ExperimentService(db)

    def submit(self, payload: TrustSurveyRequest) -> TrustSurveyResponse:
        experiment = self.experiments.get_model(payload.experiment_id)
        if not experiment.trust_survey_enabled:
            raise ValidationError(
                "The trust survey is disabled for this experiment",
                ["Enable trust_survey_enabled before collecting survey answers"],
            )

        participant = self.repository.get_participant(
            payload.experiment_id, payload.participant_id
        )
        if participant is None:
            raise NotFoundError(
                f"Participant {payload.participant_id} is not in experiment "
                f"{payload.experiment_id}"
            )

        existing = self.repository.get_survey(
            payload.experiment_id, payload.participant_id, payload.question_type
        )
        if existing is not None:
            raise ConflictError(
                "This participant has already answered that survey question"
            )

        survey = TrustSurvey(
            experiment_id=payload.experiment_id,
            participant_id=payload.participant_id,
            question_type=payload.question_type,
            score=payload.score,
        )
        self.db.add(survey)
        self.db.commit()
        self.db.refresh(survey)
        return TrustSurveyResponse.model_validate(survey)

    def list_for_experiment(
        self, experiment_id: uuid.UUID
    ) -> list[TrustSurveyResponse]:
        self.experiments.get_model(experiment_id)
        return [
            TrustSurveyResponse.model_validate(row)
            for row in self.repository.list_surveys(experiment_id)
        ]

    def statistics(self, experiment_id: uuid.UUID) -> TrustSurveyStatisticsResponse:
        """Survey averages, plus their correlation with observed cooperation."""
        self.experiments.get_model(experiment_id)
        surveys = [
            TrustSurveyRecord(
                participant_id=str(row.participant_id),
                question_type=row.question_type.value,
                score=row.score,
            )
            for row in self.repository.list_surveys(experiment_id)
        ]
        cooperation = self.experiments.cooperation_by_participant(experiment_id)
        payload = trust_survey_statistics(surveys, cooperation)

        return TrustSurveyStatisticsResponse(
            experiment_id=experiment_id,
            responses=payload["responses"],
            expected_cooperation_responses=payload["expected_cooperation_responses"],
            trust_after_responses=payload["trust_after_responses"],
            average_expected_cooperation=payload["average_expected_cooperation"],
            average_trust_after=payload["average_trust_after"],
            expected_cooperation_statistics=DescriptiveStatisticsResponse.model_validate(
                payload["expected_cooperation_statistics"]
            ),
            trust_after_statistics=DescriptiveStatisticsResponse.model_validate(
                payload["trust_after_statistics"]
            ),
            actual_cooperation_rate=payload["actual_cooperation_rate"],
            correlation_expected_vs_actual=payload["correlation_expected_vs_actual"],
            correlation_trust_after_vs_actual=payload["correlation_trust_after_vs_actual"],
            interpretation_note=payload["interpretation_note"],
        )

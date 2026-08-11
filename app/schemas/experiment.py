"""Schemas for the human classroom experiment and the trust survey."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.game_theory.actions import Action
from app.models.experiment import ExperimentStatus, SurveyQuestionType
from app.schemas.statistics import DescriptiveStatisticsResponse

MAX_EXPERIMENT_ROUNDS = 500


class ExperimentCreateRequest(BaseModel):
    name: str = Field(
        min_length=1, max_length=200, examples=["Game Theory Classroom Experiment"]
    )
    description: str | None = Field(default=None, max_length=1000)
    rounds: int = Field(default=10, ge=1, le=MAX_EXPERIMENT_ROUNDS)
    anonymous_mode: bool = Field(
        default=True, description="Report participants by code rather than by name"
    )
    trust_survey_enabled: bool = True
    payoff_matrix_id: uuid.UUID | None = Field(
        default=None, description="Defaults to the stored default matrix"
    )


class ExperimentUpdateRequest(BaseModel):
    """Settings may only be changed while the experiment is a DRAFT."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    rounds: int | None = Field(default=None, ge=1, le=MAX_EXPERIMENT_ROUNDS)
    anonymous_mode: bool | None = None
    trust_survey_enabled: bool | None = None


class ParticipantCreateRequest(BaseModel):
    code: str = Field(
        min_length=1,
        max_length=60,
        examples=["S01"],
        description="Unique within the experiment",
    )
    display_name: str | None = Field(default=None, max_length=200)


class ParticipantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    display_name: str | None
    created_at: datetime


class ExperimentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    status: ExperimentStatus
    rounds: int
    anonymous_mode: bool
    trust_survey_enabled: bool
    payoff_matrix_id: uuid.UUID
    participant_count: int = 0
    pair_count: int = 0
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


class HumanMatchResponse(BaseModel):
    id: uuid.UUID
    pair_number: int
    participant_a_id: uuid.UUID
    participant_b_id: uuid.UUID
    participant_a_label: str
    participant_b_label: str
    player_a_score: float
    player_b_score: float
    rounds_recorded: int
    is_complete: bool


class ExperimentStartResponse(BaseModel):
    experiment_id: uuid.UUID
    status: ExperimentStatus
    pairs: list[HumanMatchResponse]
    unpaired_participant_ids: list[uuid.UUID] = Field(
        default_factory=list,
        description="Populated when an odd number of participants was registered",
    )


class RoundSubmissionRequest(BaseModel):
    """Submit one round of human play.

    The two actions are recorded; the payoffs are computed by the backend from
    the experiment's payoff matrix.
    """

    match_id: uuid.UUID
    round_number: int = Field(ge=1, le=MAX_EXPERIMENT_ROUNDS)
    player_a_action: Action
    player_b_action: Action


class HumanRoundResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    experiment_id: uuid.UUID
    match_id: uuid.UUID
    round_number: int
    player_a_id: uuid.UUID
    player_b_id: uuid.UUID
    player_a_action: Action
    player_b_action: Action
    player_a_payoff: float
    player_b_payoff: float


class ExperimentResultsResponse(BaseModel):
    experiment_id: uuid.UUID
    status: ExperimentStatus
    rounds_configured: int
    matches: list[HumanMatchResponse]
    rounds: list[HumanRoundResponse]


class RateByRound(BaseModel):
    round_number: int
    cooperation_rate: float | None = None
    defection_rate: float | None = None
    average_payoff: float | None = None
    total_payoff: float | None = None


class ExperimentStatisticsResponse(BaseModel):
    """Every rate and average from the classroom data."""

    experiment_id: uuid.UUID
    rounds_recorded: int
    decisions_recorded: int
    cooperation_rate: float
    defection_rate: float
    mutual_cooperation_rate: float
    mutual_defection_rate: float
    cd_rate: float
    dc_rate: float
    average_payoff: float
    total_payoff: float
    payoff_statistics: DescriptiveStatisticsResponse
    outcome_frequency: dict[str, int]
    cooperation_rate_by_round: list[RateByRound]
    defection_rate_by_round: list[RateByRound]
    payoff_by_round: list[RateByRound]
    nash_prediction_cooperation_rate: float = Field(
        default=0.0,
        description=(
            "Cooperation rate predicted by the one-shot Nash equilibrium when "
            "defection is dominant for both players."
        ),
    )
    nash_prediction_applies: bool = Field(
        description=(
            "True when the experiment's matrix actually has mutual defection as "
            "its unique equilibrium, so the prediction above is meaningful."
        )
    )


# ----------------------------------------------------------------- surveys --
class TrustSurveyRequest(BaseModel):
    """One survey answer.

    A short classroom survey inspired by the textbook's discussion of trust
    and suspicion. It is not a standardised psychological instrument.
    """

    experiment_id: uuid.UUID
    participant_id: uuid.UUID
    question_type: SurveyQuestionType
    score: int = Field(ge=1, le=5, description="1 = not at all, 5 = very much")


class TrustSurveyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    experiment_id: uuid.UUID
    participant_id: uuid.UUID
    question_type: SurveyQuestionType
    score: int
    created_at: datetime


class TrustSurveyStatisticsResponse(BaseModel):
    experiment_id: uuid.UUID
    responses: int
    expected_cooperation_responses: int
    trust_after_responses: int
    average_expected_cooperation: float | None
    average_trust_after: float | None
    expected_cooperation_statistics: DescriptiveStatisticsResponse
    trust_after_statistics: DescriptiveStatisticsResponse
    actual_cooperation_rate: float
    correlation_expected_vs_actual: float | None
    correlation_trust_after_vs_actual: float | None
    interpretation_note: str

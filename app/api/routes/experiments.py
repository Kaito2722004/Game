"""Human classroom experiment endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query, status
from fastapi.responses import Response

from app.api.dependencies import DbSession, PaginationParams, TeacherUser
from app.schemas.common import ERROR_RESPONSES, APIResponse, success
from app.schemas.experiment import (
    ExperimentCreateRequest,
    ExperimentResponse,
    ExperimentResultsResponse,
    ExperimentStartResponse,
    ExperimentStatisticsResponse,
    ExperimentUpdateRequest,
    HumanRoundResponse,
    ParticipantCreateRequest,
    ParticipantResponse,
    RoundSubmissionRequest,
    TrustSurveyResponse,
    TrustSurveyStatisticsResponse,
)
from app.services.experiment_service import ExperimentService
from app.services.export_service import ExportService
from app.services.survey_service import SurveyService

router = APIRouter(prefix="/experiments", tags=["Human Experiments"])


@router.post(
    "",
    response_model=APIResponse[ExperimentResponse],
    status_code=status.HTTP_201_CREATED,
    responses=ERROR_RESPONSES,
    summary="Create a classroom experiment",
    description=(
        "Creates an experiment in DRAFT state with a number of rounds, an "
        "anonymity setting, an optional trust survey and a payoff matrix. "
        "Requires a TEACHER or ADMIN account."
    ),
)
def create_experiment(
    payload: ExperimentCreateRequest, db: DbSession, actor: TeacherUser
) -> APIResponse[ExperimentResponse]:
    return success(ExperimentService(db).create(payload, actor), "Experiment created")


@router.get(
    "",
    response_model=APIResponse[list[ExperimentResponse]],
    summary="List experiments",
)
def list_experiments(
    db: DbSession, pagination: PaginationParams
) -> APIResponse[list[ExperimentResponse]]:
    return success(
        ExperimentService(db).list(limit=pagination.limit, offset=pagination.offset)
    )


@router.get(
    "/{experiment_id}",
    response_model=APIResponse[ExperimentResponse],
    responses=ERROR_RESPONSES,
    summary="Get one experiment",
)
def get_experiment(
    experiment_id: uuid.UUID, db: DbSession
) -> APIResponse[ExperimentResponse]:
    return success(ExperimentService(db).get(experiment_id))


@router.put(
    "/{experiment_id}",
    response_model=APIResponse[ExperimentResponse],
    responses=ERROR_RESPONSES,
    summary="Update a DRAFT experiment's settings",
)
def update_experiment(
    experiment_id: uuid.UUID,
    payload: ExperimentUpdateRequest,
    db: DbSession,
    actor: TeacherUser,
) -> APIResponse[ExperimentResponse]:
    return success(ExperimentService(db).update(experiment_id, payload), "Experiment updated")


# ------------------------------------------------------------ participants --
@router.post(
    "/{experiment_id}/participants",
    response_model=APIResponse[ParticipantResponse],
    status_code=status.HTTP_201_CREATED,
    responses=ERROR_RESPONSES,
    summary="Add a participant",
    description="Only possible while the experiment is a DRAFT. Codes are unique per experiment.",
)
def add_participant(
    experiment_id: uuid.UUID,
    payload: ParticipantCreateRequest,
    db: DbSession,
    actor: TeacherUser,
) -> APIResponse[ParticipantResponse]:
    return success(
        ExperimentService(db).add_participant(experiment_id, payload), "Participant added"
    )


@router.get(
    "/{experiment_id}/participants",
    response_model=APIResponse[list[ParticipantResponse]],
    responses=ERROR_RESPONSES,
    summary="List participants",
)
def list_participants(
    experiment_id: uuid.UUID, db: DbSession
) -> APIResponse[list[ParticipantResponse]]:
    return success(ExperimentService(db).list_participants(experiment_id))


@router.delete(
    "/{experiment_id}/participants/{participant_id}",
    response_model=APIResponse[None],
    responses=ERROR_RESPONSES,
    summary="Remove a participant",
)
def remove_participant(
    experiment_id: uuid.UUID,
    participant_id: uuid.UUID,
    db: DbSession,
    actor: TeacherUser,
) -> APIResponse[None]:
    ExperimentService(db).remove_participant(experiment_id, participant_id)
    return success(None, "Participant removed")


# -------------------------------------------------------------- lifecycle --
@router.post(
    "/{experiment_id}/start",
    response_model=APIResponse[ExperimentStartResponse],
    responses=ERROR_RESPONSES,
    summary="Pair participants and open the experiment",
    description=(
        "Randomly pairs the registered participants and moves the experiment "
        "to RUNNING, after which rounds may be submitted. Pass `seed` for a "
        "reproducible pairing. With an odd number of participants, the one "
        "left over is reported in `unpaired_participant_ids`."
    ),
)
def start_experiment(
    experiment_id: uuid.UUID,
    db: DbSession,
    actor: TeacherUser,
    seed: int | None = Query(default=None, description="Seed for reproducible pairing"),
) -> APIResponse[ExperimentStartResponse]:
    return success(ExperimentService(db).start(experiment_id, seed=seed), "Experiment started")


@router.post(
    "/{experiment_id}/complete",
    response_model=APIResponse[ExperimentResponse],
    responses=ERROR_RESPONSES,
    summary="Close the experiment to further rounds",
)
def complete_experiment(
    experiment_id: uuid.UUID, db: DbSession, actor: TeacherUser
) -> APIResponse[ExperimentResponse]:
    return success(ExperimentService(db).complete(experiment_id), "Experiment completed")


# ----------------------------------------------------------------- rounds --
@router.post(
    "/{experiment_id}/rounds",
    response_model=APIResponse[HumanRoundResponse],
    status_code=status.HTTP_201_CREATED,
    responses=ERROR_RESPONSES,
    summary="Record one round of human play",
    description=(
        "Records both players' actions for one round of one pair. **Payoffs "
        "are computed by the backend** from the experiment's payoff matrix; "
        "the client does not supply them and cannot influence the score."
    ),
)
def submit_round(
    experiment_id: uuid.UUID,
    payload: RoundSubmissionRequest,
    db: DbSession,
    actor: TeacherUser,
) -> APIResponse[HumanRoundResponse]:
    return success(ExperimentService(db).submit_round(experiment_id, payload), "Round recorded")


# ---------------------------------------------------------------- results --
@router.get(
    "/{experiment_id}/results",
    response_model=APIResponse[ExperimentResultsResponse],
    responses=ERROR_RESPONSES,
    summary="Pairs and every recorded round",
)
def experiment_results(
    experiment_id: uuid.UUID, db: DbSession
) -> APIResponse[ExperimentResultsResponse]:
    return success(ExperimentService(db).results(experiment_id))


@router.get(
    "/{experiment_id}/statistics",
    response_model=APIResponse[ExperimentStatisticsResponse],
    responses=ERROR_RESPONSES,
    summary="Cooperation, defection and payoff statistics",
    description=(
        "Overall cooperation and defection rates, the four outcome rates "
        "(CC, CD, DC, DD), average and total payoff, and each of those broken "
        "down by round. Also reports whether the one-shot Nash prediction of "
        "mutual defection actually applies to this experiment's matrix."
    ),
)
def experiment_statistics(
    experiment_id: uuid.UUID, db: DbSession
) -> APIResponse[ExperimentStatisticsResponse]:
    return success(ExperimentService(db).statistics(experiment_id))


# ---------------------------------------------------------------- surveys --
@router.get(
    "/{experiment_id}/surveys/trust",
    response_model=APIResponse[list[TrustSurveyResponse]],
    responses=ERROR_RESPONSES,
    summary="All trust-survey answers for an experiment",
)
def list_trust_surveys(
    experiment_id: uuid.UUID, db: DbSession
) -> APIResponse[list[TrustSurveyResponse]]:
    return success(SurveyService(db).list_for_experiment(experiment_id))


@router.get(
    "/{experiment_id}/surveys/trust/statistics",
    response_model=APIResponse[TrustSurveyStatisticsResponse],
    responses=ERROR_RESPONSES,
    summary="Trust-survey summary and its correlation with cooperation",
    description=(
        "Average expected cooperation before play, average trust afterwards, "
        "the observed cooperation rate, and the correlation between them. The "
        "correlation is descriptive only and does not establish causation."
    ),
)
def trust_survey_statistics(
    experiment_id: uuid.UUID, db: DbSession
) -> APIResponse[TrustSurveyStatisticsResponse]:
    return success(SurveyService(db).statistics(experiment_id))


# ----------------------------------------------------------------- export --
@router.get(
    "/{experiment_id}/export/rounds.csv",
    response_class=Response,
    responses={**ERROR_RESPONSES, 200: {"content": {"text/csv": {}}}},
    summary="Download the recorded rounds as CSV",
)
def export_rounds(experiment_id: uuid.UUID, db: DbSession) -> Response:
    csv_text = ExportService(db).experiment_rounds_csv(experiment_id)
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={
            "Content-Disposition": (
                f'attachment; filename="experiment-{experiment_id}-rounds.csv"'
            )
        },
    )


@router.get(
    "/{experiment_id}/export/surveys.csv",
    response_class=Response,
    responses={**ERROR_RESPONSES, 200: {"content": {"text/csv": {}}}},
    summary="Download the survey answers as CSV",
)
def export_surveys(experiment_id: uuid.UUID, db: DbSession) -> Response:
    csv_text = ExportService(db).experiment_surveys_csv(experiment_id)
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={
            "Content-Disposition": (
                f'attachment; filename="experiment-{experiment_id}-surveys.csv"'
            )
        },
    )

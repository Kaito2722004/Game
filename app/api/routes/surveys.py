"""Trust survey submission."""

from __future__ import annotations

from fastapi import APIRouter, status

from app.api.dependencies import DbSession, TeacherUser
from app.schemas.common import ERROR_RESPONSES, APIResponse, success
from app.schemas.experiment import TrustSurveyRequest, TrustSurveyResponse
from app.services.survey_service import SurveyService

router = APIRouter(prefix="/surveys", tags=["Trust Survey"])


@router.post(
    "/trust",
    response_model=APIResponse[TrustSurveyResponse],
    status_code=status.HTTP_201_CREATED,
    responses=ERROR_RESPONSES,
    summary="Record one trust-survey answer",
    description=(
        "Stores a 1-5 answer to one of the two classroom survey questions: "
        "EXPECTED_COOPERATION before play ('how likely do you think your "
        "opponent is to cooperate?') or TRUST_AFTER afterwards ('how much did "
        "you trust your opponent?').\n\n"
        "This is a short project-specific survey inspired by the textbook's "
        "discussion of trust and suspicion. It is not a standardised "
        "psychological instrument, and its results do not establish causation."
    ),
)
def submit_trust_survey(
    payload: TrustSurveyRequest, db: DbSession, actor: TeacherUser
) -> APIResponse[TrustSurveyResponse]:
    return success(SurveyService(db).submit(payload), "Survey answer recorded")

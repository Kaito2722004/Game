"""Single-match simulation endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter

from app.api.dependencies import DbSession, OptionalUser
from app.schemas.common import ERROR_RESPONSES, APIResponse, success
from app.schemas.simulation import MatchResultResponse, MatchSimulationRequest
from app.services.match_service import MatchService

router = APIRouter(prefix="/matches", tags=["Match Simulation"])


@router.post(
    "/simulate",
    response_model=APIResponse[MatchResultResponse],
    responses=ERROR_RESPONSES,
    summary="Simulate one iterated match",
    description=(
        "Plays two strategies against each other for a fixed number of rounds "
        "and returns the full round-by-round history, both players' totals, "
        "cooperation and defection rates, outcome counts and cumulative "
        "scores.\n\n"
        "Set `seed` for a reproducible run. Set `continuation_probability` to "
        "model a repeated game whose end is uncertain: after each round "
        "another follows with that probability, with `rounds` as an upper "
        "bound. Set `persist` to store the match and get an id back."
    ),
)
def simulate_match(
    payload: MatchSimulationRequest, db: DbSession, actor: OptionalUser
) -> APIResponse[MatchResultResponse]:
    return success(MatchService(db).simulate(payload, actor))


@router.get(
    "/{match_id}",
    response_model=APIResponse[MatchResultResponse],
    responses=ERROR_RESPONSES,
    summary="Fetch a stored match",
    description="Works for persisted ad hoc matches and for tournament matches.",
)
def get_match(match_id: uuid.UUID, db: DbSession) -> APIResponse[MatchResultResponse]:
    return success(MatchService(db).get(match_id))

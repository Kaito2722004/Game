"""Game-theory analysis endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter

from app.api.dependencies import DbSession
from app.schemas.common import ERROR_RESPONSES, APIResponse, success
from app.schemas.game_theory import AnalyzeGameRequest, GameAnalysisResponse
from app.services.game_theory_service import GameTheoryService

router = APIRouter(prefix="/game-theory", tags=["Game Theory"])


@router.post(
    "/analyze",
    response_model=APIResponse[GameAnalysisResponse],
    responses=ERROR_RESPONSES,
    summary="Analyse a 2x2 payoff matrix",
    description=(
        "Computes, from the payoff numbers alone: whether the matrix meets the "
        "Prisoner's Dilemma conditions (T > R > P > S and R > (S+T)/2), the "
        "values of T, R, P and S for each player, each player's dominant "
        "action if one exists, every pure-strategy Nash equilibrium, which "
        "outcomes are Pareto-optimal and which Pareto-inferior, and whether "
        "mutual cooperation Pareto-dominates mutual defection.\n\n"
        "Nothing is hard-coded: a matrix that is not a Prisoner's Dilemma "
        "produces a correspondingly different analysis."
    ),
)
def analyze(payload: AnalyzeGameRequest, db: DbSession) -> APIResponse[GameAnalysisResponse]:
    return success(GameTheoryService(db).analyse(payload))


@router.get(
    "/analyze/{payoff_matrix_id}",
    response_model=APIResponse[GameAnalysisResponse],
    responses=ERROR_RESPONSES,
    summary="Analyse a stored payoff matrix",
)
def analyze_stored(
    payoff_matrix_id: uuid.UUID, db: DbSession
) -> APIResponse[GameAnalysisResponse]:
    return success(GameTheoryService(db).analyse_matrix_id(payoff_matrix_id))

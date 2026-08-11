"""Tournament endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, status
from fastapi.responses import Response

from app.api.dependencies import DbSession, PaginationParams, TeacherUser
from app.schemas.common import ERROR_RESPONSES, APIResponse, success
from app.schemas.simulation import (
    TournamentCreateRequest,
    TournamentMatchDetailResponse,
    TournamentMatchSummaryResponse,
    TournamentResponse,
    TournamentResultsResponse,
)
from app.schemas.statistics import TournamentStatisticsResponse
from app.services.export_service import ExportService
from app.services.tournament_service import TournamentService

router = APIRouter(prefix="/tournaments", tags=["Tournaments"])


@router.post(
    "",
    response_model=APIResponse[TournamentResponse],
    status_code=status.HTTP_201_CREATED,
    responses=ERROR_RESPONSES,
    summary="Create a tournament",
    description=(
        "Registers a round-robin tournament in PENDING state. The simulation "
        "is not run until POST /tournaments/{id}/run.\n\n"
        "The strategy list, rounds per match, payoff matrix, repetitions, "
        "random seed, continuation probability and self-play are all "
        "configurable. Requires a TEACHER or ADMIN account."
    ),
)
def create_tournament(
    payload: TournamentCreateRequest, db: DbSession, actor: TeacherUser
) -> APIResponse[TournamentResponse]:
    return success(TournamentService(db).create(payload, actor), "Tournament created")


@router.get(
    "",
    response_model=APIResponse[list[TournamentResponse]],
    summary="List tournaments",
)
def list_tournaments(
    db: DbSession, pagination: PaginationParams
) -> APIResponse[list[TournamentResponse]]:
    return success(
        TournamentService(db).list(limit=pagination.limit, offset=pagination.offset)
    )


@router.get(
    "/{tournament_id}",
    response_model=APIResponse[TournamentResponse],
    responses=ERROR_RESPONSES,
    summary="Get one tournament",
)
def get_tournament(
    tournament_id: uuid.UUID, db: DbSession
) -> APIResponse[TournamentResponse]:
    return success(TournamentService(db).get(tournament_id))


@router.post(
    "/{tournament_id}/run",
    response_model=APIResponse[TournamentResultsResponse],
    responses=ERROR_RESPONSES,
    summary="Run the tournament and return the final table",
    description=(
        "Simulates every pairing, stores every match and round, computes the "
        "ranking and marks the tournament COMPLETED.\n\n"
        "A tournament that has already completed cannot be re-run: its stored "
        "results are the evidence behind a report and must not change. Create "
        "a new tournament instead.\n\n"
        "The ranking is whatever the simulation produces. No expected ordering "
        "is built into the software."
    ),
)
def run_tournament(
    tournament_id: uuid.UUID, db: DbSession, actor: TeacherUser
) -> APIResponse[TournamentResultsResponse]:
    return success(TournamentService(db).run(tournament_id), "Tournament completed")


@router.get(
    "/{tournament_id}/results",
    response_model=APIResponse[TournamentResultsResponse],
    responses=ERROR_RESPONSES,
    summary="Final ranking table",
)
def tournament_results(
    tournament_id: uuid.UUID, db: DbSession
) -> APIResponse[TournamentResultsResponse]:
    return success(TournamentService(db).results(tournament_id))


@router.get(
    "/{tournament_id}/matches",
    response_model=APIResponse[list[TournamentMatchSummaryResponse]],
    responses=ERROR_RESPONSES,
    summary="Every match in the tournament",
)
def tournament_matches(
    tournament_id: uuid.UUID, db: DbSession
) -> APIResponse[list[TournamentMatchSummaryResponse]]:
    return success(TournamentService(db).matches(tournament_id))


@router.get(
    "/{tournament_id}/matches/{match_id}",
    response_model=APIResponse[TournamentMatchDetailResponse],
    responses=ERROR_RESPONSES,
    summary="One match, with its full round history",
)
def tournament_match_detail(
    tournament_id: uuid.UUID, match_id: uuid.UUID, db: DbSession
) -> APIResponse[TournamentMatchDetailResponse]:
    return success(TournamentService(db).match_detail(tournament_id, match_id))


@router.get(
    "/{tournament_id}/statistics",
    response_model=APIResponse[TournamentStatisticsResponse],
    responses=ERROR_RESPONSES,
    summary="Statistics for a completed tournament",
    description=(
        "Mean, median and standard deviation of scores and cooperation rates, "
        "outcome frequencies, cooperation by round, and the head-to-head "
        "average payoff for every ordered pair of strategies."
    ),
)
def tournament_statistics(
    tournament_id: uuid.UUID, db: DbSession
) -> APIResponse[TournamentStatisticsResponse]:
    return success(TournamentService(db).statistics(tournament_id))


@router.get(
    "/{tournament_id}/export/results.csv",
    response_class=Response,
    responses={**ERROR_RESPONSES, 200: {"content": {"text/csv": {}}}},
    summary="Download the ranking table as CSV",
)
def export_results(tournament_id: uuid.UUID, db: DbSession) -> Response:
    csv_text = ExportService(db).tournament_results_csv(tournament_id)
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={
            "Content-Disposition": (
                f'attachment; filename="tournament-{tournament_id}-results.csv"'
            )
        },
    )


@router.get(
    "/{tournament_id}/export/rounds.csv",
    response_class=Response,
    responses={**ERROR_RESPONSES, 200: {"content": {"text/csv": {}}}},
    summary="Download every round as CSV",
)
def export_rounds(tournament_id: uuid.UUID, db: DbSession) -> Response:
    csv_text = ExportService(db).tournament_rounds_csv(tournament_id)
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={
            "Content-Disposition": (
                f'attachment; filename="tournament-{tournament_id}-rounds.csv"'
            )
        },
    )

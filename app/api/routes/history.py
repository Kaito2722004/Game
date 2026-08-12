"""Combined activity history."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.dependencies import DbSession
from app.schemas.common import ERROR_RESPONSES, APIResponse, success
from app.schemas.history import HistoryKind, HistoryResponse
from app.services.history_service import HistoryService

router = APIRouter(prefix="/history", tags=["History"])


@router.get(
    "",
    response_model=APIResponse[HistoryResponse],
    responses=ERROR_RESPONSES,
    summary="Everything that has been played, in one list",
    description=(
        "Tournaments, classroom experiments and kept one-off simulated matches "
        "flattened into a single list ordered newest first, together with "
        "totals across the whole record.\n\n"
        "The totals always describe everything, so they do not change when "
        "`kind` narrows the list. Readable without signing in."
    ),
)
def get_history(
    db: DbSession,
    kind: HistoryKind | None = Query(
        default=None, description="Show only one category of activity"
    ),
    limit: int = Query(default=200, ge=1, le=1000),
) -> APIResponse[HistoryResponse]:
    return success(HistoryService(db).build(kind=kind, limit=limit))

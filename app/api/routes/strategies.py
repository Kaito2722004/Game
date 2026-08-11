"""Strategy catalogue endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.common import ERROR_RESPONSES, APIResponse, success
from app.schemas.simulation import StrategyResponse
from app.strategies.registry import strategy_registry

router = APIRouter(prefix="/strategies", tags=["Strategies"])


def _to_response(metadata) -> StrategyResponse:
    return StrategyResponse(
        id=metadata.id,
        name=metadata.name,
        description=metadata.description,
        rules=list(metadata.rules),
        category=metadata.category,
        is_deterministic=metadata.is_deterministic,
    )


@router.get(
    "",
    response_model=APIResponse[list[StrategyResponse]],
    summary="List every available strategy",
    description=(
        "Returns the strategies the simulation engine can run, with their "
        "rules and metadata. The list comes from the strategy registry, so a "
        "newly registered strategy appears here without any change to this "
        "endpoint."
    ),
)
def list_strategies() -> APIResponse[list[StrategyResponse]]:
    return success([_to_response(meta) for meta in strategy_registry.all_metadata()])


@router.get(
    "/{strategy_id}",
    response_model=APIResponse[StrategyResponse],
    responses=ERROR_RESPONSES,
    summary="Get one strategy by id",
)
def get_strategy(strategy_id: str) -> APIResponse[StrategyResponse]:
    return success(_to_response(strategy_registry.metadata(strategy_id)))

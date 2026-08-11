"""The response envelope shared by every endpoint."""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standard success envelope.

    Every successful response has the same shape, so the frontend can unwrap
    `data` without special-casing endpoints.
    """

    success: bool = True
    data: T | None = None
    message: str | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"success": True, "data": {}, "message": None}
        }
    )


class ErrorResponse(BaseModel):
    """Standard error envelope, documented for Swagger."""

    success: bool = False
    data: None = None
    message: str = Field(examples=["Validation failed"])
    errors: list[Any] = Field(default_factory=list)


def success(data: T, message: str | None = None) -> APIResponse[T]:
    """Wrap a payload in the success envelope."""
    return APIResponse[T](success=True, data=data, message=message)


class PaginationMeta(BaseModel):
    total: int
    limit: int
    offset: int


class PaginatedData(BaseModel, Generic[T]):
    items: list[T]
    pagination: PaginationMeta


ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {"model": ErrorResponse, "description": "Bad request"},
    401: {"model": ErrorResponse, "description": "Not authenticated"},
    403: {"model": ErrorResponse, "description": "Not permitted"},
    404: {"model": ErrorResponse, "description": "Not found"},
    409: {"model": ErrorResponse, "description": "Conflict"},
    422: {"model": ErrorResponse, "description": "Validation failed"},
}

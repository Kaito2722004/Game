"""Application exceptions and the handlers that turn them into responses.

Every error leaves the API in the same envelope as a success:

    {"success": false, "data": null, "message": "...", "errors": [...]}
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.simulation.match import SimulationError
from app.strategies.registry import UnknownStrategyError


class AppError(Exception):
    """Base class for errors this application raises deliberately."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    default_message: str = "Request could not be processed"

    def __init__(
        self, message: str | None = None, errors: list[str] | None = None
    ) -> None:
        self.message = message or self.default_message
        self.errors = errors or []
        super().__init__(self.message)


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    default_message = "Resource not found"


class ConflictError(AppError):
    status_code = status.HTTP_409_CONFLICT
    default_message = "Resource conflict"


class ValidationError(AppError):
    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    default_message = "Validation failed"


class BadRequestError(AppError):
    status_code = status.HTTP_400_BAD_REQUEST
    default_message = "Bad request"


class UnauthorizedError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_message = "Not authenticated"


class ForbiddenError(AppError):
    status_code = status.HTTP_403_FORBIDDEN
    default_message = "Not permitted"


def error_response(
    status_code: int,
    message: str,
    errors: list[Any] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    """Build the standard error envelope."""
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "data": None,
            "message": message,
            "errors": errors or [],
        },
        headers=headers,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Attach every handler to the application."""

    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError) -> JSONResponse:
        headers = (
            {"WWW-Authenticate": "Bearer"}
            if isinstance(exc, UnauthorizedError)
            else None
        )
        return error_response(exc.status_code, exc.message, exc.errors, headers)

    @app.exception_handler(UnknownStrategyError)
    async def _unknown_strategy(_: Request, exc: UnknownStrategyError) -> JSONResponse:
        return error_response(
            status.HTTP_404_NOT_FOUND,
            f"Unknown strategy '{exc.strategy_id}'",
            [f"Available strategies: {', '.join(exc.available)}"],
        )

    @app.exception_handler(SimulationError)
    async def _simulation_error(_: Request, exc: SimulationError) -> JSONResponse:
        return error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "Validation failed", [str(exc)]
        )

    @app.exception_handler(RequestValidationError)
    async def _request_validation(
        _: Request, exc: RequestValidationError
    ) -> JSONResponse:
        details = [
            {
                "field": ".".join(str(part) for part in error.get("loc", [])[1:])
                or "body",
                "message": error.get("msg", "invalid value"),
                "type": error.get("type", "value_error"),
            }
            for error in exc.errors()
        ]
        return error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "Validation failed", details
        )

    @app.exception_handler(IntegrityError)
    async def _integrity_error(_: Request, exc: IntegrityError) -> JSONResponse:
        return error_response(
            status.HTTP_409_CONFLICT,
            "Resource conflict",
            ["The operation violated a database constraint."],
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_exception(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        headers = dict(exc.headers) if exc.headers else None
        return error_response(exc.status_code, str(exc.detail), headers=headers)

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception) -> JSONResponse:
        # The message stays generic; the traceback goes to the server log.
        return error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal server error"
        )

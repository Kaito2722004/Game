"""Authentication endpoints."""

from __future__ import annotations

from fastapi import APIRouter, status

from app.api.dependencies import CurrentUser, DbSession, OptionalUser
from app.schemas.auth import (
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.schemas.common import ERROR_RESPONSES, APIResponse, success
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=APIResponse[TokenResponse],
    status_code=status.HTTP_201_CREATED,
    responses=ERROR_RESPONSES,
    summary="Register a new account",
    description=(
        "Creates an account and returns an access token. Self-registration "
        "always creates a STUDENT; only an authenticated administrator may "
        "create TEACHER or ADMIN accounts."
    ),
)
def register(
    payload: UserRegisterRequest, db: DbSession, actor: OptionalUser
) -> APIResponse[TokenResponse]:
    token = AuthService(db).register(payload, actor=actor)
    return success(token, "Account created")


@router.post(
    "/login",
    response_model=APIResponse[TokenResponse],
    responses=ERROR_RESPONSES,
    summary="Log in and receive a JWT",
    description="Exchanges an email and password for a bearer token.",
)
def login(payload: UserLoginRequest, db: DbSession) -> APIResponse[TokenResponse]:
    return success(AuthService(db).login(payload), "Signed in")


@router.get(
    "/me",
    response_model=APIResponse[UserResponse],
    responses=ERROR_RESPONSES,
    summary="Current authenticated user",
)
def me(user: CurrentUser) -> APIResponse[UserResponse]:
    return success(UserResponse.model_validate(user))

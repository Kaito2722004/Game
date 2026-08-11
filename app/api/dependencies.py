"""Shared FastAPI dependencies: database session, current user, role guards."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.errors import ForbiddenError, UnauthorizedError
from app.core.security import TokenError, decode_access_token
from app.database.session import get_db
from app.models.user import User, UserRole
from app.repositories.user import UserRepository

bearer_scheme = HTTPBearer(auto_error=False, description="JWT from /auth/login")

DbSession = Annotated[Session, Depends(get_db)]
Credentials = Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)]


def get_current_user(db: DbSession, credentials: Credentials) -> User:
    """Resolve the authenticated user, or raise 401."""
    if credentials is None or not credentials.credentials:
        raise UnauthorizedError("Not authenticated")

    try:
        payload = decode_access_token(credentials.credentials)
    except TokenError as exc:
        raise UnauthorizedError(str(exc)) from exc

    try:
        user_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError) as exc:
        raise UnauthorizedError("Token subject is not a valid user id") from exc

    user = UserRepository(db).get(user_id)
    if user is None:
        raise UnauthorizedError("The account for this token no longer exists")
    if not user.is_active:
        raise ForbiddenError("This account is disabled")
    return user


def get_optional_user(db: DbSession, credentials: Credentials) -> User | None:
    """The authenticated user if a valid token was sent, otherwise None.

    Used by endpoints that are public but behave differently for a signed-in
    caller, such as registration granting elevated roles only to admins.
    """
    if credentials is None or not credentials.credentials:
        return None
    try:
        return get_current_user(db, credentials)
    except (UnauthorizedError, ForbiddenError):
        return None


CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[User | None, Depends(get_optional_user)]


def require_roles(*roles: UserRole):
    """Build a dependency that admits only the given roles."""

    allowed = set(roles)

    def _dependency(user: CurrentUser) -> User:
        if user.role not in allowed:
            raise ForbiddenError(
                "This operation requires one of these roles: "
                + ", ".join(sorted(role.value for role in allowed))
            )
        return user

    return _dependency


require_admin = require_roles(UserRole.ADMIN)
require_teacher = require_roles(UserRole.ADMIN, UserRole.TEACHER)

AdminUser = Annotated[User, Depends(require_admin)]
TeacherUser = Annotated[User, Depends(require_teacher)]


class Pagination:
    """Standard limit/offset pagination."""

    def __init__(
        self,
        limit: Annotated[int, Query(ge=1, le=500)] = 100,
        offset: Annotated[int, Query(ge=0)] = 0,
    ) -> None:
        self.limit = limit
        self.offset = offset


PaginationParams = Annotated[Pagination, Depends(Pagination)]

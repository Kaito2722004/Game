"""Registration, login and current-user lookup."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import ConflictError, ForbiddenError, UnauthorizedError
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User, UserRole
from app.repositories.user import UserRepository
from app.schemas.auth import (
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)

    def register(
        self, payload: UserRegisterRequest, actor: User | None = None
    ) -> TokenResponse:
        """Create an account and return a token for it.

        Self-registration always produces a STUDENT. Only an authenticated
        admin may create TEACHER or ADMIN accounts, so nobody can grant
        themselves privileges by editing the request body.
        """
        if self.users.email_exists(payload.email):
            raise ConflictError("An account with that email already exists")

        requested_role = payload.role
        if requested_role is not UserRole.STUDENT:
            if actor is None or not actor.is_admin:
                raise ForbiddenError(
                    "Only an administrator may create TEACHER or ADMIN accounts"
                )

        user = User(
            email=payload.email.strip().lower(),
            full_name=payload.full_name.strip(),
            hashed_password=hash_password(payload.password),
            role=requested_role,
            is_active=True,
        )
        self.users.add(user)
        self.db.commit()
        self.db.refresh(user)
        return self._token_for(user)

    def login(self, payload: UserLoginRequest) -> TokenResponse:
        """Authenticate by email and password.

        A wrong email and a wrong password produce the same error, so the
        endpoint does not reveal which accounts exist.
        """
        user = self.users.get_by_email(payload.email)
        if user is None or not verify_password(payload.password, user.hashed_password):
            raise UnauthorizedError("Incorrect email or password")
        if not user.is_active:
            raise ForbiddenError("This account is disabled")
        return self._token_for(user)

    def get_user(self, user_id: uuid.UUID) -> User | None:
        return self.users.get(user_id)

    def _token_for(self, user: User) -> TokenResponse:
        token = create_access_token(subject=str(user.id), role=user.role.value)
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            user=UserResponse.model_validate(user),
        )

"""Password hashing and JWT creation/verification."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ACCESS_TOKEN_TYPE = "access"


class TokenError(Exception):
    """Raised when a token cannot be decoded or is not the expected type."""


def hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt."""
    # bcrypt silently truncates beyond 72 bytes; rejecting is clearer than
    # letting two different long passwords authenticate the same account.
    if len(password.encode("utf-8")) > 72:
        raise ValueError("password must not exceed 72 bytes")
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a plaintext password against a stored hash."""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except ValueError:
        return False


def create_access_token(
    subject: str,
    role: str,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Issue a signed JWT for `subject` (the user id)."""
    expire_at = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "type": ACCESS_TOKEN_TYPE,
        "exp": expire_at,
        "iat": datetime.now(timezone.utc),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT, raising TokenError if it is not usable."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError as exc:
        raise TokenError("could not validate credentials") from exc

    if payload.get("type") != ACCESS_TOKEN_TYPE:
        raise TokenError("token is not an access token")
    if not payload.get("sub"):
        raise TokenError("token has no subject")
    return payload

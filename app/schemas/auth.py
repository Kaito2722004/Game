"""Authentication and user schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class UserRegisterRequest(BaseModel):
    """Registration payload.

    New accounts default to STUDENT. Requesting ADMIN or TEACHER is only
    honoured when the caller is an authenticated admin.
    """

    email: EmailStr = Field(examples=["teacher@example.com"])
    full_name: str = Field(min_length=1, max_length=255, examples=["A. Teacher"])
    password: str = Field(min_length=8, max_length=72, examples=["a-strong-password"])
    role: UserRole = Field(default=UserRole.STUDENT)


class UserLoginRequest(BaseModel):
    email: EmailStr = Field(examples=["teacher@example.com"])
    password: str = Field(min_length=1, max_length=72)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    user: UserResponse

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: Literal["student", "institution_admin", "admin"]


class SignupResponse(BaseModel):
    user_id: UUID
    email: str
    role: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    expires_in: int
    token_type: str = "Bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    user_id: UUID
    email: str
    role: str
    created_at: datetime


class LoginResponse(TokenResponse):
    """Login returns tokens plus the current user so the client can skip GET /auth/me."""

    user: UserResponse

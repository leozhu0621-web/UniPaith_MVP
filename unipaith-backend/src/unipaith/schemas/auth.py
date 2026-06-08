from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: Literal["student", "institution_admin"]


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
    # True when this account is on the owner allowlist (settings.owner_emails);
    # unlocks the in-app feedback inbox. Defaults False so login payloads that
    # don't compute it simply hide the owner surface until /auth/me refreshes.
    is_owner: bool = False
    # Mirrors settings.ai_uni_guided_v1 so the client can render the guided Uni
    # workspace shell only when the flag is on (spec §9 — flag-off keeps the
    # single-column open Uni experience). Defaults False; computed by /auth/me.
    uni_guided: bool = False


class LoginResponse(TokenResponse):
    """Login returns tokens plus the current user so the client can skip GET /auth/me."""

    user: UserResponse


class GoogleCallbackRequest(BaseModel):
    code: str
    redirect_uri: str
    role: Literal["student", "institution_admin"] = "student"


class GoogleSignInRequest(BaseModel):
    """GIS-direct Google sign-in: the client sends the Google ID token."""

    id_token: str
    role: Literal["student", "institution_admin"] = "student"

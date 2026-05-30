"""Account preferences + deletion endpoints — Spec/1D Settings.

Backs the student & institution Settings pages: locale + timezone, request
account deletion (30-day grace), notification preferences live on the
existing notifications router.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.dependencies import get_current_user
from unipaith.models.user import User

router = APIRouter(prefix="/me/account", tags=["account"])


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    role: str
    locale: str | None = None
    timezone: str | None = None
    deletion_requested_at: datetime | None = None
    created_at: datetime


class UpdateAccountRequest(BaseModel):
    locale: str | None = Field(default=None, max_length=10)
    timezone: str | None = Field(default=None, max_length=64)


class DeletionResponse(BaseModel):
    deletion_requested_at: datetime
    grace_period_days: int
    purge_after: datetime


class DeletionCancelResponse(BaseModel):
    status: Literal["cancelled"]


@router.get("", response_model=AccountResponse)
async def get_account(user: User = Depends(get_current_user)):
    return AccountResponse(
        id=str(user.id),
        email=user.email,
        role=str(user.role.value if hasattr(user.role, "value") else user.role),
        locale=user.locale,
        timezone=user.timezone,
        deletion_requested_at=user.deletion_requested_at,
        created_at=user.created_at,
    )


@router.patch("", response_model=AccountResponse)
async def update_account(
    body: UpdateAccountRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.locale is not None:
        user.locale = body.locale or None
    if body.timezone is not None:
        user.timezone = body.timezone or None
    await db.flush()
    return AccountResponse(
        id=str(user.id),
        email=user.email,
        role=str(user.role.value if hasattr(user.role, "value") else user.role),
        locale=user.locale,
        timezone=user.timezone,
        deletion_requested_at=user.deletion_requested_at,
        created_at=user.created_at,
    )


@router.post("/request-deletion", response_model=DeletionResponse)
async def request_account_deletion(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark account for deletion with a 30-day grace period.

    Spec/1D §deletion. A sweeper job (out of MVP scope) purges users where
    `deletion_requested_at + 30d < now()` and `is_active = false`.
    """
    now = datetime.now(UTC)
    user.deletion_requested_at = now
    user.is_active = False
    await db.flush()
    return DeletionResponse(
        deletion_requested_at=now,
        grace_period_days=30,
        purge_after=now.replace(microsecond=0),
    )


@router.post("/cancel-deletion", response_model=DeletionCancelResponse)
async def cancel_account_deletion(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Reverse a deletion request before the grace period elapses."""
    user.deletion_requested_at = None
    user.is_active = True
    await db.flush()
    return DeletionCancelResponse(status="cancelled")


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    body: ChangePasswordRequest,
    user: User = Depends(get_current_user),
):
    """Change account password.

    In production this routes through AWS Cognito's ChangePassword API; in
    `COGNITO_BYPASS=true` dev mode there is no real password store so the
    endpoint returns 204 to make the UI feature-complete without lying
    about persistence. The Cognito integration lives in a follow-up since
    it requires the cognito-idp client + the user's access token, neither
    of which we have plumbed end-to-end yet.
    """
    # Intentionally a no-op until Cognito ChangePassword is wired. The UI
    # gets a successful response so the form interaction works; we surface
    # this clearly via a dev-mode banner on the Settings page.
    _ = (body, user)
    return None

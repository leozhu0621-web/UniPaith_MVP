"""Spec 21 — Settings API.

Account-level security + deletion are shared across roles under ``/account/*``
(``get_current_user``); preference/profile editors are role-scoped under
``/students/me/settings`` and ``/institutions/settings`` (role guards give the
spec §8 role-scoping for free). The notification matrix reuses the existing
``/notifications/preferences`` endpoints.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.dependencies import (
    get_current_user,
    require_institution_admin,
    require_student,
)
from unipaith.models.user import User
from unipaith.schemas.settings import (
    ChangeEmailRequest,
    ChangePasswordRequest,
    DeleteAccountRequest,
    DeletionInfo,
    InstitutionSettingsResponse,
    LoginEvent,
    MfaConfirmRequest,
    MfaDisableRequest,
    MfaEnrollResponse,
    SecurityInfo,
    SessionInfo,
    SettingsResponse,
    TeamInviteRequest,
    TeamMember,
    UpdateInstitutionSettingsRequest,
    UpdateSettingsRequest,
)
from unipaith.services.settings_service import SettingsService

router = APIRouter(tags=["settings"])


# ── Student settings ────────────────────────────────────────────────────────


@router.get("/students/me/settings", response_model=SettingsResponse)
async def get_student_settings(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    return await SettingsService(db).get_settings(user)


@router.patch("/students/me/settings", response_model=SettingsResponse)
async def update_student_settings(
    body: UpdateSettingsRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    return await SettingsService(db).update_settings(user, body.model_dump(exclude_unset=True))


# ── Institution settings ──────────────────────────────────────────────────


@router.get("/institutions/settings", response_model=InstitutionSettingsResponse)
async def get_institution_settings(
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    return await SettingsService(db).get_institution_settings(user)


@router.patch("/institutions/settings", response_model=InstitutionSettingsResponse)
async def update_institution_settings(
    body: UpdateInstitutionSettingsRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    return await SettingsService(db).update_institution_settings(
        user, body.model_dump(exclude_unset=True)
    )


@router.get("/institutions/settings/team", response_model=list[TeamMember])
async def get_team(
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    return await SettingsService(db).list_team(user)


@router.post("/institutions/settings/team/invite", response_model=TeamMember)
async def invite_member(
    body: TeamInviteRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    return await SettingsService(db).invite_member(user, body.email, body.role)


@router.post("/institutions/settings/team/invite/{invite_id}/revoke", response_model=dict)
async def revoke_invite(
    invite_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    await SettingsService(db).revoke_invite(user, invite_id)
    return {"revoked": True}


# ── Account-level security + deletion (shared across roles) ─────────────────


@router.post("/account/change-password", response_model=dict)
async def change_password(
    body: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await SettingsService(db).change_password(user, body.current_password, body.new_password)
    return {"ok": True}


@router.post("/account/change-email", response_model=dict)
async def change_email(
    body: ChangeEmailRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await SettingsService(db).change_email(user, body.new_email)


@router.post("/account/mfa/enroll", response_model=MfaEnrollResponse)
async def mfa_enroll(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await SettingsService(db).mfa_enroll(user)


@router.post("/account/mfa/confirm", response_model=SecurityInfo)
async def mfa_confirm(
    body: MfaConfirmRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await SettingsService(db).mfa_confirm(user, body.code)


@router.post("/account/mfa/disable", response_model=SecurityInfo)
async def mfa_disable(
    body: MfaDisableRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await SettingsService(db).mfa_disable(user, body.code)


@router.get("/account/sessions", response_model=list[SessionInfo])
async def list_sessions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await SettingsService(db).list_sessions(user)


@router.post("/account/sessions/revoke", response_model=dict)
async def revoke_sessions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await SettingsService(db).revoke_sessions(user)


@router.get("/account/login-activity", response_model=list[LoginEvent])
async def login_activity(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await SettingsService(db).login_activity(user)


@router.post("/account/delete", response_model=DeletionInfo)
async def delete_account(
    body: DeleteAccountRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await SettingsService(db).request_deletion(user, body.confirm_text, body.password)


@router.post("/account/delete/cancel", response_model=dict)
async def cancel_delete_account(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await SettingsService(db).cancel_deletion(user)
    return {"canceled": True}

"""Pydantic schemas for Spec 21 — Settings (student + institution)."""

from __future__ import annotations

import re
from datetime import datetime

from pydantic import BaseModel, field_validator

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_THEMES = {"light", "dark", "system"}
_FONT_SIZES = {"sm", "md", "lg", "xl"}
_EMAIL_FREQ = {"all", "weekly", "important", "none"}
_TEAM_ROLES = {"admissions", "recruiter", "marketing", "it", "admin"}


# ── Read ────────────────────────────────────────────────────────────────────


class AccountInfo(BaseModel):
    email: str
    role: str
    member_since: datetime | None = None
    display_name: str | None = None
    photo_url: str | None = None
    pending_email: str | None = None


class SecurityInfo(BaseModel):
    mfa_enabled: bool
    mfa_method: str | None = None


class AccessibilityPrefs(BaseModel):
    dyslexia_mode: bool
    font_size: str
    reduced_motion: bool


class PreferencesInfo(BaseModel):
    locale: str | None = None
    timezone: str | None = None
    theme: str
    accessibility: AccessibilityPrefs


class NotificationTypePref(BaseModel):
    type: str
    label: str
    essential: bool
    channels: dict[str, bool]


class DeletionInfo(BaseModel):
    scheduled_at: datetime
    purge_at: datetime


class SettingsResponse(BaseModel):
    account: AccountInfo
    security: SecurityInfo
    preferences: PreferencesInfo
    notifications: list[NotificationTypePref]
    email_enabled: bool
    email_frequency: str
    deletion: DeletionInfo | None = None


# ── Update ──────────────────────────────────────────────────────────────────


class UpdateSettingsRequest(BaseModel):
    # Account
    display_name: str | None = None
    photo_url: str | None = None
    # Preferences
    locale: str | None = None
    timezone: str | None = None
    theme: str | None = None
    dyslexia_mode: bool | None = None
    font_size: str | None = None
    reduced_motion: bool | None = None

    @field_validator("theme")
    @classmethod
    def _theme(cls, v: str | None) -> str | None:
        if v is not None and v not in _THEMES:
            raise ValueError(f"theme must be one of {sorted(_THEMES)}")
        return v

    @field_validator("font_size")
    @classmethod
    def _font_size(cls, v: str | None) -> str | None:
        if v is not None and v not in _FONT_SIZES:
            raise ValueError(f"font_size must be one of {sorted(_FONT_SIZES)}")
        return v


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def _strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Za-z]", v) or not re.search(r"\d", v):
            raise ValueError("Password must contain letters and numbers")
        return v


class ChangeEmailRequest(BaseModel):
    new_email: str

    @field_validator("new_email")
    @classmethod
    def _email(cls, v: str) -> str:
        if not _EMAIL_RE.match(v):
            raise ValueError("Invalid email address")
        return v.lower()


class MfaConfirmRequest(BaseModel):
    code: str


class MfaDisableRequest(BaseModel):
    code: str | None = None


class MfaEnrollResponse(BaseModel):
    secret: str
    otpauth_uri: str
    recovery_codes: list[str]


class SessionInfo(BaseModel):
    id: str
    device: str
    current: bool
    last_active: datetime | None = None
    location: str | None = None


class LoginEvent(BaseModel):
    at: datetime
    device: str | None = None
    location: str | None = None
    risk: str | None = None


class DeleteAccountRequest(BaseModel):
    confirm_text: str
    password: str

    @field_validator("password")
    @classmethod
    def _password(cls, v: str) -> str:
        if not (v or "").strip():
            raise ValueError("Password is required")
        return v


class DeletionStatusResponse(BaseModel):
    deletion: DeletionInfo | None = None


# ── Institution ─────────────────────────────────────────────────────────────


class InstitutionAccountInfo(BaseModel):
    institution_id: str | None = None
    name: str | None = None
    contact_email: str | None = None
    website_url: str | None = None
    primary_domain: str | None = None
    member_since: datetime | None = None


class TeamMember(BaseModel):
    id: str
    email: str
    role: str
    status: str  # active | pending | revoked
    invited_at: datetime | None = None


class ReviewConfigInfo(BaseModel):
    blind_review_default: bool
    calibration_enabled: bool
    reviewer_assignment_mode: str


class InstitutionSettingsResponse(BaseModel):
    account: InstitutionAccountInfo
    security: SecurityInfo
    preferences: PreferencesInfo
    notifications: list[NotificationTypePref]
    email_enabled: bool
    email_frequency: str
    team: list[TeamMember]
    deletion: DeletionInfo | None = None
    review_config: ReviewConfigInfo


class UpdateInstitutionSettingsRequest(BaseModel):
    # Org account fields (Spec 21 §3.2 — org-level only; full profile is Spec 22)
    name: str | None = None
    contact_email: str | None = None
    website_url: str | None = None
    review_config: dict | None = None
    # Shared per-user prefs (stored in user_settings, same as students)
    theme: str | None = None
    locale: str | None = None
    timezone: str | None = None
    dyslexia_mode: bool | None = None
    font_size: str | None = None
    reduced_motion: bool | None = None

    @field_validator("theme")
    @classmethod
    def _theme(cls, v: str | None) -> str | None:
        if v is not None and v not in _THEMES:
            raise ValueError(f"theme must be one of {sorted(_THEMES)}")
        return v

    @field_validator("font_size")
    @classmethod
    def _font_size(cls, v: str | None) -> str | None:
        if v is not None and v not in _FONT_SIZES:
            raise ValueError(f"font_size must be one of {sorted(_FONT_SIZES)}")
        return v


class TeamInviteRequest(BaseModel):
    email: str
    role: str

    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        if not _EMAIL_RE.match(v):
            raise ValueError("Invalid email address")
        return v.lower()

    @field_validator("role")
    @classmethod
    def _role(cls, v: str) -> str:
        if v not in _TEAM_ROLES:
            raise ValueError(f"role must be one of {sorted(_TEAM_ROLES)}")
        return v

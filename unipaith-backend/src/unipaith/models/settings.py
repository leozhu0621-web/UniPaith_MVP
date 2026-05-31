"""
Spec 21 — Settings models.

`UserSettings` is the canonical, role-agnostic settings store (1:1 with users)
for both students and institution admins. For students, the settings service
*writes through* the overlapping fields (locale, timezone, accessibility,
deletion) to the durable StudentProfile sub-tables so existing consumers
(calendar timezone normalisation, the Profile Data tab) stay consistent.

`InstitutionTeamInvite` is the minimal team/seats record (Spec 21 §3.1):
create / list / revoke pending invites with a role. Actual email delivery and
multi-user auth are Phase-2 — the invite row + audit trail are built now.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, backref, mapped_column, relationship

from unipaith.models.base import Base


class UserSettings(Base):
    """Per-user settings — the focused editor surface behind /s/settings + /i/settings."""

    __tablename__ = "user_settings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # ── Account ────────────────────────────────────────────────────────────
    display_name: Mapped[str | None] = mapped_column(String(255))
    photo_url: Mapped[str | None] = mapped_column(String(1000))
    pending_email: Mapped[str | None] = mapped_column(String(255))

    # ── Preferences ────────────────────────────────────────────────────────
    locale: Mapped[str | None] = mapped_column(String(30))
    timezone: Mapped[str | None] = mapped_column(String(50))
    theme: Mapped[str] = mapped_column(String(10), default="system", server_default="system")
    dyslexia_mode: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    font_size: Mapped[str] = mapped_column(String(4), default="md", server_default="md")
    reduced_motion: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    # ── Security (MFA) ─────────────────────────────────────────────────────
    # In prod these mirror Cognito state; in dev (cognito_bypass) they are the
    # source of truth so the feature is fully exercisable. mfa_secret holds the
    # base32 TOTP shared secret; recovery codes are stored as a JSON list.
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    mfa_method: Mapped[str | None] = mapped_column(String(10))  # 'totp' | 'sms'
    mfa_secret: Mapped[str | None] = mapped_column(String(64))  # pragma: allowlist secret
    mfa_pending_secret: Mapped[str | None] = mapped_column(String(64))  # pragma: allowlist secret
    mfa_recovery_codes: Mapped[list | None] = mapped_column(JSONB)

    # ── Account deletion (soft-delete + 30-day grace, Spec 46) ─────────────
    deletion_scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deletion_purge_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped[User] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "User", backref=backref("settings", uselist=False)
    )


class InstitutionTeamInvite(Base):
    """Pending staff invite for an institution (Spec 21 §3.1 — team / seats)."""

    __tablename__ = "institution_team_invites"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    # admissions | recruiter | marketing | it | admin
    role: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="pending", server_default="pending", nullable=False
    )
    invited_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    institution: Mapped[Institution] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Institution", backref="team_invites"
    )

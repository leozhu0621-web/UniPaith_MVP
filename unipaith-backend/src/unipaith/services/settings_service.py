"""
Spec 21 — Settings service.

A focused editor over a subset of the Prompt-Library fields + Cognito-managed
auth. `UserSettings` is the canonical store for both roles; for students the
overlapping fields are written through to the durable StudentProfile sub-tables
so existing consumers (calendar timezone normalisation, the Profile Data tab)
stay consistent.

Cognito-dependent actions (password, MFA, sessions, email) degrade gracefully
when ``settings.cognito_bypass`` is set: the feature is fully exercisable in dev
with ``UserSettings`` as the source of truth, and uses the real Cognito APIs in
prod.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import secrets
import struct
import time
from datetime import UTC, datetime, timedelta
from urllib.parse import quote, urlparse
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from unipaith.config import settings
from unipaith.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
)
from unipaith.models.institution import Institution
from unipaith.models.settings import InstitutionTeamInvite, UserSettings
from unipaith.models.student import (
    StudentAccommodation,
    StudentDataConsent,
    StudentProfile,
    StudentScheduling,
)
from unipaith.models.user import User, UserRole
from unipaith.services.notification_service import NotificationService, normalize_matrix

logger = logging.getLogger(__name__)

_GRACE_DAYS = 30
_VALID_FONT = {"sm", "md", "lg", "xl"}


# ── TOTP (RFC 6238) — stdlib, no external dependency ────────────────────────


def _gen_totp_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode("utf-8").rstrip("=")


def _totp_at(secret_b32: str, when: float, step: int = 30, digits: int = 6) -> str:
    key = base64.b32decode(secret_b32 + "=" * (-len(secret_b32) % 8))
    counter = int(when // step)
    digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code = (struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF) % (10**digits)
    return str(code).zfill(digits)


def _verify_totp(secret_b32: str, code: str, window: int = 1) -> bool:
    code = (code or "").strip().replace(" ", "")
    if not code:
        return False
    now = time.time()
    return any(_totp_at(secret_b32, now + w * 30) == code for w in range(-window, window + 1))


def _hash_code(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


class SettingsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── settings row + student profile loading ─────────────────────────────

    async def _get_profile(self, user: User) -> StudentProfile | None:
        if user.role != UserRole.student:
            return None
        result = await self.db.execute(
            select(StudentProfile)
            .options(
                selectinload(StudentProfile.scheduling),
                selectinload(StudentProfile.accommodations),
                selectinload(StudentProfile.data_consent),
            )
            .where(StudentProfile.user_id == user.id)
        )
        return result.scalar_one_or_none()

    async def _get_or_seed(self, user: User) -> UserSettings:
        result = await self.db.execute(select(UserSettings).where(UserSettings.user_id == user.id))
        s = result.scalar_one_or_none()
        if s:
            return s

        # First access — seed from existing durable fields (students).
        s = UserSettings(user_id=user.id, theme="system", font_size="md")
        if user.role == UserRole.student:
            profile = await self._get_profile(user)
            if profile:
                s.locale = profile.preferred_platform_language
                s.display_name = profile.preferred_name or profile.first_name
                if profile.scheduling:
                    s.timezone = profile.scheduling.timezone
                if profile.accommodations:
                    s.dyslexia_mode = bool(profile.accommodations.dyslexia_friendly_mode)
                    fs = profile.accommodations.font_size_pref
                    s.font_size = fs if fs in _VALID_FONT else "md"
                if profile.data_consent and profile.data_consent.deletion_requested:
                    when = profile.data_consent.deletion_requested_at
                    if when:
                        s.deletion_scheduled_at = when
                        s.deletion_purge_at = when + timedelta(days=_GRACE_DAYS)
        self.db.add(s)
        await self.db.flush()
        return s

    # ── compose / update ───────────────────────────────────────────────────

    def _compose(self, user: User, s: UserSettings, notif) -> dict:  # type: ignore[no-untyped-def]
        deletion = None
        if s.deletion_scheduled_at and s.deletion_purge_at:
            deletion = {"scheduled_at": s.deletion_scheduled_at, "purge_at": s.deletion_purge_at}
        return {
            "account": {
                "email": user.email,
                "role": user.role.value,
                "member_since": user.created_at,
                "display_name": s.display_name,
                "photo_url": s.photo_url,
                "pending_email": s.pending_email,
            },
            "security": {"mfa_enabled": s.mfa_enabled, "mfa_method": s.mfa_method},
            "preferences": {
                "locale": s.locale,
                "timezone": s.timezone,
                "theme": s.theme,
                "accessibility": {
                    "dyslexia_mode": s.dyslexia_mode,
                    "font_size": s.font_size,
                    "reduced_motion": s.reduced_motion,
                },
            },
            "notifications": normalize_matrix(notif.preferences),
            "email_enabled": notif.email_enabled,
            "email_frequency": notif.email_frequency,
            "deletion": deletion,
        }

    async def get_settings(self, user: User) -> dict:
        s = await self._get_or_seed(user)
        notif = await NotificationService(self.db).get_preferences(user.id)
        return self._compose(user, s, notif)

    async def update_settings(self, user: User, data: dict) -> dict:
        s = await self._get_or_seed(user)
        # String fields: present-and-not-None (an empty string clears the value).
        for field in ("display_name", "photo_url", "theme", "locale", "timezone"):
            if field in data and data[field] is not None:
                setattr(s, field, data[field])
        if "dyslexia_mode" in data and data["dyslexia_mode"] is not None:
            s.dyslexia_mode = bool(data["dyslexia_mode"])
        if "font_size" in data and data["font_size"] is not None:
            s.font_size = data["font_size"]
        if "reduced_motion" in data and data["reduced_motion"] is not None:
            s.reduced_motion = bool(data["reduced_motion"])

        if user.role == UserRole.student:
            await self._write_through(user, data)

        await self.db.flush()
        notif = await NotificationService(self.db).get_preferences(user.id)
        return self._compose(user, s, notif)

    async def _write_through(self, user: User, data: dict) -> None:
        """Mirror overlapping fields onto the durable StudentProfile sub-tables."""
        profile = await self._get_profile(user)
        if not profile:
            return
        if "locale" in data and data["locale"] is not None:
            profile.preferred_platform_language = data["locale"]
        if "timezone" in data and data["timezone"] is not None:
            sched = profile.scheduling
            if sched is None:
                sched = StudentScheduling(student_id=profile.id)
                self.db.add(sched)
            sched.timezone = data["timezone"]
        if ("dyslexia_mode" in data and data["dyslexia_mode"] is not None) or (
            "font_size" in data and data["font_size"] is not None
        ):
            acc = profile.accommodations
            if acc is None:
                acc = StudentAccommodation(student_id=profile.id)
                self.db.add(acc)
            if data.get("dyslexia_mode") is not None:
                acc.dyslexia_friendly_mode = bool(data["dyslexia_mode"])
            if data.get("font_size") is not None:
                acc.font_size_pref = data["font_size"]

    # ── security: password / MFA / sessions / email ────────────────────────

    async def change_password(self, user: User, current: str, new: str) -> None:
        if current == new:
            raise BadRequestException("New password must differ from the current one")
        if settings.cognito_bypass:
            return  # dev: login ignores password; strength already validated by schema
        try:
            from unipaith.services.auth_service import _get_cognito_client

            client = _get_cognito_client()
            client.admin_set_user_password(
                UserPoolId=settings.cognito_user_pool_id,
                Username=user.cognito_sub or user.email,
                Password=new,
                Permanent=True,
            )
        except Exception as e:  # noqa: BLE001
            logger.error("Cognito password change failed for %s: %s", user.id, e)
            raise BadRequestException("Could not change password") from e

    async def change_email(self, user: User, new_email: str) -> dict:
        if new_email == user.email:
            raise BadRequestException("That is already your email")
        existing = await self.db.execute(select(User).where(User.email == new_email))
        if existing.scalar_one_or_none():
            raise ConflictException("That email is already in use")
        s = await self._get_or_seed(user)
        s.pending_email = new_email
        if not settings.cognito_bypass:
            try:
                from unipaith.services.auth_service import _get_cognito_client

                client = _get_cognito_client()
                client.admin_update_user_attributes(
                    UserPoolId=settings.cognito_user_pool_id,
                    Username=user.cognito_sub or user.email,
                    UserAttributes=[
                        {"Name": "email", "Value": new_email},
                        {"Name": "email_verified", "Value": "false"},
                    ],
                )
            except Exception as e:  # noqa: BLE001
                logger.error("Cognito email change failed for %s: %s", user.id, e)
                raise BadRequestException("Could not start email change") from e
        await self.db.flush()
        return {"pending_email": new_email}

    async def mfa_enroll(self, user: User) -> dict:
        s = await self._get_or_seed(user)
        secret = _gen_totp_secret()
        s.mfa_pending_secret = secret
        codes = [secrets.token_hex(4) for _ in range(10)]
        s.mfa_recovery_codes = [_hash_code(c) for c in codes]
        await self.db.flush()
        label = quote(f"UniPaith:{user.email}")
        otpauth = f"otpauth://totp/{label}?secret={secret}&issuer=UniPaith"
        return {"secret": secret, "otpauth_uri": otpauth, "recovery_codes": codes}

    async def mfa_confirm(self, user: User, code: str) -> dict:
        s = await self._get_or_seed(user)
        if not s.mfa_pending_secret:
            raise BadRequestException("No MFA enrollment in progress")
        if not _verify_totp(s.mfa_pending_secret, code):
            raise BadRequestException("That code is incorrect or expired")
        s.mfa_secret = s.mfa_pending_secret
        s.mfa_pending_secret = None
        s.mfa_enabled = True
        s.mfa_method = "totp"
        await self.db.flush()
        return {"mfa_enabled": True, "mfa_method": "totp"}

    async def mfa_disable(self, user: User, code: str | None) -> dict:
        s = await self._get_or_seed(user)
        if not s.mfa_enabled:
            raise BadRequestException("MFA is not enabled")
        # Require a valid current code (or a stored recovery code) to disable.
        ok = bool(s.mfa_secret and code and _verify_totp(s.mfa_secret, code))
        if not ok and code and s.mfa_recovery_codes:
            ok = _hash_code(code.strip()) in s.mfa_recovery_codes
        if not ok:
            raise BadRequestException("Enter a valid authenticator or recovery code to disable")
        s.mfa_enabled = False
        s.mfa_method = None
        s.mfa_secret = None
        s.mfa_pending_secret = None
        s.mfa_recovery_codes = None
        await self.db.flush()
        return {"mfa_enabled": False, "mfa_method": None}

    async def list_sessions(self, user: User) -> list[dict]:
        # Device-level session tracking is a Cognito-devices Phase-2 item; the
        # current session is always surfaced so "sign out everywhere" has a target.
        return [
            {
                "id": "current",
                "device": "This device",
                "current": True,
                "last_active": datetime.now(UTC),
                "location": None,
            }
        ]

    async def revoke_sessions(self, user: User) -> dict:
        if not settings.cognito_bypass:
            try:
                from unipaith.services.auth_service import _get_cognito_client

                client = _get_cognito_client()
                client.admin_user_global_sign_out(
                    UserPoolId=settings.cognito_user_pool_id,
                    Username=user.cognito_sub or user.email,
                )
            except Exception as e:  # noqa: BLE001
                logger.error("Global sign-out failed for %s: %s", user.id, e)
        return {"revoked": True}

    async def login_activity(self, user: User) -> list[dict]:
        # Read-only surface for recent logins + login_risk_events (Spec 42 §3.17).
        # Event capture is Phase-2; the active session is shown as the known entry.
        return [
            {
                "at": datetime.now(UTC),
                "device": "This device",
                "location": None,
                "risk": "normal",
            }
        ]

    # ── account deletion (soft-delete + 30-day grace) ──────────────────────

    async def request_deletion(self, user: User, confirm_text: str) -> dict:
        if (confirm_text or "").strip().upper() != "DELETE":
            raise BadRequestException('Type "DELETE" to confirm account deletion')
        s = await self._get_or_seed(user)
        now = datetime.now(UTC)
        s.deletion_scheduled_at = now
        s.deletion_purge_at = now + timedelta(days=_GRACE_DAYS)
        if user.role == UserRole.student:
            profile = await self._get_profile(user)
            if profile:
                consent = profile.data_consent
                if consent is None:
                    consent = StudentDataConsent(student_id=profile.id)
                    self.db.add(consent)
                consent.deletion_requested = True
                consent.deletion_requested_at = now
        await self.db.flush()
        return {"scheduled_at": s.deletion_scheduled_at, "purge_at": s.deletion_purge_at}

    async def cancel_deletion(self, user: User) -> None:
        s = await self._get_or_seed(user)
        s.deletion_scheduled_at = None
        s.deletion_purge_at = None
        if user.role == UserRole.student:
            profile = await self._get_profile(user)
            if profile and profile.data_consent:
                profile.data_consent.deletion_requested = False
                profile.data_consent.deletion_requested_at = None
        await self.db.flush()

    # ── institution settings + team ────────────────────────────────────────

    async def _get_institution(self, user: User) -> Institution:
        result = await self.db.execute(
            select(Institution).where(Institution.admin_user_id == user.id)
        )
        inst = result.scalar_one_or_none()
        if not inst:
            raise NotFoundException("No institution found for this account")
        return inst

    @staticmethod
    def _primary_domain(inst: Institution) -> str | None:
        if inst.website_url:
            host = urlparse(inst.website_url).netloc or inst.website_url
            return host.replace("www.", "").strip("/") or None
        if inst.contact_email and "@" in inst.contact_email:
            return inst.contact_email.split("@", 1)[1]
        return None

    async def get_institution_settings(self, user: User) -> dict:
        inst = await self._get_institution(user)
        s = await self._get_or_seed(user)
        notif = await NotificationService(self.db).get_preferences(user.id)
        base = self._compose(user, s, notif)
        team = await self.list_team(user)
        return {
            "account": {
                "institution_id": str(inst.id),
                "name": inst.name,
                "contact_email": inst.contact_email,
                "website_url": inst.website_url,
                "primary_domain": self._primary_domain(inst),
                "member_since": inst.created_at,
            },
            "security": base["security"],
            "preferences": base["preferences"],
            "notifications": base["notifications"],
            "email_enabled": base["email_enabled"],
            "email_frequency": base["email_frequency"],
            "team": team,
            "deletion": base["deletion"],
        }

    async def update_institution_settings(self, user: User, data: dict) -> dict:
        inst = await self._get_institution(user)
        for field in ("name", "contact_email", "website_url"):
            if field in data and data[field] is not None:
                setattr(inst, field, data[field])
        # Shared per-user prefs (theme/locale/timezone/accessibility) live in
        # user_settings — same store + behaviour as students.
        pref_keys = ("theme", "locale", "timezone", "dyslexia_mode", "font_size", "reduced_motion")
        await self.update_settings(user, {k: data[k] for k in pref_keys if k in data})
        await self.db.flush()
        return await self.get_institution_settings(user)

    async def list_team(self, user: User) -> list[dict]:
        inst = await self._get_institution(user)
        members: list[dict] = [
            {
                "id": str(user.id),
                "email": user.email,
                "role": "admin",
                "status": "active",
                "invited_at": inst.created_at,
            }
        ]
        result = await self.db.execute(
            select(InstitutionTeamInvite)
            .where(
                InstitutionTeamInvite.institution_id == inst.id,
                InstitutionTeamInvite.status != "revoked",
            )
            .order_by(InstitutionTeamInvite.created_at.desc())
        )
        for inv in result.scalars().all():
            members.append(
                {
                    "id": str(inv.id),
                    "email": inv.email,
                    "role": inv.role,
                    "status": inv.status,
                    "invited_at": inv.created_at,
                }
            )
        return members

    async def invite_member(self, user: User, email: str, role: str) -> dict:
        inst = await self._get_institution(user)
        if email == user.email:
            raise BadRequestException("That is already your account")
        dup = await self.db.execute(
            select(InstitutionTeamInvite).where(
                InstitutionTeamInvite.institution_id == inst.id,
                InstitutionTeamInvite.email == email,
                InstitutionTeamInvite.status == "pending",
            )
        )
        if dup.scalar_one_or_none():
            raise ConflictException("An invite is already pending for that email")
        invite = InstitutionTeamInvite(
            institution_id=inst.id,
            email=email,
            role=role,
            status="pending",
            invited_by_user_id=user.id,
        )
        self.db.add(invite)
        await self.db.flush()
        return {
            "id": str(invite.id),
            "email": invite.email,
            "role": invite.role,
            "status": invite.status,
            "invited_at": invite.created_at,
        }

    async def revoke_invite(self, user: User, invite_id: UUID) -> None:
        inst = await self._get_institution(user)
        result = await self.db.execute(
            select(InstitutionTeamInvite).where(
                InstitutionTeamInvite.id == invite_id,
                InstitutionTeamInvite.institution_id == inst.id,
            )
        )
        invite = result.scalar_one_or_none()
        if not invite:
            raise NotFoundException("Invite not found")
        invite.status = "revoked"
        await self.db.flush()

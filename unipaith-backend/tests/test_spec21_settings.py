"""Spec 21 — Settings: backend contract tests."""

from __future__ import annotations

import time

from sqlalchemy import select

from unipaith.models.institution import Institution
from unipaith.models.settings import InstitutionTeamInvite, UserSettings
from unipaith.models.student import StudentProfile, StudentScheduling
from unipaith.services.settings_service import _totp_at

API = "/api/v1"
_CUR_PW = "oldpass123"  # pragma: allowlist secret
_NEW_PW = "newpass456"  # pragma: allowlist secret


# ── Student settings ────────────────────────────────────────────────────────


async def test_get_settings_defaults(student_client):
    r = await student_client.get(f"{API}/students/me/settings")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["account"]["role"] == "student"
    assert body["security"]["mfa_enabled"] is False
    assert body["preferences"]["theme"] == "system"
    # canonical notification matrix is present with all channels
    types = {n["type"] for n in body["notifications"]}
    assert {"deadline_reminders", "decisions", "messages"} <= types
    assert body["email_frequency"] == "all"
    assert body["deletion"] is None


async def test_patch_preferences(student_client):
    r = await student_client.patch(
        f"{API}/students/me/settings",
        json={"theme": "dark", "font_size": "lg", "locale": "es", "reduced_motion": True},
    )
    assert r.status_code == 200, r.text
    prefs = r.json()["preferences"]
    assert prefs["theme"] == "dark"
    assert prefs["accessibility"]["font_size"] == "lg"
    assert prefs["accessibility"]["reduced_motion"] is True
    assert prefs["locale"] == "es"
    # persisted across a fresh GET
    again = (await student_client.get(f"{API}/students/me/settings")).json()
    assert again["preferences"]["theme"] == "dark"


async def test_invalid_theme_rejected(student_client):
    r = await student_client.patch(f"{API}/students/me/settings", json={"theme": "neon"})
    assert r.status_code == 422


async def test_timezone_writes_through_to_scheduling(student_client, db_session, mock_student_user):
    # A profile must exist for write-through to the durable record (calendar reads this).
    db_session.add(StudentProfile(user_id=mock_student_user.id))
    await db_session.flush()

    r = await student_client.patch(
        f"{API}/students/me/settings", json={"timezone": "America/New_York"}
    )
    assert r.status_code == 200, r.text
    assert r.json()["preferences"]["timezone"] == "America/New_York"

    # The durable StudentScheduling row the calendar normalises against is updated.
    prof = (
        await db_session.execute(
            select(StudentProfile).where(StudentProfile.user_id == mock_student_user.id)
        )
    ).scalar_one()
    sched = (
        await db_session.execute(
            select(StudentScheduling).where(StudentScheduling.student_id == prof.id)
        )
    ).scalar_one()
    assert sched.timezone == "America/New_York"


# ── Notification matrix ─────────────────────────────────────────────────────


async def test_notification_matrix_persists_and_protects_essential(student_client):
    # Try to silence every channel on an essential (transactional) type.
    payload = {
        "email_enabled": True,
        "email_frequency": "weekly",
        "preferences": {
            "match_updates": {"email": False, "sms": True, "in_app": False, "push": False},
            "deadline_reminders": {"email": False, "sms": False, "in_app": False, "push": False},
        },
    }
    r = await student_client.put(f"{API}/notifications/preferences", json=payload)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["email_frequency"] == "weekly"
    matrix = {n["type"]: n for n in body["matrix"]}
    # match_updates honoured the user's choices
    assert matrix["match_updates"]["channels"]["email"] is False
    assert matrix["match_updates"]["channels"]["sms"] is True
    # essential type cannot have in-app silenced (safety)
    assert matrix["deadline_reminders"]["essential"] is True
    assert matrix["deadline_reminders"]["channels"]["in_app"] is True

    # reflected in the composed settings payload
    settings_body = (await student_client.get(f"{API}/students/me/settings")).json()
    sm = {n["type"]: n for n in settings_body["notifications"]}
    assert sm["match_updates"]["channels"]["sms"] is True
    assert settings_body["email_frequency"] == "weekly"


# ── Security: password / MFA / sessions ─────────────────────────────────────


async def test_change_password_dev(student_client):
    r = await student_client.post(
        f"{API}/account/change-password",
        json={"current_password": _CUR_PW, "new_password": _NEW_PW},
    )
    assert r.status_code == 200, r.text
    # weak password rejected by schema
    weak = await student_client.post(
        f"{API}/account/change-password",
        json={"current_password": _CUR_PW, "new_password": "short"},  # pragma: allowlist secret
    )
    assert weak.status_code == 422


async def test_mfa_enroll_confirm_disable(student_client):
    enroll = await student_client.post(f"{API}/account/mfa/enroll")
    assert enroll.status_code == 200, enroll.text
    data = enroll.json()
    assert data["secret"] and data["otpauth_uri"].startswith("otpauth://totp/")
    assert len(data["recovery_codes"]) == 10

    code = _totp_at(data["secret"], time.time())
    confirm = await student_client.post(f"{API}/account/mfa/confirm", json={"code": code})
    assert confirm.status_code == 200, confirm.text
    assert confirm.json()["mfa_enabled"] is True

    settings_body = (await student_client.get(f"{API}/students/me/settings")).json()
    assert settings_body["security"]["mfa_enabled"] is True
    assert settings_body["security"]["mfa_method"] == "totp"

    # wrong code cannot disable
    bad = await student_client.post(f"{API}/account/mfa/disable", json={"code": "000000"})
    assert bad.status_code == 400
    # valid code disables
    good_code = _totp_at(data["secret"], time.time())
    disable = await student_client.post(f"{API}/account/mfa/disable", json={"code": good_code})
    assert disable.status_code == 200, disable.text
    assert disable.json()["mfa_enabled"] is False


async def test_sessions_and_login_activity(student_client):
    sessions = await student_client.get(f"{API}/account/sessions")
    assert sessions.status_code == 200
    assert any(s["current"] for s in sessions.json())
    revoke = await student_client.post(f"{API}/account/sessions/revoke")
    assert revoke.status_code == 200
    activity = await student_client.get(f"{API}/account/login-activity")
    assert activity.status_code == 200


async def test_change_email_pending(student_client):
    r = await student_client.post(
        f"{API}/account/change-email", json={"new_email": "new.address@example.com"}
    )
    assert r.status_code == 200, r.text
    assert r.json()["pending_email"] == "new.address@example.com"
    body = (await student_client.get(f"{API}/students/me/settings")).json()
    assert body["account"]["pending_email"] == "new.address@example.com"


# ── Account deletion (soft-delete + 30-day grace) ───────────────────────────


async def test_account_deletion_grace_and_cancel(student_client, db_session, mock_student_user):
    bad = await student_client.post(f"{API}/account/delete", json={"confirm_text": "nope"})
    assert bad.status_code == 400

    ok = await student_client.post(f"{API}/account/delete", json={"confirm_text": "DELETE"})
    assert ok.status_code == 200, ok.text
    info = ok.json()
    from datetime import datetime

    scheduled = datetime.fromisoformat(info["scheduled_at"])
    purge = datetime.fromisoformat(info["purge_at"])
    assert 29 <= (purge - scheduled).days <= 30

    body = (await student_client.get(f"{API}/students/me/settings")).json()
    assert body["deletion"] is not None

    cancel = await student_client.post(f"{API}/account/delete/cancel")
    assert cancel.status_code == 200
    body2 = (await student_client.get(f"{API}/students/me/settings")).json()
    assert body2["deletion"] is None


# ── Institution settings + team ─────────────────────────────────────────────


async def _make_institution(db_session, user) -> Institution:
    inst = Institution(
        admin_user_id=user.id,
        name="Test University",
        type="university",
        country="US",
        website_url="https://www.testu.edu",
    )
    db_session.add(inst)
    await db_session.flush()
    return inst


async def test_institution_settings_and_team(institution_client, db_session, mock_institution_user):
    inst = await _make_institution(db_session, mock_institution_user)

    r = await institution_client.get(f"{API}/institutions/settings")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["account"]["name"] == "Test University"
    assert body["account"]["primary_domain"] == "testu.edu"
    # team starts with just the admin
    assert len(body["team"]) == 1 and body["team"][0]["role"] == "admin"

    # invite a member
    inv = await institution_client.post(
        f"{API}/institutions/settings/team/invite",
        json={"email": "recruiter@testu.edu", "role": "recruiter"},
    )
    assert inv.status_code == 200, inv.text
    invite_id = inv.json()["id"]

    team = (await institution_client.get(f"{API}/institutions/settings/team")).json()
    assert any(m["email"] == "recruiter@testu.edu" and m["status"] == "pending" for m in team)

    # revoke
    rev = await institution_client.post(
        f"{API}/institutions/settings/team/invite/{invite_id}/revoke"
    )
    assert rev.status_code == 200
    team2 = (await institution_client.get(f"{API}/institutions/settings/team")).json()
    assert all(m["id"] != invite_id for m in team2)

    # invite persisted but revoked
    stored = (
        (
            await db_session.execute(
                select(InstitutionTeamInvite).where(InstitutionTeamInvite.institution_id == inst.id)
            )
        )
        .scalars()
        .all()
    )
    assert len(stored) == 1 and stored[0].status == "revoked"

    # institution PATCH updates theme (shared user setting)
    patch = await institution_client.patch(
        f"{API}/institutions/settings", json={"theme": "dark", "name": "Test U Renamed"}
    )
    assert patch.status_code == 200, patch.text
    assert patch.json()["preferences"]["theme"] == "dark"
    assert patch.json()["account"]["name"] == "Test U Renamed"


# ── Role scoping (spec §8) ──────────────────────────────────────────────────


async def test_student_cannot_access_institution_settings(student_client):
    r = await student_client.get(f"{API}/institutions/settings")
    assert r.status_code == 403


async def test_institution_cannot_access_student_settings(institution_client):
    r = await institution_client.get(f"{API}/students/me/settings")
    assert r.status_code == 403


# ── user_settings row is created/seeded once ────────────────────────────────


async def test_settings_row_persisted(student_client, db_session, mock_student_user):
    await student_client.get(f"{API}/students/me/settings")
    rows = (
        (
            await db_session.execute(
                select(UserSettings).where(UserSettings.user_id == mock_student_user.id)
            )
        )
        .scalars()
        .all()
    )
    assert len(rows) == 1

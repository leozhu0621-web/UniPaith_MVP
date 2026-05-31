"""Spec 07 (Product Context §4) — subscription / billing API tests.

Covers: lazy 7-day trial auto-start, days-left math, subscribe→active, ad-free
toggle, cancel/resume, entitlement gating (free vs pro), the public plan
catalog, and auth enforcement.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.billing import StudentSubscription
from unipaith.models.student import StudentProfile
from unipaith.models.user import User

SUB = "/api/v1/students/me/subscription"
PLANS = "/api/v1/billing/plans"


async def _ensure_profile(db: AsyncSession, user: User) -> StudentProfile:
    profile = StudentProfile(user_id=user.id)
    db.add(user)
    db.add(profile)
    await db.commit()
    return profile


@pytest.mark.asyncio
async def test_subscription_auto_starts_7day_trial(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    resp = await student_client.get(SUB)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "trialing"
    assert data["plan"] == "free"
    assert data["has_pro_access"] is True  # trial = full access
    assert data["is_trialing"] is True
    assert data["days_left_in_trial"] in (6, 7)
    # Trial unlocks pro features alongside the free baseline.
    assert "expanded_matching" in data["entitlements"]
    assert "portable_profile" in data["entitlements"]


@pytest.mark.asyncio
async def test_public_plan_catalog(client: AsyncClient):
    resp = await client.get(PLANS)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["student"]["price_monthly"] == 15
    assert data["student"]["trial_days"] == 7
    assert data["student"]["ad_free_addon_monthly"] == 5
    assert data["institution"]["price_per_applicant"] == 15
    assert any(f["pro"] and not f["free"] for f in data["features"])


@pytest.mark.asyncio
async def test_subscribe_activates_pro(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    resp = await student_client.post(
        f"{SUB}/subscribe", json={"card_brand": "visa", "card_last4": "4242"}
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "active"
    assert data["plan"] == "pro"
    assert data["has_pro_access"] is True
    assert data["card_last4"] == "4242"


@pytest.mark.asyncio
async def test_subscribe_rejects_bad_card(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    resp = await student_client.post(f"{SUB}/subscribe", json={"card_last4": "12"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_ad_free_toggle(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    on = await student_client.put(f"{SUB}/ad-free", json={"enabled": True})
    assert on.status_code == 200, on.text
    assert on.json()["ad_free"] is True
    off = await student_client.put(f"{SUB}/ad-free", json={"enabled": False})
    assert off.json()["ad_free"] is False


@pytest.mark.asyncio
async def test_cancel_then_resume(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    await student_client.post(f"{SUB}/subscribe", json={"card_last4": "4242"})
    cancel = await student_client.post(f"{SUB}/cancel")
    assert cancel.status_code == 200, cancel.text
    assert cancel.json()["status"] == "canceled"
    # Still has access until the period ends.
    assert cancel.json()["has_pro_access"] is True
    resume = await student_client.post(f"{SUB}/resume")
    assert resume.json()["status"] == "active"


@pytest.mark.asyncio
async def test_cancel_requires_active(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    # Fresh trial — not active yet.
    resp = await student_client.post(f"{SUB}/cancel")
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_entitlements_lock_after_trial_expires(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    first = await student_client.get(SUB)
    assert first.json()["has_pro_access"] is True
    # Expire the trial directly in the DB, then re-read.
    sub = (await db_session.execute(select(StudentSubscription))).scalar_one()
    sub.trial_ends_at = datetime.now(UTC) - timedelta(days=1)
    await db_session.commit()
    after = await student_client.get(SUB)
    body = after.json()
    assert body["status"] == "expired"
    assert body["has_pro_access"] is False
    assert "expanded_matching" not in body["entitlements"]
    assert "portable_profile" in body["entitlements"]


@pytest.mark.asyncio
async def test_subscription_requires_auth(client: AsyncClient):
    resp = await client.get(SUB)
    assert resp.status_code >= 400  # missing auth header

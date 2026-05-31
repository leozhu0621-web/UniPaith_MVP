"""Tests for billing — student subscription lifecycle (Spec 07 §4.1 / 21 §2.7)
and institution usage billing (Spec 07 §4.2 / 21 §3.6)."""

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.application import Application
from unipaith.models.billing import StudentSubscription
from unipaith.models.institution import Institution, Program
from unipaith.models.student import StudentProfile
from unipaith.models.user import User, UserRole

STUDENT_BILLING = "/api/v1/students/me/billing"
INST_BILLING = "/api/v1/institutions/me/billing"


# ── Student subscription ─────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_get_billing_auto_creates_trial(student_client: AsyncClient):
    resp = await student_client.get(STUDENT_BILLING)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "trialing"
    assert data["is_premium"] is True
    assert data["plan_price_usd"] == 15
    assert data["ad_free_addon_usd"] == 5
    assert data["ad_free"] is False
    assert data["has_payment_method"] is False
    # 7-day trial → 7 (or 6 if a sliver elapsed); always within (0, 7].
    assert 0 < data["trial_days_left"] <= 7
    assert data["paywall_enforced"] is False


@pytest.mark.asyncio
async def test_upgrade_attaches_card_and_activates(student_client: AsyncClient):
    resp = await student_client.post(f"{STUDENT_BILLING}/upgrade")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "active"
    assert data["has_payment_method"] is True
    assert data["payment_method_last4"] == "4242"
    assert data["payment_method_brand"] == "Visa"
    assert data["current_period_end"] is not None
    assert data["is_premium"] is True


@pytest.mark.asyncio
async def test_ad_free_toggle_changes_monthly_total(student_client: AsyncClient):
    on = (await student_client.post(f"{STUDENT_BILLING}/ad-free", json={"enabled": True})).json()
    assert on["ad_free"] is True
    assert on["monthly_total_usd"] == 20  # 15 + 5

    off = (await student_client.post(f"{STUDENT_BILLING}/ad-free", json={"enabled": False})).json()
    assert off["ad_free"] is False
    assert off["monthly_total_usd"] == 15


@pytest.mark.asyncio
async def test_cancel_then_resume(student_client: AsyncClient):
    await student_client.post(f"{STUDENT_BILLING}/upgrade")

    canceled = (await student_client.post(f"{STUDENT_BILLING}/cancel")).json()
    assert canceled["cancel_at_period_end"] is True
    assert canceled["status"] == "canceled"
    # Still has access until the period ends.
    assert canceled["is_premium"] is True

    resumed = (await student_client.post(f"{STUDENT_BILLING}/resume")).json()
    assert resumed["cancel_at_period_end"] is False
    assert resumed["status"] == "active"


@pytest.mark.asyncio
async def test_expired_trial_without_card_loses_premium(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
):
    # Seed the row, then backdate the trial so the read-time reconcile fires.
    await student_client.get(STUDENT_BILLING)
    sub = (
        await db_session.execute(
            select(StudentSubscription).where(StudentSubscription.user_id == mock_student_user.id)
        )
    ).scalar_one()
    sub.trial_ends_at = datetime.now(UTC) - timedelta(days=1)
    await db_session.flush()

    data = (await student_client.get(STUDENT_BILLING)).json()
    assert data["status"] == "expired"
    assert data["is_premium"] is False


@pytest.mark.asyncio
async def test_expired_trial_with_card_auto_converts(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
):
    await student_client.post(f"{STUDENT_BILLING}/upgrade")  # card on file
    sub = (
        await db_session.execute(
            select(StudentSubscription).where(StudentSubscription.user_id == mock_student_user.id)
        )
    ).scalar_one()
    # Force the row back into a lapsed trial-with-card state.
    sub.status = "trialing"
    sub.trial_ends_at = datetime.now(UTC) - timedelta(days=1)
    sub.current_period_end = None
    await db_session.flush()

    data = (await student_client.get(STUDENT_BILLING)).json()
    assert data["status"] == "active"
    assert data["is_premium"] is True


@pytest.mark.asyncio
async def test_institution_cannot_access_student_billing(institution_client: AsyncClient):
    resp = await institution_client.get(STUDENT_BILLING)
    assert resp.status_code == 403


# ── Institution usage billing ──────────────────────────────────────────────
async def _seed_submitted_application(
    db: AsyncSession,
    institution_user: User,
    *,
    submitted_at: datetime,
) -> Institution:
    institution = Institution(
        admin_user_id=institution_user.id,
        name="Beachhead Community College",
        type="community_college",
        country="United States",
    )
    db.add(institution)
    await db.flush()

    program = Program(
        institution_id=institution.id,
        program_name="Nursing AAS",
        degree_type="associate",
        is_published=True,
    )
    db.add(program)

    applicant_user = User(
        email=f"applicant-{submitted_at.timestamp()}@example.com",
        role=UserRole.student,
    )
    db.add(applicant_user)
    await db.flush()
    profile = StudentProfile(user_id=applicant_user.id, first_name="Ap", last_name="Plicant")
    db.add(profile)
    await db.flush()

    db.add(
        Application(
            student_id=profile.id,
            program_id=program.id,
            status="submitted",
            submitted_at=submitted_at,
        )
    )
    await db.flush()
    return institution


@pytest.mark.asyncio
async def test_institution_billing_counts_current_cycle_applicant(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_institution_user: User,
):
    await _seed_submitted_application(
        db_session, mock_institution_user, submitted_at=datetime.now(UTC)
    )
    data = (await institution_client.get(INST_BILLING)).json()
    assert data["per_applicant_usd"] == 15
    assert data["applicants_processed"] == 1
    assert data["current_charge_usd"] == 15.0
    assert data["cycle_label"] == datetime.now(UTC).strftime("%B %Y")


@pytest.mark.asyncio
async def test_institution_billing_excludes_unsubmitted_and_prior_cycle(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_institution_user: User,
):
    # Build an institution + program, then add a draft (unsubmitted) and a
    # last-cycle application — neither should count toward this cycle.
    institution = Institution(
        admin_user_id=mock_institution_user.id,
        name="Regional State",
        type="university",
        country="United States",
    )
    db_session.add(institution)
    await db_session.flush()
    program = Program(
        institution_id=institution.id,
        program_name="History BA",
        degree_type="bachelors",
        is_published=True,
    )
    db_session.add(program)

    for idx, (status, submitted) in enumerate(
        [("draft", None), ("submitted", datetime.now(UTC) - timedelta(days=60))]
    ):
        u = User(email=f"x{idx}@example.com", role=UserRole.student)
        db_session.add(u)
        await db_session.flush()
        p = StudentProfile(user_id=u.id, first_name="X", last_name=str(idx))
        db_session.add(p)
        await db_session.flush()
        db_session.add(
            Application(
                student_id=p.id,
                program_id=program.id,
                status=status,
                submitted_at=submitted,
            )
        )
    await db_session.flush()

    data = (await institution_client.get(INST_BILLING)).json()
    assert data["applicants_processed"] == 0
    assert data["current_charge_usd"] == 0.0


@pytest.mark.asyncio
async def test_student_cannot_access_institution_billing(student_client: AsyncClient):
    resp = await student_client.get(INST_BILLING)
    assert resp.status_code == 403

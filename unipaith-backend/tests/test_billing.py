"""Billing / monetization tests (Spec 06 §4).

Covers: trial-on-signup, lazy trial expiry, the free-vs-paid entitlement gate,
card-on-file + subscribe conversion, declined cards, the $5 ad-free add-on,
cancel, the per-unique-applicant institution charge (with dedup), mock-provider
determinism, the 402 paywall guard on a paid endpoint, and the consent.training
lever. Everything runs under the default mock billing provider.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from unipaith.config import settings
from unipaith.models.billing import (
    PLAN_FREE,
    PLAN_PLUS,
    PLAN_TRIAL,
    STATUS_ACTIVE,
    STATUS_FREE,
    STATUS_TRIALING,
    Subscription,
)
from unipaith.models.institution import Institution, Program
from unipaith.models.student import StudentProfile
from unipaith.models.user import User, UserRole
from unipaith.services.billing.provider import (
    CardDeclinedError,
    CardInput,
    MockBillingProvider,
)
from unipaith.services.billing_service import BillingService
from unipaith.services.entitlements import (
    FREE_MATCH_LIMIT,
    Feature,
    entitlements_for,
    is_entitled,
)

# ---------------------------------------------------------------- fixtures/util


@pytest.fixture
def billing_on(monkeypatch):
    """Enable billing (default is off) for the duration of a test."""
    monkeypatch.setattr(settings, "billing_enabled", True)
    monkeypatch.setattr(settings, "billing_mock_mode", True)
    return settings


async def _student(db) -> User:
    u = User(
        email=f"s-{datetime_hex()}@ex.co",
        cognito_sub=f"sub-{datetime_hex()}",
        role=UserRole.student,
        is_active=True,
    )
    db.add(u)
    await db.flush()
    db.add(StudentProfile(user_id=u.id))
    await db.flush()
    return u


def datetime_hex() -> str:
    # Deterministic-enough unique token without importing uuid everywhere.
    import uuid

    return uuid.uuid4().hex[:8]


async def _profile_id(db, user: User):
    from sqlalchemy import select

    return (
        (await db.execute(select(StudentProfile).where(StudentProfile.user_id == user.id)))
        .scalar_one()
        .id
    )


def _visa_card() -> CardInput:
    return CardInput(number="4242424242424242", exp_month=12, exp_year=2030, cvc="123")


# ------------------------------------------------------------ entitlement logic


def test_entitlements_free_vs_trial_vs_plus():
    # Free floor: profile + baseline + limited match only.
    assert is_entitled(PLAN_FREE, Feature.PROFILE)
    assert is_entitled(PLAN_FREE, Feature.LIMITED_MATCH)
    assert not is_entitled(PLAN_FREE, Feature.WORKSHOPS)
    assert not is_entitled(PLAN_FREE, Feature.EXPANDED_MATCH)
    assert not is_entitled(PLAN_FREE, Feature.DEADLINE_ALERTS)
    assert not is_entitled(PLAN_FREE, Feature.SCHOLARSHIP_TOOLS)

    # Trial + Plus: full access.
    for plan in (PLAN_TRIAL, PLAN_PLUS):
        for feat in Feature:
            assert is_entitled(plan, feat), f"{plan} should include {feat}"

    # Unknown plan fails closed to the free floor (never to full access).
    assert is_entitled("garbage", Feature.PROFILE)
    assert not is_entitled("garbage", Feature.WORKSHOPS)
    assert entitlements_for("garbage") == entitlements_for(PLAN_FREE)
    assert FREE_MATCH_LIMIT > 0


# ------------------------------------------------------------- provider (mock)


def test_mock_provider_determinism_and_decline():
    p = MockBillingProvider()
    assert p.name == "mock"
    cust = p.create_customer(email="a@b.co", user_ref="x")
    assert cust.startswith("mock_cus_")

    pm = p.attach_payment_method(customer_id=cust, card=_visa_card())
    assert pm.brand == "visa"
    assert pm.last4 == "4242"
    assert pm.exp_month == 12 and pm.exp_year == 2030

    ch = p.charge(customer_id=cust, amount_cents=1500, description="x")
    assert ch.status == "succeeded"
    assert ch.amount_cents == 1500

    # Stripe-style decline test card.
    with pytest.raises(CardDeclinedError):
        p.attach_payment_method(customer_id=cust, card=CardInput(number="4000000000000002"))


# --------------------------------------------------------------------- trial


async def test_start_trial_creates_trialing_subscription(db_session, billing_on):
    user = await _student(db_session)
    svc = BillingService(db_session)
    sub = await svc.start_trial(user)
    assert sub is not None
    assert sub.plan == PLAN_TRIAL
    assert sub.status == STATUS_TRIALING
    assert sub.trial_ends_at is not None
    days = (sub.trial_ends_at - datetime.now(UTC)).days
    assert 6 <= days <= 7  # ~7-day window

    # Idempotent — second call returns the same row, does not duplicate.
    again = await svc.start_trial(user)
    assert again.id == sub.id


async def test_start_trial_noop_when_billing_disabled(db_session, monkeypatch):
    monkeypatch.setattr(settings, "billing_enabled", False)
    user = await _student(db_session)
    svc = BillingService(db_session)
    assert await svc.start_trial(user) is None
    status = await svc.get_status(user)
    assert status["enabled"] is False
    assert status["plan"] == PLAN_PLUS  # billing off → no paywall, all entitled


async def test_signup_starts_trial_via_hook(client, db_session, billing_on):
    from sqlalchemy import select

    resp = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": f"hook-{datetime_hex()}@ex.co",
            "password": "Passw0rd!23",  # pragma: allowlist secret
            "role": "student",
        },
    )
    assert resp.status_code == 201, resp.text
    user_id = resp.json()["user_id"]
    sub = (
        await db_session.execute(select(Subscription).where(Subscription.user_id == user_id))
    ).scalar_one_or_none()
    assert sub is not None
    assert sub.plan == PLAN_TRIAL


async def test_trial_lazily_expires_to_free(db_session, billing_on):
    user = await _student(db_session)
    # Seed a trial that ended yesterday.
    db_session.add(
        Subscription(
            user_id=user.id,
            plan=PLAN_TRIAL,
            status=STATUS_TRIALING,
            trial_started_at=datetime.now(UTC) - timedelta(days=8),
            trial_ends_at=datetime.now(UTC) - timedelta(days=1),
        )
    )
    await db_session.flush()

    svc = BillingService(db_session)
    status = await svc.get_status(user)
    assert status["plan"] == PLAN_FREE
    assert status["status"] == STATUS_FREE
    assert status["trial_days_left"] in (None, 0)
    # Free entitlements only.
    assert Feature.PROFILE.value in status["entitlements"]
    assert Feature.WORKSHOPS.value not in status["entitlements"]


# ------------------------------------------------------ payment + subscribe


async def test_subscribe_requires_card_then_converts(db_session, billing_on):
    user = await _student(db_session)
    svc = BillingService(db_session)
    await svc.start_trial(user)

    # No card on file → cannot subscribe.
    with pytest.raises(Exception) as ei:
        await svc.subscribe(user)
    assert "payment method" in str(ei.value).lower()

    pm = await svc.add_payment_method(user, _visa_card())
    assert pm["last4"] == "4242"

    status = await svc.subscribe(user)
    assert status["plan"] == PLAN_PLUS
    assert status["status"] == STATUS_ACTIVE
    assert status["has_payment_method"] is True
    assert status["current_period_end"] is not None

    history = await svc.get_history(user)
    types = {h["event_type"] for h in history}
    assert "trial_converted" in types
    assert "subscription_created" in types
    assert "payment_succeeded" in types
    # Now entitled to all paid features.
    assert is_entitled(status["plan"], Feature.WORKSHOPS)


async def test_declined_card_raises(db_session, billing_on):
    user = await _student(db_session)
    svc = BillingService(db_session)
    await svc.start_trial(user)
    with pytest.raises(Exception) as ei:
        await svc.add_payment_method(user, CardInput(number="4000000000000002"))
    assert "declined" in str(ei.value).lower()


async def test_ad_free_requires_plus_then_toggles(db_session, billing_on):
    user = await _student(db_session)
    svc = BillingService(db_session)
    await svc.start_trial(user)

    # Trial user cannot buy the ad-free add-on (it's an add-on to Plus).
    with pytest.raises(Exception):
        await svc.set_ad_free(user, True)

    await svc.add_payment_method(user, _visa_card())
    await svc.subscribe(user)
    status = await svc.set_ad_free(user, True)
    assert status["ad_free"] is True

    status = await svc.set_ad_free(user, False)
    assert status["ad_free"] is False


async def test_cancel_sets_period_end(db_session, billing_on):
    user = await _student(db_session)
    svc = BillingService(db_session)
    await svc.start_trial(user)
    await svc.add_payment_method(user, _visa_card())
    await svc.subscribe(user)

    status = await svc.cancel(user)
    assert status["cancel_at_period_end"] is True
    # Access continues until period end — still Plus.
    assert status["plan"] == PLAN_PLUS


# -------------------------------------------------- institution per-applicant


async def _institution_with_program(db_session):
    admin = User(
        email=f"inst-{datetime_hex()}@ex.co",
        cognito_sub=f"sub-{datetime_hex()}",
        role=UserRole.institution_admin,
        is_active=True,
    )
    db_session.add(admin)
    await db_session.flush()
    inst = Institution(admin_user_id=admin.id, name="Foo U", type="university", country="US")
    db_session.add(inst)
    await db_session.flush()
    progs = [
        Program(institution_id=inst.id, program_name="MS CS", degree_type="masters"),
        Program(institution_id=inst.id, program_name="MS DS", degree_type="masters"),
    ]
    for p in progs:
        db_session.add(p)
    await db_session.flush()
    return inst, progs


async def test_institution_charges_per_unique_applicant(db_session, billing_on):
    from unipaith.models.application import Application

    inst, progs = await _institution_with_program(db_session)
    svc = BillingService(db_session)

    # Student A applies to two programs at the same institution → charged once.
    user_a = await _student(db_session)
    pid_a = await _profile_id(db_session, user_a)
    app_a1 = Application(student_id=pid_a, program_id=progs[0].id, status="submitted")
    app_a2 = Application(student_id=pid_a, program_id=progs[1].id, status="submitted")
    db_session.add_all([app_a1, app_a2])
    await db_session.flush()

    c1 = await svc.record_applicant_charge(app_a1)
    c2 = await svc.record_applicant_charge(app_a2)  # dedup — same (institution, student)
    assert c1 is not None
    assert c2 is not None
    assert c1.id == c2.id
    assert c1.status == "charged"
    assert c1.amount_cents == settings.billing_institution_per_applicant_cents

    # Student B applies once → second unique applicant.
    user_b = await _student(db_session)
    pid_b = await _profile_id(db_session, user_b)
    app_b = Application(student_id=pid_b, program_id=progs[0].id, status="submitted")
    db_session.add(app_b)
    await db_session.flush()
    await svc.record_applicant_charge(app_b)

    usage = await svc.get_institution_usage(inst.id)
    assert usage["billable_applicants"] == 2
    assert usage["total_cents"] == 2 * settings.billing_institution_per_applicant_cents
    assert usage["per_applicant_cents"] == 1500


async def test_applicant_charge_noop_when_disabled(db_session, monkeypatch):
    from unipaith.models.application import Application

    monkeypatch.setattr(settings, "billing_enabled", False)
    inst, progs = await _institution_with_program(db_session)
    user_a = await _student(db_session)
    pid_a = await _profile_id(db_session, user_a)
    app = Application(student_id=pid_a, program_id=progs[0].id, status="submitted")
    db_session.add(app)
    await db_session.flush()
    svc = BillingService(db_session)
    assert await svc.record_applicant_charge(app) is None


# --------------------------------------------------------------- API + paywall


async def test_billing_status_endpoint(student_client, billing_on):
    resp = await student_client.get("/api/v1/students/me/billing")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["enabled"] is True
    assert body["plan"] == PLAN_TRIAL
    assert body["trial_days_left"] is not None
    assert "feature_matrix" in body
    assert body["prices"]["student_plan_cents"] == 1500
    assert body["prices"]["student_adfree_cents"] == 500


async def test_workshops_paywall_402_for_free_user(
    student_client, db_session, mock_student_user, billing_on
):
    # Give the student a profile + an already-lapsed trial → free tier.
    db_session.add(StudentProfile(user_id=mock_student_user.id))
    db_session.add(
        Subscription(
            user_id=mock_student_user.id,
            plan=PLAN_TRIAL,
            status=STATUS_TRIALING,
            trial_started_at=datetime.now(UTC) - timedelta(days=8),
            trial_ends_at=datetime.now(UTC) - timedelta(days=1),
        )
    )
    await db_session.flush()

    resp = await student_client.post(
        "/api/v1/students/me/workshops/essay/feedback",
        json={"essay_text": "This is my essay draft that is definitely long enough to pass."},
    )
    assert resp.status_code == 402, resp.text
    assert resp.json()["detail"]


async def test_workshops_guard_passes_for_plus_user(
    student_client, db_session, mock_student_user, billing_on
):
    db_session.add(StudentProfile(user_id=mock_student_user.id))
    db_session.add(
        Subscription(
            user_id=mock_student_user.id,
            plan=PLAN_PLUS,
            status=STATUS_ACTIVE,
            current_period_end=datetime.now(UTC) + timedelta(days=30),
        )
    )
    await db_session.flush()

    resp = await student_client.post(
        "/api/v1/students/me/workshops/essay/feedback",
        json={"essay_text": "This is my essay draft that is definitely long enough to pass."},
    )
    # The entitlement guard must NOT block a Plus subscriber (whatever the
    # handler does next, it is not a 402).
    assert resp.status_code != 402, resp.text


async def test_consent_training_default_false_and_toggle(
    student_client, db_session, mock_student_user
):
    db_session.add(StudentProfile(user_id=mock_student_user.id))
    await db_session.flush()

    # Default: turning on matching, leaving training unset → training stays False.
    resp = await student_client.put(
        "/api/v1/students/me/data-rights", json={"consent_matching": True}
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["consent_training"] is False

    # Opt in to the value-for-data training lever.
    resp = await student_client.put(
        "/api/v1/students/me/data-rights", json={"consent_training": True}
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["consent_training"] is True


async def test_institution_usage_endpoint(institution_client, db_session, mock_institution_user):
    # Institution with no charges yet still returns a well-formed usage payload.
    inst = Institution(
        admin_user_id=mock_institution_user.id, name="Bar U", type="college", country="US"
    )
    db_session.add(inst)
    await db_session.flush()

    resp = await institution_client.get("/api/v1/institutions/me/billing/usage")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["billable_applicants"] == 0
    assert body["per_applicant_cents"] == 1500

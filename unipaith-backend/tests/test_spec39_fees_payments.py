"""Spec 39 · Fees & Payments.

Covers the §10 acceptance scenarios end-to-end at the service layer (plus a few
HTTP smoke checks): pay-fee → paid → submission gate clears (idempotent, no
double-charge); request-waiver → queue → approve → waived; block-until-approved
policy; auto-waiver; deposit payment advances the enrollment state machine + is
counted by yield; refund requires the institution + is audited + partial math;
the PCI no-raw-card-data contract; and mock-confirm is 404 in stripe mode.
"""

import uuid
from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import settings
from unipaith.core.exceptions import (
    BadRequestException,
    NotFoundException,
    PaymentRequiredException,
)
from unipaith.models.application import Application
from unipaith.models.audit import AdmissionsAuditLog
from unipaith.models.institution import Institution, Program
from unipaith.models.payment import Payment
from unipaith.models.student import StudentProfile
from unipaith.models.user import User, UserRole
from unipaith.services.application_service import ApplicationService
from unipaith.services.enrollment_service import EnrollmentService
from unipaith.services.payment_service import PaymentService
from unipaith.services.payments.provider import ProviderEvent
from unipaith.services.yield_service import YieldService

# ── helpers ────────────────────────────────────────────────────────────────


def _student_user() -> User:
    return User(
        id=uuid.uuid4(),
        email=f"stu-{uuid.uuid4().hex[:6]}@example.com",
        cognito_sub=f"sub-{uuid.uuid4().hex[:8]}",
        role=UserRole("student"),
        is_active=True,
    )


async def _seed(
    db: AsyncSession,
    inst_user: User,
    *,
    fee_cents: int = 7500,
    currency: str = "USD",
    waiver_policy: str = "allow_and_reconcile",
    auto_rules: list[str] | None = None,
    deposit_cents: int = 0,
    app_status: str = "draft",
    student: User | None = None,
) -> tuple[Institution, Program, User, StudentProfile, Application]:
    db.add(inst_user)
    await db.flush()
    payment_config: dict = {"waiver": {"policy": waiver_policy, "auto_rules": auto_rules or []}}
    if fee_cents:
        payment_config["application_fee"] = {
            "enabled": True,
            "amount_cents": fee_cents,
            "currency": currency,
        }
    if deposit_cents:
        payment_config["enrollment_deposit"] = {
            "enabled": True,
            "amount_cents": deposit_cents,
            "currency": currency,
        }
    inst = Institution(
        admin_user_id=inst_user.id,
        name="Foo U",
        type="university",
        country="US",
        city="Boston",
        payment_config=payment_config,
    )
    db.add(inst)
    await db.flush()
    program = Program(
        institution_id=inst.id,
        program_name="MS Computer Science",
        degree_type="masters",
        description_text="A program.",
        tuition=48000,
        is_published=True,
    )
    db.add(program)
    await db.flush()
    su = student or _student_user()
    db.add(su)
    await db.flush()
    profile = StudentProfile(user_id=su.id, first_name="Stu", last_name="Dent")
    db.add(profile)
    await db.flush()
    app = Application(
        student_id=profile.id,
        program_id=program.id,
        status=app_status,
        submitted_at=datetime.now(UTC) if app_status != "draft" else None,
    )
    db.add(app)
    await db.flush()
    return inst, program, su, profile, app


async def _admit_and_accept(
    db: AsyncSession, inst: Institution, profile: StudentProfile, app: Application
):
    svc = ApplicationService(db)
    await svc.release_decision(
        inst.id,
        app.id,
        "admitted",
        offer={
            "offer_type": "full_admission",
            "scholarship_amount": 5000,
            "response_deadline": (date.today() + timedelta(days=20)).isoformat(),
            "start_term": {"season": "Fall", "year": 2027},
        },
    )
    await svc.respond_to_offer(profile.id, app.id, "accepted")
    await db.flush()


# ── §10.1 — pay fee → paid → submission gate clears (idempotent) ─────────────


@pytest.mark.asyncio
async def test_pay_fee_clears_submission_gate_and_is_idempotent(db_session, mock_institution_user):
    inst, program, su, profile, app = await _seed(db_session, mock_institution_user, fee_cents=7500)
    apps = ApplicationService(db_session)
    svc = PaymentService(db_session)

    # Before payment the fee gate blocks internal submission (402).
    with pytest.raises(PaymentRequiredException):
        await apps._assert_fee_clear_for_submit(app)

    checkout = await svc.create_fee_checkout(su, app.id)
    assert checkout["status"] == "pending"
    assert checkout["amount"] == 75.0
    assert checkout["currency"] == "USD"
    assert checkout["inline"] is True  # mock → in-app checkout
    payment_id = uuid.UUID(checkout["payment_id"])

    # Complete the (mock) checkout twice — idempotent, never double-charges.
    await svc.confirm_mock_payment(su, payment_id)
    first = await db_session.get(Payment, payment_id)
    paid_at = first.paid_at
    await svc.confirm_mock_payment(su, payment_id)

    rows = (
        await db_session.execute(
            select(func.count(Payment.id)).where(
                Payment.application_id == app.id, Payment.kind == "application_fee"
            )
        )
    ).scalar_one()
    assert rows == 1  # one row per (application, kind) — the idempotency key
    payment = await db_session.get(Payment, payment_id)
    assert payment.status == "paid"
    assert payment.paid_at == paid_at  # not re-applied

    # Fee paid → the submission gate no longer raises.
    await apps._assert_fee_clear_for_submit(app)


# ── §10.2 — request waiver → queue → approve → waived ────────────────────────


@pytest.mark.asyncio
async def test_request_waiver_then_institution_approve(db_session, mock_institution_user):
    inst, program, su, profile, app = await _seed(db_session, mock_institution_user, fee_cents=7500)
    apps = ApplicationService(db_session)
    svc = PaymentService(db_session)

    tracker = await svc.request_waiver(su, app.id, "first_gen", {"note": "First in my family."})
    assert tracker["fee"]["status"] == "waiver_pending"
    assert tracker["fee"]["waiver"]["basis"] == "first_gen"

    # allow_and_reconcile → a requested waiver lets submission proceed.
    await apps._assert_fee_clear_for_submit(app)

    # It appears in the institution waiver queue.
    queue = await svc.list_waivers(mock_institution_user, "pending")
    assert len(queue) == 1
    payment_id = uuid.UUID(queue[0]["payment_id"])
    assert queue[0]["basis"] == "first_gen"

    # Approve → waived.
    await svc.decide_waiver(mock_institution_user, payment_id, "approve", reason="Verified")
    payment = await db_session.get(Payment, payment_id)
    assert payment.status == "waived"
    assert payment.waiver_approved is True
    await apps._assert_fee_clear_for_submit(app)


@pytest.mark.asyncio
async def test_auto_waiver_when_basis_in_auto_rules(db_session, mock_institution_user):
    _inst, _p, su, _prof, app = await _seed(
        db_session, mock_institution_user, fee_cents=7500, auto_rules=["fee_waiver_code"]
    )
    svc = PaymentService(db_session)
    tracker = await svc.request_waiver(su, app.id, "fee_waiver_code")
    assert tracker["fee"]["status"] == "waived"  # auto-approved, no queue


@pytest.mark.asyncio
async def test_block_until_approved_policy_blocks_until_decision(db_session, mock_institution_user):
    inst, program, su, profile, app = await _seed(
        db_session, mock_institution_user, fee_cents=7500, waiver_policy="block_until_approved"
    )
    apps = ApplicationService(db_session)
    svc = PaymentService(db_session)

    await svc.request_waiver(su, app.id, "income_band")
    # Under block-until-approved a pending waiver does NOT clear the gate.
    with pytest.raises(PaymentRequiredException):
        await apps._assert_fee_clear_for_submit(app)

    payment = (
        await db_session.execute(select(Payment).where(Payment.application_id == app.id))
    ).scalar_one()
    await svc.decide_waiver(mock_institution_user, payment.id, "approve")
    await apps._assert_fee_clear_for_submit(app)


@pytest.mark.asyncio
async def test_deny_waiver_keeps_fee_due(db_session, mock_institution_user):
    inst, program, su, profile, app = await _seed(db_session, mock_institution_user, fee_cents=7500)
    apps = ApplicationService(db_session)
    svc = PaymentService(db_session)
    await svc.request_waiver(su, app.id, "other", {"note": "please"})
    payment = (
        await db_session.execute(select(Payment).where(Payment.application_id == app.id))
    ).scalar_one()
    await svc.decide_waiver(mock_institution_user, payment.id, "deny", reason="Insufficient basis")
    refreshed = await db_session.get(Payment, payment.id)
    assert refreshed.waiver_approved is False
    assert refreshed.status == "none"
    # Denied waiver → submission still blocked until the student pays.
    with pytest.raises(PaymentRequiredException):
        await apps._assert_fee_clear_for_submit(app)


# ── §2.1 per-program fee override + §7 pending/failed still gate ─────────────


@pytest.mark.asyncio
async def test_program_cost_data_fee_overrides_default(db_session, mock_institution_user):
    inst, program, su, profile, app = await _seed(db_session, mock_institution_user, fee_cents=7500)
    # Per-program override via cost_data (whole currency units) — Spec 39 §2.1.
    program.cost_data = {"application_fee": 120}
    await db_session.flush()
    svc = PaymentService(db_session)
    tracker = await svc.cost_tracker(su, app.id)
    assert tracker["fee"]["amount"] == 120.0  # program override wins over the $75 default
    checkout = await svc.create_fee_checkout(su, app.id)
    assert checkout["amount"] == 120.0


@pytest.mark.asyncio
async def test_pending_or_failed_fee_still_blocks_submit(db_session, mock_institution_user):
    inst, program, su, profile, app = await _seed(db_session, mock_institution_user, fee_cents=7500)
    apps = ApplicationService(db_session)
    svc = PaymentService(db_session)
    # An open (pending) checkout does not clear the gate (§7 — submission held).
    await svc.create_fee_checkout(su, app.id)
    with pytest.raises(PaymentRequiredException):
        await apps._assert_fee_clear_for_submit(app)
    # A failed payment also keeps it blocked (the student retries).
    payment = (
        await db_session.execute(select(Payment).where(Payment.application_id == app.id))
    ).scalar_one()
    payment.status = "failed"
    await db_session.flush()
    with pytest.raises(PaymentRequiredException):
        await apps._assert_fee_clear_for_submit(app)


# ── §10.3 — deposit payment advances enrollment + feeds yield ────────────────


@pytest.mark.asyncio
async def test_deposit_payment_advances_enrollment_and_yield(db_session, mock_institution_user):
    inst, program, su, profile, app = await _seed(
        db_session,
        mock_institution_user,
        fee_cents=0,
        deposit_cents=50000,
        app_status="submitted",
    )
    await _admit_and_accept(db_session, inst, profile, app)
    svc = PaymentService(db_session)

    checkout = await svc.create_deposit_checkout(su, app.id)
    assert checkout["kind"] == "enrollment_deposit"
    assert checkout["amount"] == 500.0
    await svc.confirm_mock_payment(su, uuid.UUID(checkout["payment_id"]))

    enr = await EnrollmentService(db_session).get_student_enrollment(profile.id, app.id)
    assert enr["deposit_status"] == "paid"
    assert enr["state"] == "deposit_recorded"
    assert enr["deposit_amount"] == 500  # cents → whole currency units

    snapshot = await YieldService(db_session).get_yield(inst.id)
    assert snapshot["deposited"] >= 1


# ── §10.4 — refund requires institution approval + audit + partial math ──────


@pytest.mark.asyncio
async def test_refund_partial_then_full_with_audit(db_session, mock_institution_user):
    inst, program, su, profile, app = await _seed(db_session, mock_institution_user, fee_cents=7500)
    svc = PaymentService(db_session)
    checkout = await svc.create_fee_checkout(su, app.id)
    payment_id = uuid.UUID(checkout["payment_id"])
    await svc.confirm_mock_payment(su, payment_id)

    # Partial refund.
    res = await svc.refund(mock_institution_user, payment_id, amount_cents=3000, reason="duplicate")
    assert res["status"] == "partially_refunded"
    assert res["refunded_amount"] == 30.0

    # Refund the remainder → fully refunded.
    res2 = await svc.refund(mock_institution_user, payment_id, amount_cents=4500)
    assert res2["status"] == "refunded"
    assert res2["refunded_amount"] == 75.0

    # Nothing left to refund.
    with pytest.raises(BadRequestException):
        await svc.refund(mock_institution_user, payment_id, amount_cents=1)

    # Two refund actions were audited.
    refunds = (
        await db_session.execute(
            select(func.count(AdmissionsAuditLog.id)).where(
                AdmissionsAuditLog.action == "payment_refunded",
                AdmissionsAuditLog.application_id == app.id,
            )
        )
    ).scalar_one()
    assert refunds == 2


@pytest.mark.asyncio
async def test_cannot_refund_unpaid_payment(db_session, mock_institution_user):
    inst, program, su, profile, app = await _seed(db_session, mock_institution_user, fee_cents=7500)
    svc = PaymentService(db_session)
    checkout = await svc.create_fee_checkout(su, app.id)  # status pending, not paid
    with pytest.raises(BadRequestException):
        await svc.refund(mock_institution_user, uuid.UUID(checkout["payment_id"]))


# ── §10.5 — PCI: no raw card data persisted (contract test) ──────────────────


def test_no_raw_card_columns_on_payment_model():
    cols = {c.name.lower() for c in Payment.__table__.columns}
    forbidden = (
        "card",
        "cvc",
        "cvv",
        "pan",
        "card_number",
        "number",
        "expiry",
        "exp_month",
        "exp_year",
    )
    leaked = [c for c in cols if any(f in c for f in forbidden)]
    assert leaked == [], f"Payment must not store raw card data; found: {leaked}"


# ── webhook + mode guards ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_webhook_checkout_completed_marks_paid(db_session, mock_institution_user):
    inst, program, su, profile, app = await _seed(db_session, mock_institution_user, fee_cents=7500)
    svc = PaymentService(db_session)
    checkout = await svc.create_fee_checkout(su, app.id)
    payment_id = checkout["payment_id"]

    # Simulate a Stripe checkout.session.completed event referencing the payment.
    event = ProviderEvent(
        type="checkout.session.completed",
        session_id="cs_test_x",
        charge_id="pi_test_x",
        metadata={"payment_id": payment_id, "kind": "application_fee"},
    )
    await svc.handle_provider_event(event)
    payment = await db_session.get(Payment, uuid.UUID(payment_id))
    assert payment.status == "paid"
    assert payment.provider_charge_id == "pi_test_x"


@pytest.mark.asyncio
async def test_confirm_mock_is_404_in_stripe_mode(db_session, mock_institution_user, monkeypatch):
    inst, program, su, profile, app = await _seed(db_session, mock_institution_user, fee_cents=7500)
    svc = PaymentService(db_session)  # mock provider
    checkout = await svc.create_fee_checkout(su, app.id)
    payment_id = uuid.UUID(checkout["payment_id"])

    # Flip to a stripe-mode service — confirm-mock must 404.
    monkeypatch.setattr(settings, "payments_provider", "stripe")
    monkeypatch.setattr(settings, "stripe_secret_key", "sk_test_dummy")
    stripe_svc = PaymentService(db_session)
    assert stripe_svc.provider.name == "stripe"
    with pytest.raises(NotFoundException):
        await stripe_svc.confirm_mock_payment(su, payment_id)


# ── HTTP smoke (the API contract) ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_http_pay_fee_then_confirm_mock(student_client, db_session, mock_student_user):
    # Build an institution + program + this student's application.
    inst_user = User(
        id=uuid.uuid4(),
        email=f"inst-{uuid.uuid4().hex[:6]}@example.edu",
        cognito_sub=f"sub-{uuid.uuid4().hex[:8]}",
        role=UserRole("institution_admin"),
        is_active=True,
    )
    inst, program, _su, profile, app = await _seed(
        db_session, inst_user, fee_cents=7500, student=mock_student_user
    )

    r = await student_client.get(f"/api/v1/payments/applications/{app.id}")
    assert r.status_code == 200
    body = r.json()
    assert body["fee"]["required"] is True
    assert body["fee"]["status"] == "due"

    r = await student_client.post(f"/api/v1/payments/applications/{app.id}/pay-fee")
    assert r.status_code == 200
    payment_id = r.json()["payment_id"]

    r = await student_client.post(f"/api/v1/payments/{payment_id}/confirm-mock")
    assert r.status_code == 200
    assert r.json()["fee"]["status"] == "paid"


@pytest.mark.asyncio
async def test_http_institution_fee_config_roundtrip(
    institution_client, db_session, mock_institution_user
):
    inst = Institution(
        admin_user_id=mock_institution_user.id,
        name="Bar College",
        type="college",
        country="US",
    )
    db_session.add(inst)
    await db_session.flush()

    payload = {
        "application_fee": {"enabled": True, "amount_cents": 6500, "currency": "USD"},
        "waiver": {"policy": "allow_and_reconcile", "auto_rules": ["first_gen"]},
        "enrollment_deposit": {"enabled": True, "amount_cents": 40000, "currency": "USD"},
    }
    r = await institution_client.put("/api/v1/payments/institution/fee-config", json=payload)
    assert r.status_code == 200
    cfg = r.json()
    assert cfg["application_fee"]["amount_cents"] == 6500
    assert "first_gen" in cfg["waiver"]["auto_rules"]
    assert cfg["enrollment_deposit"]["amount_cents"] == 40000

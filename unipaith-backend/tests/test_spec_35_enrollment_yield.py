"""Spec 35 · Enrollment Confirmation & Yield.

Covers the §10 acceptance scenarios end-to-end at the service layer (plus a
couple of HTTP smoke checks): the enrollment state machine, the post-accept
checklist, decline-frees-seat, waitlist offer-to-next (promote + offer + notify +
audit), yield-rate / melt / funnel-tail math, the cohort fairness lens, and the
status-only-deposit + audit invariant.
"""

import uuid
from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.application import Application, OfferLetter
from unipaith.models.audit import AdmissionsAuditLog
from unipaith.models.institution import Institution, IntakeRound, Program
from unipaith.models.student import StudentProfile
from unipaith.models.user import User, UserRole
from unipaith.models.workflow import Notification
from unipaith.services.application_service import ApplicationService
from unipaith.services.enrollment_service import EnrollmentService
from unipaith.services.yield_service import YieldService


async def _seed(
    db: AsyncSession,
    inst_user: User,
    *,
    n_students: int = 1,
    capacity: int | None = None,
) -> tuple[Institution, Program, list[tuple[StudentProfile, Application]]]:
    db.add(inst_user)
    await db.flush()
    inst = Institution(
        admin_user_id=inst_user.id, name="Foo U", type="university", country="US", city="Boston"
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
    if capacity is not None:
        db.add(
            IntakeRound(
                program_id=program.id,
                round_name="Fall 2027",
                intake_term="Fall 2027",
                capacity=capacity,
            )
        )
        await db.flush()

    pairs: list[tuple[StudentProfile, Application]] = []
    for i in range(n_students):
        su = User(
            id=uuid.uuid4(),
            email=f"stu-{i}-{uuid.uuid4().hex[:6]}@example.com",
            cognito_sub=f"sub-{uuid.uuid4().hex[:8]}",
            role=UserRole("student"),
            is_active=True,
        )
        db.add(su)
        await db.flush()
        profile = StudentProfile(user_id=su.id, first_name=f"Stu{i}", last_name="Dent")
        db.add(profile)
        await db.flush()
        app = Application(
            student_id=profile.id,
            program_id=program.id,
            status="submitted",
            submitted_at=datetime.now(UTC),
        )
        db.add(app)
        await db.flush()
        pairs.append((profile, app))
    await db.commit()
    return inst, program, pairs


async def _admit_and_accept(
    db: AsyncSession, inst: Institution, profile: StudentProfile, app: Application
) -> OfferLetter:
    """Release an admit + offer, then have the student accept it."""
    svc = ApplicationService(db)
    _app, offer = await svc.release_decision(
        inst.id,
        app.id,
        "admitted",
        offer={
            "offer_type": "full_admission",
            "scholarship_amount": 10000,
            "response_deadline": (date.today() + timedelta(days=20)).isoformat(),
            "start_term": {"season": "Fall", "year": 2027},
        },
    )
    await svc.respond_to_offer(profile.id, app.id, "accepted")
    await db.commit()
    return offer


# --------------------------------------------------------------------------
# §10.1 — accept offer → Enrollment window appears with the program checklist
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_accept_offer_surfaces_enrollment_with_checklist(db_session, mock_institution_user):
    inst, program, pairs = await _seed(db_session, mock_institution_user)
    profile, app = pairs[0]

    # Before accept: enrollment window hidden (§7).
    enr_svc = EnrollmentService(db_session)
    pre = await enr_svc.get_student_enrollment(profile.id, app.id)
    assert pre["available"] is False

    await _admit_and_accept(db_session, inst, profile, app)

    view = await enr_svc.get_student_enrollment(profile.id, app.id)
    assert view["available"] is True
    assert view["state"] == "accepted"
    keys = {item["key"] for item in view["checklist"]}
    assert {"confirm_intent", "deposit", "final_transcript", "orientation"} <= keys


# --------------------------------------------------------------------------
# §10.2 — confirm enrollment → intent_confirmed; institution yield increments
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_confirm_intent_advances_state_and_increments_yield(
    db_session, mock_institution_user
):
    inst, program, pairs = await _seed(db_session, mock_institution_user)
    profile, app = pairs[0]
    await _admit_and_accept(db_session, inst, profile, app)
    enr_svc = EnrollmentService(db_session)

    before = await YieldService(db_session).get_yield(inst.id)
    assert before["intent_confirmed"] == 0

    out = await enr_svc.confirm_intent(profile.id, app.id)
    await db_session.commit()
    assert out["state"] == "intent_confirmed"
    assert out["intent_confirmed_at"] is not None
    # The confirm_intent checklist item is now complete.
    ci = next(i for i in out["checklist"] if i["key"] == "confirm_intent")
    assert ci["status"] == "complete"

    after = await YieldService(db_session).get_yield(inst.id)
    assert after["intent_confirmed"] == 1


# --------------------------------------------------------------------------
# §10.3 — decline-after-accept frees the seat (waitlist sees it open)
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_decline_after_accept_frees_seat(db_session, mock_institution_user):
    # capacity 1: one confirmed student fills the class, a second is waitlisted.
    inst, program, pairs = await _seed(db_session, mock_institution_user, n_students=2, capacity=1)
    (p0, a0), (p1, a1) = pairs
    await _admit_and_accept(db_session, inst, p0, a0)
    enr_svc = EnrollmentService(db_session)
    await enr_svc.confirm_intent(p0.id, a0.id)
    await db_session.commit()

    # Waitlist the second applicant.
    a1.decision = "waitlisted"
    a1.status = "decision_made"
    a1.waitlist_rank = 1
    a1.waitlisted_at = datetime.now(UTC)
    await db_session.commit()

    wl_before = await enr_svc.get_waitlist(inst.id, program.id)
    assert wl_before["seats_open"] == 0  # the one seat is filled
    assert wl_before["waitlist_count"] == 1

    # The confirmed student changes their mind.
    out = await enr_svc.decline_after_accept(p0.id, a0.id, reason="Took another offer")
    await db_session.commit()
    assert out["state"] == "withdrew"
    refreshed = await db_session.get(Application, a0.id)
    assert refreshed.student_decision == "declined_by_student"

    wl_after = await enr_svc.get_waitlist(inst.id, program.id)
    assert wl_after["seats_open"] == 1  # seat freed


# --------------------------------------------------------------------------
# §10.4 — offer-to-next promotes the top-ranked waitlisted applicant
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_offer_to_next_waitlisted_promotes_and_audits(db_session, mock_institution_user):
    inst, program, pairs = await _seed(db_session, mock_institution_user, n_students=2, capacity=2)
    (p0, a0), (p1, a1) = pairs
    # Both waitlisted, ranked.
    for app, rank in ((a0, 2), (a1, 1)):
        app.decision = "waitlisted"
        app.status = "decision_made"
        app.waitlist_rank = rank
        app.waitlisted_at = datetime.now(UTC)
    await db_session.commit()

    enr_svc = EnrollmentService(db_session)
    res = await enr_svc.offer_to_next(inst.id, program.id, actor_user_id=mock_institution_user.id)
    await db_session.commit()

    # The top-ranked (rank 1 = a1) is promoted.
    assert res["promoted_application_id"] == str(a1.id)
    promoted = await db_session.get(Application, a1.id)
    assert promoted.decision == "admitted"
    offer = (
        await db_session.execute(select(OfferLetter).where(OfferLetter.application_id == a1.id))
    ).scalar_one_or_none()
    assert offer is not None

    # Student notified.
    notifs = (
        (await db_session.execute(select(Notification).where(Notification.user_id == p1.user_id)))
        .scalars()
        .all()
    )
    assert notifs, "promoted student should be notified"

    # Audit logged.
    audits = (
        (
            await db_session.execute(
                select(AdmissionsAuditLog).where(AdmissionsAuditLog.action == "waitlist_offer_made")
            )
        )
        .scalars()
        .all()
    )
    assert audits, "waitlist promotion must be audited"


# --------------------------------------------------------------------------
# §10.5 — yield rate + melt + funnel tail compute correctly
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_yield_rate_melt_and_funnel(db_session, mock_institution_user):
    inst, program, pairs = await _seed(db_session, mock_institution_user, n_students=4, capacity=4)
    enr_svc = EnrollmentService(db_session)

    # 4 admitted. Student A: enrolled. B: confirmed-not-enrolled (melt). C: just
    # accepted (no confirm). D: admitted, never responded.
    pa, pb, pc, pd = pairs
    await _admit_and_accept(db_session, inst, pa[0], pa[1])
    await _admit_and_accept(db_session, inst, pb[0], pb[1])
    await _admit_and_accept(db_session, inst, pc[0], pc[1])
    # D: admit + offer but no student response.
    await ApplicationService(db_session).release_decision(
        inst.id, pd[1].id, "admitted", offer={"offer_type": "full_admission"}
    )
    await db_session.commit()

    # A → enrolled (final), B → confirmed only.
    await enr_svc.confirm_intent(pa[0].id, pa[1].id)
    await enr_svc.mark_enrollment_confirmed(
        inst.id, pa[1].id, final=True, actor_user_id=mock_institution_user.id
    )
    await enr_svc.confirm_intent(pb[0].id, pb[1].id)
    await db_session.commit()

    y = await YieldService(db_session).get_yield(inst.id)
    assert y["admitted"] == 4
    assert y["intent_confirmed"] == 2  # A + B
    assert y["enrolled"] == 1  # A
    assert y["yield_rate"] == pytest.approx(1 / 4)
    assert y["melt"] == 1  # B confirmed but not enrolled
    # Funnel tail: Admitted → Confirmed intent → Deposited → Enrolled
    funnel = {step["step"]: step["count"] for step in y["funnel"]}
    assert funnel["Admitted"] == 4
    assert funnel["Confirmed intent"] == 2
    assert funnel["Enrolled"] == 1
    assert y["target_class_size"] == 4


# --------------------------------------------------------------------------
# §10.6 — yield disparity by cohort routes to the fairness lens
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_yield_by_cohort_flags_disparity(db_session, mock_institution_user):
    inst, program, pairs = await _seed(
        db_session, mock_institution_user, n_students=12, capacity=12
    )
    enr_svc = EnrollmentService(db_session)
    # 6 "domestic" all enroll; 6 "international" none enroll → 100% vs 0% gap.
    for i, (profile, app) in enumerate(pairs):
        profile.residency_status_for_tuition = "domestic" if i < 6 else "international"
        db_session.add(profile)
    await db_session.commit()
    for i, (profile, app) in enumerate(pairs):
        await _admit_and_accept(db_session, inst, profile, app)
        if i < 6:
            await enr_svc.confirm_intent(profile.id, app.id)
            await enr_svc.mark_enrollment_confirmed(
                inst.id, app.id, final=True, actor_user_id=mock_institution_user.id
            )
    await db_session.commit()

    y = await YieldService(db_session).get_yield(inst.id)
    residency = next(c for c in y["cohorts"] if c["dimension"] == "residency")
    assert residency["disparity"] is not None
    assert residency["fairness_concern"] is True  # 100% vs 0% >> 15pp
    groups = {g["group"]: g["yield_rate"] for g in residency["groups"]}
    assert groups["domestic"] == pytest.approx(1.0)
    assert groups["international"] == pytest.approx(0.0)


# --------------------------------------------------------------------------
# §10.7 — deposit is status-only (no money) and audit-logged
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_record_deposit_is_status_only_and_audited(db_session, mock_institution_user):
    inst, program, pairs = await _seed(db_session, mock_institution_user)
    profile, app = pairs[0]
    await _admit_and_accept(db_session, inst, profile, app)
    enr_svc = EnrollmentService(db_session)
    await enr_svc.confirm_intent(profile.id, app.id)
    await db_session.commit()

    out = await enr_svc.record_deposit(
        inst.id, app.id, "paid", deposit_amount=500, actor_user_id=mock_institution_user.id
    )
    await db_session.commit()
    assert out["deposit_status"] == "paid"
    assert out["deposit_amount"] == 500
    assert out["state"] == "deposit_recorded"

    audit = (
        (
            await db_session.execute(
                select(AdmissionsAuditLog).where(
                    AdmissionsAuditLog.action == "enrollment_deposit_recorded"
                )
            )
        )
        .scalars()
        .first()
    )
    assert audit is not None
    assert "status-only" in (audit.description or "").lower()


# --------------------------------------------------------------------------
# Deferral request + approval (§2.2 / §3.1)
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_deferral_request_then_approve(db_session, mock_institution_user):
    inst, program, pairs = await _seed(db_session, mock_institution_user)
    profile, app = pairs[0]
    await _admit_and_accept(db_session, inst, profile, app)
    enr_svc = EnrollmentService(db_session)

    out = await enr_svc.request_deferral(profile.id, app.id, {"season": "Spring", "year": 2028})
    await db_session.commit()
    assert out["deferral"]["requested"] is True
    assert out["deferral"]["approved"] is False

    out2 = await enr_svc.approve_deferral(
        inst.id, app.id, approved=True, actor_user_id=mock_institution_user.id
    )
    await db_session.commit()
    assert out2["deferral"]["approved"] is True
    assert out2["state"] == "deferred"


# --------------------------------------------------------------------------
# HTTP smoke — endpoints wire end-to-end (one client per test: both client
# fixtures share the same get_current_user override, so they can't co-exist).
# --------------------------------------------------------------------------


async def _inst_program_for_student(
    db: AsyncSession, student_user: User
) -> tuple[Institution, Program, StudentProfile, Application]:
    admin = User(
        id=uuid.uuid4(),
        email=f"admin-{uuid.uuid4().hex[:6]}@example.com",
        cognito_sub=f"sub-{uuid.uuid4().hex[:8]}",
        role=UserRole("institution_admin"),
        is_active=True,
    )
    db.add(admin)
    await db.flush()
    inst = Institution(admin_user_id=admin.id, name="HTTP U", type="university", country="US")
    db.add(inst)
    await db.flush()
    program = Program(
        institution_id=inst.id, program_name="MS Data", degree_type="masters", is_published=True
    )
    db.add(program)
    await db.flush()
    profile = (
        await db.execute(select(StudentProfile).where(StudentProfile.user_id == student_user.id))
    ).scalar_one_or_none()
    if profile is None:
        profile = StudentProfile(user_id=student_user.id, first_name="Http", last_name="Stu")
        db.add(profile)
        await db.flush()
    app = Application(
        student_id=profile.id,
        program_id=program.id,
        status="submitted",
        submitted_at=datetime.now(UTC),
    )
    db.add(app)
    await db.commit()
    return inst, program, profile, app


@pytest.mark.asyncio
async def test_student_enrollment_endpoints_http(db_session, student_client, mock_student_user):
    inst, program, profile, app = await _inst_program_for_student(db_session, mock_student_user)

    # No accepted offer yet → enrollment window hidden (§7).
    r = await student_client.get(f"/api/v1/applications/me/{app.id}/enrollment")
    assert r.status_code == 200
    assert r.json()["available"] is False

    # Admit + accept, then confirm via HTTP → celebratory intent_confirmed.
    await _admit_and_accept(db_session, inst, profile, app)
    r = await student_client.post(f"/api/v1/applications/me/{app.id}/enrollment/confirm")
    assert r.status_code == 200, r.text
    assert r.json()["state"] == "intent_confirmed"


@pytest.mark.asyncio
async def test_institution_yield_endpoint_http(
    db_session, institution_client, mock_institution_user
):
    inst, program, pairs = await _seed(db_session, mock_institution_user, capacity=5)
    profile, app = pairs[0]
    await _admit_and_accept(db_session, inst, profile, app)
    await EnrollmentService(db_session).confirm_intent(profile.id, app.id)
    await db_session.commit()

    ry = await institution_client.get("/api/v1/institutions/me/yield")
    assert ry.status_code == 200, ry.text
    body = ry.json()
    assert body["admitted"] >= 1 and body["intent_confirmed"] >= 1

    rw = await institution_client.get("/api/v1/institutions/me/waitlist")
    assert rw.status_code == 200, rw.text

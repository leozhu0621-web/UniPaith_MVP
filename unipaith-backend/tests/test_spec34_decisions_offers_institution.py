"""Spec 34 · Decisions & Offers (institution-side) — decision release, offer
minting, student notification (Inbox + email + Calendar), batch release with
per-applicant audit, offer-status / yield-risk, and extend / rescind deadline.

Mirrors the student-side coverage in ``test_spec18_offers.py``.
"""

import uuid
from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.core.exceptions import BadRequestException
from unipaith.models.application import Application, OfferLetter
from unipaith.models.audit import AdmissionsAuditLog
from unipaith.models.engagement import Conversation, Message, StudentCalendar
from unipaith.models.institution import Institution, Program
from unipaith.models.student import StudentProfile
from unipaith.models.user import User, UserRole
from unipaith.models.workflow import Notification
from unipaith.services.application_service import ApplicationService


async def _seed(
    db: AsyncSession,
    inst_user: User,
    *,
    n_students: int = 1,
    status: str = "submitted",
) -> tuple[Institution, Program, list[tuple[StudentProfile, Application]]]:
    """Institution (owned by ``inst_user``) + one published program + N students
    each with a submitted application."""
    db.add(inst_user)
    await db.flush()
    inst = Institution(
        admin_user_id=inst_user.id,
        name="Foo U",
        type="university",
        country="US",
        city="Boston",
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
        profile = StudentProfile(user_id=su.id)
        db.add(profile)
        await db.flush()
        app = Application(
            student_id=profile.id,
            program_id=program.id,
            status=status,
            submitted_at=datetime.now(UTC),
        )
        db.add(app)
        await db.flush()
        pairs.append((profile, app))
    await db.commit()
    return inst, program, pairs


# --------------------------------------------------------------------------
# Single decision release (§3, §12)
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_admit_release_creates_offer_notifies_and_updates_calendar(
    db_session, mock_institution_user
):
    inst, program, pairs = await _seed(db_session, mock_institution_user)
    profile, app = pairs[0]
    svc = ApplicationService(db_session)

    app_out, offer = await svc.release_decision(
        inst.id,
        app.id,
        "admitted",
        actor_user_id=mock_institution_user.id,
        offer={
            "offer_type": "full_admission",
            "scholarship_amount": 15000,
            "response_deadline": (date.today() + timedelta(days=30)).isoformat(),
            "start_term": {"season": "Fall", "year": 2027},
        },
    )

    assert app_out.decision == "admitted"
    assert offer is not None and offer.status == "sent"
    assert offer.scholarship_amount == 15000
    assert offer.plain_language_brief and offer.plain_language_brief["summary"]

    # Inbox: a system thread + message for the application (§3.4)
    conv = (
        await db_session.execute(select(Conversation).where(Conversation.application_id == app.id))
    ).scalar_one_or_none()
    assert conv is not None and conv.thread_type == "system"
    msgs = (
        (await db_session.execute(select(Message).where(Message.conversation_id == conv.id)))
        .scalars()
        .all()
    )
    assert len(msgs) == 1 and "admitted" in msgs[0].message_body.lower()

    # Notification (in-app + email channel) fired
    notifs = (
        (
            await db_session.execute(
                select(Notification).where(Notification.user_id == profile.user_id)
            )
        )
        .scalars()
        .all()
    )
    assert any(n.notification_type == "decision_made" for n in notifs)

    # Calendar: a respond-by reminder at the deadline (§3.4)
    cal = (
        (
            await db_session.execute(
                select(StudentCalendar).where(StudentCalendar.application_id == app.id)
            )
        )
        .scalars()
        .all()
    )
    assert any(c.entry_type == "reminder" for c in cal)

    # Audit: a per-application decision_release entry (§5/§12)
    audits = (
        (
            await db_session.execute(
                select(AdmissionsAuditLog).where(AdmissionsAuditLog.application_id == app.id)
            )
        )
        .scalars()
        .all()
    )
    assert any(a.action == "decision_release" for a in audits)


@pytest.mark.asyncio
async def test_reject_release_notifies_without_offer(db_session, mock_institution_user):
    inst, _program, pairs = await _seed(db_session, mock_institution_user)
    profile, app = pairs[0]
    svc = ApplicationService(db_session)

    app_out, offer = await svc.release_decision(
        inst.id, app.id, "rejected", actor_user_id=mock_institution_user.id
    )
    assert app_out.decision == "rejected"
    assert offer is None
    # no offer row exists
    o = (
        await db_session.execute(select(OfferLetter).where(OfferLetter.application_id == app.id))
    ).scalar_one_or_none()
    assert o is None
    # but the student was still notified (§3.4)
    notifs = (
        (
            await db_session.execute(
                select(Notification).where(Notification.user_id == profile.user_id)
            )
        )
        .scalars()
        .all()
    )
    assert len(notifs) >= 1


@pytest.mark.asyncio
async def test_conditional_admission_mints_conditional_offer(db_session, mock_institution_user):
    inst, _program, pairs = await _seed(db_session, mock_institution_user)
    _profile, app = pairs[0]
    svc = ApplicationService(db_session)

    _app_out, offer = await svc.release_decision(
        inst.id,
        app.id,
        "conditional_admission",
        actor_user_id=mock_institution_user.id,
        offer={"conditions": {"summary": "Maintain a 3.5 GPA in your final term"}},
    )
    assert offer is not None
    assert offer.offer_type == "conditional"
    assert offer.conditions["summary"].startswith("Maintain")


@pytest.mark.asyncio
async def test_admit_release_auto_mints_offer_without_terms(db_session, mock_institution_user):
    """§3.3 — an accept with no explicit terms still produces an offer row."""
    inst, _program, pairs = await _seed(db_session, mock_institution_user)
    _profile, app = pairs[0]
    svc = ApplicationService(db_session)
    _app_out, offer = await svc.release_decision(inst.id, app.id, "admitted")
    assert offer is not None and offer.offer_type == "full_admission"


# --------------------------------------------------------------------------
# Batch release (§5)
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_batch_release_per_applicant_decisions_and_audit(db_session, mock_institution_user):
    inst, _program, pairs = await _seed(db_session, mock_institution_user, n_students=3)
    svc = ApplicationService(db_session)
    items = [
        {
            "application_id": pairs[0][1].id,
            "decision": "admitted",
            "offer": {"scholarship_amount": 5000},
        },
        {"application_id": pairs[1][1].id, "decision": "rejected"},
        {"application_id": pairs[2][1].id, "decision": "waitlisted"},
    ]
    result = await svc.batch_release_decisions(
        inst.id, items, actor_user_id=mock_institution_user.id
    )
    assert result["success_count"] == 3
    assert result["failed_count"] == 0

    # each application audited individually (§5)
    audits = (
        (
            await db_session.execute(
                select(AdmissionsAuditLog).where(AdmissionsAuditLog.action == "decision_release")
            )
        )
        .scalars()
        .all()
    )
    audited_apps = {a.application_id for a in audits}
    assert {p[1].id for p in pairs} <= audited_apps

    # decisions landed
    a0 = await db_session.get(Application, pairs[0][1].id)
    a1 = await db_session.get(Application, pairs[1][1].id)
    assert a0.decision == "admitted" and a1.decision == "rejected"


@pytest.mark.asyncio
async def test_batch_release_collects_per_item_errors(db_session, mock_institution_user):
    inst, _program, pairs = await _seed(db_session, mock_institution_user, n_students=1)
    svc = ApplicationService(db_session)
    bogus = uuid.uuid4()
    items = [
        {"application_id": pairs[0][1].id, "decision": "admitted"},
        {"application_id": bogus, "decision": "rejected"},
    ]
    result = await svc.batch_release_decisions(inst.id, items)
    assert result["success_count"] == 1
    assert result["failed_count"] == 1
    failed = [r for r in result["results"] if not r["ok"]]
    assert failed and str(bogus) == failed[0]["application_id"]


# --------------------------------------------------------------------------
# Offer-status / response flow (§7) + extend / rescind (§7/§8)
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_offer_status_reflects_student_response(db_session, mock_institution_user):
    inst, _program, pairs = await _seed(db_session, mock_institution_user)
    profile, app = pairs[0]
    svc = ApplicationService(db_session)

    await svc.release_decision(
        inst.id,
        app.id,
        "admitted",
        offer={"response_deadline": (date.today() + timedelta(days=10)).isoformat()},
    )

    status = await svc.get_offer_status(inst.id, app.id)
    assert status["has_offer"] is True
    assert status["response_state"] == "awaiting_response"
    assert status["days_remaining"] == 10
    assert status["deadline_passed"] is False

    # student accepts (student-side service) → institution status flips
    await svc.respond_to_offer(profile.id, app.id, "accepted")
    status2 = await svc.get_offer_status(inst.id, app.id)
    assert status2["response_state"] == "accepted"
    assert status2["student_response"] == "accepted"


@pytest.mark.asyncio
async def test_offer_status_deadline_passed(db_session, mock_institution_user):
    inst, _program, pairs = await _seed(db_session, mock_institution_user)
    _profile, app = pairs[0]
    svc = ApplicationService(db_session)
    await svc.release_decision(
        inst.id,
        app.id,
        "admitted",
        offer={"response_deadline": (date.today() - timedelta(days=2)).isoformat()},
    )
    status = await svc.get_offer_status(inst.id, app.id)
    assert status["deadline_passed"] is True
    assert status["response_state"] == "deadline_passed"


@pytest.mark.asyncio
async def test_extend_deadline_reactivates_and_renotifies(db_session, mock_institution_user):
    inst, _program, pairs = await _seed(db_session, mock_institution_user)
    profile, app = pairs[0]
    svc = ApplicationService(db_session)
    _app_out, offer = await svc.release_decision(
        inst.id,
        app.id,
        "admitted",
        offer={"response_deadline": (date.today() - timedelta(days=1)).isoformat()},
    )
    new_deadline = date.today() + timedelta(days=21)
    updated = await svc.extend_offer_deadline(inst.id, offer.id, new_deadline)
    assert updated.response_deadline == new_deadline
    status = await svc.get_offer_status(inst.id, app.id)
    assert status["deadline_passed"] is False
    assert status["days_remaining"] == 21


@pytest.mark.asyncio
async def test_cannot_extend_after_student_responded(db_session, mock_institution_user):
    inst, _program, pairs = await _seed(db_session, mock_institution_user)
    profile, app = pairs[0]
    svc = ApplicationService(db_session)
    _app_out, offer = await svc.release_decision(
        inst.id,
        app.id,
        "admitted",
        offer={"response_deadline": (date.today() + timedelta(days=5)).isoformat()},
    )
    await svc.respond_to_offer(profile.id, app.id, "declined")
    with pytest.raises(BadRequestException):
        await svc.extend_offer_deadline(inst.id, offer.id, date.today() + timedelta(days=30))


@pytest.mark.asyncio
async def test_rescind_offer(db_session, mock_institution_user):
    inst, _program, pairs = await _seed(db_session, mock_institution_user)
    _profile, app = pairs[0]
    svc = ApplicationService(db_session)
    _app_out, offer = await svc.release_decision(
        inst.id,
        app.id,
        "admitted",
        offer={"response_deadline": (date.today() - timedelta(days=3)).isoformat()},
    )
    rescinded = await svc.rescind_offer(inst.id, offer.id)
    assert rescinded.status == "rescinded"


# --------------------------------------------------------------------------
# Yield-risk alerts (§6)
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_yield_risk_alerts_fire_on_threshold(db_session, mock_institution_user):
    inst, _program, pairs = await _seed(db_session, mock_institution_user, n_students=3)
    svc = ApplicationService(db_session)
    # student 0: deadline in 3 days, unanswered → high
    await svc.release_decision(
        inst.id,
        pairs[0][1].id,
        "admitted",
        offer={"response_deadline": (date.today() + timedelta(days=3)).isoformat()},
    )
    # student 1: deadline in 12 days, unanswered → medium
    await svc.release_decision(
        inst.id,
        pairs[1][1].id,
        "admitted",
        offer={"response_deadline": (date.today() + timedelta(days=12)).isoformat()},
    )
    # student 2: deadline in 3 days, but student accepted → NOT a risk
    await svc.release_decision(
        inst.id,
        pairs[2][1].id,
        "admitted",
        offer={"response_deadline": (date.today() + timedelta(days=3)).isoformat()},
    )
    await svc.respond_to_offer(pairs[2][0].id, pairs[2][1].id, "accepted")

    result = await svc.get_yield_risk_alerts(inst.id)
    ids = {a["application_id"] for a in result["alerts"]}
    assert str(pairs[0][1].id) in ids  # high-risk surfaced
    assert str(pairs[1][1].id) in ids  # medium-risk surfaced
    assert str(pairs[2][1].id) not in ids  # accepted excluded
    by_id = {a["application_id"]: a for a in result["alerts"]}
    assert by_id[str(pairs[0][1].id)]["risk_level"] == "high"
    assert by_id[str(pairs[1][1].id)]["risk_level"] == "medium"


# --------------------------------------------------------------------------
# HTTP wiring (end-to-end via institution client)
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_release_endpoint_e2e(institution_client, db_session, mock_institution_user):
    inst, _program, pairs = await _seed(db_session, mock_institution_user)
    _profile, app = pairs[0]
    r = await institution_client.post(
        f"/api/v1/applications/review/{app.id}/release",
        json={
            "decision": "admitted",
            "offer": {
                "scholarship_amount": 10000,
                "response_deadline": (date.today() + timedelta(days=14)).isoformat(),
            },
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["application"]["decision"] == "admitted"
    assert body["offer"] is not None
    assert body["offer"]["scholarship_amount"] == 10000

    # offer-status endpoint
    s = await institution_client.get(f"/api/v1/applications/review/{app.id}/offer-status")
    assert s.status_code == 200, s.text
    assert s.json()["response_state"] == "awaiting_response"


@pytest.mark.asyncio
async def test_batch_release_endpoint_e2e(institution_client, db_session, mock_institution_user):
    inst, _program, pairs = await _seed(db_session, mock_institution_user, n_students=2)
    r = await institution_client.post(
        "/api/v1/applications/batch-release-decision",
        json={
            "items": [
                {"application_id": str(pairs[0][1].id), "decision": "admitted"},
                {"application_id": str(pairs[1][1].id), "decision": "deferred"},
            ]
        },
    )
    assert r.status_code == 200, r.text
    assert r.json()["success_count"] == 2


@pytest.mark.asyncio
async def test_yield_risks_endpoint_e2e(institution_client, db_session, mock_institution_user):
    inst, _program, pairs = await _seed(db_session, mock_institution_user)
    svc = ApplicationService(db_session)
    await svc.release_decision(
        inst.id,
        pairs[0][1].id,
        "admitted",
        offer={"response_deadline": (date.today() + timedelta(days=4)).isoformat()},
    )
    r = await institution_client.get("/api/v1/institutions/me/intelligence/yield-risks")
    assert r.status_code == 200, r.text
    assert r.json()["count"] >= 1

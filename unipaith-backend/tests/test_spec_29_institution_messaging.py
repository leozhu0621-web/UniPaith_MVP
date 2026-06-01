"""Spec 29 (Institution Messaging & Inbox) — §12 acceptance.

Covers:
- reason_code → student action_label mapping + due-date requirement (§4/§5)
- request_document + attach → student checklist item + calendar nudge + the
  student's Spec 17 thread shows "Document requested" with a due date (§5/§12)
- assignment + reassignment audit-logged (§2/§12)
- bulk → one thread per recipient; marketing-consent suppression applies to
  marketing-class only, not active-application transactional messages (§6/§12)
- AI draft renders, is editable, send tagged AI-assisted in the audit (§8/§12)
- role scoping: student cannot read the institution inbox; institution cannot
  read the student inbox (§12)
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai.institution_reply import InstitutionReplyResult
from unipaith.config import settings
from unipaith.models.application import Application, ApplicationChecklist
from unipaith.models.audit import AdmissionsAuditLog
from unipaith.models.engagement import Conversation, Message, StudentCalendar
from unipaith.models.institution import Institution, Program
from unipaith.models.student import StudentDataConsent, StudentProfile
from unipaith.models.user import User, UserRole
from unipaith.models.workflow import Notification
from unipaith.services.inbox_service import InboxService
from unipaith.services.institution_inbox_service import InstitutionInboxService

INST_INBOX = "/api/v1/institutions/me/inbox"
STU_INBOX = "/api/v1/students/me/inbox"


# ── seed helpers ────────────────────────────────────────────────────────────


async def _institution(db: AsyncSession, inst_user: User) -> Institution:
    db.add(inst_user)
    inst = Institution(
        admin_user_id=inst_user.id,
        name="University of Foo",
        type="university",
        country="United States",
    )
    db.add(inst)
    await db.flush()
    return inst


async def _student(db: AsyncSession, *, first: str = "Sienna") -> tuple[User, StudentProfile]:
    user = User(
        id=uuid.uuid4(),
        email=f"{first.lower()}-{uuid.uuid4().hex[:6]}@example.com",
        cognito_sub=f"dev-{uuid.uuid4().hex[:8]}",
        role=UserRole.student,
        is_active=True,
    )
    db.add(user)
    profile = StudentProfile(user_id=user.id, first_name=first, last_name="Reyes")
    db.add(profile)
    await db.flush()
    return user, profile


async def _program(db: AsyncSession, inst: Institution) -> Program:
    program = Program(
        institution_id=inst.id,
        program_name="CS MS",
        degree_type="masters",
        is_published=True,
        tuition=50000,
        requirements={"recommendation_letters": 2},
    )
    db.add(program)
    await db.flush()
    return program


async def _application(db: AsyncSession, profile, program, status="under_review") -> Application:
    app = Application(student_id=profile.id, program_id=program.id, status=status)
    db.add(app)
    await db.flush()
    return app


async def _thread(
    db: AsyncSession,
    *,
    student_id,
    institution_id,
    program_id=None,
    application_id=None,
    student_message: str | None = "Hi — my recommender form still shows missing.",
) -> Conversation:
    base = datetime.now(UTC)
    conv = Conversation(
        student_id=student_id,
        institution_id=institution_id,
        program_id=program_id,
        application_id=application_id,
        thread_type="human",
        waiting_on="school",  # applicant wrote in → we owe a reply
        subject="Recommender form",
        status="active",
        last_message_at=base,
    )
    db.add(conv)
    await db.flush()
    if student_message:
        db.add(
            Message(
                conversation_id=conv.id,
                sender_type="student",
                message_body=student_message,
                status="sent",
                sent_at=base,
            )
        )
        await db.flush()
    return conv


# ── §4/§5 reason mapping + due-date requirement ──────────────────────────────


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "reason,expected_action",
    [
        ("request_document", "document_requested"),
        ("request_clarification", "clarification_required"),
        ("interview_invite", "interview_invite"),
        ("status_update", "status_update_only"),
        ("general_reply", "needs_reply"),
        ("decision_notice", "status_update_only"),
    ],
)
async def test_reason_code_maps_to_student_action_label(
    db_session: AsyncSession, mock_institution_user: User, reason, expected_action
):
    inst = await _institution(db_session, mock_institution_user)
    _user, profile = await _student(db_session)
    program = await _program(db_session, inst)
    app = await _application(db_session, profile, program)
    conv = await _thread(
        db_session,
        student_id=profile.id,
        institution_id=inst.id,
        program_id=program.id,
        application_id=app.id,
    )

    svc = InstitutionInboxService(db_session)
    due = datetime.now(UTC) + timedelta(days=5)
    await svc.post_message(
        mock_institution_user.id,
        conv.id,
        body="Please see the note.",
        reason_code=reason,
        due_date=due,
    )
    await db_session.refresh(conv)
    assert conv.action_label == expected_action
    assert conv.reason_code == reason
    assert conv.waiting_on == "student"


@pytest.mark.asyncio
async def test_due_date_required_for_request_document(
    db_session: AsyncSession, mock_institution_user: User
):
    inst = await _institution(db_session, mock_institution_user)
    _user, profile = await _student(db_session)
    program = await _program(db_session, inst)
    conv = await _thread(
        db_session, student_id=profile.id, institution_id=inst.id, program_id=program.id
    )
    svc = InstitutionInboxService(db_session)
    with pytest.raises(Exception) as exc:
        await svc.post_message(
            mock_institution_user.id,
            conv.id,
            body="Please upload your transcript.",
            reason_code="request_document",
            due_date=None,
        )
    assert "due date" in str(exc.value).lower()


# ── §5/§12 request_document → checklist item + calendar + student mirror ─────


@pytest.mark.asyncio
async def test_request_document_creates_checklist_item_and_student_thread(
    db_session: AsyncSession, mock_institution_user: User
):
    inst = await _institution(db_session, mock_institution_user)
    student_user, profile = await _student(db_session)
    program = await _program(db_session, inst)
    app = await _application(db_session, profile, program)
    # Pre-existing checklist with one item.
    db_session.add(
        ApplicationChecklist(
            student_id=profile.id,
            program_id=program.id,
            items=[{"key": "essays", "category": "essays", "label": "Essays", "completed": False}],
            completion_percentage=0,
        )
    )
    conv = await _thread(
        db_session,
        student_id=profile.id,
        institution_id=inst.id,
        program_id=program.id,
        application_id=app.id,
    )

    svc = InstitutionInboxService(db_session)
    due = datetime.now(UTC) + timedelta(days=7)
    await svc.post_message(
        mock_institution_user.id,
        conv.id,
        body="Please upload your official transcript.",
        reason_code="request_document",
        attachments=[{"name": "Transcript request", "kind": "document"}],
        due_date=due,
        request_document=True,
        requested_item="transcripts",
    )
    await db_session.refresh(conv)

    # Thread carries the student-facing label + due date on the institution end.
    assert conv.action_label == "document_requested"
    assert conv.due_date is not None
    assert conv.linked_checklist_item_category == "transcripts"

    # A checklist item was created for the applicant.
    checklist = await db_session.scalar(
        select(ApplicationChecklist).where(
            ApplicationChecklist.student_id == profile.id,
            ApplicationChecklist.program_id == program.id,
        )
    )
    keys = {it.get("key") for it in (checklist.items or [])}
    assert f"inst_request:{conv.id}" in keys

    # A calendar nudge with the due date lands on the student's end.
    cal = await db_session.scalar(
        select(StudentCalendar).where(StudentCalendar.reference_id == conv.id)
    )
    assert cal is not None and cal.status == "scheduled"

    # The student's Spec 17 inbox shows the thread as "Document requested".
    student_threads = await InboxService(db_session).list_threads(student_user.id)
    match = next((t for t in student_threads if t.id == conv.id), None)
    assert match is not None
    assert match.action_label == "document_requested"
    assert match.due_date is not None

    # The applicant got an (essential) notification.
    notif = await db_session.scalar(
        select(Notification).where(Notification.user_id == student_user.id)
    )
    assert notif is not None
    assert notif.notification_type == "application_missing_item"

    # Audit ledger row written for the send.
    audit = await db_session.scalar(
        select(AdmissionsAuditLog).where(
            AdmissionsAuditLog.institution_id == inst.id,
            AdmissionsAuditLog.action == "inbox.message_sent",
        )
    )
    assert audit is not None
    assert audit.metadata_json.get("reason_code") == "request_document"


# ── §2/§12 assignment + reassignment audit ──────────────────────────────────


@pytest.mark.asyncio
async def test_assignment_and_reassignment_audit_logged(
    db_session: AsyncSession, mock_institution_user: User
):
    inst = await _institution(db_session, mock_institution_user)
    _user, profile = await _student(db_session)
    program = await _program(db_session, inst)
    conv = await _thread(
        db_session, student_id=profile.id, institution_id=inst.id, program_id=program.id
    )
    svc = InstitutionInboxService(db_session)

    # Assign to self (the admin is the assignable roster in MVP).
    res = await svc.assign(mock_institution_user.id, conv.id, mock_institution_user.id)
    assert res.assigned_to == mock_institution_user.id

    # Unassign (reassignment to None).
    res2 = await svc.assign(mock_institution_user.id, conv.id, None)
    assert res2.assigned_to is None

    # Assigning to a non-member is rejected.
    with pytest.raises(Exception):
        await svc.assign(mock_institution_user.id, conv.id, uuid.uuid4())

    logs = (
        (
            await db_session.execute(
                select(AdmissionsAuditLog).where(AdmissionsAuditLog.action == "inbox.assigned")
            )
        )
        .scalars()
        .all()
    )
    assert len(logs) >= 2  # assign + unassign both logged


# ── §6/§12 bulk + reason-aware suppression ───────────────────────────────────


@pytest.mark.asyncio
async def test_bulk_marketing_suppresses_outreach_optout(
    db_session: AsyncSession, mock_institution_user: User
):
    inst = await _institution(db_session, mock_institution_user)
    program = await _program(db_session, inst)
    u1, p1 = await _student(db_session, first="Ada")
    u2, p2 = await _student(db_session, first="Bo")
    a1 = await _application(db_session, p1, program)
    a2 = await _application(db_session, p2, program)
    # Bo opted out of outreach.
    db_session.add(StudentDataConsent(student_id=p2.id, consent_outreach=False))
    await db_session.flush()

    svc = InstitutionInboxService(db_session)

    # Marketing-class reason (status_update) → Bo is suppressed.
    res = await svc.bulk_message(
        mock_institution_user.id,
        application_ids=[a1.id, a2.id],
        body="A quick update on your program {{program}}.",
        reason_code="status_update",
    )
    assert res.recipient_count == 2
    assert res.sent_count == 1
    assert res.suppressed_count == 1


@pytest.mark.asyncio
async def test_bulk_transactional_not_suppressed(
    db_session: AsyncSession, mock_institution_user: User
):
    inst = await _institution(db_session, mock_institution_user)
    program = await _program(db_session, inst)
    u1, p1 = await _student(db_session, first="Ada")
    u2, p2 = await _student(db_session, first="Bo")
    a1 = await _application(db_session, p1, program)
    a2 = await _application(db_session, p2, program)
    db_session.add(StudentDataConsent(student_id=p2.id, consent_outreach=False))
    await db_session.flush()

    svc = InstitutionInboxService(db_session)
    due = datetime.now(UTC) + timedelta(days=3)
    # Transactional reason tied to an active application → NOT suppressed.
    res = await svc.bulk_message(
        mock_institution_user.id,
        application_ids=[a1.id, a2.id],
        body="Please complete this item.",
        reason_code="request_document",
        due_date=due,
    )
    assert res.sent_count == 2
    assert res.suppressed_count == 0
    # One thread per recipient.
    assert len(res.thread_ids) == 2
    assert len(set(res.thread_ids)) == 2


# ── §8/§12 AI draft renders + editable + send tagged AI-assisted ─────────────


class _StubDrafter:
    async def draft(self, *, input_view, db=None):
        return InstitutionReplyResult(
            draft="Hi Sienna — please upload your official transcript when you can.",
            tone="professional",
            length="short",
        )


@pytest.mark.asyncio
async def test_ai_draft_renders_and_send_is_tagged(
    db_session: AsyncSession, mock_institution_user: User, monkeypatch
):
    monkeypatch.setattr(settings, "ai_institution_reply_v2_enabled", True)
    inst = await _institution(db_session, mock_institution_user)
    _user, profile = await _student(db_session)
    program = await _program(db_session, inst)
    app = await _application(db_session, profile, program)
    conv = await _thread(
        db_session,
        student_id=profile.id,
        institution_id=inst.id,
        program_id=program.id,
        application_id=app.id,
    )

    svc = InstitutionInboxService(db_session, reply_drafter=_StubDrafter())
    draft = await svc.ai_draft(mock_institution_user.id, conv.id)
    assert draft is not None
    assert "transcript" in draft.draft.lower()

    # Send seeded from the AI draft → message + audit are tagged AI-assisted.
    await svc.post_message(
        mock_institution_user.id,
        conv.id,
        body=draft.draft,
        reason_code="request_clarification",
        due_date=datetime.now(UTC) + timedelta(days=4),
        ai_draft_used=True,
    )
    msg = await db_session.scalar(
        select(Message).where(
            Message.conversation_id == conv.id, Message.sender_type == "institution"
        )
    )
    assert msg is not None and msg.ai_draft_used is True
    audit = await db_session.scalar(
        select(AdmissionsAuditLog).where(AdmissionsAuditLog.action == "inbox.message_sent")
    )
    assert audit.metadata_json.get("ai_assisted") is True


@pytest.mark.asyncio
async def test_ai_draft_hidden_when_flag_off(
    db_session: AsyncSession, mock_institution_user: User, monkeypatch
):
    monkeypatch.setattr(settings, "ai_institution_reply_v2_enabled", False)
    inst = await _institution(db_session, mock_institution_user)
    _user, profile = await _student(db_session)
    program = await _program(db_session, inst)
    conv = await _thread(
        db_session, student_id=profile.id, institution_id=inst.id, program_id=program.id
    )
    svc = InstitutionInboxService(db_session, reply_drafter=_StubDrafter())
    assert await svc.ai_draft(mock_institution_user.id, conv.id) is None


# ── §12 role scoping ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_student_cannot_read_institution_inbox(student_client: AsyncClient):
    r = await student_client.get(f"{INST_INBOX}/threads")
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_institution_cannot_read_student_inbox(institution_client: AsyncClient):
    r = await institution_client.get(f"{STU_INBOX}/threads")
    assert r.status_code == 403


# ── list + get thread (context panel) ────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_and_get_thread_with_context(
    db_session: AsyncSession, mock_institution_user: User
):
    inst = await _institution(db_session, mock_institution_user)
    _user, profile = await _student(db_session)
    program = await _program(db_session, inst)
    app = await _application(db_session, profile, program, status="under_review")
    db_session.add(
        ApplicationChecklist(
            student_id=profile.id,
            program_id=program.id,
            items=[
                {"key": "essays", "label": "Essays", "completed": True, "status": "completed"},
                {"key": "rec", "label": "Recommendation 2", "completed": False},
            ],
            completion_percentage=50,
        )
    )
    conv = await _thread(
        db_session,
        student_id=profile.id,
        institution_id=inst.id,
        program_id=program.id,
        application_id=app.id,
    )
    svc = InstitutionInboxService(db_session)

    threads = await svc.list_threads(mock_institution_user.id)
    assert len(threads) == 1
    row = threads[0]
    assert row.status == "awaiting_us"  # applicant wrote in
    assert row.unread_count == 1
    assert row.student.name == "Sienna Reyes"

    full = await svc.get_thread(mock_institution_user.id, conv.id)
    assert full.context.checklist_total == 2
    assert full.context.checklist_complete == 1
    assert "Recommendation 2" in full.context.missing_items
    assert full.context.stage == "under_review"
    # Opening the thread marks the applicant's message read.
    refreshed = await svc.list_threads(mock_institution_user.id)
    assert refreshed[0].unread_count == 0

"""Spec 29 — Institution inbox: reason-coded send, assign, bulk, student mirror."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai.institution_inbox_reply import InstitutionReplyResult
from unipaith.config import settings
from unipaith.models.application import Application
from unipaith.models.audit import AdmissionsAuditLog
from unipaith.models.engagement import Conversation, Message, StudentCalendar
from unipaith.models.institution import Institution, Program
from unipaith.models.student import StudentDataConsent, StudentProfile
from unipaith.models.user import User
from unipaith.services.checklist_service import ChecklistService
from unipaith.services.institution_inbox_service import InstitutionInboxService

INST_INBOX = "/api/v1/institutions/me/inbox"
STUDENT_INBOX = "/api/v1/students/me/inbox"


async def _seed(
    db: AsyncSession, student_user: User, institution_user: User
) -> tuple[StudentProfile, Institution, Program]:
    db.add(student_user)
    db.add(institution_user)
    await db.flush()
    profile = StudentProfile(user_id=student_user.id, first_name="Sienna", last_name="Park")
    db.add(profile)
    institution = Institution(
        admin_user_id=institution_user.id,
        name="University of Foo",
        type="university",
        country="United States",
    )
    db.add(institution)
    await db.flush()
    program = Program(
        institution_id=institution.id,
        program_name="CS MS",
        degree_type="masters",
        is_published=True,
        tuition=50000,
        requirements={"recommendation_letters": 2},
    )
    db.add(program)
    await db.flush()
    return profile, institution, program


async def _thread(
    db: AsyncSession,
    *,
    student_id,
    institution_id,
    program_id=None,
    application_id=None,
    action_label=None,
    waiting_on="school",
    messages=None,
) -> Conversation:
    conv = Conversation(
        student_id=student_id,
        institution_id=institution_id,
        program_id=program_id,
        application_id=application_id,
        thread_type="human",
        action_label=action_label,
        waiting_on=waiting_on,
        subject="Recommender question",
        status="open",
        last_message_at=datetime.now(UTC),
    )
    db.add(conv)
    await db.flush()
    for m in messages or []:
        db.add(
            Message(
                conversation_id=conv.id,
                sender_type=m.get("sender_type", "student"),
                sender_id=m.get("sender_id"),
                message_body=m["body"],
            )
        )
    await db.flush()
    return conv


@pytest.mark.asyncio
async def test_institution_send_request_document_updates_student_inbox(
    institution_client: AsyncClient,
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    profile, institution, program = await _seed(
        db_session, mock_student_user, mock_institution_user
    )
    app = Application(student_id=profile.id, program_id=program.id, status="in_review")
    db_session.add(app)
    await db_session.flush()
    await ChecklistService(db_session).generate_checklist(profile.id, app.id)

    thread = await _thread(
        db_session,
        student_id=profile.id,
        institution_id=institution.id,
        program_id=program.id,
        application_id=app.id,
        waiting_on="school",
        messages=[
            {"sender_type": "student", "sender_id": mock_student_user.id, "body": "Still missing?"}
        ],
    )
    await db_session.commit()

    due = (datetime.now(UTC) + timedelta(days=5)).isoformat()
    r = await institution_client.post(
        f"{INST_INBOX}/threads/{thread.id}/messages",
        json={
            "body": "Please upload your mid-year transcript.",
            "reason_code": "request_document",
            "due_date": due,
            "checklist_category": "transcript",
        },
    )
    assert r.status_code == 201

    sr = await student_client.get(f"{STUDENT_INBOX}/threads/{thread.id}")
    assert sr.status_code == 200
    assert sr.json()["action_label"] == "document_requested"
    assert sr.json()["due_date"] is not None
    assert sr.json()["waiting_on"] == "student"

    conv = await db_session.scalar(select(Conversation).where(Conversation.id == thread.id))
    assert conv.action_label == "document_requested"
    assert conv.linked_checklist_item_category == "transcript"

    cal = await db_session.scalar(
        select(StudentCalendar).where(StudentCalendar.reference_id == thread.id)
    )
    assert cal is not None


@pytest.mark.asyncio
async def test_assign_thread_audit_logged(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    profile, institution, program = await _seed(
        db_session, mock_student_user, mock_institution_user
    )
    thread = await _thread(
        db_session,
        student_id=profile.id,
        institution_id=institution.id,
        program_id=program.id,
        waiting_on="school",
    )
    await db_session.commit()

    r = await institution_client.post(
        f"{INST_INBOX}/threads/{thread.id}/assign",
        json={"staff_user_id": str(mock_institution_user.id)},
    )
    assert r.status_code == 200
    assert r.json()["assigned_to"] == str(mock_institution_user.id)

    logs = list(
        (
            await db_session.execute(
                select(AdmissionsAuditLog).where(
                    AdmissionsAuditLog.action == "inbox_thread_assigned",
                    AdmissionsAuditLog.entity_id == str(thread.id),
                )
            )
        ).scalars()
    )
    assert len(logs) >= 1


@pytest.mark.asyncio
async def test_bulk_respects_marketing_consent(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    profile, institution, program = await _seed(
        db_session, mock_student_user, mock_institution_user
    )
    db_session.add(StudentDataConsent(student_id=profile.id, consent_outreach=False))
    await db_session.commit()

    r = await institution_client.post(
        f"{INST_INBOX}/bulk-message",
        json={
            "application_ids": [],
            "segment_id": None,
            "body": "Hello prospects",
            "reason_code": "status_update",
        },
    )
    assert r.status_code == 400  # no segment or apps

    app = Application(student_id=profile.id, program_id=program.id, status="draft")
    db_session.add(app)
    await db_session.flush()
    await db_session.commit()

    r2 = await institution_client.post(
        f"{INST_INBOX}/bulk-message",
        json={
            "application_ids": [str(app.id)],
            "body": "Your application status was updated.",
            "reason_code": "status_update",
        },
    )
    assert r2.status_code == 200
    assert r2.json()["sent_count"] == 1


class _FakeInstDrafter:
    async def draft(self, *, input_view, db=None, student_id=None):
        return InstitutionReplyResult(
            draft="Thank you for reaching out — we are reviewing your file."
        )


@pytest.mark.asyncio
async def test_ai_draft_and_ai_assisted_send(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
    monkeypatch,
):
    monkeypatch.setattr(settings, "ai_institution_inbox_v2_enabled", True)
    profile, institution, program = await _seed(
        db_session, mock_student_user, mock_institution_user
    )
    thread = await _thread(
        db_session,
        student_id=profile.id,
        institution_id=institution.id,
        program_id=program.id,
        waiting_on="school",
        messages=[{"body": "Question about deadline"}],
    )
    await db_session.commit()

    svc = InstitutionInboxService(db_session, reply_drafter=_FakeInstDrafter())
    draft = await svc.ai_draft(mock_institution_user.id, thread.id)
    assert draft is not None
    assert "reviewing" in draft.draft

    r = await institution_client.post(
        f"{INST_INBOX}/threads/{thread.id}/messages",
        json={
            "body": draft.draft,
            "reason_code": "general_reply",
            "ai_draft_used": True,
        },
    )
    assert r.status_code == 201
    msg = await db_session.scalar(
        select(Message).where(Message.conversation_id == thread.id).order_by(Message.sent_at.desc())
    )
    assert msg.ai_draft_used is True

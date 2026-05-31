"""Spec 17 (Inbox) — filters/sort, reply persistence, mark-complete
propagation to checklist + calendar, and AI suggested-reply behavior."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai.inbox_reply import InboxReplyResult
from unipaith.config import settings
from unipaith.models.application import Application
from unipaith.models.engagement import Conversation, Message, StudentCalendar
from unipaith.models.institution import Institution, Program
from unipaith.models.student import StudentProfile
from unipaith.models.user import User
from unipaith.services.checklist_service import ChecklistService
from unipaith.services.inbox_service import InboxService

INBOX = "/api/v1/students/me/inbox"


# ── seed helpers ────────────────────────────────────────────────────────────


async def _seed(
    db: AsyncSession, student_user: User, institution_user: User
) -> tuple[StudentProfile, Institution, Program]:
    db.add(institution_user)
    profile = StudentProfile(user_id=student_user.id, first_name="Sienna", last_name="Reyes")
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


async def _application(db: AsyncSession, student_id, program_id) -> Application:
    app = Application(student_id=student_id, program_id=program_id, status="draft")
    db.add(app)
    await db.flush()
    return app


async def _thread(
    db: AsyncSession,
    *,
    student_id,
    institution_id=None,
    program_id=None,
    application_id=None,
    thread_type="human",
    action_label=None,
    waiting_on="none",
    due_date=None,
    linked_category=None,
    subject="Thread",
    messages=None,
) -> Conversation:
    base = datetime.now(UTC)
    conv = Conversation(
        student_id=student_id,
        institution_id=institution_id,
        program_id=program_id,
        application_id=application_id,
        thread_type=thread_type,
        action_label=action_label,
        waiting_on=waiting_on,
        due_date=due_date,
        linked_checklist_item_category=linked_category,
        subject=subject,
        status="active",
        last_message_at=base,
    )
    db.add(conv)
    await db.flush()
    for i, m in enumerate(messages or []):
        db.add(
            Message(
                conversation_id=conv.id,
                sender_type=m["sender_type"],
                sender_id=m.get("sender_id"),
                message_body=m["body"],
                status="sent",
                read_at=m.get("read_at"),
                sent_at=base + timedelta(seconds=i),
            )
        )
    await db.flush()
    return conv


# ── filters + sort ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_filters_and_sort(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    profile, institution, program = await _seed(
        db_session, mock_student_user, mock_institution_user
    )
    app = await _application(db_session, profile.id, program.id)

    await _thread(
        db_session,
        student_id=profile.id,
        institution_id=institution.id,
        program_id=program.id,
        application_id=app.id,
        action_label="needs_reply",
        waiting_on="student",
        due_date=datetime.now(UTC) + timedelta(days=2),
        subject="Please reply",
    )
    await _thread(
        db_session,
        student_id=profile.id,
        thread_type="system",
        action_label="document_requested",
        waiting_on="student",
        subject="Missing item",
        messages=[{"sender_type": "system", "sender_id": None, "body": "Transcript missing"}],
    )
    await _thread(
        db_session,
        student_id=profile.id,
        institution_id=institution.id,
        action_label="completed",
        waiting_on="none",
        subject="Done",
    )
    await db_session.commit()

    # No filter → all 3
    r = await student_client.get(f"{INBOX}/threads")
    assert r.status_code == 200
    assert len(r.json()) == 3

    # type=system → 1
    r = await student_client.get(f"{INBOX}/threads", params={"type": "system"})
    assert [t["type"] for t in r.json()] == ["system"]

    # state=needs_reply → 1
    r = await student_client.get(f"{INBOX}/threads", params={"state": "needs_reply"})
    assert [t["action_label"] for t in r.json()] == ["needs_reply"]

    # state=requested → the document_requested system thread
    r = await student_client.get(f"{INBOX}/threads", params={"state": "requested"})
    assert [t["action_label"] for t in r.json()] == ["document_requested"]

    # application filter → only the one with application_id
    r = await student_client.get(f"{INBOX}/threads", params={"application_id": str(app.id)})
    assert len(r.json()) == 1 and r.json()[0]["subject"] == "Please reply"

    # urgent sort (default): completed sinks to the bottom
    r = await student_client.get(f"{INBOX}/threads", params={"sort": "urgent"})
    assert r.json()[-1]["action_label"] == "completed"

    # action_required sort: needs_reply first
    r = await student_client.get(f"{INBOX}/threads", params={"sort": "action_required"})
    assert r.json()[0]["action_label"] == "needs_reply"


# ── get thread marks read ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_thread_marks_read_and_returns_messages(
    student_client: AsyncClient,
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
        action_label="needs_reply",
        waiting_on="student",
        subject="Clarify",
        messages=[
            {
                "sender_type": "institution",
                "sender_id": mock_institution_user.id,
                "body": "Hi Sienna",
            },
        ],
    )
    await db_session.commit()

    # Before open: unread
    r = await student_client.get(f"{INBOX}/threads")
    assert r.json()[0]["unread"] is True

    # Open thread
    r = await student_client.get(f"{INBOX}/threads/{thread.id}")
    assert r.status_code == 200
    data = r.json()
    assert len(data["messages"]) == 1
    assert data["messages"][0]["sender"] == "admissions_officer"
    assert {p["role"] for p in data["participants"]} == {"student", "admissions_officer"}

    # After open: read
    r = await student_client.get(f"{INBOX}/threads")
    assert r.json()[0]["unread"] is False


# ── reply persists + thread updated + ai_draft_used ─────────────────────────


@pytest.mark.asyncio
async def test_reply_persists_and_records_ai_draft(
    student_client: AsyncClient,
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
        action_label="needs_reply",
        waiting_on="student",
        subject="Reply please",
    )
    await db_session.commit()

    r = await student_client.post(
        f"{INBOX}/threads/{thread.id}/messages",
        json={
            "body": "Thanks for the heads up — sending now.",
            "attachments": [{"name": "transcript.pdf", "kind": "document"}],
            "ai_draft_used": True,
        },
    )
    assert r.status_code == 201
    body = r.json()
    assert body["sender"] == "student"
    assert body["attachments"][0]["name"] == "transcript.pdf"

    # The message persisted with ai_draft_used + the thread flipped to school.
    msg = await db_session.scalar(select(Message).where(Message.conversation_id == thread.id))
    assert msg.ai_draft_used is True
    conv = await db_session.scalar(select(Conversation).where(Conversation.id == thread.id))
    assert conv.waiting_on == "school"
    assert conv.last_message_at is not None


# ── mark complete → checklist override (durable) + calendar ─────────────────


@pytest.mark.asyncio
async def test_mark_complete_updates_checklist_and_calendar(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    profile, institution, program = await _seed(
        db_session, mock_student_user, mock_institution_user
    )
    app = await _application(db_session, profile.id, program.id)

    # A real checklist with a recommendation_letters item (completed=False).
    checklist = await ChecklistService(db_session).generate_checklist(profile.id, app.id)
    rec = next(i for i in checklist.items if i["category"] == "recommendation_letters")
    assert rec["completed"] is False

    thread = await _thread(
        db_session,
        student_id=profile.id,
        institution_id=institution.id,
        program_id=program.id,
        application_id=app.id,
        action_label="document_requested",
        waiting_on="student",
        linked_category="recommendation_letters",
        subject="Second recommender",
    )
    # A linked calendar deadline (reference_id = thread id).
    cal = StudentCalendar(
        student_id=profile.id,
        entry_type="inbox_deadline",
        reference_id=thread.id,
        title="Recommender form due",
        start_time=datetime.now(UTC) + timedelta(days=3),
    )
    db_session.add(cal)
    await db_session.commit()

    r = await student_client.post(f"{INBOX}/threads/{thread.id}/mark-complete")
    assert r.status_code == 200
    assert r.json()["action_label"] == "completed"

    # Checklist item now complete + override recorded.
    await db_session.refresh(checklist)
    assert checklist.manual_overrides.get("recommendation_letters") is True
    rec = next(i for i in checklist.items if i["category"] == "recommendation_letters")
    assert rec["completed"] is True

    # Calendar deadline marked done.
    await db_session.refresh(cal)
    assert cal.completed_at is not None

    # Durability: regenerating the checklist must NOT revert the completion.
    regenerated = await ChecklistService(db_session).generate_checklist(profile.id, app.id)
    rec = next(i for i in regenerated.items if i["category"] == "recommendation_letters")
    assert rec["completed"] is True, "manual override must survive regeneration"


# ── AI suggested reply ──────────────────────────────────────────────────────


class _FakeDrafter:
    def __init__(self, result):
        self._result = result

    async def draft(self, *, input_view, db=None):
        return self._result


@pytest.mark.asyncio
async def test_suggested_reply_renders_with_injected_drafter(
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
    monkeypatch,
):
    await _persist_user_local(db_session, mock_student_user)
    profile, institution, program = await _seed(
        db_session, mock_student_user, mock_institution_user
    )
    thread = await _thread(
        db_session,
        student_id=profile.id,
        institution_id=institution.id,
        action_label="needs_reply",
        waiting_on="student",
        subject="Clarification needed",
        messages=[
            {
                "sender_type": "institution",
                "sender_id": mock_institution_user.id,
                "body": "Can you clarify your second recommender?",
            },
        ],
    )
    await db_session.commit()

    monkeypatch.setattr(settings, "ai_inbox_v2_enabled", True)
    fake = _FakeDrafter(
        InboxReplyResult(
            draft="Hi — thanks for the note. My second recommender is Dr. Lee; "
            "I'll have the form in by Wednesday.",
            tone="professional",
            length="medium",
            alternate_drafts=["Shorter: I'll send it by Wed.", "Warmer: So sorry for the delay!"],
        )
    )
    svc = InboxService(db_session, reply_drafter=fake)
    res = await svc.suggested_reply(mock_student_user.id, thread.id)
    assert res is not None
    assert res.draft.startswith("Hi")
    assert len(res.alternate_drafts) == 2


@pytest.mark.asyncio
async def test_suggested_reply_hidden_on_agent_failure(
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
    monkeypatch,
):
    await _persist_user_local(db_session, mock_student_user)
    profile, institution, program = await _seed(
        db_session, mock_student_user, mock_institution_user
    )
    thread = await _thread(
        db_session,
        student_id=profile.id,
        institution_id=institution.id,
        action_label="needs_reply",
        waiting_on="student",
        subject="Clarify",
    )
    await db_session.commit()

    monkeypatch.setattr(settings, "ai_inbox_v2_enabled", True)
    # None simulates consent-deny / parse failure → card hidden.
    svc = InboxService(db_session, reply_drafter=_FakeDrafter(None))
    assert await svc.suggested_reply(mock_student_user.id, thread.id) is None


@pytest.mark.asyncio
async def test_suggested_reply_null_when_flag_off(
    student_client: AsyncClient,
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
        action_label="needs_reply",
        waiting_on="student",
        subject="Clarify",
    )
    await db_session.commit()

    # Flag is off by default → endpoint returns null, UI hides the card.
    r = await student_client.post(f"{INBOX}/threads/{thread.id}/suggested-reply")
    assert r.status_code == 200
    assert r.json() is None


async def _persist_user_local(db: AsyncSession, user: User) -> None:
    """Service-level tests don't use student_client, so persist the user row
    here for FK integrity."""
    existing = await db.scalar(select(User).where(User.id == user.id))
    if existing is None:
        db.add(user)
        await db.flush()

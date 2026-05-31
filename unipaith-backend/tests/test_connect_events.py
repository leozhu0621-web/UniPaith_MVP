"""Spec 20 §5 / §12 — Connect Events tab.

Covers: RSVP creates a Calendar item + Inbox confirmation + attendee row;
capacity → waitlist; cancel promotes the next waitlisted student; events list
scopes; meeting-link reveal near start.
"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.engagement import Conversation, Message, StudentCalendar
from unipaith.models.institution import Event, EventRSVP, Institution, Program
from unipaith.models.student import StudentProfile
from unipaith.models.user import User, UserRole
from unipaith.services.event_service import EventService


async def _seed(
    db, student_user, institution_user, *, capacity=None, meeting_link=None, start=None
):
    db.add(student_user)
    db.add(institution_user)
    profile = StudentProfile(user_id=student_user.id, first_name="Test", last_name="Student")
    db.add(profile)
    institution = Institution(
        admin_user_id=institution_user.id,
        name="Foo University",
        type="university",
        country="United States",
    )
    db.add(institution)
    await db.flush()
    program = Program(
        institution_id=institution.id,
        program_name="CS Masters",
        degree_type="masters",
        is_published=True,
        tuition=50000,
    )
    db.add(program)
    await db.flush()  # populate program.id before it's used as the event FK
    start = start or (datetime.now(UTC) + timedelta(days=3))
    event = Event(
        institution_id=institution.id,
        program_id=program.id,
        event_name="Info Session",
        event_type="info_session",
        start_time=start,
        end_time=start + timedelta(hours=1),
        capacity=capacity,
        rsvp_count=0,
        status="upcoming",
        meeting_link=meeting_link,
    )
    db.add(event)
    await db.commit()
    return profile, institution, program, event


async def _other_student(db) -> StudentProfile:
    u = User(
        id=uuid.uuid4(),
        email=f"other-{uuid.uuid4().hex[:6]}@example.com",
        cognito_sub=f"dev-{uuid.uuid4().hex[:8]}",
        role=UserRole("student"),
        is_active=True,
    )
    db.add(u)
    p = StudentProfile(user_id=u.id, first_name="Other", last_name="Peer")
    db.add(p)
    await db.commit()
    return p, u


@pytest.mark.asyncio
async def test_rsvp_creates_calendar_inbox_and_attendee(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    profile, institution, _, event = await _seed(
        db_session, mock_student_user, mock_institution_user, capacity=10
    )

    resp = await student_client.post(f"/api/v1/events/{event.id}/rsvp")
    assert resp.status_code == 201

    # Attendee row
    rsvp = await db_session.scalar(
        select(EventRSVP).where(EventRSVP.event_id == event.id, EventRSVP.student_id == profile.id)
    )
    assert rsvp is not None and rsvp.rsvp_status == "registered"

    # Calendar item (Spec 16)
    cal = await db_session.scalar(
        select(StudentCalendar).where(
            StudentCalendar.student_id == profile.id,
            StudentCalendar.entry_type == "event",
            StudentCalendar.reference_id == event.id,
        )
    )
    assert cal is not None

    # Inbox confirmation (Spec 17) — a system message threaded under the institution
    conv = await db_session.scalar(
        select(Conversation).where(
            Conversation.student_id == profile.id,
            Conversation.institution_id == institution.id,
            Conversation.thread_type == "system",
        )
    )
    assert conv is not None
    msg = await db_session.scalar(select(Message).where(Message.conversation_id == conv.id))
    assert msg is not None and "confirmed" in msg.message_body.lower()


@pytest.mark.asyncio
async def test_capacity_waitlists(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    _, _, _, event = await _seed(db_session, mock_student_user, mock_institution_user, capacity=1)
    # Fill the single seat with another student via the service.
    other, other_user = await _other_student(db_session)
    await EventService(db_session).rsvp(other.id, event.id, other_user.id)
    await db_session.commit()

    # The client student now hits capacity → waitlisted (not a 409).
    resp = await student_client.post(f"/api/v1/events/{event.id}/rsvp")
    assert resp.status_code == 201

    mine = (await student_client.get("/api/v1/connect/events?scope=mine")).json()["events"]
    assert len(mine) == 1
    assert mine[0]["rsvp_state"] == "waitlist"
    assert mine[0]["at_capacity"] is True

    refreshed = await db_session.get(Event, event.id)
    assert refreshed.rsvp_count == 1  # waitlisted seat not counted


@pytest.mark.asyncio
async def test_cancel_promotes_waitlist(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    profile, _, _, event = await _seed(
        db_session, mock_student_user, mock_institution_user, capacity=1
    )
    # Client student takes the seat.
    await student_client.post(f"/api/v1/events/{event.id}/rsvp")
    # Another student waitlists.
    other, other_user = await _other_student(db_session)
    await EventService(db_session).rsvp(other.id, event.id, other_user.id)
    await db_session.commit()

    # Client student cancels → the waitlisted student is promoted.
    cancel = await student_client.delete(f"/api/v1/events/{event.id}/rsvp")
    assert cancel.status_code == 204

    promoted = await db_session.scalar(
        select(EventRSVP).where(EventRSVP.event_id == event.id, EventRSVP.student_id == other.id)
    )
    assert promoted.rsvp_status == "registered"
    refreshed = await db_session.get(Event, event.id)
    assert refreshed.rsvp_count == 1
    # Promoted student gets a calendar item.
    cal = await db_session.scalar(
        select(StudentCalendar).where(
            StudentCalendar.student_id == other.id, StudentCalendar.reference_id == event.id
        )
    )
    assert cal is not None


@pytest.mark.asyncio
async def test_events_scope_and_recommended(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    _, _, program, event = await _seed(
        db_session, mock_student_user, mock_institution_user, capacity=10
    )
    # Save the program → auto-follow → event shows in upcoming + recommended.
    await student_client.post("/api/v1/students/me/saved", json={"program_id": str(program.id)})

    upcoming = (await student_client.get("/api/v1/connect/events?scope=upcoming")).json()["events"]
    assert len(upcoming) == 1
    assert upcoming[0]["recommended"] is True
    assert upcoming[0]["rsvp_state"] == "none"

    await student_client.post(f"/api/v1/events/{event.id}/rsvp")
    mine = (await student_client.get("/api/v1/connect/events?scope=mine")).json()["events"]
    assert mine[0]["rsvp_state"] == "rsvp"


@pytest.mark.asyncio
async def test_meeting_link_reveal_window(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    # Event starting in 2h with a meeting link → revealed to RSVP'd student.
    soon = datetime.now(UTC) + timedelta(hours=2)
    _, _, program, event = await _seed(
        db_session,
        mock_student_user,
        mock_institution_user,
        capacity=10,
        meeting_link="https://zoom.example/abc",
        start=soon,
    )
    await student_client.post("/api/v1/students/me/saved", json={"program_id": str(program.id)})
    await student_client.post(f"/api/v1/events/{event.id}/rsvp")

    mine = (await student_client.get("/api/v1/connect/events?scope=mine")).json()["events"]
    assert mine[0]["meeting_link"] == "https://zoom.example/abc"

"""Spec 16 · Calendar — aggregation, persistence, and overdue tests.

Covers Spec 16 §11:
  • items appear from every source
  • application-linked navigation
  • reminder + work-block creation persists
  • overdue computation = start_at < now AND status ∉ {completed, cancelled}
  • PATCH mark-complete on student-created AND derived items
"""

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.application import Application, Interview, OfferLetter
from unipaith.models.institution import Event, EventRSVP, Institution, Program, Reviewer
from unipaith.models.student import RecommendationRequest, StudentProfile
from unipaith.models.user import User

API = "/api/v1/me/calendar"


async def _seed_base(
    db: AsyncSession,
    student_user: User,
    institution_user: User,
    *,
    deadline_days: int = 30,
    app_status: str = "draft",
):
    """Student profile + institution + program (with deadline) + application."""
    db.add(institution_user)
    profile = StudentProfile(user_id=student_user.id, first_name="Test", last_name="Student")
    db.add(profile)
    inst = Institution(
        admin_user_id=institution_user.id,
        name="University of Foo",
        type="university",
        country="United States",
    )
    db.add(inst)
    await db.flush()
    program = Program(
        institution_id=inst.id,
        program_name="Computer Science MS",
        degree_type="MS",
        application_deadline=(datetime.now(UTC) + timedelta(days=deadline_days)).date(),
    )
    db.add(program)
    await db.flush()
    app = Application(student_id=profile.id, program_id=program.id, status=app_status)
    db.add(app)
    await db.flush()
    return profile, inst, program, app


@pytest.mark.asyncio
async def test_calendar_aggregates_all_sources(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    profile, inst, program, app = await _seed_base(
        db_session, mock_student_user, mock_institution_user
    )
    now = datetime.now(UTC)

    reviewer = Reviewer(
        institution_id=inst.id, user_id=mock_institution_user.id, name="Dr. Reviewer"
    )
    db_session.add(reviewer)
    await db_session.flush()
    db_session.add(
        Interview(
            application_id=app.id,
            interviewer_id=reviewer.id,
            interview_type="video",
            confirmed_time=now + timedelta(days=3),
            location_or_link="https://zoom.us/j/123",
            status="confirmed",
            duration_minutes=30,
        )
    )
    event = Event(
        institution_id=inst.id,
        event_name="Campus Tour",
        event_type="campus_visit",
        start_time=now + timedelta(days=5),
        end_time=now + timedelta(days=5, hours=2),
        location="Main Campus",
    )
    db_session.add(event)
    await db_session.flush()
    db_session.add(EventRSVP(event_id=event.id, student_id=profile.id, rsvp_status="registered"))
    db_session.add(
        OfferLetter(
            application_id=app.id,
            offer_type="admit",
            response_deadline=(now + timedelta(days=20)).date(),
            status="extended",
        )
    )
    db_session.add(
        RecommendationRequest(
            student_id=profile.id,
            recommender_name="Prof. Lee",
            status="requested",
            due_date=(now + timedelta(days=10)).date(),
            target_program_id=program.id,
        )
    )
    await db_session.flush()

    resp = await student_client.get(API)
    assert resp.status_code == 200, resp.text
    items = resp.json()
    by_type = {i["type"] for i in items}
    assert "submission_deadline" in by_type
    assert "interview_live" in by_type
    assert "campus_visit" in by_type
    assert "deposit_deadline" in by_type
    assert "recommendation_deadline" in by_type

    interview = next(i for i in items if i["type"] == "interview_live")
    assert interview["meeting_link"] == "https://zoom.us/j/123"
    assert interview["application_id"] == str(app.id)
    rec = next(i for i in items if i["type"] == "recommendation_deadline")
    assert rec["recommender_name"] == "Prof. Lee"


@pytest.mark.asyncio
async def test_application_linked_navigation(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    _, _, _, app = await _seed_base(db_session, mock_student_user, mock_institution_user)
    resp = await student_client.get(API)
    assert resp.status_code == 200
    sub = next(i for i in resp.json() if i["type"] == "submission_deadline")
    assert sub["application_id"] == str(app.id)
    assert sub["link"] == f"/s/applications/{app.id}"


@pytest.mark.asyncio
async def test_create_reminder_persists(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    await _seed_base(db_session, mock_student_user, mock_institution_user)
    start = (datetime.now(UTC) + timedelta(days=2)).isoformat()
    resp = await student_client.post(
        f"{API}/reminders",
        json={"title": "Email recommender", "start_at": start, "notes": "Nudge Prof. Lee"},
    )
    assert resp.status_code == 201, resp.text
    created = resp.json()
    assert created["type"] == "reminder"
    assert created["editable"] is True

    # Persisted — appears on a fresh GET.
    listing = await student_client.get(API)
    titles = {i["title"] for i in listing.json()}
    assert "Email recommender" in titles


@pytest.mark.asyncio
async def test_create_work_block_persists_with_duration(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    await _seed_base(db_session, mock_student_user, mock_institution_user)
    start = datetime.now(UTC) + timedelta(days=1)
    resp = await student_client.post(
        f"{API}/work-blocks",
        json={
            "title": "Draft CS essay",
            "start_at": start.isoformat(),
            "duration_minutes": 120,
            "category": "essay_draft",
        },
    )
    assert resp.status_code == 201, resp.text
    block = resp.json()
    assert block["type"] == "work_block"
    end = datetime.fromisoformat(block["end_at"])
    assert abs((end - start).total_seconds() - 7200) < 5  # 2h block


@pytest.mark.asyncio
async def test_overdue_computation(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    # Past deadline, application NOT submitted → overdue.
    _, _, _, app = await _seed_base(
        db_session, mock_student_user, mock_institution_user, deadline_days=-5, app_status="draft"
    )
    resp = await student_client.get(API)
    sub = next(i for i in resp.json() if i["type"] == "submission_deadline")
    assert sub["status"] == "overdue"


@pytest.mark.asyncio
async def test_submitted_application_deadline_not_overdue(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    # Past deadline but already submitted → completed, never overdue.
    await _seed_base(
        db_session,
        mock_student_user,
        mock_institution_user,
        deadline_days=-5,
        app_status="submitted",
    )
    resp = await student_client.get(API)
    sub = next(i for i in resp.json() if i["type"] == "submission_deadline")
    assert sub["status"] == "completed"


@pytest.mark.asyncio
async def test_mark_reminder_complete(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    await _seed_base(db_session, mock_student_user, mock_institution_user)
    start = (datetime.now(UTC) + timedelta(days=2)).isoformat()
    created = (
        await student_client.post(
            f"{API}/reminders", json={"title": "Pay deposit", "start_at": start}
        )
    ).json()
    resp = await student_client.patch(f"{API}/{created['id']}", json={"status": "completed"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "completed"


@pytest.mark.asyncio
async def test_mark_derived_deadline_complete_persists(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    # A past (overdue) submission deadline → mark complete → overlay persists,
    # and it is no longer overdue on re-read.
    _, _, _, app = await _seed_base(
        db_session, mock_student_user, mock_institution_user, deadline_days=-3, app_status="draft"
    )
    item_id = f"submission_deadline:{app.id}"
    patched = await student_client.patch(f"{API}/{item_id}", json={"status": "completed"})
    assert patched.status_code == 200, patched.text
    assert patched.json()["status"] == "completed"

    again = await student_client.get(API)
    sub = next(i for i in again.json() if i["id"] == item_id)
    assert sub["status"] == "completed"


@pytest.mark.asyncio
async def test_range_filter_excludes_out_of_window(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    # Deadline 30 days out; query a window that ends in 7 days → excluded.
    await _seed_base(db_session, mock_student_user, mock_institution_user, deadline_days=30)
    now = datetime.now(UTC)
    resp = await student_client.get(
        API,
        params={"from": now.isoformat(), "to": (now + timedelta(days=7)).isoformat()},
    )
    assert resp.status_code == 200
    assert all(i["type"] != "submission_deadline" for i in resp.json())

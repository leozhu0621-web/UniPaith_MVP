"""Tests for events — create, RSVP, cancel, list."""

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.institution import Event, Institution
from unipaith.models.student import StudentProfile
from unipaith.models.user import User


async def _seed_student_institution_event(
    db: AsyncSession, student_user: User, institution_user: User
):
    """Seed student, institution, and a future event directly in DB."""
    db.add(student_user)
    db.add(institution_user)

    profile = StudentProfile(user_id=student_user.id, first_name="Test", last_name="Student")
    db.add(profile)

    institution = Institution(
        admin_user_id=institution_user.id,
        name="Test University",
        type="university",
        country="United States",
    )
    db.add(institution)
    await db.flush()

    now = datetime.now(UTC)
    event = Event(
        institution_id=institution.id,
        event_name="Campus Tour",
        event_type="campus_visit",
        start_time=now + timedelta(days=7),
        end_time=now + timedelta(days=7, hours=2),
        description="A campus tour for prospective students.",
        location="Main Campus",
        capacity=100,
        rsvp_count=0,
        status="upcoming",
    )
    db.add(event)
    await db.commit()
    return profile, institution, event


def _event_payload() -> dict:
    now = datetime.now(UTC)
    return {
        "event_name": "Campus Tour",
        "event_type": "campus_visit",
        "start_time": (now + timedelta(days=7)).isoformat(),
        "end_time": (now + timedelta(days=7, hours=2)).isoformat(),
        "description": "A campus tour for prospective students.",
        "location": "Main Campus",
        "capacity": 100,
    }


@pytest.mark.asyncio
async def test_create_event(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_institution_user: User,
):
    db_session.add(mock_institution_user)

    institution = Institution(
        admin_user_id=mock_institution_user.id,
        name="Test University",
        type="university",
        country="United States",
    )
    db_session.add(institution)
    await db_session.commit()

    resp = await institution_client.post(
        "/api/v1/events/manage",
        json=_event_payload(),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["event_name"] == "Campus Tour"


@pytest.mark.asyncio
async def test_rsvp(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    profile, institution, event = await _seed_student_institution_event(
        db_session, mock_student_user, mock_institution_user
    )

    # RSVP as student
    resp = await student_client.post(f"/api/v1/events/{event.id}/rsvp")
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_cancel_rsvp(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    profile, institution, event = await _seed_student_institution_event(
        db_session, mock_student_user, mock_institution_user
    )

    # RSVP then cancel
    await student_client.post(f"/api/v1/events/{event.id}/rsvp")
    resp = await student_client.delete(f"/api/v1/events/{event.id}/rsvp")
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_list_upcoming(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_institution_user: User,
):
    db_session.add(mock_institution_user)

    institution = Institution(
        admin_user_id=mock_institution_user.id,
        name="Test University",
        type="university",
        country="United States",
    )
    db_session.add(institution)
    await db_session.commit()

    # Create an event
    await institution_client.post("/api/v1/events/manage", json=_event_payload())

    # List upcoming events (public endpoint, no auth required)
    resp = await institution_client.get("/api/v1/events")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1

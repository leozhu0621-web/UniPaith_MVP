"""Tests for interviews — propose, confirm, complete, score."""

from datetime import UTC

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.application import Application, Interview
from unipaith.models.institution import Institution, Program, Reviewer
from unipaith.models.student import StudentProfile
from unipaith.models.user import User


async def _seed_interview_context(db: AsyncSession, student_user: User, institution_user: User):
    """Create all entities needed for interview tests."""
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

    program = Program(
        institution_id=institution.id,
        program_name="CS Masters",
        degree_type="masters",
        is_published=True,
        tuition=50000,
    )
    db.add(program)
    await db.flush()

    application = Application(
        student_id=profile.id,
        program_id=program.id,
        status="under_review",
    )
    db.add(application)

    reviewer = Reviewer(
        institution_id=institution.id,
        user_id=institution_user.id,
        name="Dr. Interviewer",
        department="Computer Science",
    )
    db.add(reviewer)
    await db.commit()
    return profile, institution, program, application, reviewer


@pytest.mark.asyncio
async def test_propose_interview(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    _, _, _, application, reviewer = await _seed_interview_context(
        db_session, mock_student_user, mock_institution_user
    )
    resp = await institution_client.post(
        "/api/v1/interviews",
        json={
            "application_id": str(application.id),
            "interviewer_id": str(reviewer.id),
            "interview_type": "video",
            "proposed_times": [
                "2026-04-10T10:00:00Z",
                "2026-04-11T14:00:00Z",
            ],
            "duration_minutes": 30,
            "location_or_link": "https://zoom.us/j/123456",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["proposed_times"] is not None


@pytest.mark.asyncio
async def test_confirm_interview(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    _, _, _, application, reviewer = await _seed_interview_context(
        db_session, mock_student_user, mock_institution_user
    )

    # Seed interview directly in DB to avoid dual-client fixture conflict
    interview = Interview(
        application_id=application.id,
        interviewer_id=reviewer.id,
        interview_type="video",
        proposed_times=["2026-04-10T10:00:00Z", "2026-04-11T14:00:00Z"],
        duration_minutes=30,
        status="proposed",
    )
    db_session.add(interview)
    await db_session.commit()

    # Confirm as student
    resp = await student_client.post(
        f"/api/v1/interviews/{interview.id}/confirm",
        json={"confirmed_time": "2026-04-10T10:00:00Z"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "confirmed"


@pytest.mark.asyncio
async def test_complete_interview(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    _, _, _, application, reviewer = await _seed_interview_context(
        db_session, mock_student_user, mock_institution_user
    )

    # Seed a confirmed interview directly
    from datetime import datetime

    interview = Interview(
        application_id=application.id,
        interviewer_id=reviewer.id,
        interview_type="video",
        proposed_times=["2026-04-10T10:00:00Z"],
        confirmed_time=datetime(2026, 4, 10, 10, 0, 0, tzinfo=UTC),
        duration_minutes=30,
        status="confirmed",
    )
    db_session.add(interview)
    await db_session.commit()

    resp = await institution_client.post(f"/api/v1/interviews/{interview.id}/complete")
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"


@pytest.mark.asyncio
async def test_score_interview(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    _, _, _, application, reviewer = await _seed_interview_context(
        db_session, mock_student_user, mock_institution_user
    )

    # Seed a completed interview directly
    from datetime import datetime

    interview = Interview(
        application_id=application.id,
        interviewer_id=reviewer.id,
        interview_type="video",
        proposed_times=["2026-04-10T10:00:00Z"],
        confirmed_time=datetime(2026, 4, 10, 10, 0, 0, tzinfo=UTC),
        duration_minutes=30,
        status="completed",
    )
    db_session.add(interview)
    await db_session.commit()

    # Score
    resp = await institution_client.post(
        f"/api/v1/interviews/{interview.id}/score",
        json={
            "criterion_scores": {"communication": 8, "technical": 9},
            "total_weighted_score": 8.5,
            "interviewer_notes": "Strong candidate.",
            "recommendation": "accept",
        },
    )
    assert resp.status_code == 200

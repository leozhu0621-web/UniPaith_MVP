"""Tests for interviews — propose, confirm, complete, score."""

from datetime import UTC

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.application import Application, Interview
from unipaith.models.engagement import Conversation, Message
from unipaith.models.institution import Institution, Program, Reviewer
from unipaith.models.student import StudentProfile
from unipaith.models.user import User

LIVE_SLOTS = [
    "2026-05-10T10:00:00Z",
    "2026-05-11T10:00:00Z",
    "2026-05-12T10:00:00Z",
]


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
            "interview_type": "live",
            "proposed_times": [
                "2026-04-10T10:00:00Z",
                "2026-04-11T14:00:00Z",
                "2026-04-12T16:00:00Z",
            ],
            "duration_minutes": 30,
            "location_or_link": "https://zoom.us/j/123456",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    # Spec 33 §5 — propose returns one interview per applicant (a list).
    assert isinstance(data, list) and len(data) == 1
    assert data[0]["proposed_times"] is not None
    assert data[0]["status"] == "proposed"
    assert data[0]["applicant"]["name"] == "Test Student"


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


# ── Spec 33 §12 — propose creates Inbox + Calendar; new lifecycle actions ─────


@pytest.mark.asyncio
async def test_propose_creates_inbox_message(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    """Spec 33 §3 step 2 / §12 — propose lands an interview_invite in the Inbox."""
    profile, _, _, application, _ = await _seed_interview_context(
        db_session, mock_student_user, mock_institution_user
    )
    resp = await institution_client.post(
        "/api/v1/interviews",
        json={
            "application_id": str(application.id),
            "interview_type": "live",
            "proposed_times": LIVE_SLOTS,
        },
    )
    assert resp.status_code == 201

    conv = await db_session.scalar(
        select(Conversation).where(Conversation.application_id == application.id)
    )
    assert conv is not None
    assert conv.reason_code == "interview_invite"
    assert conv.action_label == "interview_invite"
    assert conv.waiting_on == "student"
    msg = await db_session.scalar(select(Message).where(Message.conversation_id == conv.id))
    assert msg is not None
    assert msg.sender_type == "institution"
    assert msg.message_body


@pytest.mark.asyncio
async def test_propose_appears_on_student_calendar(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    """Spec 33 §12 — the proposed interview is auto-derived onto the calendar.

    Uses CalendarService directly (not the student HTTP client) to avoid the
    dual-client get_current_user override conflict.
    """
    from unipaith.services.calendar_service import CalendarService

    profile, _, _, application, _ = await _seed_interview_context(
        db_session, mock_student_user, mock_institution_user
    )
    resp = await institution_client.post(
        "/api/v1/interviews",
        json={
            "application_id": str(application.id),
            "interview_type": "live",
            "proposed_times": LIVE_SLOTS,
        },
    )
    assert resp.status_code == 201

    items = await CalendarService(db_session).get_calendar(profile.id)
    assert any("interview" in (it.type or "") for it in items)
    interview_items = [it for it in items if it.interview_id]
    assert interview_items
    assert interview_items[0].can_confirm is True
    assert len(interview_items[0].proposed_times) == 3


@pytest.mark.asyncio
async def test_propose_multiple_applicants(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    profile, institution, program, application, _ = await _seed_interview_context(
        db_session, mock_student_user, mock_institution_user
    )
    # A second applicant on the same program.
    other_user = User(
        id=__import__("uuid").uuid4(),
        email="other@example.com",
        cognito_sub="dev-other",
        role=mock_student_user.role,
        is_active=True,
    )
    db_session.add(other_user)
    other_profile = StudentProfile(user_id=other_user.id, first_name="Other", last_name="Student")
    db_session.add(other_profile)
    await db_session.flush()
    app2 = Application(student_id=other_profile.id, program_id=program.id, status="under_review")
    db_session.add(app2)
    await db_session.commit()

    resp = await institution_client.post(
        "/api/v1/interviews",
        json={
            "application_ids": [str(application.id), str(app2.id)],
            "interview_type": "live",
            "proposed_times": LIVE_SLOTS,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_propose_live_requires_three_slots(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    """Spec 33 §5 — live interviews need three or more proposed slots."""
    _, _, _, application, _ = await _seed_interview_context(
        db_session, mock_student_user, mock_institution_user
    )
    resp = await institution_client.post(
        "/api/v1/interviews",
        json={
            "application_id": str(application.id),
            "interview_type": "live",
            "proposed_times": ["2026-05-10T10:00:00Z", "2026-05-11T10:00:00Z"],
        },
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_cancel_interview(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    _, _, _, application, reviewer = await _seed_interview_context(
        db_session, mock_student_user, mock_institution_user
    )
    interview = Interview(
        application_id=application.id,
        interviewer_id=reviewer.id,
        interview_type="live",
        proposed_times=["2026-05-10T10:00:00Z"],
        status="proposed",
    )
    db_session.add(interview)
    await db_session.commit()

    resp = await institution_client.post(f"/api/v1/interviews/{interview.id}/cancel")
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"


@pytest.mark.asyncio
async def test_no_show_interview(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    from datetime import datetime

    _, _, _, application, reviewer = await _seed_interview_context(
        db_session, mock_student_user, mock_institution_user
    )
    interview = Interview(
        application_id=application.id,
        interviewer_id=reviewer.id,
        interview_type="live",
        proposed_times=["2026-05-10T10:00:00Z"],
        confirmed_time=datetime(2026, 5, 10, 10, 0, 0, tzinfo=UTC),
        status="confirmed",
    )
    db_session.add(interview)
    await db_session.commit()

    resp = await institution_client.post(f"/api/v1/interviews/{interview.id}/no-show")
    assert resp.status_code == 200
    assert resp.json()["status"] == "no_show"


@pytest.mark.asyncio
async def test_async_window_expired_renders_no_submission(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    """Spec 33 §8 — an async interview past its window with no recording renders
    as 'No submission received' (async_expired=True)."""
    from datetime import datetime, timedelta

    _, _, _, application, reviewer = await _seed_interview_context(
        db_session, mock_student_user, mock_institution_user
    )
    interview = Interview(
        application_id=application.id,
        interviewer_id=reviewer.id,
        interview_type="recorded_async",
        proposed_times=[],
        async_window_end=datetime.now(UTC) - timedelta(days=1),
        status="proposed",
    )
    db_session.add(interview)
    await db_session.commit()

    resp = await institution_client.get("/api/v1/interviews/institution")
    assert resp.status_code == 200
    rows = resp.json()
    target = next(r for r in rows if r["id"] == str(interview.id))
    assert target["async_expired"] is True


@pytest.mark.asyncio
async def test_score_sets_denormalized_recommendation(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    """Spec 33 §3 step 6 — scoring feeds the packet via the denormalized
    recommendation surfaced on the interview row."""
    from datetime import datetime

    _, _, _, application, reviewer = await _seed_interview_context(
        db_session, mock_student_user, mock_institution_user
    )
    interview = Interview(
        application_id=application.id,
        interviewer_id=reviewer.id,
        interview_type="live",
        proposed_times=["2026-05-10T10:00:00Z"],
        confirmed_time=datetime(2026, 5, 10, 10, 0, 0, tzinfo=UTC),
        status="completed",
    )
    db_session.add(interview)
    await db_session.commit()

    score = await institution_client.post(
        f"/api/v1/interviews/{interview.id}/score",
        json={
            "criterion_scores": {"communication": 4},
            "total_weighted_score": 4.0,
            "recommendation": "recommend",
        },
    )
    assert score.status_code == 200

    rows = (await institution_client.get("/api/v1/interviews/institution")).json()
    target = next(r for r in rows if r["id"] == str(interview.id))
    assert target["recommendation"] == "recommend"
    assert len(target["scores"]) == 1


@pytest.mark.asyncio
async def test_interview_rubrics_includes_default(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    await _seed_interview_context(db_session, mock_student_user, mock_institution_user)
    resp = await institution_client.get("/api/v1/interviews/rubrics")
    assert resp.status_code == 200
    rubrics = resp.json()
    assert len(rubrics) >= 1
    # The built-in default is always present.
    assert any(r["rubric_kind"] == "interview" and r["criteria"] for r in rubrics)


@pytest.mark.asyncio
async def test_ai_draft_invite_falls_back_when_disabled(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    """Spec 33 §9 — AI endpoints never 5xx; they degrade to available=False."""
    _, _, _, application, _ = await _seed_interview_context(
        db_session, mock_student_user, mock_institution_user
    )
    resp = await institution_client.post(
        "/api/v1/interviews/draft-invite",
        json={
            "application_id": str(application.id),
            "interview_type": "live",
            "proposed_times": ["2026-05-10T10:00:00Z"],
        },
    )
    assert resp.status_code == 200
    assert resp.json()["available"] is False


@pytest.mark.asyncio
async def test_ai_draft_invite_graceful_when_enabled(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
    monkeypatch,
):
    """With the flag on but AI_MOCK_MODE, the agent returns None — still a clean
    200 with available=False (no 5xx)."""
    from unipaith.config import settings

    monkeypatch.setattr(settings, "ai_interview_v2_enabled", True)
    _, _, _, application, _ = await _seed_interview_context(
        db_session, mock_student_user, mock_institution_user
    )
    resp = await institution_client.post(
        "/api/v1/interviews/draft-invite",
        json={
            "application_id": str(application.id),
            "interview_type": "live",
            "proposed_times": ["2026-05-10T10:00:00Z"],
        },
    )
    assert resp.status_code == 200
    assert resp.json()["available"] is False


@pytest.mark.asyncio
async def test_reschedule_interview(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    """Spec 33 §13 — institution reschedules: back to proposed with new times."""
    from datetime import datetime

    _, _, _, application, reviewer = await _seed_interview_context(
        db_session, mock_student_user, mock_institution_user
    )
    interview = Interview(
        application_id=application.id,
        interviewer_id=reviewer.id,
        interview_type="live",
        proposed_times=["2026-05-10T10:00:00Z"],
        confirmed_time=datetime(2026, 5, 10, 10, 0, 0, tzinfo=UTC),
        status="confirmed",
    )
    db_session.add(interview)
    await db_session.commit()

    resp = await institution_client.post(
        f"/api/v1/interviews/{interview.id}/reschedule",
        json={"proposed_times": LIVE_SLOTS},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "proposed"
    assert data["scheduled_at"] is None
    assert len(data["proposed_times"]) == 3


@pytest.mark.asyncio
async def test_student_request_reschedule(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    """Spec 33 §8 — student requests a reschedule; staff is notified (no 5xx)."""
    from datetime import datetime

    _, _, _, application, reviewer = await _seed_interview_context(
        db_session, mock_student_user, mock_institution_user
    )
    interview = Interview(
        application_id=application.id,
        interviewer_id=reviewer.id,
        interview_type="live",
        proposed_times=["2026-05-10T10:00:00Z"],
        confirmed_time=datetime(2026, 5, 10, 10, 0, 0, tzinfo=UTC),
        status="confirmed",
    )
    db_session.add(interview)
    await db_session.commit()

    resp = await student_client.post(f"/api/v1/interviews/{interview.id}/request-reschedule")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_confirm_async_interview(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    """Async types confirm by accepting the submission window (no slot pick)."""
    from datetime import datetime, timedelta

    _, _, _, application, reviewer = await _seed_interview_context(
        db_session, mock_student_user, mock_institution_user
    )
    interview = Interview(
        application_id=application.id,
        interviewer_id=reviewer.id,
        interview_type="recorded_async",
        proposed_times=[],
        async_window_end=datetime.now(UTC) + timedelta(days=7),
        status="proposed",
    )
    db_session.add(interview)
    await db_session.commit()

    resp = await student_client.post(
        f"/api/v1/interviews/{interview.id}/confirm",
        json={"confirmed_time": None},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "confirmed"

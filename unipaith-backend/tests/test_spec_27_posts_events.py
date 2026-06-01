"""Spec 27 — Posts, Updates & Events acceptance tests.

Covers §11:
1. Post draft -> schedule -> publish -> pinned; CTAs + visibility persist (§2.4/§2.3).
2. Event cancel -> RSVP'd students notified (§7) + calendar item removed.
3. Per-object engagement metrics roll up (§5).
4. Event attendance capture (attended | no_show) (§3.1).
5. Promotion target kind + custom landing URL (§4.1).
"""

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.engagement import Conversation, Message, StudentCalendar
from unipaith.models.institution import Event, EventRSVP, Institution, InstitutionPost
from unipaith.models.student import StudentProfile
from unipaith.models.user import User


async def _seed_institution(db: AsyncSession, user: User) -> Institution:
    db.add(user)
    inst = Institution(
        admin_user_id=user.id,
        name="Test University",
        type="university",
        country="United States",
    )
    db.add(inst)
    await db.flush()
    return inst


# ── §11.1 — post lifecycle + CTAs + visibility ────────────────────────────────


@pytest.mark.asyncio
async def test_post_lifecycle_ctas_visibility(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_institution_user: User,
):
    await _seed_institution(db_session, mock_institution_user)
    await db_session.commit()

    # Create a scheduled post with CTAs + a non-public visibility scope.
    when = (datetime.now(UTC) + timedelta(days=2)).isoformat()
    resp = await institution_client.post(
        "/api/v1/institutions/me/posts",
        json={
            "title": "Open House",
            "body": "Join our virtual open house.",
            "status": "scheduled",
            "scheduled_for": when,
            "ctas": [
                {"type": "request_info", "label": "Request info", "target": None},
                {"type": "view_program", "label": "View program", "target": ""},
            ],
            "visibility": {"public": False, "segment_ids": [], "region_scopes": ["Europe"]},
        },
    )
    assert resp.status_code == 201, resp.text
    post = resp.json()
    assert post["status"] == "scheduled"
    assert post["scheduled_for"] is not None
    assert len(post["ctas"]) == 2
    assert post["ctas"][0]["type"] == "request_info"
    assert post["visibility"]["public"] is False
    assert post["visibility"]["region_scopes"] == ["Europe"]
    post_id = post["id"]

    # Publish it.
    resp = await institution_client.post(f"/api/v1/institutions/me/posts/{post_id}/publish")
    assert resp.status_code == 200
    assert resp.json()["status"] == "published"
    assert resp.json()["published_at"] is not None

    # Pin it (toggle).
    resp = await institution_client.post(f"/api/v1/institutions/me/posts/{post_id}/pin")
    assert resp.status_code == 200
    assert resp.json()["pinned"] is True


# ── §5 / §11.4 — per-object engagement rollup ────────────────────────────────


@pytest.mark.asyncio
async def test_engagement_metrics_rollup(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    inst = await _seed_institution(db_session, mock_institution_user)
    post = InstitutionPost(
        institution_id=inst.id,
        title="Update",
        body="Body",
        status="published",
        published_at=datetime.now(UTC),
    )
    db_session.add(post)
    await db_session.commit()

    for action in ["view", "click", "save", "request_info", "apply_started"]:
        resp = await student_client.post(
            "/api/v1/institutions/track/engagement",
            json={"object_type": "post", "object_id": str(post.id), "action": action},
        )
        assert resp.status_code == 204, resp.text

    await db_session.refresh(post)
    assert post.view_count == 1
    assert post.click_count == 1
    assert post.save_count == 1
    assert post.request_info_count == 1
    assert post.apply_started_count == 1


# ── §7 — cancelled event notifies RSVP'd students ────────────────────────────


@pytest.mark.asyncio
async def test_cancel_event_notifies_rsvped_students(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    inst = await _seed_institution(db_session, mock_institution_user)
    db_session.add(mock_student_user)
    profile = StudentProfile(user_id=mock_student_user.id, first_name="Test", last_name="Student")
    db_session.add(profile)
    now = datetime.now(UTC)
    event = Event(
        institution_id=inst.id,
        event_name="Webinar",
        event_type="webinar",
        start_time=now + timedelta(days=3),
        end_time=now + timedelta(days=3, hours=1),
        capacity=50,
        rsvp_count=1,
        status="upcoming",
    )
    db_session.add(event)
    await db_session.flush()
    db_session.add(EventRSVP(event_id=event.id, student_id=profile.id, rsvp_status="registered"))
    db_session.add(
        StudentCalendar(
            student_id=profile.id,
            entry_type="event",
            reference_id=event.id,
            title="Webinar",
            start_time=event.start_time,
        )
    )
    await db_session.commit()

    resp = await institution_client.post(f"/api/v1/events/manage/{event.id}/cancel")
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"

    # A cancellation system message reached the student.
    msgs = (
        (
            await db_session.execute(
                select(Message)
                .join(Conversation, Conversation.id == Message.conversation_id)
                .where(Conversation.student_id == profile.id)
            )
        )
        .scalars()
        .all()
    )
    assert any("cancelled" in (m.message_body or "").lower() for m in msgs)

    # Their calendar item was removed.
    cal = (
        (
            await db_session.execute(
                select(StudentCalendar).where(
                    StudentCalendar.student_id == profile.id,
                    StudentCalendar.reference_id == event.id,
                )
            )
        )
        .scalars()
        .all()
    )
    assert cal == []


# ── §3.1 — attendance capture ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_event_attendance_marking(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    inst = await _seed_institution(db_session, mock_institution_user)
    db_session.add(mock_student_user)
    profile = StudentProfile(user_id=mock_student_user.id, first_name="A", last_name="B")
    db_session.add(profile)
    now = datetime.now(UTC)
    event = Event(
        institution_id=inst.id,
        event_name="Tour",
        event_type="campus_visit",
        start_time=now - timedelta(days=1),
        end_time=now - timedelta(hours=23),
        rsvp_count=1,
        status="upcoming",
    )
    db_session.add(event)
    await db_session.flush()
    rsvp = EventRSVP(event_id=event.id, student_id=profile.id, rsvp_status="registered")
    db_session.add(rsvp)
    await db_session.commit()

    resp = await institution_client.put(
        f"/api/v1/events/manage/{event.id}/rsvps/{rsvp.id}/attendance",
        json={"attendance_status": "no_show"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["attendance_status"] == "no_show"

    await db_session.refresh(rsvp)
    assert rsvp.attendance_status == "no_show"


# ── §4.1 — promotion target kind + landing URL ───────────────────────────────


@pytest.mark.asyncio
async def test_promotion_target_kind(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_institution_user: User,
):
    await _seed_institution(db_session, mock_institution_user)
    await db_session.commit()

    resp = await institution_client.post(
        "/api/v1/institutions/me/promotions",
        json={
            "title": "Scholarship drive",
            "promotion_type": "banner",
            "target_kind": "landing",
            "target_url": "https://example.edu/scholarships",
            "targeting": {"regions": ["Asia"]},
        },
    )
    assert resp.status_code in (200, 201), resp.text
    promo = resp.json()
    assert promo["target_kind"] == "landing"
    assert promo["target_url"] == "https://example.edu/scholarships"

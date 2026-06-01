"""Spec 20 §4 / §9 / §12 — Connect Updates feed.

Covers: feed scoped to followed institutions; muted institution suppressed;
program_change never suppressed; deadline reminders from saved programs;
relevance ranking falls back cleanly.
"""

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.institution import Institution, InstitutionPost, Program
from unipaith.models.student import StudentProfile
from unipaith.models.user import User


async def _seed(db: AsyncSession, student_user: User, institution_user: User, *, deadline=None):
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
        application_deadline=deadline,
    )
    db.add(program)
    await db.commit()
    return profile, institution, program


async def _publish_post(db: AsyncSession, institution_id, title="Scholarship news", pinned=False):
    post = InstitutionPost(
        institution_id=institution_id,
        title=title,
        body="We extended the merit-scholarship deadline.",
        status="published",
        pinned=pinned,
        published_at=datetime.now(UTC),
    )
    db.add(post)
    await db.commit()
    return post


@pytest.mark.asyncio
async def test_feed_shows_posts_from_followed_only(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    _, institution, program = await _seed(db_session, mock_student_user, mock_institution_user)
    await _publish_post(db_session, institution.id)

    # Not following yet → empty feed.
    empty = (await student_client.get("/api/v1/connect/feed")).json()
    assert empty["followed_count"] == 0
    assert empty["items"] == []

    # Save the program → auto-follow → post appears.
    await student_client.post("/api/v1/students/me/saved", json={"program_id": str(program.id)})
    feed = (await student_client.get("/api/v1/connect/feed")).json()
    assert feed["followed_count"] == 1
    kinds = [i["kind"] for i in feed["items"]]
    assert "post" in kinds


@pytest.mark.asyncio
async def test_mute_suppresses_posts(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    _, institution, program = await _seed(db_session, mock_student_user, mock_institution_user)
    await _publish_post(db_session, institution.id)
    await student_client.post("/api/v1/students/me/saved", json={"program_id": str(program.id)})

    await student_client.patch(f"/api/v1/connect/follows/{institution.id}", json={"muted": True})
    feed = (await student_client.get("/api/v1/connect/feed")).json()
    assert all(i["kind"] != "post" for i in feed["items"])
    assert feed["muted_count"] == 1


@pytest.mark.asyncio
async def test_program_change_never_muted(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    profile, institution, program = await _seed(
        db_session, mock_student_user, mock_institution_user
    )
    await student_client.post("/api/v1/students/me/saved", json={"program_id": str(program.id)})

    # Simulate the institution editing the program AFTER the save.
    program.updated_at = datetime.now(UTC) + timedelta(hours=2)
    program.description_text = "Now requires a portfolio."
    await db_session.commit()

    # Mute the institution — program_change must STILL appear (Spec 20 §4.3).
    await student_client.patch(f"/api/v1/connect/follows/{institution.id}", json={"muted": True})
    feed = (await student_client.get("/api/v1/connect/feed")).json()
    changes = [i for i in feed["items"] if i["kind"] == "program_change"]
    assert len(changes) == 1
    assert changes[0]["program_id"] == str(program.id)
    assert changes[0]["muted"] is True  # shown despite mute


@pytest.mark.asyncio
async def test_deadline_item_from_saved_program(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    # Use the same UTC basis the feed service uses (connect_service computes
    # days_until from datetime.now(UTC).date()), so the assertion is stable
    # regardless of the local time-of-day the suite runs at.
    soon = datetime.now(UTC).date() + timedelta(days=21)
    _, institution, program = await _seed(
        db_session, mock_student_user, mock_institution_user, deadline=soon
    )
    await student_client.post("/api/v1/students/me/saved", json={"program_id": str(program.id)})

    feed = (await student_client.get("/api/v1/connect/feed")).json()
    deadlines = [i for i in feed["items"] if i["kind"] == "deadline"]
    assert len(deadlines) == 1
    assert deadlines[0]["days_until"] == 21
    assert deadlines[0]["program_id"] == str(program.id)


@pytest.mark.asyncio
async def test_relevant_rank_returns_feed(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    _, institution, program = await _seed(db_session, mock_student_user, mock_institution_user)
    await _publish_post(db_session, institution.id)
    await student_client.post("/api/v1/students/me/saved", json={"program_id": str(program.id)})

    # relevant rank must work (falls back to heuristic if the agent is off/fails).
    feed = (await student_client.get("/api/v1/connect/feed?rank=relevant")).json()
    assert any(i["kind"] == "post" for i in feed["items"])

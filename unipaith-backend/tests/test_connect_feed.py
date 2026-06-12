"""Spec 20 §4 / §9 / §12 — Connect Updates feed.

Covers: feed scoped to followed institutions; muted institution suppressed;
program_change never suppressed; deadline reminders from saved programs;
relevance ranking falls back cleanly.
"""

from datetime import UTC, date, datetime, timedelta

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
    # connect_service computes days_until against a naive `date.today()`
    # reference (matching how a deadline is stored, and consistent with the
    # rest of the deadline logic, e.g. checklist_service). Build the deadline on
    # the same basis so the assertion is stable regardless of the local
    # time-of-day the suite runs at.
    soon = date.today() + timedelta(days=21)
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


@pytest.mark.asyncio
async def test_feed_kinds_filter_deadline_only(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    """?kinds=deadline returns only deadline items (rail deadline radar)."""
    deadline = date.today() + timedelta(days=30)
    _, institution, program = await _seed(
        db_session, mock_student_user, mock_institution_user, deadline=deadline
    )
    await _publish_post(db_session, institution.id)
    # Save the program → auto-follow (source='saved') → both kinds in the feed.
    await student_client.post("/api/v1/students/me/saved", json={"program_id": str(program.id)})

    res = await student_client.get("/api/v1/connect/feed", params={"kinds": "deadline"})
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) >= 1
    assert all(it["kind"] == "deadline" for it in items)

    res2 = await student_client.get("/api/v1/connect/feed", params={"kinds": "post"})
    assert all(it["kind"] == "post" for it in res2.json()["items"])


@pytest.mark.asyncio
async def test_feed_items_carry_follow_source(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    """Each feed item carries the follow row's source for 'because you follow'
    attribution (Spec 2026-06-12 §5.2)."""
    _, institution, program = await _seed(db_session, mock_student_user, mock_institution_user)
    await _publish_post(db_session, institution.id)
    # Save the program → auto-follow with source='saved'.
    await student_client.post("/api/v1/students/me/saved", json={"program_id": str(program.id)})

    res = await student_client.get("/api/v1/connect/feed")
    items = res.json()["items"]
    assert items, "expected at least one feed item"
    for it in items:
        assert it["follow_source"] == "saved"


@pytest.mark.asyncio
async def test_saved_search_alert_items_in_feed(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    """Recently-alerted saved searches surface as feed items; disabled/stale/
    zero-count don't (Spec 2026-06-12 §5.4)."""
    from unipaith.models.saved_search import SavedSearch

    await _seed(db_session, mock_student_user, mock_institution_user)
    now = datetime.now(UTC)
    db_session.add_all(
        [
            SavedSearch(  # should appear
                user_id=mock_student_user.id,
                name="CS in California",
                query={"query": "cs", "chips": [], "filters": {}, "sort": "relevance"},
                alert_enabled=True,
                last_alerted_at=now - timedelta(days=2),
                last_match_count=5,
            ),
            SavedSearch(  # alert disabled → absent
                user_id=mock_student_user.id,
                name="No alerts",
                query={},
                alert_enabled=False,
                last_alerted_at=now - timedelta(days=2),
                last_match_count=3,
            ),
            SavedSearch(  # stale (>14d) → absent
                user_id=mock_student_user.id,
                name="Stale",
                query={},
                alert_enabled=True,
                last_alerted_at=now - timedelta(days=30),
                last_match_count=3,
            ),
            SavedSearch(  # zero matches → absent
                user_id=mock_student_user.id,
                name="Empty",
                query={},
                alert_enabled=True,
                last_alerted_at=now - timedelta(days=1),
                last_match_count=0,
            ),
        ]
    )
    await db_session.commit()

    res = await student_client.get("/api/v1/connect/feed")
    assert res.status_code == 200
    alerts = [it for it in res.json()["items"] if it["kind"] == "saved_search_alert"]
    assert len(alerts) == 1
    a = alerts[0]
    assert a["search_name"] == "CS in California"
    assert a["match_count"] == 5
    assert a["search_query"]["query"] == "cs"
    assert a["institution_id"] is None

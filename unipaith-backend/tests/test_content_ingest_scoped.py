"""Scope-aware, gated content-ingest upserts.

Exercises the rule that Events/Updates are tagged to the right scope
(institution / school / program) and that the keyword relevance gate keeps
only genuinely-relevant items. Uses the upsert_* methods directly with
NormalizedItem fixtures (no network).
"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from unipaith.models.institution import Event, Institution, InstitutionPost, Program, School
from unipaith.models.user import User, UserRole
from unipaith.services.content_ingest.base import NormalizedItem
from unipaith.services.content_ingest.service import ContentIngestService

pytestmark = pytest.mark.asyncio


async def _scaffold(db_session) -> tuple[Institution, School, Program]:
    admin = User(
        id=uuid.uuid4(),
        email=f"ci-admin-{uuid.uuid4().hex[:6]}@example.com",
        cognito_sub=f"dev-sub-{uuid.uuid4().hex[:8]}",
        role=UserRole("institution_admin"),
        is_active=True,
    )
    db_session.add(admin)
    await db_session.flush()
    inst = Institution(
        admin_user_id=admin.id,
        name="Test University",
        type="university",
        country="United States",
        description_text="stub",
        student_body_size=1,
    )
    db_session.add(inst)
    await db_session.flush()
    school = School(institution_id=inst.id, name="Test School of Management")
    db_session.add(school)
    await db_session.flush()
    program = Program(
        institution_id=inst.id,
        school_id=school.id,
        program_name="Master of Business Analytics",
        degree_type="masters",
        slug=f"test-mban-{uuid.uuid4().hex[:6]}",
        is_published=True,
    )
    db_session.add(program)
    await db_session.flush()
    return inst, school, program


def _post(ext, title, body=""):
    return NormalizedItem(kind="post", external_id=ext, title=title, body=body)


def _event(ext, title, days=5, location=None):
    return NormalizedItem(
        kind="event",
        external_id=ext,
        title=title,
        start_time=datetime.now(UTC) + timedelta(days=days),
        location=location,
    )


async def test_school_scoped_post_tagged_and_curated(db_session):
    inst, school, _ = await _scaffold(db_session)
    svc = ContentIngestService(db_session)
    # curated feed → kept wholesale even without a keyword hit
    n = await svc.upsert_posts(
        inst.id,
        [_post("a1", "Ten from MIT accept Fulbright awards")],
        school_id=school.id,
        keywords=["sloan"],
        curated=True,
    )
    assert n == 1
    row = (await db_session.scalars(select(InstitutionPost))).first()
    assert row.institution_id == inst.id
    assert row.school_id == school.id
    assert row.program_id is None
    assert row.source == "news_rss"


async def test_program_scoped_post_gated_by_keyword(db_session):
    inst, _, program = await _scaffold(db_session)
    svc = ContentIngestService(db_session)
    items = [
        _post("b1", "Business Analytics demo day", "MBAn students present"),
        _post("b2", "Poetry reading in Killian Court"),
    ]
    n = await svc.upsert_posts(
        inst.id,
        items,
        program_id=program.id,
        keywords=["mban", "business analytics"],
        curated=False,
    )
    assert n == 1  # only the relevant one
    rows = (await db_session.scalars(select(InstitutionPost))).all()
    assert len(rows) == 1
    assert rows[0].program_id == program.id
    assert rows[0].school_id is None


async def test_events_status_upcoming_and_gated(db_session):
    inst, school, _ = await _scaffold(db_session)
    svc = ContentIngestService(db_session)
    items = [
        _event("e1", "MIT Sloan info session"),
        _event("e2", "Random campus-wide talk"),
    ]
    n = await svc.upsert_events(inst.id, items, school_id=school.id, keywords=["sloan"])
    assert n == 1  # gate drops the non-Sloan event
    ev = (await db_session.scalars(select(Event))).first()
    assert ev.school_id == school.id
    assert ev.status == "upcoming"  # surfaces via list_upcoming_events
    assert ev.source == "events_feed"


async def test_same_external_id_distinct_per_scope(db_session):
    """The same article id can exist once at institution scope and once at
    school scope — the scope is part of the dedupe key."""
    inst, school, _ = await _scaffold(db_session)
    svc = ContentIngestService(db_session)
    await svc.upsert_posts(inst.id, [_post("dup", "Shared article")], keywords=None)
    await svc.upsert_posts(
        inst.id, [_post("dup", "Shared article")], school_id=school.id, keywords=None
    )
    rows = (await db_session.scalars(select(InstitutionPost))).all()
    assert len(rows) == 2
    scopes = sorted((r.school_id is None) for r in rows)
    assert scopes == [False, True]  # one institution-scope, one school-scope


async def test_idempotent_rerun_no_duplicates(db_session):
    inst, school, _ = await _scaffold(db_session)
    svc = ContentIngestService(db_session)
    items = [_post("x1", "MIT Sloan launches new lab")]
    await svc.upsert_posts(inst.id, items, school_id=school.id, keywords=["sloan"])
    await svc.upsert_posts(inst.id, items, school_id=school.id, keywords=["sloan"])
    rows = (await db_session.scalars(select(InstitutionPost))).all()
    assert len(rows) == 1


async def test_post_persists_image_url(db_session):
    inst, school, _ = await _scaffold(db_session)
    svc = ContentIngestService(db_session)
    item = NormalizedItem(
        kind="post",
        external_id="img1",
        title="MIT Sloan launches lab",
        image_url="https://news.mit.edu/cover.jpg",
    )
    await svc.upsert_posts(inst.id, [item], school_id=school.id, keywords=["sloan"])
    row = (await db_session.scalars(select(InstitutionPost))).first()
    assert row.image_url == "https://news.mit.edu/cover.jpg"


async def test_institution_scope_dedups_cross_scope(db_session):
    from unipaith.services.institution_service import InstitutionService

    inst, school, _ = await _scaffold(db_session)
    svc = ContentIngestService(db_session)
    # Same article ingested at BOTH institution scope and school scope.
    await svc.upsert_posts(inst.id, [_post("dup", "Shared article")], keywords=None)
    await svc.upsert_posts(
        inst.id, [_post("dup", "Shared article")], school_id=school.id, keywords=None
    )
    isvc = InstitutionService(db_session)
    inst_only = await isvc.get_public_posts(inst.id, institution_scope=True)
    assert len(inst_only) == 1  # only the institution-wide copy — no duplicate
    everything = await isvc.get_public_posts(inst.id)
    assert len(everything) == 2  # unfiltered still returns both scopes


async def test_archived_post_not_resurrected(db_session):
    inst, school, _ = await _scaffold(db_session)
    svc = ContentIngestService(db_session)
    items = [_post("h1", "Sloan story")]
    await svc.upsert_posts(inst.id, items, school_id=school.id, keywords=["sloan"])
    row = (await db_session.scalars(select(InstitutionPost))).first()
    row.status = "archived"
    await db_session.flush()
    # re-ingest → stays archived, not re-published
    await svc.upsert_posts(inst.id, items, school_id=school.id, keywords=["sloan"])
    rows = (await db_session.scalars(select(InstitutionPost))).all()
    assert len(rows) == 1
    assert rows[0].status == "archived"

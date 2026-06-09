"""Tests for the channel-source ingestion (news RSS → posts, iCal → events)."""

import uuid

from sqlalchemy import func, select

from unipaith.models.institution import Event, Institution, InstitutionPost
from unipaith.models.user import User, UserRole
from unipaith.services.content_ingest import (
    ContentIngestService,
    EventsFeedSource,
    NewsRssSource,
)

_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>MIT News</title>
<item><title>MIT discovers X</title><link>https://news.mit.edu/2026/x</link>
<guid>https://news.mit.edu/2026/x</guid>
<description>&lt;p&gt;A &lt;b&gt;breakthrough&lt;/b&gt;.&lt;/p&gt;</description>
<pubDate>Mon, 09 Jun 2026 10:00:00 GMT</pubDate></item>
<item><title>MIT launches Y</title><link>https://news.mit.edu/2026/y</link>
<guid>https://news.mit.edu/2026/y</guid><description>Details Y</description>
<pubDate>Tue, 10 Jun 2026 10:00:00 GMT</pubDate></item>
</channel></rss>"""

_ICAL = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//MIT//Calendar//EN
BEGIN:VEVENT
UID:evt-123@mit.edu
SUMMARY:MIT Open House
DTSTART:20260915T140000Z
DTEND:20260915T160000Z
LOCATION:Killian Court
URL:https://calendar.mit.edu/event/123
DESCRIPTION:Come visit.
END:VEVENT
END:VCALENDAR"""


def test_news_rss_parses_posts():
    items = NewsRssSource().parse(_RSS)
    assert len(items) == 2
    first = next(i for i in items if "discovers X" in i.title)
    assert first.kind == "post"
    assert first.external_id == "https://news.mit.edu/2026/x"
    assert first.url == "https://news.mit.edu/2026/x"
    assert "breakthrough" in first.body and "<b>" not in first.body  # HTML stripped
    assert first.published_at is not None


def test_events_ical_parses_events():
    items = EventsFeedSource().parse(_ICAL)
    assert len(items) == 1
    e = items[0]
    assert e.kind == "event"
    assert e.external_id == "evt-123@mit.edu"
    assert e.title == "MIT Open House"
    assert e.location == "Killian Court"
    assert e.url == "https://calendar.mit.edu/event/123"
    assert e.start_time is not None and e.end_time is not None
    assert e.end_time > e.start_time


def test_events_malformed_ical_is_safe():
    assert EventsFeedSource().parse("not a calendar") == []


async def _make_institution(db_session) -> Institution:
    admin = User(
        id=uuid.uuid4(),
        email=f"inst-{uuid.uuid4().hex[:6]}@example.com",
        cognito_sub=f"dev-{uuid.uuid4().hex[:8]}",
        role=UserRole("institution_admin"),
        is_active=True,
    )
    db_session.add(admin)
    await db_session.flush()
    inst = Institution(
        admin_user_id=admin.id,
        name=f"Test U {uuid.uuid4().hex[:4]}",
        type="university",
        country="United States",
        description_text="stub",
        student_body_size=1,
        is_verified=True,
    )
    db_session.add(inst)
    await db_session.commit()
    return inst


async def test_upsert_posts_idempotent_and_attributed(db_session):
    inst = await _make_institution(db_session)
    svc = ContentIngestService(db_session)
    items = NewsRssSource().parse(_RSS)

    created = await svc.upsert_posts(inst.id, items)
    assert created == 2
    again = await svc.upsert_posts(inst.id, items)  # re-run → no new rows
    assert again == 0

    rows = (
        (
            await db_session.execute(
                select(InstitutionPost).where(InstitutionPost.institution_id == inst.id)
            )
        )
        .scalars()
        .all()
    )
    assert len(rows) == 2
    p = rows[0]
    assert p.source == "news_rss"
    assert p.source_url and p.source_url.startswith("https://news.mit.edu/")
    assert p.status == "published"


async def test_archived_post_not_resurrected(db_session):
    inst = await _make_institution(db_session)
    svc = ContentIngestService(db_session)
    items = NewsRssSource().parse(_RSS)
    await svc.upsert_posts(inst.id, items)

    hidden = (
        await db_session.execute(
            select(InstitutionPost).where(InstitutionPost.institution_id == inst.id).limit(1)
        )
    ).scalar_one()
    hidden.status = "archived"
    await db_session.flush()

    await svc.upsert_posts(inst.id, items)  # re-run must NOT republish it
    await db_session.refresh(hidden)
    assert hidden.status == "archived"


async def test_upsert_events_idempotent(db_session):
    inst = await _make_institution(db_session)
    svc = ContentIngestService(db_session)
    items = EventsFeedSource().parse(_ICAL)

    assert await svc.upsert_events(inst.id, items) == 1
    assert await svc.upsert_events(inst.id, items) == 0  # dedup by UID

    count = await db_session.scalar(
        select(func.count()).select_from(Event).where(Event.institution_id == inst.id)
    )
    assert count == 1
    ev = (
        await db_session.execute(select(Event).where(Event.institution_id == inst.id))
    ).scalar_one()
    assert ev.source == "events_feed"
    assert ev.external_id == "evt-123@mit.edu"
    assert ev.source_url == "https://calendar.mit.edu/event/123"

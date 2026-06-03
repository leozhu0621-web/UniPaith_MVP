"""Spec 69 §3 — crawl → extract → ingest program pipeline.

The wiring that lets the continuous crawler add schools/programs on its own:
deterministic, grounded extraction (schema.org JSON-LD + conservative text) →
first-party-safe catalog ingestion → driven by the engine tick for any source
linked to an institution. Everything here runs without a network or an LLM.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.crawler import CrawlSource
from unipaith.models.institution import Institution, Program
from unipaith.models.knowledge import CrawlFrontier
from unipaith.models.user import User
from unipaith.services.catalog import (
    CatalogIngestService,
    extract_programs,
    ingest_programs_from_page,
    to_ingest_rows,
)
from unipaith.services.catalog.program_extractor import strip_html
from unipaith.services.crawler.engine import KnowledgeEngine
from unipaith.services.crawler.fetcher import FetchResult

# ── sample fetched pages ─────────────────────────────────────────────────────
JSONLD_PAGE = (
    '<html><head><script type="application/ld+json">'
    '{"@type":"EducationalOccupationalProgram",'
    '"name":"Master of Science in Computer Science",'
    '"educationalCredentialAwarded":"Master of Science",'
    '"description":"A graduate CS program."}'
    "</script></head><body>x</body></html>"
)
TEXT_PAGE = (
    "<html><body><h1>Graduate Programs</h1><p>We offer a PhD in Computer Science, "
    "an MS in Data Science, an MBA in Finance, a Bachelor of Science in Mechanical "
    "Engineering, and an MEng in Civil Engineering.</p></body></html>"
)
JUNK_PAGE = (
    "<html><body><p>Welcome to campus! Life here is wonderful. Apply today.</p></body></html>"
)


# ── extractor (pure, no DB) ──────────────────────────────────────────────────


def test_extract_from_jsonld():
    progs = extract_programs(JSONLD_PAGE)
    assert len(progs) == 1
    assert progs[0]["program_name"] == "Master of Science in Computer Science"
    assert progs[0]["degree_type"] == "MS"
    assert progs[0]["cip_code"] == "11.0701"


def test_extract_from_text_multiple():
    by = {(p["program_name"], p["degree_type"]) for p in extract_programs(TEXT_PAGE)}
    assert ("Computer Science (PhD)", "PhD") in by
    assert ("Data Science (MS)", "MS") in by
    assert ("Finance (MBA)", "MBA") in by
    assert ("Mechanical Engineering (BS)", "BS") in by
    assert ("Civil Engineering (MEng)", "MEng") in by


def test_extract_junk_is_empty():
    # No degree+field signal → nothing (grounded, never fabricates).
    assert extract_programs(JUNK_PAGE) == []
    assert extract_programs("") == []


def test_to_ingest_rows_stable_external_id():
    rows = to_ingest_rows(extract_programs(TEXT_PAGE))
    assert all(r["external_id"] for r in rows)
    # Deterministic: same input → same external_ids (so a re-crawl updates in place).
    again = to_ingest_rows(extract_programs(TEXT_PAGE))
    assert [r["external_id"] for r in rows] == [r["external_id"] for r in again]


def test_strip_html_drops_scripts():
    assert "alert" not in strip_html("<p>Hi</p><script>alert(1)</script>")


# ── orchestration (DB) ───────────────────────────────────────────────────────


async def _institution(db: AsyncSession, inst_user: User) -> Institution:
    db.add(inst_user)
    inst = Institution(
        admin_user_id=inst_user.id, name="Test U", type="university", country="United States"
    )
    db.add(inst)
    await db.flush()
    return inst


async def _programs(db: AsyncSession, inst_id) -> list[Program]:
    res = await db.execute(select(Program).where(Program.institution_id == inst_id))
    return list(res.scalars().all())


@pytest.mark.asyncio
async def test_ingest_from_page_creates_programs(db_session: AsyncSession, mock_institution_user):
    inst = await _institution(db_session, mock_institution_user)
    summary = await ingest_programs_from_page(
        db_session,
        institution_id=inst.id,
        url="https://grad.testu.edu/programs",
        content=TEXT_PAGE,
    )
    assert summary["extracted"] == 5
    assert summary["created"] == 5
    progs = await _programs(db_session, inst.id)
    assert {p.degree_type for p in progs} == {"doctoral", "masters", "bachelors"}
    assert all(p.catalog_source == "crawled" and p.is_published for p in progs)


@pytest.mark.asyncio
async def test_ingest_from_page_empty_on_junk(db_session: AsyncSession, mock_institution_user):
    inst = await _institution(db_session, mock_institution_user)
    summary = await ingest_programs_from_page(
        db_session, institution_id=inst.id, url="https://grad.testu.edu/x", content=JUNK_PAGE
    )
    assert summary == {"extracted": 0, "created": 0, "updated": 0, "skipped": 0}
    assert await _programs(db_session, inst.id) == []


@pytest.mark.asyncio
async def test_ingest_from_page_non_text_safe(db_session: AsyncSession, mock_institution_user):
    inst = await _institution(db_session, mock_institution_user)
    for bad in (None, b"bytes", 123, "   "):
        summary = await ingest_programs_from_page(
            db_session, institution_id=inst.id, url="https://grad.testu.edu/x", content=bad
        )
        assert summary["extracted"] == 0
    assert await _programs(db_session, inst.id) == []


@pytest.mark.asyncio
async def test_crawl_never_overwrites_verified(db_session: AsyncSession, mock_institution_user):
    inst = await _institution(db_session, mock_institution_user)
    # An institution-verified program the crawl will also "see" on the page.
    await CatalogIngestService(db_session).ingest_programs(
        inst.id,
        [{"program_name": "Computer Science (PhD)", "degree_type": "PhD", "tuition": "61990"}],
        source="institution_verified",
    )
    summary = await ingest_programs_from_page(
        db_session,
        institution_id=inst.id,
        url="https://grad.testu.edu/programs",
        content=TEXT_PAGE,
    )
    # The verified CS-PhD is skipped (authority); the other 4 are still added.
    assert summary["skipped"] >= 1
    assert summary["created"] == 4
    cs = next(
        p
        for p in await _programs(db_session, inst.id)
        if p.program_name == "Computer Science (PhD)"
    )
    assert cs.catalog_source == "institution_verified"  # crawl never overwrote it
    assert cs.tuition == 61990


# ── tick wiring (DB, no network) ─────────────────────────────────────────────


def _inject(content: object, host: str):
    """A fetcher.fetch replacement that returns injected content (no network)."""

    def _fetch(url, **_kwargs):
        return FetchResult(
            url=url, status="ok", content=content, content_format="text", source_domain=host
        )

    return _fetch


@pytest.mark.asyncio
async def test_tick_extracts_programs_for_linked_source(
    db_session: AsyncSession, mock_institution_user
):
    inst = await _institution(db_session, mock_institution_user)
    db_session.add(
        CrawlSource(
            name="grad.testu.edu",
            slug="grad-testu-edu",
            domain="grad.testu.edu",
            publisher_kind="academic",
            trust_tier=2,
            allowlisted=True,
            enabled=True,
            institution_id=inst.id,
        )
    )
    db_session.add(
        CrawlFrontier(
            url="https://grad.testu.edu/programs",
            domain="grad.testu.edu",
            priority=85,
            status="pending",
            content_format_hint="web",
        )
    )
    await db_session.flush()

    engine = KnowledgeEngine(db_session)
    engine.fetcher.fetch = _inject(TEXT_PAGE, "grad.testu.edu")  # inject the page

    result = await engine.tick()
    assert result["processed"] == 1
    assert result["programs_added"] == 5
    assert len(await _programs(db_session, inst.id)) == 5


@pytest.mark.asyncio
async def test_tick_no_extraction_for_unlinked_source(db_session: AsyncSession):
    # A source with no institution_id is fetched but yields no program extraction.
    db_session.add(
        CrawlSource(
            name="grad.other.edu",
            slug="grad-other-edu",
            domain="grad.other.edu",
            publisher_kind="academic",
            trust_tier=2,
            allowlisted=True,
            enabled=True,
        )
    )
    db_session.add(
        CrawlFrontier(
            url="https://grad.other.edu/programs",
            domain="grad.other.edu",
            priority=85,
            status="pending",
            content_format_hint="web",
        )
    )
    await db_session.flush()

    engine = KnowledgeEngine(db_session)
    engine.fetcher.fetch = _inject(TEXT_PAGE, "grad.other.edu")

    result = await engine.tick()
    assert result["processed"] == 1
    assert result["programs_added"] == 0


# ── re-crawl on cadence (keeps the 30-min routine doing real work) ────────────


def _linked_source(inst_id):
    return CrawlSource(
        name="grad.testu.edu",
        slug="grad-testu-edu",
        domain="grad.testu.edu",
        publisher_kind="academic",
        trust_tier=2,
        allowlisted=True,
        enabled=True,
        institution_id=inst_id,
    )


@pytest.mark.asyncio
async def test_tick_recrawls_completed_due_item(db_session: AsyncSession, mock_institution_user):
    inst = await _institution(db_session, mock_institution_user)
    db_session.add(_linked_source(inst.id))
    # A completed item already past its re-crawl interval → re-crawled this tick.
    db_session.add(
        CrawlFrontier(
            url="https://grad.testu.edu/programs",
            domain="grad.testu.edu",
            priority=85,
            status="completed",
            next_crawl_after=datetime.now(UTC) - timedelta(hours=1),
            content_format_hint="web",
        )
    )
    await db_session.flush()

    engine = KnowledgeEngine(db_session)
    engine.fetcher.fetch = _inject(TEXT_PAGE, "grad.testu.edu")

    result = await engine.tick()
    assert result["processed"] == 1  # the due completed item was re-crawled
    assert result["programs_added"] == 5


@pytest.mark.asyncio
async def test_tick_skips_completed_not_due(db_session: AsyncSession, mock_institution_user):
    inst = await _institution(db_session, mock_institution_user)
    db_session.add(_linked_source(inst.id))
    # A completed item NOT yet due (future) → must NOT re-crawl (polite cadence).
    db_session.add(
        CrawlFrontier(
            url="https://grad.testu.edu/programs",
            domain="grad.testu.edu",
            priority=85,
            status="completed",
            next_crawl_after=datetime.now(UTC) + timedelta(hours=12),
            content_format_hint="web",
        )
    )
    await db_session.flush()

    engine = KnowledgeEngine(db_session)
    engine.fetcher.fetch = _inject(TEXT_PAGE, "grad.testu.edu")

    result = await engine.tick()
    assert result["processed"] == 0  # not due → untouched
    assert result["programs_added"] == 0
    assert await _programs(db_session, inst.id) == []

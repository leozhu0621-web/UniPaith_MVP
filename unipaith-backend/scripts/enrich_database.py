"""Put the crawler to work — enrich the database end to end.

Usage:
    cd unipaith-backend
    PYTHONPATH=src DATABASE_URL=<...> python -m scripts.enrich_database
    # add CRAWLER_LIVE_FETCH_ENABLED=true to also run live crawl ticks

Idempotent + resilient (each stage independent; reports what landed). Stages:
  1. schema (create_all + pgvector)
  2. seed_all — the crawler's Tier-1 reference seeders (ref_* / scholarships /
     crawl_sources / knowledge_entities)
  3. crawl frontier — queue university program pages for the engine
  4. program catalog — real programs via the Spec-69 ingestion (sample_catalog)
  5. live crawl — engine ticks against the frontier (only fetches if live fetch on)
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from urllib.parse import urlparse

from sqlalchemy import select, text

import unipaith.models  # noqa: F401 — registers every table on Base.metadata
from unipaith.config import settings
from unipaith.database import async_session, engine
from unipaith.models.base import Base
from unipaith.models.institution import Institution
from unipaith.models.knowledge import CrawlFrontier
from unipaith.models.user import User, UserRole
from unipaith.services.catalog import seed_catalog_for_institution
from unipaith.services.crawler.engine import KnowledgeEngine
from unipaith.services.crawler.seed import seed_all

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("enrich_database")

_TABLES = [
    "crawl_sources",
    "knowledge_entities",
    "reference_entities",
    "scholarships",
    "ref_occupations",
    "ref_tests",
    "ref_visas",
    "ref_rankings",
    "ref_majors",
    "crawl_frontier",
    "institutions",
    "programs",
]

# A representative frontier slice (full list in scripts.seed_knowledge_engine).
_FRONTIER = [
    "https://www.mit.edu/education/",
    "https://grad.stanford.edu/programs/",
    "https://gsas.harvard.edu/programs-of-study",
    "https://www.cmu.edu/graduate/",
    "https://grad.berkeley.edu/programs/",
    "https://www.gradschool.cornell.edu/academics/fields-of-study/",
    "https://gradadmissions.mit.edu/programs",
    "https://admission.gatech.edu/graduate",
    "https://grad.illinois.edu/admissions/programs",
    "https://www.gradschool.wisc.edu/academics/programs/",
]


async def _counts() -> dict:
    out: dict[str, object] = {}
    async with async_session() as db:
        for t in _TABLES:
            try:
                r = await db.execute(text(f"SELECT count(*) FROM {t}"))  # noqa: S608 — fixed allowlist
                out[t] = r.scalar_one()
            except Exception:
                await db.rollback()
                out[t] = "—"
    return out


async def _seed_frontier() -> int:
    added = 0
    async with async_session() as db:
        existing = {u for (u,) in (await db.execute(select(CrawlFrontier.url))).all()}
        for url in _FRONTIER:
            if url in existing:
                continue
            db.add(
                CrawlFrontier(
                    url=url,
                    domain=urlparse(url).netloc,
                    priority=85,
                    status="pending",
                    content_format_hint="web",
                )
            )
            added += 1
        await db.commit()
    return added


async def _ensure_catalog() -> dict:
    """Ensure an institution + a real program catalog (Spec-69 ingestion)."""
    async with async_session() as db:
        inst = (await db.execute(select(Institution).limit(1))).scalar_one_or_none()
        if inst is None:
            user = User(
                id=uuid.uuid4(),
                email=f"ref-{uuid.uuid4().hex[:6]}@unipaith.co",
                cognito_sub=f"sys-{uuid.uuid4().hex[:8]}",
                role=UserRole.institution_admin,
                is_active=True,
            )
            db.add(user)
            await db.flush()
            inst = Institution(
                admin_user_id=user.id,
                name="UniPaith Reference University",
                type="university",
                country="United States",
            )
            db.add(inst)
            await db.flush()
        summary = await seed_catalog_for_institution(db, inst.id, source="first_party")
        await db.commit()
    return summary


async def _allowlist_frontier_domains() -> int:
    """Allowlist the frontier's university domains so the engine may fetch them
    (the registry blocks non-allowlisted domains by design, §11)."""
    from unipaith.models.crawler import CrawlSource

    added = 0
    async with async_session() as db:
        have = {d for (d,) in (await db.execute(select(CrawlSource.domain))).all()}
        for url in _FRONTIER:
            domain = urlparse(url).netloc
            if domain in have:
                continue
            db.add(
                CrawlSource(
                    name=domain,
                    slug=domain.replace(".", "-"),
                    domain=domain,
                    publisher_kind="academic",
                    trust_tier=2,
                    allowlisted=True,
                    enabled=True,
                )
            )
            have.add(domain)
            added += 1
        await db.commit()
    return added


async def _live_crawl() -> dict:
    total = {"processed": 0, "errors": 0, "skipped": 0, "due": 0}
    async with async_session() as db:
        # Re-queue previously blocked/completed items so newly-allowlisted domains crawl.
        await db.execute(
            text(
                "UPDATE crawl_frontier SET status='pending', next_crawl_after=NULL "
                "WHERE status IN ('blocked', 'completed')"
            )
        )
        await db.commit()
        eng = KnowledgeEngine(db)
        for _ in range(3):
            r = await eng.tick(limit=10)
            for k in total:
                total[k] += r.get(k, 0)
        await db.commit()
    return total


async def _stage(name: str, coro):
    try:
        return await coro
    except Exception as exc:  # resilient: one stage failing doesn't abort the rest
        logger.warning("stage %s failed: %s", name, exc)
        return {"error": str(exc)[:160]}


async def main() -> None:
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)

    before = await _counts()

    async def _seed():
        async with async_session() as db:
            return await seed_all(db, commit=True)

    seed_result = await _stage("seed_all", _seed())
    frontier_added = await _stage("frontier", _seed_frontier())
    catalog = await _stage("catalog", _ensure_catalog())
    if settings.crawler_live_fetch_enabled:
        allowlisted = await _stage("allowlist", _allowlist_frontier_domains())
        live = await _stage("live_crawl", _live_crawl())
    else:
        allowlisted = 0
        live = {"skipped": "crawler_live_fetch_enabled is OFF"}
    after = await _counts()

    print("\n=== Crawler enrichment ===")
    print(f"  seed_all:        {seed_result}")
    print(f"  frontier seeded: +{frontier_added}")
    print(f"  catalog ingest:  {catalog}")
    print(f"  domains allowlisted: +{allowlisted}")
    print(f"  live crawl:      {live}")
    print("\n  table: before → after")
    for t in _TABLES:
        mark = "  +" if before.get(t) != after.get(t) else "   "
        print(f"{mark} {t}: {before.get(t)} → {after.get(t)}")


if __name__ == "__main__":
    asyncio.run(main())

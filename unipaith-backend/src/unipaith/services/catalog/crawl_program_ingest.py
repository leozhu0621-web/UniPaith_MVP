"""Spec 69 §3 — crawl → extract → ingest programs.

The orchestration that turns a crawled university page into Program rows. The
continuous engine tick calls this for any frontier item whose ``CrawlSource`` is
linked to an institution (``institution_id`` set).

Grounded + idempotent + never-5xx:
- extraction (``program_extractor``) yields nothing on a junk/marketing page, so
  nothing is written unless the page actually lists programs;
- ingestion is first-party-safe — ``source='crawled'`` has authority 1, so it
  *adds* programs the institution hasn't published but never overwrites
  institution-verified or uploaded data (``CatalogIngestService`` skips the
  conflict and routes it to review).
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.services.catalog.ingest_service import CatalogIngestService
from unipaith.services.catalog.program_extractor import extract_programs, to_ingest_rows


async def ingest_programs_from_page(
    db: AsyncSession,
    *,
    institution_id: UUID,
    url: str,
    content: object | None,
    source: str = "crawled",
    school_id: UUID | None = None,
) -> dict:
    """Extract programs from a fetched page and ingest them under the institution.

    Returns ``{extracted, created, updated, skipped}``. Safe on any input:
    non-text content, an empty body, or a page with no clear program signal all
    yield ``{extracted: 0, created: 0, updated: 0, skipped: 0}``.
    """
    summary = {"extracted": 0, "created": 0, "updated": 0, "skipped": 0}
    if not isinstance(content, str) or not content.strip():
        return summary
    programs = extract_programs(content)
    summary["extracted"] = len(programs)
    if not programs:
        return summary
    rows = to_ingest_rows(programs)
    result = await CatalogIngestService(db).ingest_programs(
        institution_id, rows, source=source, source_url=url, school_id=school_id
    )
    summary.update(result)
    return summary

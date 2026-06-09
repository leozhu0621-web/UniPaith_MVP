"""Ingest a scope's public channel feeds into Events / InstitutionPosts.

A *scope* is an institution, a school, or a program — each may carry a
``content_sources`` config. Scheduled (daily) + on-demand via the refresh
endpoint. Idempotent: rows are keyed by
``(institution_id, school_id, program_id, source, external_id)``; a row a
school has hidden (archived/cancelled) is never resurrected. Fail-soft per feed.

Relevance: items from authoritative channels are kept only when they actually
pertain to the scope — ``passes_relevance`` drops a feed item whose visible text
does not contain a configured keyword (curated topic feeds bypass the gate).
"""

from __future__ import annotations

import logging
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from unipaith.models.institution import (
    Event,
    Institution,
    InstitutionPost,
    Program,
    School,
)

from .base import NormalizedItem, passes_relevance
from .events_feed import EventsFeedSource
from .rss import NewsRssSource

logger = logging.getLogger(__name__)

_NEWS = NewsRssSource.name  # "news_rss"
_EVENTS = EventsFeedSource.name  # "events_feed"
_HEADERS = {"User-Agent": "UniPaithBot/1.0 (+https://unipaith.co)"}


class ContentIngestService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def ingest_all(self) -> dict:
        """Refresh every institution/school/program that has content_sources."""
        total = {"institutions": 0, "schools": 0, "programs": 0, "posts": 0, "events": 0}

        insts = (
            await self.session.scalars(
                select(Institution).where(Institution.content_sources.isnot(None))
            )
        ).all()
        for inst in insts:
            c = await self._ingest_scope(inst.id, inst.content_sources)
            total["institutions"] += 1
            total["posts"] += c["posts"]
            total["events"] += c["events"]

        schools = (
            await self.session.scalars(select(School).where(School.content_sources.isnot(None)))
        ).all()
        for sch in schools:
            c = await self._ingest_scope(sch.institution_id, sch.content_sources, school_id=sch.id)
            total["schools"] += 1
            total["posts"] += c["posts"]
            total["events"] += c["events"]

        programs = (
            await self.session.scalars(select(Program).where(Program.content_sources.isnot(None)))
        ).all()
        for prog in programs:
            c = await self._ingest_scope(
                prog.institution_id, prog.content_sources, program_id=prog.id
            )
            total["programs"] += 1
            total["posts"] += c["posts"]
            total["events"] += c["events"]

        return total

    async def ingest_institution(self, inst: Institution) -> dict:
        return await self._ingest_scope(inst.id, inst.content_sources)

    async def _ingest_scope(
        self,
        inst_id: UUID,
        cfg: dict | None,
        *,
        school_id: UUID | None = None,
        program_id: UUID | None = None,
    ) -> dict:
        cfg = cfg or {}
        keywords = cfg.get("keywords")
        counts = {"posts": 0, "events": 0}

        news_url = cfg.get("news_rss")
        if news_url:
            items = await self._fetch_and_parse(news_url, NewsRssSource())
            counts["posts"] = await self.upsert_posts(
                inst_id,
                items,
                school_id=school_id,
                program_id=program_id,
                keywords=keywords,
                curated=bool(cfg.get("news_curated")),
            )

        ef = cfg.get("events_feed") or {}
        if ef.get("url"):
            src = EventsFeedSource(feed_type=ef.get("type", "ical"))
            items = await self._fetch_and_parse(ef["url"], src)
            counts["events"] = await self.upsert_events(
                inst_id,
                items,
                school_id=school_id,
                program_id=program_id,
                keywords=keywords,
            )

        return counts

    async def _fetch_and_parse(self, url: str, source) -> list[NormalizedItem]:
        try:
            async with httpx.AsyncClient(
                timeout=15.0, follow_redirects=True, headers=_HEADERS
            ) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                return source.parse(resp.text)
        except Exception as exc:  # noqa: BLE001 — one bad feed must not break the run
            logger.warning("content_ingest: fetch/parse failed for %s: %s", url, exc)
            return []

    async def upsert_posts(
        self,
        inst_id: UUID,
        items: list[NormalizedItem],
        *,
        school_id: UUID | None = None,
        program_id: UUID | None = None,
        keywords: list[str] | None = None,
        curated: bool = False,
    ) -> int:
        created = 0
        for it in items:
            if not passes_relevance(it, keywords, curated):
                continue
            existing = await self.session.scalar(
                select(InstitutionPost).where(
                    InstitutionPost.institution_id == inst_id,
                    InstitutionPost.school_id == school_id,
                    InstitutionPost.program_id == program_id,
                    InstitutionPost.source == _NEWS,
                    InstitutionPost.external_id == it.external_id,
                )
            )
            if existing is not None:
                if existing.status == "archived":  # school hid it — leave it hidden
                    continue
                existing.title = it.title
                existing.body = it.body or it.title
                existing.source_url = it.url
                existing.published_at = it.published_at
                continue
            self.session.add(
                InstitutionPost(
                    institution_id=inst_id,
                    school_id=school_id,
                    program_id=program_id,
                    title=it.title,
                    body=it.body or it.title,
                    source=_NEWS,
                    external_id=it.external_id,
                    source_url=it.url,
                    status="published",
                    published_at=it.published_at,
                )
            )
            created += 1
        await self.session.flush()
        return created

    async def upsert_events(
        self,
        inst_id: UUID,
        items: list[NormalizedItem],
        *,
        school_id: UUID | None = None,
        program_id: UUID | None = None,
        keywords: list[str] | None = None,
    ) -> int:
        created = 0
        for it in items:
            if not it.start_time:
                continue
            if not passes_relevance(it, keywords, curated=False):
                continue
            existing = await self.session.scalar(
                select(Event).where(
                    Event.institution_id == inst_id,
                    Event.school_id == school_id,
                    Event.program_id == program_id,
                    Event.source == _EVENTS,
                    Event.external_id == it.external_id,
                )
            )
            end = it.end_time or it.start_time
            if existing is not None:
                if existing.status == "cancelled":  # school cancelled it — leave it
                    continue
                existing.event_name = it.title
                existing.description = it.body
                existing.start_time = it.start_time
                existing.end_time = end
                existing.location = it.location
                existing.source_url = it.url
                # Heal rows seeded/ingested before the status fix (stored "live"),
                # which list_upcoming_events filters out. The item is still in the
                # feed → it is upcoming; "cancelled" was already skipped above.
                existing.status = "upcoming"
                continue
            self.session.add(
                Event(
                    institution_id=inst_id,
                    school_id=school_id,
                    program_id=program_id,
                    event_name=it.title,
                    description=it.body,
                    start_time=it.start_time,
                    end_time=end,
                    location=it.location,
                    source=_EVENTS,
                    external_id=it.external_id,
                    source_url=it.url,
                    # "upcoming" is the live state the public list endpoint filters on
                    # (EventService.create + list_upcoming_events). Was "live" — a bug
                    # that kept ingested events from ever surfacing.
                    status="upcoming",
                )
            )
            created += 1
        await self.session.flush()
        return created


def _seed_scope_sync(
    session: Session,
    *,
    inst_id: UUID,
    cfg: dict | None,
    school_id: UUID | None = None,
    program_id: UUID | None = None,
) -> dict:
    """Best-effort, sync one-shot populate for the Alembic seed migration.

    Mirrors the async ingest (scope tagging + relevance gate + status="upcoming")
    on a sync session + sync HTTP, fully fail-soft so a slow/down feed never
    breaks the migration. Only inserts new rows (never resurrects/edits).
    """
    cfg = cfg or {}
    keywords = cfg.get("keywords")
    curated = bool(cfg.get("news_curated"))
    counts = {"posts": 0, "events": 0}

    def _fetch(url, source):
        try:
            with httpx.Client(timeout=12.0, follow_redirects=True, headers=_HEADERS) as client:
                resp = client.get(url)
                resp.raise_for_status()
                return source.parse(resp.text)
        except Exception as exc:  # noqa: BLE001 — best-effort seed; never break the migration
            logger.warning("content_ingest(seed): %s failed: %s", url, exc)
            return []

    news_url = cfg.get("news_rss")
    if news_url:
        for it in _fetch(news_url, NewsRssSource()):
            if not passes_relevance(it, keywords, curated):
                continue
            exists = session.scalar(
                select(InstitutionPost.id).where(
                    InstitutionPost.institution_id == inst_id,
                    InstitutionPost.school_id == school_id,
                    InstitutionPost.program_id == program_id,
                    InstitutionPost.source == _NEWS,
                    InstitutionPost.external_id == it.external_id,
                )
            )
            if exists:
                continue
            session.add(
                InstitutionPost(
                    institution_id=inst_id,
                    school_id=school_id,
                    program_id=program_id,
                    title=it.title,
                    body=it.body or it.title,
                    source=_NEWS,
                    external_id=it.external_id,
                    source_url=it.url,
                    status="published",
                    published_at=it.published_at,
                )
            )
            counts["posts"] += 1

    ef = cfg.get("events_feed") or {}
    if ef.get("url"):
        for it in _fetch(ef["url"], EventsFeedSource(feed_type=ef.get("type", "ical"))):
            if not it.start_time:
                continue
            if not passes_relevance(it, keywords, curated=False):
                continue
            exists = session.scalar(
                select(Event.id).where(
                    Event.institution_id == inst_id,
                    Event.school_id == school_id,
                    Event.program_id == program_id,
                    Event.source == _EVENTS,
                    Event.external_id == it.external_id,
                )
            )
            if exists:
                continue
            session.add(
                Event(
                    institution_id=inst_id,
                    school_id=school_id,
                    program_id=program_id,
                    event_name=it.title,
                    description=it.body,
                    start_time=it.start_time,
                    end_time=it.end_time or it.start_time,
                    location=it.location,
                    source=_EVENTS,
                    external_id=it.external_id,
                    source_url=it.url,
                    status="upcoming",
                )
            )
            counts["events"] += 1

    session.flush()
    return counts


def seed_populate_sync(session: Session, institution: Institution) -> dict:
    """Institution-scope seed populate (back-compat wrapper)."""
    return _seed_scope_sync(session, inst_id=institution.id, cfg=institution.content_sources)


def seed_populate_sync_scope(
    session: Session,
    *,
    inst_id: UUID,
    cfg: dict | None,
    school_id: UUID | None = None,
    program_id: UUID | None = None,
) -> dict:
    """School/program-scope seed populate for the data migration."""
    return _seed_scope_sync(
        session, inst_id=inst_id, cfg=cfg, school_id=school_id, program_id=program_id
    )

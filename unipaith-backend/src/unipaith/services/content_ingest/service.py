"""Ingest a school's public channel feeds into Events / InstitutionPosts.

Scheduled (daily) + on-demand via the refresh endpoint. Idempotent: rows are
keyed by (institution_id, source, external_id); a row a school has hidden
(archived/cancelled) is never resurrected. Fail-soft per feed.
"""

from __future__ import annotations

import logging

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from unipaith.models.institution import Event, Institution, InstitutionPost

from .base import NormalizedItem
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
        rows = (
            await self.session.scalars(
                select(Institution).where(Institution.content_sources.isnot(None))
            )
        ).all()
        total = {"institutions": 0, "posts": 0, "events": 0}
        for inst in rows:
            counts = await self.ingest_institution(inst)
            total["institutions"] += 1
            total["posts"] += counts["posts"]
            total["events"] += counts["events"]
        return total

    async def ingest_institution(self, inst: Institution) -> dict:
        cfg = inst.content_sources or {}
        counts = {"posts": 0, "events": 0}

        news_url = cfg.get("news_rss")
        if news_url:
            items = await self._fetch_and_parse(news_url, NewsRssSource())
            counts["posts"] = await self.upsert_posts(inst, items)

        ef = cfg.get("events_feed") or {}
        if ef.get("url"):
            src = EventsFeedSource(feed_type=ef.get("type", "ical"))
            items = await self._fetch_and_parse(ef["url"], src)
            counts["events"] = await self.upsert_events(inst, items)

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

    async def upsert_posts(self, inst: Institution, items: list[NormalizedItem]) -> int:
        created = 0
        for it in items:
            existing = await self.session.scalar(
                select(InstitutionPost).where(
                    InstitutionPost.institution_id == inst.id,
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
                    institution_id=inst.id,
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

    async def upsert_events(self, inst: Institution, items: list[NormalizedItem]) -> int:
        created = 0
        for it in items:
            if not it.start_time:
                continue
            existing = await self.session.scalar(
                select(Event).where(
                    Event.institution_id == inst.id,
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
                continue
            self.session.add(
                Event(
                    institution_id=inst.id,
                    event_name=it.title,
                    description=it.body,
                    start_time=it.start_time,
                    end_time=end,
                    location=it.location,
                    source=_EVENTS,
                    external_id=it.external_id,
                    source_url=it.url,
                    status="upcoming",
                )
            )
            created += 1
        await self.session.flush()
        return created


def seed_populate_sync(session: Session, institution: Institution) -> dict:
    """Best-effort, sync one-shot populate for the Alembic seed migration.

    Mirrors the async ingest but on a sync session + sync HTTP, and is fully
    fail-soft so a slow/down feed never breaks the migration. Only inserts new
    rows (never resurrects/edits) — ongoing refresh is the async service's job.
    """

    def _fetch(url, source):
        try:
            with httpx.Client(timeout=12.0, follow_redirects=True, headers=_HEADERS) as client:
                resp = client.get(url)
                resp.raise_for_status()
                return source.parse(resp.text)
        except Exception as exc:  # noqa: BLE001 — best-effort seed; never break the migration
            logger.warning("content_ingest(seed): %s failed: %s", url, exc)
            return []

    cfg = institution.content_sources or {}
    counts = {"posts": 0, "events": 0}

    news_url = cfg.get("news_rss")
    if news_url:
        for it in _fetch(news_url, NewsRssSource()):
            exists = session.scalar(
                select(InstitutionPost.id).where(
                    InstitutionPost.institution_id == institution.id,
                    InstitutionPost.source == _NEWS,
                    InstitutionPost.external_id == it.external_id,
                )
            )
            if exists:
                continue
            session.add(
                InstitutionPost(
                    institution_id=institution.id,
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
            exists = session.scalar(
                select(Event.id).where(
                    Event.institution_id == institution.id,
                    Event.source == _EVENTS,
                    Event.external_id == it.external_id,
                )
            )
            if exists:
                continue
            session.add(
                Event(
                    institution_id=institution.id,
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

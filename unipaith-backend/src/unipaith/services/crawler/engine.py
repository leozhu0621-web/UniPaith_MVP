"""Spec 60 §6 — the knowledge-engine orchestrator.

Runs the pipeline (0)→(6) for one record: source → (already discovered) → fetch
→ extract → normalize → resolve → enrich-write, then emits change_events for any
material diff. Idempotent on (source_url, content_hash): unchanged content is
skipped before any parse/write (§15). The single entry both the seeder and the
scheduled tick call.

Two speeds (§6): Tier-1/2 official bulk lands structured → ``ingest_record`` with
``content_format='structured'`` skips heavy extraction (the extractor maps keys
directly); Tier-3/4 crawl uses ``content_format='text'`` for the rule-based
template path. The deterministic path is the default; nothing here requires an
LLM or the live network.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.crawler import CrawlSource
from unipaith.models.knowledge import CrawlFrontier, EngineLoopSnapshot, KnowledgeDocument
from unipaith.services.crawler.change_detector import ChangeDetector
from unipaith.services.crawler.enrichment import REF_TARGETS, EnrichmentWriter
from unipaith.services.crawler.extractor import SourceExtractionAgent
from unipaith.services.crawler.fetcher import Fetcher, content_hash
from unipaith.services.crawler.normalizer import Normalizer
from unipaith.services.crawler.resolver import EntityResolver
from unipaith.services.crawler.schemas import schema_for
from unipaith.services.crawler.sources import SourceRegistry, domain_of
from unipaith.services.crawler.util import to_jsonable

# domain -> (entity_type, name_field)
_ENTITY_OF = {
    "occupations": ("occupation", "title"),
    "tests": ("test", "name"),
    "visas": ("visa", "name"),
    "cost": ("geo_cost", "locale"),
    "majors": ("major", "title"),
    "rankings": ("ranking", "entity_name"),
    "accreditation": ("accreditation", "entity_name"),
    "scholarships": ("scholarship", "name"),
    "reference": ("reference", "name"),
}


@dataclass
class IngestResult:
    status: str  # ingested | skipped_unchanged | no_data | denied | error
    document_id: UUID | None = None
    domain: str = ""
    created: bool = False
    applied_fields: list[str] = field(default_factory=list)
    review_fields: list[str] = field(default_factory=list)
    change_event_ids: list[UUID] = field(default_factory=list)
    reason: str | None = None


class KnowledgeEngine:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.registry = SourceRegistry(db)
        self.fetcher = Fetcher()
        self.extractor = SourceExtractionAgent()
        self.normalizer = Normalizer()
        self.resolver = EntityResolver(db)
        self.writer = EnrichmentWriter(db)
        self.changes = ChangeDetector(db)

    async def _already_ingested(self, source_url: str, chash: str) -> bool:
        result = await self.db.execute(
            select(KnowledgeDocument.id).where(
                KnowledgeDocument.source_url == source_url,
                KnowledgeDocument.processing_status == "processed",
            )
        )
        for (doc_id,) in result.all():
            meta = await self.db.execute(
                select(KnowledgeDocument.metadata_json).where(KnowledgeDocument.id == doc_id)
            )
            md = meta.scalar_one_or_none() or {}
            if md.get("content_hash") == chash:
                return True
        return False

    async def ingest_record(
        self,
        *,
        domain: str,
        record: dict | None = None,
        text: str | None = None,
        url: str,
        source: str = "crawled",
        source_slug: str | None = None,
        trust_tier: int = 2,
        content_format: str = "structured",
        route_changes: bool = True,
        emit_changes: bool = True,
    ) -> IngestResult:
        """Run the full pipeline for one source record. ``source`` is the
        provenance class ('seed' | 'crawled' | …). ``emit_changes`` is False for
        the initial seed load (a first load is not a "change")."""
        schema = schema_for(domain)
        if schema is None or domain not in REF_TARGETS:
            return IngestResult(status="error", domain=domain, reason="unknown domain")

        payload_obj = record if content_format == "structured" else text
        chash = content_hash(payload_obj)
        # (2) conditional GET equivalent — idempotency before any write (§15).
        if await self._already_ingested(url, chash):
            return IngestResult(status="skipped_unchanged", domain=domain, reason="unchanged hash")

        sdomain = domain_of(url)
        doc = KnowledgeDocument(
            source_url=url,
            source_domain=sdomain,
            content_format="news" if content_format == "text" else "structured",
            title=(record or {}).get("title") if record else None,
            raw_text=text,
            extracted_facts=to_jsonable(record) if content_format == "structured" else None,
            metadata_json={
                "content_hash": chash,
                "domain": domain,
                "source_slug": source_slug,
                "trust_tier": trust_tier,
            },
            processing_status="processed",
            ingested_at=datetime.now(UTC),
            relevance_score=1.0,
        )
        self.db.add(doc)
        await self.db.flush()

        # (3) extract — grounded, schema-strict, never invents.
        payload = {
            "format": content_format,
            "trust_tier": trust_tier,
            "data": record or {},
            "text": text or "",
        }
        extraction = self.extractor.extract(domain, payload)
        if not extraction.fields:
            doc.processing_status = "no_data"
            return IngestResult(status="no_data", document_id=doc.id, domain=domain)

        # (4) normalize.
        values = self.normalizer.normalize(domain, extraction.values())
        # Confidence = mean of grounded per-field confidences.
        confs = [f.confidence for f in extraction.fields.values()]
        confidence = round(sum(confs) / len(confs), 3) if confs else 0.5

        # (6) enrich-write (with §8 authority).
        outcome = await self.writer.upsert_reference(
            domain=domain,
            values=values,
            source=source,
            confidence=confidence,
            source_url=url,
            source_domain=sdomain,
            source_document_id=doc.id,
        )

        # (5) resolve → canonical entity + raw-graph link.
        entity_type, name_field = _ENTITY_OF[domain]
        _, key_fields, _ = REF_TARGETS[domain]
        canonical_key = "|".join(str(values.get(k)) for k in key_fields)
        entity = await self.resolver.resolve(
            entity_type=entity_type,
            canonical_key=canonical_key,
            canonical_name=str(values.get(name_field) or canonical_key),
            domain=domain,
            source=source,
            confidence=confidence,
            source_url=url,
            source_domain=sdomain,
            source_document_id=doc.id,
            attributes=values,
        )
        await self.resolver.link_document(document_id=doc.id, entity=entity, confidence=confidence)

        # change_events (§3B) — new scholarships + material field diffs.
        change_ids: list[UUID] = []
        target_id = getattr(outcome.row, "id", None)
        target_name = str(values.get(name_field) or canonical_key)
        if emit_changes and outcome.created and domain == "scholarships":
            ev = await self.changes.record_change(
                domain=domain,
                target_type="scholarship",
                target_id=target_id,
                target_name=target_name,
                field=None,
                old=None,
                new=values.get("name"),
                confidence=confidence,
                source_url=url,
                source_document_id=doc.id,
                created=True,
            )
            if route_changes:
                await self.changes.route(ev)
            change_ids.append(ev.id)
        for fname, old, new in outcome.changes if emit_changes else []:
            ev = await self.changes.record_change(
                domain=domain,
                target_type=REF_TARGETS[domain][2],
                target_id=target_id,
                target_name=target_name,
                field=fname,
                old=old,
                new=new,
                confidence=confidence,
                source_url=url,
                source_document_id=doc.id,
            )
            if route_changes:
                await self.changes.route(ev)
            change_ids.append(ev.id)

        return IngestResult(
            status="ingested",
            document_id=doc.id,
            domain=domain,
            created=outcome.created,
            applied_fields=outcome.applied_fields,
            review_fields=outcome.review_fields,
            change_event_ids=change_ids,
        )

    async def ingest_batch(
        self,
        *,
        domain: str,
        records: list[dict],
        url_prefix: str,
        source: str = "seed",
        source_slug: str | None = None,
        trust_tier: int = 1,
        route_changes: bool = False,
    ) -> dict:
        """Tier-1 structured bulk-load (§6): each record lands structured → skips
        heavy extraction. Used by the seeder."""
        _, key_fields, _ = REF_TARGETS[domain]
        summary = {"ingested": 0, "skipped": 0, "no_data": 0, "created": 0}
        for rec in records:
            key = "-".join(str(rec.get(k)) for k in key_fields)
            url = f"{url_prefix}#{key}"
            res = await self.ingest_record(
                domain=domain,
                record=rec,
                url=url,
                source=source,
                source_slug=source_slug,
                trust_tier=trust_tier,
                content_format="structured",
                route_changes=route_changes,
                emit_changes=route_changes,
            )
            if res.status == "ingested":
                summary["ingested"] += 1
                if res.created:
                    summary["created"] += 1
            elif res.status == "skipped_unchanged":
                summary["skipped"] += 1
            elif res.status == "no_data":
                summary["no_data"] += 1
        return summary

    async def tick(self, *, limit: int | None = None) -> dict:
        """One scheduled engine tick (§6 / §10). Pulls due frontier items, fetches
        (gated), ingests, reschedules, and persists an ``EngineLoopSnapshot``.
        With live fetch off, due items report ``fetch_disabled`` and the tick is a
        cheap heartbeat that still records observability."""
        limit = limit or 25
        now = datetime.now(UTC)
        result = await self.db.execute(
            select(CrawlFrontier)
            .where(
                CrawlFrontier.status == "pending",
            )
            .order_by(CrawlFrontier.priority.desc())
            .limit(limit)
        )
        items = [
            it
            for it in result.scalars().all()
            if it.next_crawl_after is None or it.next_crawl_after <= now
        ]
        # Spec 69 §3 — sources linked to an institution get program extraction.
        inst_by_domain = await self._institution_domains()
        processed = errors = skipped = programs_added = 0
        for item in items:
            decision = await self.registry.is_url_allowed(item.url)
            if not decision.allowed:
                item.status = "blocked"
                item.last_error = decision.reason
                errors += 1
                continue
            fetched = self.fetcher.fetch(
                item.url, content_format=item.content_format_hint or "text"
            )
            if fetched.status in ("fetch_disabled", "denied", "error"):
                item.consecutive_failures = (item.consecutive_failures or 0) + (
                    0 if fetched.status == "fetch_disabled" else 1
                )
                item.last_error = fetched.reason
                item.next_crawl_after = now + timedelta(hours=item.domain_crawl_delay_seconds or 6)
                skipped += 1
                continue
            # Spec 69 §3 — if this source is linked to an institution, extract +
            # ingest programs from the fetched page. Grounded (nothing on a junk
            # page) and first-party-safe (source='crawled' never overwrites
            # verified data). Wrapped so a parse error never fails the tick.
            institution_id = inst_by_domain.get(item.domain) or inst_by_domain.get(
                domain_of(item.url)
            )
            if institution_id is not None:
                programs_added += await self._ingest_programs(item, fetched.content, institution_id)
            item.last_crawled_at = now
            item.crawl_count = (item.crawl_count or 0) + 1
            item.status = "completed"
            item.next_crawl_after = now + timedelta(hours=168)
            processed += 1

        await self._write_snapshot(
            processed=processed,
            errors=errors,
            skipped=skipped,
            pending_before=len(items),
        )
        return {
            "processed": processed,
            "errors": errors,
            "skipped": skipped,
            "due": len(items),
            "programs_added": programs_added,
        }

    async def _institution_domains(self) -> dict[str, UUID]:
        """§69 §3 — map domain → institution_id for sources linked to an
        institution (the ones whose crawled pages feed the program catalog)."""
        res = await self.db.execute(
            select(CrawlSource.domain, CrawlSource.institution_id).where(
                CrawlSource.institution_id.is_not(None),
                CrawlSource.enabled.is_(True),
            )
        )
        return {d: iid for d, iid in res.all() if d}

    async def _ingest_programs(self, item, content: object, institution_id: UUID) -> int:
        """Extract + ingest programs from one fetched page; return # created.
        Never raises — a parse/ingest error is recorded on the item, not surfaced."""
        # Lazy import to avoid any crawler↔catalog import cycle at module load.
        from unipaith.services.catalog.crawl_program_ingest import ingest_programs_from_page

        try:
            res = await ingest_programs_from_page(
                self.db, institution_id=institution_id, url=item.url, content=content
            )
            return res.get("created", 0)
        except Exception as exc:  # noqa: BLE001 — extraction never fails the tick
            item.last_error = f"program_ingest_error: {exc}"
            return 0

    async def _write_snapshot(
        self, *, processed: int, errors: int, skipped: int, pending_before: int
    ) -> None:
        result = await self.db.execute(select(EngineLoopSnapshot).where(EngineLoopSnapshot.id == 1))
        snap = result.scalar_one_or_none()
        if snap is None:
            snap = EngineLoopSnapshot(id=1)
            self.db.add(snap)
        snap.last_tick_at = datetime.now(UTC)
        snap.last_processed = processed
        snap.last_errors = errors
        snap.last_skipped = skipped
        snap.frontier_pending_before = pending_before
        snap.frontier_pending_after = max(0, pending_before - processed)
        snap.batch_was_empty = pending_before == 0
        snap.tick_status = "completed"
        snap.cumulative_processed = (snap.cumulative_processed or 0) + processed
        snap.cumulative_errors = (snap.cumulative_errors or 0) + errors
        await self.db.flush()


async def get_source_for_domain_tag(db: AsyncSession, tag: str) -> CrawlSource | None:
    result = await db.execute(
        select(CrawlSource).where(CrawlSource.enabled.is_(True)).order_by(CrawlSource.trust_tier)
    )
    for s in result.scalars().all():
        if tag in (s.domain_tags or []):
            return s
    return None

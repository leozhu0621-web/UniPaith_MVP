"""Spec 60 §9 / §12 — internal ops API + institution enrichment-review API.

There is **no platform-admin tier** (05 §2). The ops surface (``/crawler/*``) is
system-guarded by ``require_system`` (an ``X-Ops-Token``); the institution
surface (``/institutions/me/enrichments/*``) is the claim & verify extension (23):
an institution reviews crawled enrichments proposed for *its own* entities and
confirms or corrects them — first-party always wins (§8).
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.dependencies import require_institution_admin, require_system
from unipaith.models.crawler import ChangeEvent, CrawlSource, EntityEnrichment, KnowledgeEntity
from unipaith.models.institution import Institution, Program
from unipaith.models.knowledge import CrawlFrontier, EngineLoopSnapshot
from unipaith.models.user import User
from unipaith.services.crawler.engine import KnowledgeEngine
from unipaith.services.crawler.enrichment import EnrichmentWriter
from unipaith.services.crawler.reference_service import ReferenceService
from unipaith.services.crawler.seed import seed_all
from unipaith.services.crawler.sources import REFERENCE_DOMAINS, SOURCE_ALLOWLIST

# ── Ops API (system-guarded) ────────────────────────────────────────────────
router = APIRouter(prefix="/crawler", tags=["crawler-ops"], dependencies=[Depends(require_system)])


def _source_dict(s: CrawlSource) -> dict:
    return {
        "id": str(s.id),
        "slug": s.slug,
        "name": s.name,
        "domain": s.domain,
        "publisher_kind": s.publisher_kind,
        "trust_tier": s.trust_tier,
        "domain_tags": s.domain_tags,
        "volatility_tier": s.volatility_tier,
        "cadence_hours": s.cadence_hours,
        "allowlisted": s.allowlisted,
        "respect_robots": s.respect_robots,
        "enabled": s.enabled,
        "license": s.license,
    }


@router.get("/sources", summary="List registered allowlisted sources")
async def list_sources(db: AsyncSession = Depends(get_db)) -> list[dict]:
    rows = (
        (await db.execute(select(CrawlSource).order_by(CrawlSource.trust_tier, CrawlSource.name)))
        .scalars()
        .all()
    )
    return [_source_dict(s) for s in rows]


@router.get("/allowlist", summary="The static source allowlist policy (§11)")
async def get_allowlist() -> dict:
    return {
        "domains": [s.domain for s in SOURCE_ALLOWLIST],
        "reference_domains": list(REFERENCE_DOMAINS),
        "count": len(SOURCE_ALLOWLIST),
    }


@router.get("/status", summary="Engine status: snapshot + queue + reference counts")
async def engine_status(db: AsyncSession = Depends(get_db)) -> dict:
    snap = (
        await db.execute(select(EngineLoopSnapshot).where(EngineLoopSnapshot.id == 1))
    ).scalar_one_or_none()
    frontier_pending = int(
        (
            await db.execute(
                select(func.count())
                .select_from(CrawlFrontier)
                .where(CrawlFrontier.status == "pending")
            )
        ).scalar_one()
        or 0
    )
    entities = int(
        (await db.execute(select(func.count()).select_from(KnowledgeEntity))).scalar_one() or 0
    )
    review = int(
        (
            await db.execute(
                select(func.count())
                .select_from(EntityEnrichment)
                .where(EntityEnrichment.status.in_(("pending", "review")))
            )
        ).scalar_one()
        or 0
    )
    pending_changes = int(
        (
            await db.execute(
                select(func.count()).select_from(ChangeEvent).where(ChangeEvent.status == "pending")
            )
        ).scalar_one()
        or 0
    )
    return {
        "last_tick_at": snap.last_tick_at.isoformat() if snap and snap.last_tick_at else None,
        "cumulative_processed": snap.cumulative_processed if snap else 0,
        "frontier_pending": frontier_pending,
        "knowledge_entities": entities,
        "review_queue": review,
        "pending_change_events": pending_changes,
        "reference": await ReferenceService(db).summary(),
    }


@router.post("/seed", summary="Seed the allowlist + curated reference dataset (idempotent)")
async def run_seed(db: AsyncSession = Depends(get_db)) -> dict:
    result = await seed_all(db)
    await db.commit()
    return result


@router.post("/tick", summary="Run one engine tick (gated by live-fetch config)")
async def run_tick(limit: int = Query(25, le=200), db: AsyncSession = Depends(get_db)) -> dict:
    result = await KnowledgeEngine(db).tick(limit=limit)
    await db.commit()
    return result


@router.get("/change-events", summary="List detected change events")
async def list_change_events(
    status: str | None = Query(None),
    materiality: str | None = Query(None),
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    stmt = select(ChangeEvent).order_by(ChangeEvent.detected_at.desc()).limit(limit)
    if status:
        stmt = stmt.where(ChangeEvent.status == status)
    if materiality:
        stmt = stmt.where(ChangeEvent.materiality == materiality)
    rows = (await db.execute(stmt)).scalars().all()
    return [
        {
            "id": str(r.id),
            "target_type": r.target_type,
            "target_name": r.target_name,
            "change_type": r.change_type,
            "field_path": r.field_path,
            "materiality": r.materiality,
            "confidence": r.confidence,
            "status": r.status,
            "source_url": r.source_url,
            "routing": r.routing,
            "detected_at": r.detected_at.isoformat() if r.detected_at else None,
        }
        for r in rows
    ]


@router.get("/review-queue", summary="Low-confidence / conflicting enrichments awaiting review")
async def review_queue(
    limit: int = Query(100, le=500), db: AsyncSession = Depends(get_db)
) -> list[dict]:
    stmt = (
        select(EntityEnrichment)
        .where(EntityEnrichment.status.in_(("pending", "review")))
        .order_by(EntityEnrichment.created_at.desc())
        .limit(limit)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return [_enrichment_dict(r) for r in rows]


@router.post("/enrichments/{enrichment_id}/decide", summary="Ops decision on an enrichment")
async def decide_enrichment(
    enrichment_id: UUID,
    action: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
) -> dict:
    row = await EnrichmentWriter(db).decide(enrichment_id, action=action, decided_by=None)
    await db.commit()
    if row is None:
        return {"status": "not_found"}
    return _enrichment_dict(row)


# ── Institution enrichment-review API (claim & verify, §9) ───────────────────
enrichment_router = APIRouter(
    prefix="/institutions/me/enrichments", tags=["institution-enrichments"]
)


def _enrichment_dict(r: EntityEnrichment) -> dict:
    return {
        "id": str(r.id),
        "target_type": r.target_type,
        "target_id": str(r.target_id) if r.target_id else None,
        "target_key": r.target_key,
        "field_path": r.field_path,
        "proposed_value": r.proposed_value,
        "current_value": r.current_value,
        "source": r.source,
        "source_url": r.source_url,
        "confidence": r.confidence,
        "source_count": r.source_count,
        "status": r.status,
        "review_reason": r.review_reason,
    }


async def _my_institution(db: AsyncSession, user: User) -> Institution | None:
    return (
        await db.execute(select(Institution).where(Institution.admin_user_id == user.id))
    ).scalar_one_or_none()


@enrichment_router.get("", summary="Crawled enrichments proposed for my entities")
async def my_enrichments(
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    inst = await _my_institution(db, user)
    if inst is None:
        return []
    program_ids = [
        pid
        for (pid,) in (
            await db.execute(select(Program.id).where(Program.institution_id == inst.id))
        ).all()
    ]
    targets = or_(
        (EntityEnrichment.target_type == "institution") & (EntityEnrichment.target_id == inst.id),
        (EntityEnrichment.target_type == "program")
        & (EntityEnrichment.target_id.in_(program_ids or [inst.id])),
    )
    rows = (
        (
            await db.execute(
                select(EntityEnrichment)
                .where(targets, EntityEnrichment.status.in_(("pending", "review")))
                .order_by(EntityEnrichment.created_at.desc())
                .limit(200)
            )
        )
        .scalars()
        .all()
    )
    return [_enrichment_dict(r) for r in rows]


@enrichment_router.post(
    "/{enrichment_id}/decide", summary="Confirm or correct a proposed enrichment"
)
async def decide_my_enrichment(
    enrichment_id: UUID,
    action: str = Body(..., embed=True, description="approve | reject"),
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    inst = await _my_institution(db, user)
    if inst is None:
        return {"status": "no_institution"}
    row = await EnrichmentWriter(db).decide(enrichment_id, action=action, decided_by=user.id)
    await db.commit()
    if row is None:
        return {"status": "not_found"}
    return _enrichment_dict(row)

"""Admin-only endpoints for the Phase 5 Data Crawler.

Provides endpoints covering:
- Dashboard overview (v1 legacy + v2 aggregated)
- Data source CRUD + seed defaults
- Crawl triggers (per-source, all-scheduled, single-URL)
- Crawl job listing and detail
- Review queue (list, stats, detail, approve, reject)
- Enrichment application
- Frontier management (retry, add-urls, delete)
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import Float, case, cast, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import settings
from unipaith.core.exceptions import NotFoundException
from unipaith.crawler.enrichment import EnrichmentPipeline
from unipaith.crawler.orchestrator import CrawlerOrchestrator
from unipaith.crawler.review_queue import ReviewQueue
from unipaith.crawler.source_registry import SourceRegistry
from unipaith.database import get_db
from unipaith.dependencies import require_admin
from unipaith.models.crawler import CrawlJob, ExtractedProgram
from unipaith.models.knowledge import CrawlFrontier, KnowledgeDocument
from unipaith.models.matching import DataSource
from unipaith.models.pipeline import PipelineStageSnapshot
from unipaith.models.user import User
from unipaith.schemas.crawler import (
    CrawlerDashboardResponse,
    CrawlJobListResponse,
    CrawlJobResponse,
    CrawlSingleURLRequest,
    CreateSourceRequest,
    ExtractedProgramDetailResponse,
    PipelineResultResponse,
    ReviewApproveRequest,
    ReviewListResponse,
    ReviewRejectRequest,
    ReviewStatsResponse,
    SourceListResponse,
    SourceResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/crawler", tags=["crawler-admin"])


# ======================================================================
# Dashboard v2 (aggregated)
# ======================================================================


class RetryRequest(BaseModel):
    frontier_ids: list[str]


class AddUrlsRequest(BaseModel):
    urls: list[str]


@router.get("/dashboard-v2")
async def dashboard_v2(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> dict[str, Any]:
    """Aggregated crawler dashboard data for the v2 UI."""

    snap = await db.get(PipelineStageSnapshot, "crawl")
    status = snap.status if snap else "off"
    last_activity_at = snap.last_activity_at.isoformat() if snap and snap.last_activity_at else None

    queue_rows = (
        await db.execute(select(CrawlFrontier.status, func.count()).group_by(CrawlFrontier.status))
    ).all()
    queue: dict[str, int] = {"pending": 0, "completed": 0, "failed": 0}
    total = 0
    for row_status, cnt in queue_rows:
        queue[row_status] = cnt
        total += cnt

    recent_result = await db.execute(
        select(
            CrawlFrontier.url,
            CrawlFrontier.domain,
            CrawlFrontier.status,
            CrawlFrontier.updated_at,
            CrawlFrontier.last_error,
        )
        .order_by(CrawlFrontier.updated_at.desc())
        .limit(30)
    )
    recent_activity = [
        {
            "url": r.url,
            "domain": r.domain,
            "status": r.status,
            "updated_at": r.updated_at.isoformat() if r.updated_at else None,
            "error": r.last_error,
        }
        for r in recent_result.all()
    ]

    now = datetime.now(UTC)
    since_24h = now - timedelta(hours=24)
    tp_result = await db.execute(
        select(
            func.date_trunc("hour", KnowledgeDocument.ingested_at).label("hour"),
            func.count().label("docs_crawled"),
            func.sum(
                case(
                    (KnowledgeDocument.processing_status == "failed", 1),
                    else_=0,
                )
            ).label("docs_failed"),
        )
        .where(KnowledgeDocument.ingested_at >= since_24h)
        .group_by("hour")
        .order_by("hour")
    )
    throughput_24h = [
        {
            "hour": r.hour.isoformat() if r.hour else None,
            "docs_crawled": r.docs_crawled,
            "docs_failed": int(r.docs_failed or 0),
        }
        for r in tp_result.all()
    ]

    domain_result = await db.execute(
        select(
            KnowledgeDocument.source_domain.label("domain"),
            func.count().label("doc_count"),
            func.sum(
                case(
                    (KnowledgeDocument.processing_status == "raw", 1),
                    else_=0,
                )
            ).label("pending"),
            func.sum(
                case(
                    (KnowledgeDocument.processing_status == "failed", 1),
                    else_=0,
                )
            ).label("failed"),
            func.avg(cast(KnowledgeDocument.quality_score, Float)).label("avg_quality"),
        )
        .where(KnowledgeDocument.source_domain.isnot(None))
        .group_by(KnowledgeDocument.source_domain)
        .order_by(func.count().desc())
        .limit(20)
    )
    domains = [
        {
            "domain": r.domain,
            "doc_count": r.doc_count,
            "pending": int(r.pending or 0),
            "failed": int(r.failed or 0),
            "avg_quality": round(float(r.avg_quality or 0), 2),
        }
        for r in domain_result.all()
    ]

    error_result = await db.execute(
        select(
            CrawlFrontier.id,
            CrawlFrontier.url,
            CrawlFrontier.domain,
            CrawlFrontier.last_error,
            CrawlFrontier.consecutive_failures,
            CrawlFrontier.last_crawled_at,
        )
        .where(CrawlFrontier.consecutive_failures > 0)
        .order_by(CrawlFrontier.consecutive_failures.desc())
        .limit(50)
    )
    errors = [
        {
            "id": str(r.id),
            "url": r.url,
            "domain": r.domain,
            "last_error": r.last_error,
            "consecutive_failures": r.consecutive_failures,
            "last_crawled_at": (r.last_crawled_at.isoformat() if r.last_crawled_at else None),
        }
        for r in error_result.all()
    ]

    disc_result = (
        await db.execute(
            select(CrawlFrontier.discovery_method, func.count())
            .where(CrawlFrontier.discovery_method.isnot(None))
            .group_by(CrawlFrontier.discovery_method)
        )
    ).all()
    discovery: dict[str, int] = {}
    for method, cnt in disc_result:
        discovery[method] = cnt

    seed_count = (
        await db.scalar(
            select(func.count())
            .select_from(CrawlFrontier)
            .where(
                CrawlFrontier.discovery_method.in_(["bootstrap_seed", "fallback_seed", "manual"])
            )
        )
        or 0
    )

    total_domains = await db.scalar(select(func.count(func.distinct(CrawlFrontier.domain)))) or 0

    return {
        "status": status,
        "rpm": settings.pipeline_crawl_rpm,
        "last_activity_at": last_activity_at,
        "queue": {**queue, "total": total},
        "recent_activity": recent_activity,
        "throughput_24h": throughput_24h,
        "domains": domains,
        "errors": errors,
        "discovery": discovery,
        "seed_urls_count": seed_count,
        "total_domains": total_domains,
    }


@router.post("/retry")
async def retry_frontier(
    body: RetryRequest,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> dict:
    """Reset failed frontier entries back to pending."""
    ids = [UUID(fid) for fid in body.frontier_ids]
    result = await db.execute(
        update(CrawlFrontier)
        .where(CrawlFrontier.id.in_(ids))
        .values(
            status="pending",
            consecutive_failures=0,
            last_error=None,
            next_crawl_after=None,
        )
    )
    await db.commit()
    return {"reset_count": result.rowcount}


@router.post("/add-urls")
async def add_urls(
    body: AddUrlsRequest,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> dict:
    """Add URLs to the crawl frontier manually."""
    from urllib.parse import urlparse

    added = 0
    for raw_url in body.urls:
        url = raw_url.strip()
        if not url:
            continue
        parsed = urlparse(url)
        domain = parsed.netloc or url
        existing = await db.scalar(
            select(func.count()).select_from(CrawlFrontier).where(CrawlFrontier.url == url)
        )
        if existing and existing > 0:
            continue
        db.add(
            CrawlFrontier(
                url=url,
                domain=domain,
                priority=60,
                discovery_method="manual",
            )
        )
        added += 1
    if added:
        await db.commit()
    return {"added": added, "skipped": len(body.urls) - added}


@router.delete("/frontier/{frontier_id}")
async def delete_frontier(
    frontier_id: UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> dict:
    """Remove a frontier entry."""
    result = await db.execute(delete(CrawlFrontier).where(CrawlFrontier.id == frontier_id))
    await db.commit()
    if result.rowcount == 0:
        raise NotFoundException("Frontier entry not found")
    return {"deleted": str(frontier_id)}


# ======================================================================
# Dashboard (legacy v1)
# ======================================================================


@router.get("/dashboard", response_model=CrawlerDashboardResponse)
async def dashboard(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Return an overview of the crawler system status."""
    # Active sources count
    src_count_q = await db.execute(
        select(func.count(DataSource.id)).where(DataSource.is_active.is_(True))
    )
    active_sources = src_count_q.scalar() or 0

    # Total jobs
    job_count_q = await db.execute(select(func.count(CrawlJob.id)))
    total_jobs = job_count_q.scalar() or 0

    # Recent jobs
    recent_q = await db.execute(select(CrawlJob).order_by(CrawlJob.created_at.desc()).limit(10))
    recent_jobs = [
        CrawlJobResponse.model_validate(j, from_attributes=True) for j in recent_q.scalars().all()
    ]

    # Review stats
    queue = ReviewQueue(db)
    pending = await queue.get_pending_count()
    stats_raw = await queue.get_review_stats()
    review_stats = ReviewStatsResponse(**stats_raw)

    # Sources
    registry = SourceRegistry(db)
    sources_raw = await registry.list_sources(active_only=True, limit=50)
    sources = [SourceResponse.model_validate(s, from_attributes=True) for s in sources_raw]

    return CrawlerDashboardResponse(
        active_sources=active_sources,
        total_jobs=total_jobs,
        recent_jobs=recent_jobs,
        pending_reviews=pending,
        review_stats=review_stats,
        sources=sources,
    )


# ======================================================================
# Sources
# ======================================================================


@router.post("/sources", response_model=SourceResponse, status_code=201)
async def create_source(
    body: CreateSourceRequest,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Register a new data source."""
    registry = SourceRegistry(db)
    source = await registry.create_source(
        name=body.name,
        url=body.url,
        source_type=body.source_type,
        category=body.category,
        frequency_hours=body.frequency_hours,
        url_patterns=[p.model_dump() for p in body.url_patterns] if body.url_patterns else None,
    )
    return source


@router.get("/sources", response_model=SourceListResponse)
async def list_sources(
    active_only: bool = Query(default=True),
    limit: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """List registered data sources."""
    registry = SourceRegistry(db)
    sources = await registry.list_sources(active_only=active_only, limit=limit)
    return SourceListResponse(sources=sources, total=len(sources))


@router.get("/sources/{source_id}", response_model=SourceResponse)
async def get_source(
    source_id: UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Get a single data source by ID."""
    registry = SourceRegistry(db)
    return await registry.get_source(source_id)


@router.delete("/sources/{source_id}")
async def delete_source(
    source_id: UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Soft-delete a data source."""
    registry = SourceRegistry(db)
    await registry.delete_source(source_id)
    return {"message": f"Source {source_id} deactivated"}


@router.post("/sources/seed-defaults", response_model=SourceListResponse)
async def seed_default_sources(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Seed default data sources for demonstration."""
    registry = SourceRegistry(db)
    sources = await registry.seed_default_sources()
    return SourceListResponse(sources=sources, total=len(sources))


# ======================================================================
# Crawl triggers
# ======================================================================


@router.post("/crawl/{source_id}", response_model=PipelineResultResponse)
async def crawl_source(
    source_id: UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Trigger the full pipeline for a specific data source."""
    orchestrator = CrawlerOrchestrator(db)
    result = await orchestrator.run_full_pipeline(source_id)
    return PipelineResultResponse(**result)


@router.post("/crawl-all")
async def crawl_all_scheduled(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Trigger crawls for all due scheduled sources."""
    orchestrator = CrawlerOrchestrator(db)
    return await orchestrator.run_scheduled_crawls()


@router.post("/crawl-url")
async def crawl_single_url(
    body: CrawlSingleURLRequest,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Crawl a single URL for testing."""
    orchestrator = CrawlerOrchestrator(db)
    return await orchestrator.crawl_single_url(body.url, body.source_id)


# ======================================================================
# Jobs
# ======================================================================


@router.get("/jobs", response_model=CrawlJobListResponse)
async def list_jobs(
    limit: int = Query(default=50, ge=1, le=200),
    source_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """List crawl jobs, optionally filtered by source."""
    stmt = select(CrawlJob).order_by(CrawlJob.created_at.desc()).limit(limit)
    if source_id:
        stmt = stmt.where(CrawlJob.source_id == source_id)
    result = await db.execute(stmt)
    jobs = list(result.scalars().all())
    return CrawlJobListResponse(jobs=jobs, total=len(jobs))


@router.get("/jobs/{job_id}", response_model=CrawlJobResponse)
async def get_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Get a single crawl job by ID."""
    job = await db.get(CrawlJob, job_id)
    if not job:
        raise NotFoundException("Crawl job not found")
    return job


# ======================================================================
# Review queue
# ======================================================================


@router.get("/review", response_model=ReviewListResponse)
async def list_reviews(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    source_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """List extracted programs awaiting review."""
    queue = ReviewQueue(db)
    items = await queue.list_pending(limit=limit, offset=offset, source_id=source_id)
    pending = await queue.get_pending_count()
    return ReviewListResponse(items=items, total=len(items), pending_count=pending)


@router.get("/review/stats", response_model=ReviewStatsResponse)
async def review_stats(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Return aggregate review statistics."""
    queue = ReviewQueue(db)
    stats = await queue.get_review_stats()
    return ReviewStatsResponse(**stats)


@router.get("/review/{extracted_id}", response_model=ExtractedProgramDetailResponse)
async def get_review_item(
    extracted_id: UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Get full details of an extracted program for review."""
    ep = await db.get(ExtractedProgram, extracted_id)
    if not ep:
        raise NotFoundException("Extracted program not found")
    return ep


@router.post("/review/{extracted_id}/approve")
async def approve_review(
    extracted_id: UUID,
    body: ReviewApproveRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Approve an extracted program, optionally with edits."""
    queue = ReviewQueue(db)
    return await queue.approve(
        extracted_id=extracted_id,
        reviewer_id=admin.id,
        edits=body.edits,
        notes=body.notes,
    )


@router.post("/review/{extracted_id}/reject")
async def reject_review(
    extracted_id: UUID,
    body: ReviewRejectRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Reject an extracted program."""
    queue = ReviewQueue(db)
    return await queue.reject(
        extracted_id=extracted_id,
        reviewer_id=admin.id,
        reason=body.reason,
    )


# ======================================================================
# Enrichment
# ======================================================================


@router.post("/enrichment/apply-all")
async def apply_all_enrichments(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Apply all pending enrichments to their target programs."""
    pipeline = EnrichmentPipeline(db)
    return await pipeline.apply_all_pending_enrichments()

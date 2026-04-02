"""Admin-only endpoints for the Phase 5 Data Crawler.

Provides 17 endpoints covering:
- Dashboard overview
- Data source CRUD + seed defaults
- Crawl triggers (per-source, all-scheduled, single-URL)
- Crawl job listing and detail
- Review queue (list, stats, detail, approve, reject)
- Enrichment application
"""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.core.exceptions import NotFoundException
from unipaith.crawler.enrichment import EnrichmentPipeline
from unipaith.crawler.orchestrator import CrawlerOrchestrator
from unipaith.crawler.review_queue import ReviewQueue
from unipaith.crawler.source_registry import SourceRegistry
from unipaith.database import get_db
from unipaith.dependencies import require_admin
from unipaith.models.crawler import CrawlJob, ExtractedProgram
from unipaith.models.matching import DataSource
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
# Dashboard
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

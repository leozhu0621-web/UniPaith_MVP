from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.dependencies import require_admin
from unipaith.models.application import Application
from unipaith.models.institution import Institution, Program
from unipaith.models.student import StudentProfile
from unipaith.models.user import User, UserRole
from unipaith.services.matching_service import MatchingService

router = APIRouter(prefix="/internal", tags=["internal"])


@router.get("/stats")
async def platform_stats(
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    students = (await db.execute(
        select(func.count()).select_from(User).where(User.role == UserRole.student)
    )).scalar_one()
    institutions = (await db.execute(
        select(func.count()).select_from(Institution)
    )).scalar_one()
    programs = (await db.execute(
        select(func.count()).select_from(Program).where(Program.is_published.is_(True))
    )).scalar_one()
    applications = (await db.execute(
        select(func.count()).select_from(Application)
    )).scalar_one()

    return {
        "total_students": students,
        "total_institutions": institutions,
        "published_programs": programs,
        "total_applications": applications,
    }


@router.get("/users")
async def list_users(
    role: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(User)
    if role:
        stmt = stmt.where(User.role == UserRole(role))

    total = (await db.execute(
        select(func.count()).select_from(stmt.subquery())
    )).scalar_one()

    results = await db.execute(
        stmt.offset((page - 1) * page_size).limit(page_size)
    )
    users = results.scalars().all()

    return {
        "items": [
            {
                "id": str(u.id),
                "email": u.email,
                "role": u.role.value,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.patch("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    import uuid as _uuid
    result = await db.execute(select(User).where(User.id == _uuid.UUID(user_id)))
    target = result.scalar_one_or_none()
    if not target:
        from unipaith.core.exceptions import NotFoundException
        raise NotFoundException("User not found")
    target.is_active = False
    await db.flush()
    return {"message": f"User {user_id} deactivated"}


@router.patch("/users/{user_id}/activate")
async def activate_user(
    user_id: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    import uuid as _uuid
    result = await db.execute(select(User).where(User.id == _uuid.UUID(user_id)))
    target = result.scalar_one_or_none()
    if not target:
        from unipaith.core.exceptions import NotFoundException
        raise NotFoundException("User not found")
    target.is_active = True
    await db.flush()
    return {"message": f"User {user_id} activated"}


@router.patch("/institutions/{institution_id}/verify")
async def verify_institution(
    institution_id: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    import uuid as _uuid
    result = await db.execute(
        select(Institution).where(Institution.id == _uuid.UUID(institution_id))
    )
    inst = result.scalar_one_or_none()
    if not inst:
        from unipaith.core.exceptions import NotFoundException
        raise NotFoundException("Institution not found")
    inst.is_verified = True
    await db.flush()
    return {"message": f"Institution {inst.name} verified"}


# --- AI Admin ---


@router.post("/ai/bootstrap-programs")
async def bootstrap_program_features(
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Extract features + generate embeddings for all published programs."""
    svc = MatchingService(db)
    return await svc.bootstrap_all_programs()


@router.post("/ai/refresh-student/{student_id}")
async def refresh_student_features(
    student_id: UUID,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger feature re-extraction for a student."""
    svc = MatchingService(db)
    features = await svc.refresh_student_features(student_id)
    return {"student_id": str(student_id), "features": features}


@router.post("/ai/refresh-program/{program_id}")
async def refresh_program_features(
    program_id: UUID,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger feature re-extraction for a program."""
    svc = MatchingService(db)
    features = await svc.refresh_program_features(program_id)
    return {"program_id": str(program_id), "features": features}


# --- GPU / AI Cost Monitoring ---


@router.post("/ai/bootstrap")
async def trigger_bootstrap(
    user: User = Depends(require_admin),
):
    """Trigger the full AI bootstrap pipeline in the background.

    Returns immediately. Monitor progress via GET /ai/bootstrap-status.
    """
    import asyncio

    from unipaith.config import settings as s

    if s.gpu_mode == "mock" or s.ai_mock_mode:
        from unipaith.core.exceptions import BadRequestException
        raise BadRequestException(
            "Cannot bootstrap in mock mode. Set GPU_MODE=aws or GPU_MODE=local."
        )

    # Run in background — don't block the HTTP response
    asyncio.create_task(_run_bootstrap_background())

    return {"status": "started", "message": "Crawl started. Watch progress on this page — it refreshes automatically."}


async def _run_bootstrap_background():
    """Background task: crawl all sources, extract features, generate embeddings."""
    import logging
    logger = logging.getLogger("unipaith.bootstrap")

    from unipaith.database import async_session

    try:
        async with async_session() as db:
            from unipaith.crawler.orchestrator import CrawlerOrchestrator
            orch = CrawlerOrchestrator(db)
            logger.info("Bootstrap: starting scheduled crawls")
            results = await orch.run_scheduled_crawls()
            await db.commit()

            total_pages = sum(r.get("pages_crawled", 0) for r in results.get("results", []))
            total_extracted = sum(r.get("items_extracted", 0) for r in results.get("results", []))
            logger.info(
                "Bootstrap crawl done: %d sources, %d pages, %d extracted",
                results.get("sources_processed", 0), total_pages, total_extracted,
            )

        # Phase 2: features + embeddings for all programs
        async with async_session() as db:
            from unipaith.ai.embedding_pipeline import EmbeddingPipeline
            from unipaith.ai.feature_extraction import FeatureExtractor
            from unipaith.models.institution import Program

            result = await db.execute(select(Program.id))
            program_ids = [row[0] for row in result.all()]

            if program_ids:
                extractor = FeatureExtractor(db)
                pipeline = EmbeddingPipeline(db)
                for pid in program_ids:
                    try:
                        await extractor.extract_program_features(pid)
                        await pipeline.generate_program_embedding(pid)
                    except Exception as exc:
                        logger.warning("AI pipeline failed for %s: %s", pid, exc)
                await db.commit()

            logger.info("Bootstrap complete: %d programs processed", len(program_ids))
    except Exception:
        logger.exception("Bootstrap failed")


@router.get("/ai/bootstrap-status")
async def bootstrap_status(
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Current state of the AI engine's knowledge."""
    from unipaith.models.crawler import CrawlJob, ExtractedProgram
    from unipaith.models.matching import DataSource, Embedding, InstitutionFeature

    sources = (await db.execute(
        select(func.count()).select_from(DataSource).where(DataSource.is_active.is_(True))
    )).scalar_one()
    crawl_jobs = (await db.execute(
        select(func.count()).select_from(CrawlJob)
    )).scalar_one()
    extracted = (await db.execute(
        select(func.count()).select_from(ExtractedProgram)
    )).scalar_one()
    programs = (await db.execute(
        select(func.count()).select_from(Program)
    )).scalar_one()
    features = (await db.execute(
        select(func.count()).select_from(InstitutionFeature)
    )).scalar_one()
    embeddings = (await db.execute(
        select(func.count()).select_from(Embedding)
    )).scalar_one()

    return {
        "active_sources": sources,
        "crawl_jobs_run": crawl_jobs,
        "programs_extracted": extracted,
        "programs_in_db": programs,
        "features_generated": features,
        "embeddings_generated": embeddings,
        "engine_ready": embeddings > 0,
    }


@router.get("/crawl-jobs")
async def list_crawl_jobs(
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Recent crawl jobs with source names."""
    from unipaith.models.crawler import CrawlJob
    from unipaith.models.matching import DataSource

    stmt = (
        select(
            CrawlJob.id,
            CrawlJob.status,
            CrawlJob.pages_crawled,
            CrawlJob.pages_failed,
            CrawlJob.items_extracted,
            CrawlJob.items_ingested,
            CrawlJob.items_duplicate,
            CrawlJob.created_at,
            CrawlJob.completed_at,
            DataSource.source_name,
        )
        .join(DataSource, DataSource.id == CrawlJob.source_id)
        .order_by(CrawlJob.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.all()

    return {
        "items": [
            {
                "id": str(r[0]),
                "status": r[1],
                "pages_crawled": r[2],
                "pages_failed": r[3],
                "items_extracted": r[4],
                "items_ingested": r[5],
                "items_duplicate": r[6],
                "created_at": r[7].isoformat() if r[7] else None,
                "completed_at": r[8].isoformat() if r[8] else None,
                "source_name": r[9],
            }
            for r in rows
        ],
        "total": len(rows),
    }


@router.get("/extracted-programs")
async def list_extracted_programs(
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Recently extracted programs."""
    from unipaith.models.crawler import ExtractedProgram

    stmt = (
        select(ExtractedProgram)
        .order_by(ExtractedProgram.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    programs = result.scalars().all()

    return {
        "items": [
            {
                "id": str(p.id),
                "institution_name": p.institution_name,
                "program_name": p.program_name,
                "degree_type": p.degree_type,
                "department": p.department,
                "confidence": float(p.extraction_confidence) if p.extraction_confidence else None,
                "review_status": p.review_status,
                "match_type": p.match_type,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in programs
        ],
        "total": len(programs),
    }


@router.get("/ai-costs")
async def ai_costs(user: User = Depends(require_admin)):
    """GPU usage and cost tracking for the AI engine."""
    from unipaith.ai.cost_tracker import get_cost_tracker
    return get_cost_tracker().get_usage_summary()


@router.get("/ai-status")
async def ai_status(user: User = Depends(require_admin)):
    """Current status of all AI engine components."""
    from unipaith.config import settings as s

    status = {
        "gpu_mode": s.gpu_mode,
        "8b_instance": {"configured": bool(s.gpu_8b_instance_id)},
        "70b_instance": {"configured": bool(s.gpu_70b_instance_id)},
    }

    if s.gpu_mode == "aws":
        from unipaith.ai.gpu_manager import get_8b_manager, get_70b_manager
        m8b = get_8b_manager()
        m70b = get_70b_manager()
        status["8b_instance"]["state"] = m8b.get_instance_state()
        status["70b_instance"]["state"] = m70b.get_instance_state()
        idle = m70b.idle_seconds
        status["70b_instance"]["idle_seconds"] = round(idle, 1) if idle else None

    return status

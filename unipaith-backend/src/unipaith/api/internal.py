from __future__ import annotations

import asyncio
from datetime import UTC
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.core.ai_runtime_metrics import slo_snapshot
from unipaith.database import get_db
from unipaith.dependencies import require_admin
from unipaith.models.institution import Institution, Program
from unipaith.models.user import User
from unipaith.services.ai_control_plane_service import AIControlPlaneService
from unipaith.services.ai_engine_orchestrator import AIEngineOrchestrator
from unipaith.services.internal_admin_service import InternalAdminService
from unipaith.services.matching_service import MatchingService

router = APIRouter(prefix="/internal", tags=["internal"])


class AIControlPolicyPatchRequest(BaseModel):
    autonomy_enabled: bool | None = None
    auto_fix_enabled: bool | None = None
    emergency_stop: bool | None = None


class ActionReasonRequest(BaseModel):
    reason: str | None = None


class BulkUsersActiveRequest(BaseModel):
    user_ids: list[UUID]
    active: bool
    reason: str | None = None


class BulkInstitutionsVerifyRequest(BaseModel):
    institution_ids: list[UUID]
    reason: str | None = None


class DatabaseActionRequest(BaseModel):
    scope: str = "all"
    dry_run: bool = True
    reason: str | None = None


@router.get("/stats")
async def platform_stats(
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await InternalAdminService(db).get_platform_stats()


@router.get("/users")
async def list_users(
    role: str | None = Query(None),
    q: str | None = Query(None),
    is_active: bool | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await InternalAdminService(db).list_users(
        role=role,
        q=q,
        is_active=is_active,
        page=page,
        page_size=page_size,
    )
    return {
        "items": result.items,
        "total": result.total,
        "page": result.page,
        "page_size": result.page_size,
    }


@router.patch("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: UUID,
    payload: ActionReasonRequest | None = None,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    target = await InternalAdminService(db).set_user_active(
        user_id=user_id,
        active=False,
        actor_user_id=admin.id,
        reason=payload.reason if payload else None,
    )
    return {"message": f"User {target.id} deactivated"}


@router.patch("/users/{user_id}/activate")
async def activate_user(
    user_id: UUID,
    payload: ActionReasonRequest | None = None,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    target = await InternalAdminService(db).set_user_active(
        user_id=user_id,
        active=True,
        actor_user_id=admin.id,
        reason=payload.reason if payload else None,
    )
    return {"message": f"User {target.id} activated"}


@router.patch("/institutions/{institution_id}/verify")
async def verify_institution(
    institution_id: UUID,
    payload: ActionReasonRequest | None = None,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    inst = await InternalAdminService(db).verify_institution(
        institution_id=institution_id,
        actor_user_id=admin.id,
        reason=payload.reason if payload else None,
    )
    return {"message": f"Institution {inst.name} verified"}


@router.post("/users/bulk-active")
async def bulk_set_users_active(
    payload: BulkUsersActiveRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await InternalAdminService(db).bulk_set_users_active(
        user_ids=payload.user_ids,
        active=payload.active,
        actor_user_id=admin.id,
        reason=payload.reason,
    )


@router.post("/institutions/bulk-verify")
async def bulk_verify_institutions(
    payload: BulkInstitutionsVerifyRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await InternalAdminService(db).bulk_verify_institutions(
        institution_ids=payload.institution_ids,
        actor_user_id=admin.id,
        reason=payload.reason,
    )


@router.get("/audit/admin-actions")
async def list_admin_audit_actions(
    limit: int = Query(50, ge=1, le=500),
    entity_type: str | None = Query(None),
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    items = await InternalAdminService(db).list_admin_audit_events(
        limit=limit,
        entity_type=entity_type,
    )
    return {"items": items}


@router.get("/database/health")
async def database_health(
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await InternalAdminService(db).get_database_health()


@router.get("/database/quality")
async def database_quality(
    scope: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await InternalAdminService(db).get_database_quality(scope=scope, limit=limit)


@router.get("/database/recommendations")
async def database_recommendations(
    limit: int = Query(10, ge=1, le=50),
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await InternalAdminService(db).get_database_recommendations(limit=limit)


@router.get("/database/jobs")
async def database_jobs(
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await InternalAdminService(db).get_database_jobs(limit=limit)


@router.post("/database/actions/dedupe")
async def database_action_dedupe(
    payload: DatabaseActionRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await InternalAdminService(db).run_database_dedupe_action(
        scope=payload.scope,
        dry_run=payload.dry_run,
        reason=payload.reason,
        actor_user_id=admin.id,
    )


@router.post("/database/actions/repair")
async def database_action_repair(
    payload: DatabaseActionRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await InternalAdminService(db).run_database_repair_action(
        scope=payload.scope,
        dry_run=payload.dry_run,
        reason=payload.reason,
        actor_user_id=admin.id,
    )


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
    from unipaith.config import settings as s

    if s.gpu_mode == "mock" or s.ai_mock_mode:
        from unipaith.core.exceptions import BadRequestException

        raise BadRequestException(
            "Cannot bootstrap in mock mode. Set GPU_MODE=aws or GPU_MODE=local."
        )

    # Run in background — don't block the HTTP response
    asyncio.create_task(_run_bootstrap_background())

    return {
        "status": "started",
        "message": ("Crawl started. Watch progress on this page — it refreshes automatically."),
    }


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
                results.get("sources_processed", 0),
                total_pages,
                total_extracted,
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
                sem = asyncio.Semaphore(5)

                async def process_program(pid):
                    async with sem:
                        try:
                            await extractor.extract_program_features(pid)
                            await pipeline.generate_program_embedding(pid)
                        except Exception as exc:
                            logger.warning("AI pipeline failed for %s: %s", pid, exc)

                await asyncio.gather(*(process_program(pid) for pid in program_ids))
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

    sources = (
        await db.execute(
            select(func.count()).select_from(DataSource).where(DataSource.is_active.is_(True))
        )
    ).scalar_one()
    crawl_jobs = (await db.execute(select(func.count()).select_from(CrawlJob))).scalar_one()
    extracted = (await db.execute(select(func.count()).select_from(ExtractedProgram))).scalar_one()
    programs = (await db.execute(select(func.count()).select_from(Program))).scalar_one()
    features = (await db.execute(select(func.count()).select_from(InstitutionFeature))).scalar_one()
    embeddings = (await db.execute(select(func.count()).select_from(Embedding))).scalar_one()

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

    stmt = select(ExtractedProgram).order_by(ExtractedProgram.created_at.desc()).limit(limit)
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


@router.get("/ai/control/status")
async def ai_control_status(
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Unified AI control-plane status for admin UI."""
    return await AIControlPlaneService(db).get_status()


@router.patch("/ai/control/policy")
async def ai_control_policy(
    body: AIControlPolicyPatchRequest,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update runtime autonomy policy toggles."""
    policy = await AIControlPlaneService(db).update_policy(
        autonomy_enabled=body.autonomy_enabled,
        auto_fix_enabled=body.auto_fix_enabled,
        emergency_stop=body.emergency_stop,
    )
    return {"policy": policy}


@router.post("/ai/control/run-loop")
async def ai_control_run_loop(
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Run a single autonomous self-driving tick immediately."""
    result = await AIControlPlaneService(db).run_self_driving_tick(trigger="manual")
    return {"result": result}


@router.get("/ai/control/audit")
async def ai_control_audit(
    limit: int = Query(100, ge=1, le=500),
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List recent autonomous loop audit events."""
    return {"items": await AIControlPlaneService(db).list_audit_events(limit=limit)}


@router.get("/ai/control/slo")
async def ai_control_slo(
    user: User = Depends(require_admin),
):
    """Current SLO-oriented runtime metrics."""
    return slo_snapshot()


@router.get("/ai/ops/snapshot")
async def ai_ops_snapshot(
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Consolidated AI operations payload for the unified admin control center."""
    return await AIControlPlaneService(db).get_ops_snapshot()


@router.post("/ai/engine/run")
async def ai_engine_run(
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Run the full ingest->feature/embedding->ML orchestration graph."""
    return await AIEngineOrchestrator(db).run_full_graph(trigger="manual")


@router.get("/ai/engine/state")
async def ai_engine_state(
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Read runtime state of the unified engine orchestrator."""
    return AIEngineOrchestrator(db).get_runtime_state()


@router.get("/health")
async def engine_health(
    db: AsyncSession = Depends(get_db),
):
    """Deep health check — used by the watchdog. No auth required for monitoring."""
    import time
    from datetime import datetime, timedelta

    from unipaith.models.crawler import CrawlJob, ExtractedProgram
    from unipaith.models.matching import DataSource

    checks: dict = {}
    overall = "healthy"

    # 1. Database connectivity
    try:
        t0 = time.monotonic()
        await db.execute(select(func.count()).select_from(DataSource))
        db_ms = round((time.monotonic() - t0) * 1000, 1)
        checks["database"] = {"status": "ok", "latency_ms": db_ms}
        if db_ms > 5000:
            checks["database"]["status"] = "slow"
            overall = "degraded"
    except Exception as exc:
        checks["database"] = {"status": "error", "error": str(exc)}
        overall = "critical"

    # 2. Crawl activity
    try:
        one_hour_ago = datetime.now(UTC) - timedelta(hours=1)
        recent_jobs = (
            await db.execute(
                select(func.count())
                .select_from(CrawlJob)
                .where(CrawlJob.created_at >= one_hour_ago)
            )
        ).scalar_one()
        recent_errors = (
            await db.execute(
                select(func.count())
                .select_from(CrawlJob)
                .where(
                    CrawlJob.status == "failed",
                    CrawlJob.created_at >= one_hour_ago,
                )
            )
        ).scalar_one()
        total_extracted = (
            await db.execute(select(func.count()).select_from(ExtractedProgram))
        ).scalar_one()
        total_jobs = (await db.execute(select(func.count()).select_from(CrawlJob))).scalar_one()
        checks["crawl"] = {
            "status": "ok",
            "recent_jobs_1h": recent_jobs,
            "recent_errors_1h": recent_errors,
            "total_jobs": total_jobs,
            "total_programs_extracted": total_extracted,
        }
        if recent_errors > 5:
            checks["crawl"]["status"] = "warning"
            if overall == "healthy":
                overall = "degraded"
    except Exception as exc:
        checks["crawl"] = {"status": "error", "error": str(exc)}
        overall = "critical"

    # 3. OpenAI API reachability
    try:
        from unipaith.config import settings as s

        has_key = bool(s.openai_api_key and len(s.openai_api_key) > 10)
        checks["openai"] = {
            "status": "ok" if has_key else "error",
            "api_key_configured": has_key,
            "model": s.llm_feature_model,
        }
        if not has_key:
            overall = "critical"
    except Exception as exc:
        checks["openai"] = {"status": "error", "error": str(exc)}

    # 4. Service uptime
    import os

    pid = os.getpid()
    try:
        import pathlib

        stat_path = pathlib.Path(f"/proc/{pid}/stat")
        if stat_path.exists():
            boot_time = float(stat_path.read_text().split(")")[1].split()[19])
            clk_tck = os.sysconf("SC_CLK_TCK")
            with open("/proc/uptime") as f:
                sys_uptime = float(f.read().split()[0])
            proc_start = sys_uptime - (boot_time / clk_tck)
            checks["uptime_seconds"] = round(sys_uptime - proc_start, 0) if proc_start > 0 else None
    except Exception:
        pass

    return {
        "status": overall,
        "timestamp": datetime.now(UTC).isoformat(),
        "checks": checks,
    }


# --- Bulk Seed ---


class SeedProgramItem(BaseModel):
    program_name: str
    degree_type: str = "bachelors"
    department: str | None = None


class SeedInstitutionRequest(BaseModel):
    name: str
    type: str = "university"
    country: str = "United States"
    region: str | None = None
    city: str | None = None
    website_url: str | None = None
    contact_email: str | None = None
    description_text: str | None = None
    logo_url: str | None = None
    media_gallery: list[str] | None = None
    ranking_data: dict | None = None
    programs: list[SeedProgramItem] = []


class SeedBatchRequest(BaseModel):
    institutions: list[SeedInstitutionRequest]


@router.post("/seed-institutions")
async def seed_institutions(
    body: SeedBatchRequest,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin-only: bulk create institutions + programs from seed data."""
    from unipaith.models.user import UserRole

    created = 0
    skipped = 0
    total_programs = 0

    for inst_data in body.institutions:
        # Check if already exists
        existing = await db.execute(
            select(Institution).where(Institution.name == inst_data.name)
        )
        if existing.scalar_one_or_none():
            skipped += 1
            continue

        # Create system user
        import uuid as _uuid

        system_user = User(
            email=f"system+{_uuid.uuid4().hex[:8]}@unipaith.co",
            role=UserRole.institution_admin,
            cognito_sub=f"system-{_uuid.uuid4().hex}",
        )
        db.add(system_user)
        await db.flush()

        institution = Institution(
            admin_user_id=system_user.id,
            name=inst_data.name,
            type=inst_data.type,
            country=inst_data.country,
            region=inst_data.region,
            city=inst_data.city,
            website_url=inst_data.website_url,
            contact_email=inst_data.contact_email,
            description_text=inst_data.description_text,
            logo_url=inst_data.logo_url,
            media_gallery=inst_data.media_gallery,
            ranking_data=inst_data.ranking_data,
            claimed_from_source="public_catalog",
            is_verified=False,
        )
        db.add(institution)
        await db.flush()

        # Create programs
        seen: set[str] = set()
        for prog in inst_data.programs:
            key = f"{prog.program_name}|{prog.department or ''}"
            if key in seen:
                continue
            seen.add(key)
            program = Program(
                institution_id=institution.id,
                program_name=prog.program_name,
                degree_type=prog.degree_type,
                department=prog.department,
                is_published=True,
            )
            db.add(program)
            total_programs += 1

        created += 1

    await db.commit()
    return {
        "created": created,
        "skipped": skipped,
        "total_programs": total_programs,
    }


class EnrichInstitutionRequest(BaseModel):
    name: str
    student_body_size: int | None = None
    ranking_data: dict | None = None
    description_text: str | None = None
    campus_description: str | None = None
    campus_setting: str | None = None
    logo_url: str | None = None
    media_gallery: list[str] | None = None
    website_url: str | None = None
    contact_email: str | None = None
    # Institution-profile JSONB dicts — previously ignored by the enrich
    # pipeline, leaving NYU permanently null on these fields despite the
    # data existing on the model.
    social_links: dict | None = None
    inquiry_routing: dict | None = None
    support_services: dict | None = None
    policies: dict | None = None
    international_info: dict | None = None
    school_outcomes: dict | None = None


class EnrichProgramRequest(BaseModel):
    program_name: str
    institution_name: str
    department: str | None = None
    tuition: int | None = None
    duration_months: int | None = None
    description_text: str | None = None
    acceptance_rate: float | None = None
    delivery_format: str | None = None
    application_deadline: str | None = None
    highlights: list[str] | None = None
    media_urls: list[str] | None = None
    outcomes_data: dict | None = None
    application_requirements: list[dict] | None = None
    # Extended program detail fields populated from scraped/structured sources
    cost_data: dict | None = None
    intake_rounds: dict | None = None
    tracks: dict | None = None
    requirements: dict | None = None
    faculty_contacts: dict | None = None
    clear_fields: list[str] | None = None


class EnrichBatchRequest(BaseModel):
    institutions: list[EnrichInstitutionRequest] | None = None
    programs: list[EnrichProgramRequest] | None = None


@router.post("/enrich")
async def enrich_data(
    body: EnrichBatchRequest,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin-only: enrich existing institutions/programs with additional data."""
    updated_inst = 0
    updated_prog = 0

    if body.institutions:
        for inst_data in body.institutions:
            result = await db.execute(
                select(Institution).where(
                    Institution.name == inst_data.name,
                )
            )
            inst = result.scalar_one_or_none()
            if not inst:
                continue
            for field, value in inst_data.model_dump(
                exclude_unset=True, exclude={"name"},
            ).items():
                if value is not None:
                    setattr(inst, field, value)
            updated_inst += 1

    if body.programs:
        for prog_data in body.programs:
            # Find institution
            inst_r = await db.execute(
                select(Institution).where(
                    Institution.name == prog_data.institution_name,
                )
            )
            inst = inst_r.scalar_one_or_none()
            if not inst:
                continue
            # Build query — optionally filter by department to target specific program
            prog_stmt = select(Program).where(
                Program.institution_id == inst.id,
                Program.program_name == prog_data.program_name,
            )
            if prog_data.department:
                prog_stmt = prog_stmt.where(
                    Program.department == prog_data.department
                )
            # Use scalars().all() to handle duplicate names (e.g. CS in CAS + Tandon)
            prog_r = await db.execute(prog_stmt)
            matching_progs = prog_r.scalars().all()
            if not matching_progs:
                continue
            for prog in matching_progs:
                # Explicitly NULL out clear_fields
                if prog_data.clear_fields:
                    for cf in prog_data.clear_fields:
                        if hasattr(prog, cf):
                            setattr(prog, cf, None)
                # Set non-null values (skip 0 and "" as they mean "no data")
                for field, value in prog_data.model_dump(
                    exclude_unset=True,
                    exclude={"program_name", "institution_name", "department", "clear_fields"},
                ).items():
                    if value is not None:
                        setattr(prog, field, value)
                updated_prog += 1

    await db.commit()
    return {
        "updated_institutions": updated_inst,
        "updated_programs": updated_prog,
    }


# --- Seed Program Reviews & Employer Feedback (curated external sources) ---


class ProgramReviewSeed(BaseModel):
    rating_teaching: int | None = None
    rating_workload: int | None = None
    rating_career_support: int | None = None
    rating_internship_access: int | None = None
    rating_community_culture: int | None = None
    rating_roi: int | None = None
    rating_overall: int | None = None
    review_text: str | None = None
    who_thrives_here: str | None = None
    reviewer_context: dict | None = None
    external_source: dict
    is_verified: bool = True
    is_published: bool = True


class SeedProgramReviewsRequest(BaseModel):
    institution_name: str
    program_name: str
    department: str | None = None
    entries: list[ProgramReviewSeed]
    # When True, delete all external-sourced reviews for matching programs
    # before inserting. Use to re-seed after the source list changes so the
    # DB state matches the script exactly (no stale entries left behind).
    # First-party reviews (student_id set, external_source null) are never
    # touched.
    replace: bool = False


@router.post("/seed-program-reviews")
async def seed_program_reviews(
    body: SeedProgramReviewsRequest,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin-only: insert reviews sourced from authoritative external
    publishers (NYU Stories, Niche, bulletin). Idempotent on
    ``external_source.source_url`` - re-runs update rather than duplicate.
    Pass ``replace=True`` to first wipe external-sourced reviews for the
    program and re-seed from scratch."""
    from sqlalchemy import delete

    from unipaith.models.institution import StudentProgramReview

    inst_r = await db.execute(
        select(Institution).where(Institution.name == body.institution_name)
    )
    inst = inst_r.scalar_one_or_none()
    if not inst:
        return {"inserted": 0, "updated": 0, "deleted": 0, "skipped": "institution_not_found"}

    prog_stmt = select(Program).where(
        Program.institution_id == inst.id,
        Program.program_name == body.program_name,
    )
    if body.department:
        prog_stmt = prog_stmt.where(Program.department == body.department)
    prog_r = await db.execute(prog_stmt)
    programs = prog_r.scalars().all()
    if not programs:
        return {"inserted": 0, "updated": 0, "deleted": 0, "skipped": "program_not_found"}

    inserted = 0
    updated = 0
    deleted = 0
    for prog in programs:
        if body.replace:
            del_stmt = delete(StudentProgramReview).where(
                StudentProgramReview.program_id == prog.id,
                StudentProgramReview.external_source.isnot(None),
            )
            del_result = await db.execute(del_stmt)
            deleted += del_result.rowcount or 0

        for entry in body.entries:
            source_url = (entry.external_source or {}).get("source_url")
            existing = None
            if source_url and not body.replace:
                # Match on program_id + source_url for idempotency.
                ex_stmt = select(StudentProgramReview).where(
                    StudentProgramReview.program_id == prog.id,
                    StudentProgramReview.external_source[
                        "source_url"
                    ].astext == source_url,
                )
                ex_r = await db.execute(ex_stmt)
                existing = ex_r.scalars().first()

            if existing is not None:
                for field, value in entry.model_dump(exclude_unset=True).items():
                    setattr(existing, field, value)
                updated += 1
            else:
                row = StudentProgramReview(
                    program_id=prog.id,
                    student_id=None,
                    **entry.model_dump(exclude_unset=True),
                )
                db.add(row)
                inserted += 1

    await db.commit()
    return {"inserted": inserted, "updated": updated, "deleted": deleted}


class EmployerFeedbackSeed(BaseModel):
    employer_name: str
    industry: str | None = None
    rating_technical: int | None = None
    rating_practical: int | None = None
    rating_communication: int | None = None
    rating_teamwork: int | None = None
    rating_reliability: int | None = None
    rating_overall: int | None = None
    job_readiness_sentiment: str | None = None
    feedback_text: str | None = None
    hiring_pattern: str | None = None
    feedback_year: int | None = None
    is_published: bool = True


class SeedEmployerFeedbackRequest(BaseModel):
    institution_name: str
    program_name: str
    department: str | None = None
    entries: list[EmployerFeedbackSeed]
    # When True, delete all existing employer feedback for matching programs
    # before inserting. Use to re-seed cleanly when the source list changes.
    replace: bool = False


@router.post("/seed-employer-feedback")
async def seed_employer_feedback(
    body: SeedEmployerFeedbackRequest,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin-only: insert employer feedback sourced from institution-published
    outcome reports (e.g., NYU Stern Undergraduate Outcomes). Idempotent on
    ``(employer_name, feedback_year)`` - re-runs update rather than duplicate.
    Pass ``replace=True`` to wipe and reseed."""
    from sqlalchemy import delete

    from unipaith.models.institution import EmployerFeedback

    inst_r = await db.execute(
        select(Institution).where(Institution.name == body.institution_name)
    )
    inst = inst_r.scalar_one_or_none()
    if not inst:
        return {"inserted": 0, "updated": 0, "deleted": 0, "skipped": "institution_not_found"}

    prog_stmt = select(Program).where(
        Program.institution_id == inst.id,
        Program.program_name == body.program_name,
    )
    if body.department:
        prog_stmt = prog_stmt.where(Program.department == body.department)
    prog_r = await db.execute(prog_stmt)
    programs = prog_r.scalars().all()
    if not programs:
        return {"inserted": 0, "updated": 0, "deleted": 0, "skipped": "program_not_found"}

    inserted = 0
    updated = 0
    deleted = 0
    for prog in programs:
        if body.replace:
            del_stmt = delete(EmployerFeedback).where(
                EmployerFeedback.program_id == prog.id,
            )
            del_result = await db.execute(del_stmt)
            deleted += del_result.rowcount or 0

        for entry in body.entries:
            existing = None
            if not body.replace:
                ex_stmt = select(EmployerFeedback).where(
                    EmployerFeedback.program_id == prog.id,
                    EmployerFeedback.employer_name == entry.employer_name,
                    EmployerFeedback.feedback_year.is_(entry.feedback_year)
                    if entry.feedback_year is None
                    else EmployerFeedback.feedback_year == entry.feedback_year,
                )
                ex_r = await db.execute(ex_stmt)
                existing = ex_r.scalars().first()

            if existing is not None:
                for field, value in entry.model_dump(exclude_unset=True).items():
                    setattr(existing, field, value)
                updated += 1
            else:
                row = EmployerFeedback(
                    program_id=prog.id,
                    **entry.model_dump(exclude_unset=True),
                )
                db.add(row)
                inserted += 1

    await db.commit()
    return {"inserted": inserted, "updated": updated, "deleted": deleted}


# --- Bulk-add Programs (no full institution seed; just inserts new program rows) ---


class BulkProgramSeed(BaseModel):
    program_name: str
    degree_type: str  # bachelors / masters / phd / certificate / diploma
    department: str | None = None
    description_text: str | None = None
    is_published: bool = True
    # Free-form JSONB fields admin can pre-populate via the bulk path.
    tracks: list | dict | None = None
    highlights: list[str] | None = None
    application_requirements: list | dict | None = None
    intake_rounds: list | dict | None = None
    cost_data: dict | None = None
    outcomes_data: dict | None = None
    media_urls: list[str] | None = None


class BulkAddProgramsRequest(BaseModel):
    institution_name: str
    programs: list[BulkProgramSeed]


@router.post("/bulk-add-programs")
async def bulk_add_programs(
    body: BulkAddProgramsRequest,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin-only: bulk-insert program rows for an institution. Idempotent on
    ``(institution_id, program_name, department)`` - re-runs skip duplicates
    rather than insert. Use to scale an institution's catalog past the
    initial seed (e.g., add all NYU graduate + PhD + certificate programs)."""
    inst_r = await db.execute(
        select(Institution).where(Institution.name == body.institution_name)
    )
    inst = inst_r.scalar_one_or_none()
    if not inst:
        return {"inserted": 0, "skipped_existing": 0, "skipped_reason": "institution_not_found"}

    inserted = 0
    skipped = 0
    for entry in body.programs:
        # Dedup by (program_name, department) within this institution.
        existing_stmt = select(Program).where(
            Program.institution_id == inst.id,
            Program.program_name == entry.program_name,
        )
        if entry.department:
            existing_stmt = existing_stmt.where(Program.department == entry.department)
        ex = (await db.execute(existing_stmt)).scalars().first()
        if ex is not None:
            skipped += 1
            continue
        row = Program(
            institution_id=inst.id,
            **entry.model_dump(exclude_unset=True, exclude_defaults=False),
        )
        db.add(row)
        inserted += 1

    await db.commit()
    return {"inserted": inserted, "skipped_existing": skipped}


# --- One-shot DDL repair (divergent-revision safety net) ---
#
# The duplicate m3n4o5p6q7r8 revision in alembic means the entrypoint script
# stamps head rather than upgrading, so new columns defined after that
# revision don't land. This endpoint idempotently applies the DDL for the
# review/employer rating-dimension columns from migration 4c9d6e1a8b3f. It
# is safe to call repeatedly; ``ADD COLUMN IF NOT EXISTS`` is a no-op when
# the column already exists.


@router.post("/ensure-review-employer-dims")
async def ensure_review_employer_dims(
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import text

    statements = [
        "ALTER TABLE student_program_reviews "
        "ADD COLUMN IF NOT EXISTS rating_internship_access INTEGER",
        "ALTER TABLE student_program_reviews "
        "ADD COLUMN IF NOT EXISTS rating_community_culture INTEGER",
        "ALTER TABLE employer_feedback "
        "ADD COLUMN IF NOT EXISTS rating_teamwork INTEGER",
        "ALTER TABLE employer_feedback "
        "ADD COLUMN IF NOT EXISTS rating_reliability INTEGER",
    ]
    applied = []
    for stmt in statements:
        await db.execute(text(stmt))
        applied.append(stmt)
    await db.commit()
    return {"applied": applied, "count": len(applied)}


# --- Image Download & Upload to S3 ---


class DownloadImageRequest(BaseModel):
    urls: list[str]
    prefix: str = "catalog"


@router.post("/download-images")
async def download_and_upload_images(
    body: DownloadImageRequest,
    user: User = Depends(require_admin),
):
    """Download external images, upload to our S3, return permanent URLs."""
    import httpx

    from unipaith.config import settings
    from unipaith.core.s3 import S3Client

    s3 = S3Client()
    results = []

    async with httpx.AsyncClient(
        headers={"User-Agent": "UniPaith-Bot/1.0"},
        follow_redirects=True,
        timeout=15,
    ) as client:
        for url in body.urls:
            try:
                resp = await client.get(url)
                if resp.status_code != 200:
                    results.append({
                        "url": url,
                        "status": "failed",
                        "code": resp.status_code,
                    })
                    continue

                ct = resp.headers.get("content-type", "image/jpeg")
                ext = ".jpg"
                if "png" in ct:
                    ext = ".png"
                elif "svg" in ct:
                    ext = ".svg"
                elif "webp" in ct:
                    ext = ".webp"

                import uuid as _uuid

                key = f"{body.prefix}/{_uuid.uuid4().hex}{ext}"

                if settings.s3_local_mode:
                    import pathlib

                    lp = pathlib.Path(settings.s3_local_path) / key
                    lp.parent.mkdir(parents=True, exist_ok=True)
                    lp.write_bytes(resp.content)
                    s3_url = f"/uploads/{key}"
                else:
                    s3.client.put_object(
                        Bucket=s3.bucket,
                        Key=key,
                        Body=resp.content,
                        ContentType=ct,
                    )
                    # Use direct public URL for catalog images
                    # (bucket policy allows public read on catalog/*)
                    # Avoids presigned URL length/expiration issues
                    s3_url = f"https://{s3.bucket}.s3.amazonaws.com/{key}"

                results.append({
                    "url": url,
                    "status": "ok",
                    "s3_key": key,
                    "s3_url": s3_url,
                    "size": len(resp.content),
                })
            except Exception as e:
                results.append({
                    "url": url,
                    "status": "error",
                    "error": str(e),
                })

    ok = sum(1 for r in results if r.get("status") == "ok")
    return {"uploaded": ok, "total": len(body.urls), "results": results}


class WipeInstitutionRequest(BaseModel):
    institution_name: str


@router.post("/wipe-institution")
async def wipe_institution(
    body: WipeInstitutionRequest,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete an institution and all its programs for re-import."""
    from unipaith.models.user import UserRole

    result = await db.execute(
        select(Institution).where(
            Institution.name == body.institution_name,
        )
    )
    inst = result.scalar_one_or_none()
    if not inst:
        return {"status": "not_found"}

    progs = await db.execute(
        select(Program).where(Program.institution_id == inst.id)
    )
    prog_count = 0
    for p in progs.scalars().all():
        await db.delete(p)
        prog_count += 1

    admin_id = inst.admin_user_id
    await db.delete(inst)

    sys_user_r = await db.execute(select(User).where(User.id == admin_id))
    sys_user = sys_user_r.scalar_one_or_none()
    if sys_user and sys_user.role == UserRole.institution_admin:
        if sys_user.email.startswith("system+"):
            await db.delete(sys_user)

    await db.commit()
    return {
        "status": "deleted",
        "institution": body.institution_name,
        "programs_deleted": prog_count,
    }

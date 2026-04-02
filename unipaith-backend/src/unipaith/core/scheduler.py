"""Background job scheduling using APScheduler."""
from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from unipaith.config import settings

logger = logging.getLogger("unipaith.scheduler")

scheduler = AsyncIOScheduler()
_ml_cycle_tick_count = 0


def _job_defaults() -> dict:
    return {
        "replace_existing": True,
        "max_instances": 1,
        "coalesce": True,
        "misfire_grace_time": settings.scheduler_misfire_grace_seconds,
    }


def setup_scheduler() -> None:
    """Register all scheduled jobs. Called during app startup."""
    if scheduler.running:
        logger.info("Scheduler already running; skipping re-initialization")
        return
    scheduler_is_enabled = settings.scheduler_enabled or (
        settings.scheduler_auto_enable_non_test and settings.environment != "test"
    )
    if not scheduler_is_enabled:
        logger.info("Scheduler disabled by configuration")
        return
    if settings.scheduler_require_leader and not settings.scheduler_is_leader:
        logger.info("Scheduler disabled on this instance (leader-only mode)")
        return

    # Unified ML cycle: evaluate -> drift -> decision -> train -> fairness -> promote
    scheduler.add_job(
        _run_ml_cycle,
        "interval",
        minutes=settings.ml_cycle_schedule_minutes,
        id="ml_cycle",
        name="ML Full Cycle",
        **_job_defaults(),
    )

    # Daily feature refresh
    scheduler.add_job(
        _run_feature_refresh,
        "interval",
        hours=24,
        id="feature_refresh",
        name="Daily Feature Refresh",
        **_job_defaults(),
    )

    # GPU idle shutdown check — every 5 minutes (only in aws mode)
    if settings.gpu_mode == "aws":
        scheduler.add_job(
            _check_gpu_idle,
            "interval",
            minutes=5,
            id="gpu_idle_check",
            name="GPU Idle Shutdown Check",
            **_job_defaults(),
        )
        logger.info(
            "GPU idle shutdown enabled (threshold=%dm)",
            settings.gpu_70b_idle_shutdown_minutes,
        )

    # Weekly crawler run (if crawler sources exist)
    scheduler.add_job(
        _run_crawler,
        "interval",
        hours=settings.crawler_default_frequency_hours,
        id="crawler_weekly",
        name="Weekly University Crawler",
        **_job_defaults(),
    )

    if settings.scheduler_self_driving_enabled:
        scheduler.add_job(
            _run_self_driving_loop,
            "interval",
            minutes=settings.scheduler_self_driving_interval_minutes,
            id="ai_self_driving",
            name="AI Self-Driving Loop",
            **_job_defaults(),
        )

    if settings.engine_loop_enabled:
        scheduler.add_job(
            _run_knowledge_engine_tick,
            "interval",
            minutes=settings.engine_loop_interval_minutes,
            id="knowledge_engine",
            name="Knowledge Engine Loop",
            **_job_defaults(),
        )

    scheduler.start()
    logger.info(
        "Scheduler started with %d jobs: %s",
        len(scheduler.get_jobs()),
        [j.name for j in scheduler.get_jobs()],
    )


def shutdown_scheduler() -> None:
    """Gracefully shut down the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")


async def _run_ml_cycle() -> None:
    """Run the unified ML full-cycle pipeline with cadence mode."""
    from unipaith.database import async_session
    from unipaith.ml.orchestrator import MLOrchestrator

    global _ml_cycle_tick_count
    _ml_cycle_tick_count += 1
    force_full_every = max(1, settings.ml_cycle_force_full_every_n_cycles)
    preferred_mode = "full" if (_ml_cycle_tick_count % force_full_every == 0) else "fast"
    trigger = f"scheduled_{preferred_mode}"

    logger.info("Starting scheduled ML full cycle (mode=%s)", preferred_mode)
    try:
        async with async_session() as db:
            orch = MLOrchestrator(db)
            await orch.run_full_cycle(
                triggered_by=trigger,
                preferred_mode=preferred_mode,
            )
        logger.info("ML full cycle completed (mode=%s)", preferred_mode)
    except Exception:
        logger.exception("ML full cycle failed")


async def _run_feature_refresh() -> None:
    """Refresh student and program features."""
    from unipaith.ai.jobs import daily_feature_refresh
    from unipaith.database import async_session

    logger.info("Starting daily feature refresh")
    try:
        async with async_session() as db:
            await daily_feature_refresh(db)
        logger.info("Feature refresh completed")
    except Exception:
        logger.exception("Feature refresh failed")


async def _check_gpu_idle() -> None:
    """Check if 70B GPU instance should be shut down due to idleness."""
    from unipaith.ai.cost_tracker import get_cost_tracker
    from unipaith.ai.gpu_manager import get_70b_manager

    try:
        manager = get_70b_manager()
        stopped = await manager.check_idle_shutdown()
        if stopped:
            tracker = get_cost_tracker()
            tracker.record_stop("70b")
    except Exception:
        logger.exception("GPU idle check failed")


async def _run_crawler() -> None:
    """Run the university data crawler for all active sources."""
    from unipaith.database import async_session

    logger.info("Starting scheduled university crawl")
    try:
        async with async_session() as db:
            from unipaith.crawler.orchestrator import CrawlerOrchestrator
            orch = CrawlerOrchestrator(db)
            await orch.run_scheduled_crawls()
        logger.info("University crawl completed")
    except Exception:
        logger.exception("University crawl failed")


async def _run_knowledge_engine_tick() -> None:
    """Run one tick of the perpetual knowledge engine loop."""
    from unipaith.database import async_session
    from unipaith.services.engine_loop import EngineLoop

    logger.info("Starting knowledge engine tick")
    try:
        async with async_session() as db:
            loop = EngineLoop(db)
            result = await loop.run_tick()
            await db.commit()
            logger.info(
                "Knowledge engine tick: processed=%d, errors=%d, discovered=%d",
                result.get("processed", 0),
                result.get("errors", 0),
                result.get("discovered", 0),
            )
    except Exception:
        logger.exception("Knowledge engine tick failed")


async def _run_self_driving_loop() -> None:
    """Run one autonomous AI control-plane tick."""
    from unipaith.database import async_session
    from unipaith.services.ai_control_plane_service import AIControlPlaneService

    logger.info("Starting scheduled self-driving AI loop")
    try:
        async with async_session() as db:
            service = AIControlPlaneService(db)
            result = await service.run_self_driving_tick(trigger="scheduled")
            logger.info("Self-driving loop result: %s", result.get("status"))
    except Exception:
        logger.exception("Self-driving AI loop failed")

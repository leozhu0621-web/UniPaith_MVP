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

    # ML cycle: now handled by ContinuousPipeline Stage 3.
    # Legacy scheduled job kept only when pipeline is disabled.
    if not settings.pipeline_enabled:
        scheduler.add_job(
            _run_ml_cycle,
            "interval",
            minutes=settings.ml_cycle_schedule_minutes,
            id="ml_cycle",
            name="ML Full Cycle (legacy)",
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

    # Crawler: now handled by ContinuousPipeline Stage 1.
    if not settings.pipeline_enabled:
        scheduler.add_job(
            _run_crawler,
            "interval",
            hours=settings.crawler_default_frequency_hours,
            id="crawler_weekly",
            name="University Crawler (legacy)",
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

    # Knowledge engine tick: now handled by ContinuousPipeline Stages 1+2.
    if not settings.pipeline_enabled and settings.engine_loop_enabled:
        scheduler.add_job(
            _run_knowledge_engine_tick,
            "interval",
            minutes=settings.engine_loop_interval_minutes,
            id="knowledge_engine",
            name="Knowledge Engine Loop (legacy)",
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
    # ML orchestrator skipped (engine being rebuilt)
    logger.info("ML cycle skipped (engine being rebuilt)")


async def _run_feature_refresh() -> None:
    """Refresh student and program features."""
    # AI feature refresh skipped (engine being rebuilt)
    logger.info("Feature refresh skipped (engine being rebuilt)")


async def _check_gpu_idle() -> None:
    """Check if 70B GPU instance should be shut down due to idleness."""
    # GPU manager skipped (engine being rebuilt)
    logger.debug("GPU idle check skipped (engine being rebuilt)")


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
    # Knowledge engine skipped (engine being rebuilt)
    logger.info("Knowledge engine tick skipped (engine being rebuilt)")


async def _run_self_driving_loop() -> None:
    """Run one autonomous AI control-plane tick."""
    # AI control plane skipped (engine being rebuilt)
    logger.info("Self-driving AI loop skipped (engine being rebuilt)")

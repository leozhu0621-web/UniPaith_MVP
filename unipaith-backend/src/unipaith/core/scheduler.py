"""Background job scheduling using APScheduler."""
from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from unipaith.config import settings

logger = logging.getLogger("unipaith.scheduler")

scheduler = AsyncIOScheduler()


def setup_scheduler() -> None:
    """Register all scheduled jobs. Called during app startup."""
    if not settings.scheduler_enabled:
        logger.info("Scheduler disabled (SCHEDULER_ENABLED=false)")
        return

    # Evaluation (Person B) — every eval_schedule_hours
    scheduler.add_job(
        _run_evaluation,
        "interval",
        hours=settings.eval_schedule_hours,
        id="ml_evaluation",
        name="ML Model Evaluation",
        replace_existing=True,
    )

    # Training (Person C) — every training_schedule_hours
    scheduler.add_job(
        _run_training,
        "interval",
        hours=settings.training_schedule_hours,
        id="ml_training",
        name="ML Model Training",
        replace_existing=True,
    )

    # Daily feature refresh
    scheduler.add_job(
        _run_feature_refresh,
        "interval",
        hours=24,
        id="feature_refresh",
        name="Daily Feature Refresh",
        replace_existing=True,
    )

    # GPU idle shutdown check — every 5 minutes (only in aws mode)
    if settings.gpu_mode == "aws":
        scheduler.add_job(
            _check_gpu_idle,
            "interval",
            minutes=5,
            id="gpu_idle_check",
            name="GPU Idle Shutdown Check",
            replace_existing=True,
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
        replace_existing=True,
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


async def _run_evaluation() -> None:
    """Run the ML evaluation pipeline."""
    from unipaith.database import async_session
    from unipaith.ml.orchestrator import MLOrchestrator

    logger.info("Starting scheduled ML evaluation")
    try:
        async with async_session() as db:
            orch = MLOrchestrator(db)
            await orch.run_evaluation()
        logger.info("ML evaluation completed")
    except Exception:
        logger.exception("ML evaluation failed")


async def _run_training() -> None:
    """Run the ML training pipeline."""
    from unipaith.database import async_session
    from unipaith.ml.orchestrator import MLOrchestrator

    logger.info("Starting scheduled ML training")
    try:
        async with async_session() as db:
            orch = MLOrchestrator(db)
            await orch.run_training()
        logger.info("ML training completed")
    except Exception:
        logger.exception("ML training failed")


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

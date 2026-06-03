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

    if settings.scheduler_self_driving_enabled:
        scheduler.add_job(
            _run_self_driving_loop,
            "interval",
            minutes=settings.scheduler_self_driving_interval_minutes,
            id="ai_self_driving",
            name="AI Self-Driving Loop",
            **_job_defaults(),
        )

    # Saved-search alert loop (Spec 56 §6) — re-run alert-enabled saved searches
    # and notify on new matches. Consent-gated + per-user-per-day capped.
    if settings.saved_search_alerts_enabled:
        scheduler.add_job(
            _run_saved_search_alerts,
            "interval",
            minutes=settings.saved_search_alert_interval_minutes,
            id="saved_search_alerts",
            name="Saved-Search Alert Loop",
            **_job_defaults(),
        )

    # Spec 60 §10 — the governed knowledge-engine tick. Off by default
    # (crawler_engine_enabled); public-non-personal reference enrichment only, and
    # live network fetching stays separately gated by crawler_live_fetch_enabled.
    if settings.crawler_engine_enabled:
        scheduler.add_job(
            _run_crawler_engine_tick,
            "interval",
            minutes=settings.crawler_tick_interval_minutes,
            id="crawler_engine_tick",
            name="Knowledge Engine Tick (spec 60)",
            **_job_defaults(),
        )

    # Notification digest loop (Spec 57 §6) — batch un-emailed digest-class
    # notifications (feed updates, non-urgent change events, saved-search hits)
    # into one periodic email per user. Urgent events are emailed immediately by
    # NotificationService; this only sweeps the digest class.
    if settings.notification_digest_enabled:
        scheduler.add_job(
            _run_notification_digest,
            "interval",
            minutes=settings.notification_digest_interval_minutes,
            id="notification_digest",
            name="Notification Digest Loop",
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


async def _run_knowledge_engine_tick() -> None:
    """Run one tick of the perpetual knowledge engine loop."""
    # Knowledge engine skipped (engine being rebuilt)
    logger.info("Knowledge engine tick skipped (engine being rebuilt)")


async def _run_self_driving_loop() -> None:
    """Run one autonomous AI control-plane tick."""
    # AI control plane skipped (engine being rebuilt)
    logger.info("Self-driving AI loop skipped (engine being rebuilt)")


async def _run_saved_search_alerts() -> None:
    """Re-run alert-enabled saved searches and notify on new matches (Spec 56 §6).

    Opens its own session; a failed tick logs and is retried next interval — a
    scheduled job must never crash the loop.
    """
    from unipaith.database import async_session
    from unipaith.services.saved_search_service import SavedSearchService

    try:
        async with async_session() as session:
            emitted = await SavedSearchService(session).run_alerts()
            await session.commit()
        if emitted:
            logger.info("Saved-search alert loop emitted %d alert(s)", emitted)
    except Exception as exc:  # noqa: BLE001 — never let a tick break the scheduler
        logger.warning("Saved-search alert loop failed: %s", exc)


async def _run_crawler_engine_tick() -> None:
    """Spec 60 §10 — one governed knowledge-engine tick (flag-gated, off by default).

    Pulls due frontier items, runs the deterministic pipeline (live fetch stays
    separately gated), and persists an EngineLoopSnapshot. Opens its own session;
    a failed tick logs and retries next interval — never crashes the loop.
    """
    from unipaith.database import async_session
    from unipaith.services.crawler.engine import KnowledgeEngine

    try:
        async with async_session() as session:
            result = await KnowledgeEngine(session).tick(limit=settings.crawler_tick_batch_size)
            await session.commit()
        logger.info("Knowledge engine tick: %s", result)
    except Exception as exc:  # noqa: BLE001 — never let a tick break the scheduler
        logger.warning("Knowledge engine tick failed: %s", exc)


async def _run_notification_digest() -> None:
    """Batch un-emailed digest-class notifications into one email per user (Spec 57 §6).

    Opens its own session; a failed tick logs and is retried next interval — a
    scheduled job must never crash the loop.
    """
    from unipaith.database import async_session
    from unipaith.services.notification_service import NotificationService

    try:
        async with async_session() as session:
            sent = await NotificationService(session).run_digest()
            await session.commit()
        if sent:
            logger.info("Notification digest loop sent %d digest email(s)", sent)
    except Exception as exc:  # noqa: BLE001 — never let a tick break the scheduler
        logger.warning("Notification digest loop failed: %s", exc)

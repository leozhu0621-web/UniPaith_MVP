"""The daily content-ingest refresh scheduler job.

Verifies the job is registered only when enabled and that the handler is
fail-soft (a raising ingest_all never propagates — a tick must not crash the
scheduler loop).
"""

from unipaith.core import scheduler as sched


def test_handler_is_fail_soft(monkeypatch):
    """A raising ingest_all is swallowed (logged, not propagated)."""

    class _BoomService:
        def __init__(self, _session):
            pass

        async def ingest_all(self):
            raise RuntimeError("feed down")

    # async_session() is used as `async with`; provide a no-op async ctx manager.
    class _Session:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def commit(self):
            pass

    import unipaith.database as db
    import unipaith.services.content_ingest as ci

    monkeypatch.setattr(db, "async_session", lambda: _Session())
    monkeypatch.setattr(ci, "ContentIngestService", _BoomService)

    import asyncio

    # Must NOT raise.
    asyncio.run(sched._run_content_ingest_refresh())


def test_job_registered_when_enabled(monkeypatch):
    """setup_scheduler registers the content_ingest_refresh job when the flag is
    on, and not when off."""
    from apscheduler.schedulers.asyncio import AsyncIOScheduler

    from unipaith.config import settings

    # Force a clean, enabled, leader scheduler in a non-test guise.
    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings, "scheduler_enabled", True)
    monkeypatch.setattr(settings, "scheduler_require_leader", False)
    monkeypatch.setattr(settings, "scheduler_self_driving_enabled", False)
    monkeypatch.setattr(settings, "saved_search_alerts_enabled", False)
    monkeypatch.setattr(settings, "notification_digest_enabled", False)
    monkeypatch.setattr(settings, "pipeline_enabled", True)
    monkeypatch.setattr(settings, "gpu_mode", "local")

    fresh = AsyncIOScheduler()
    # start() needs a running event loop; jobs are added before start, so stub it.
    monkeypatch.setattr(fresh, "start", lambda *a, **k: None)
    monkeypatch.setattr(sched, "scheduler", fresh)

    monkeypatch.setattr(settings, "content_ingest_refresh_enabled", True)
    sched.setup_scheduler()
    assert fresh.get_job("content_ingest_refresh") is not None

    # ...and absent when the flag is off.
    fresh2 = AsyncIOScheduler()
    monkeypatch.setattr(fresh2, "start", lambda *a, **k: None)
    monkeypatch.setattr(sched, "scheduler", fresh2)
    monkeypatch.setattr(settings, "content_ingest_refresh_enabled", False)
    sched.setup_scheduler()
    assert fresh2.get_job("content_ingest_refresh") is None

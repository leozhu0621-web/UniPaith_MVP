"""Spec 55 §8 — health & readiness probes.

``GET /health`` — **liveness**: DB-free and 200-always. The ALB target group and
the ECS container health check both poll this (``infra/alb.tf``,
``infra/ecs.tf``), so it must never touch the DB — a transient DB blip must not
deregister every task. Response shape is pinned by ``tests/test_health.py``
(``status="ok"``, ``version="0.1.0"``) and only ever extended, never narrowed.

``GET /ready`` — **readiness**: a real ``SELECT 1`` against the pool plus a
dependency report. 200 when the app can serve real traffic, 503 otherwise.
Deliberately *not* wired to the ALB — it is the deep diagnostic probe and the
evidence the ``/goal/backend`` page reads for "readiness gate: live".
"""

from __future__ import annotations

import time

from fastapi import APIRouter, Response
from sqlalchemy import text

from unipaith.config import settings
from unipaith.core.cache import cache
from unipaith.core.scheduler import scheduler
from unipaith.database import async_session

router = APIRouter(tags=["health"])

_APP_VERSION = "0.1.0"
_BOOT_MONOTONIC = time.monotonic()


@router.get("/health", summary="Liveness probe (DB-free, 200-always)")
async def health_check() -> dict:
    """Liveness — the process is up and the event loop is serving.

    Intentionally does no I/O so it stays fast and cannot be taken down by a
    dependency. Backs the ALB + ECS health checks.
    """
    return {
        "status": "ok",
        "version": _APP_VERSION,
        "environment": settings.environment,
        "uptime_s": round(time.monotonic() - _BOOT_MONOTONIC, 1),
    }


@router.get("/ready", summary="Readiness probe (checks DB + reports deps)")
async def readiness_check(response: Response) -> dict:
    """Readiness — can this task serve real traffic right now?

    Hard-gates on the database (a ``SELECT 1`` round-trip). The scheduler and
    cache are reported but never gate readiness: a paused scheduler or an
    in-process (non-distributed) cache is *degraded*, not *down*.
    """
    checks: dict[str, dict] = {}

    # Database — the one hard dependency for serving real traffic.
    db_ok = False
    db_detail = ""
    start = time.perf_counter()
    try:
        async with async_session() as db:
            await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception as exc:  # noqa: BLE001 — readiness must never raise
        db_detail = type(exc).__name__
    checks["database"] = {
        "ok": db_ok,
        "latency_ms": round((time.perf_counter() - start) * 1000, 1),
        "pool_size": settings.db_pool_size,
        "detail": db_detail,
    }

    # Scheduler — reported, not gated. Running is the steady state.
    checks["scheduler"] = {"ok": True, "running": scheduler.running}

    # Cache — always present (in-process); surface distributed-backend readiness.
    cache_stats = cache.stats()
    checks["cache"] = {
        "ok": True,
        "backend": cache_stats["backend"],
        "distributed_ready": cache_stats["distributed_ready"],
    }

    ready = db_ok
    if not ready:
        response.status_code = 503
    return {"status": "ready" if ready else "not_ready", "checks": checks}

"""Spec 55 — backend production-readiness, as queryable data.

Spec 55 hardens the FastAPI backend to production-SaaS grade. It is explicit that
the backend is "further along than a greenfield" — readiness = *filling gaps*
(observability, Redis, queue, breakers) and *formalizing* what's half-built
(scheduler, rate-limit, pipeline). This module turns that spec into the payload
behind ``GET /build/production`` and the ``/goal/backend`` page, the same way
``ai.catalog`` turns spec 45 into ``GET /ai/agents``.

The self-verifying hooks (read live from the running app, never asserted in
prose):

- the **live config knobs** (pool / rate-limit / scheduler / resilience / cache /
  cost) are read straight off ``unipaith.config.settings`` — the same object the
  app boots with, so the page shows the deployed values;
- the **middleware count** is ``len(app.user_middleware)`` — the real stack;
- the **health probes** are resolved from ``app.routes`` — so the page can only
  claim ``/health`` + ``/ready`` if they are actually served;
- the **cache hit-rate** is the live ``core.cache`` counter.

The narrative (pillars, their build/plan split, the §9 checklist, the SLOs) is
authored from spec 55; the numbers are introspected. Each pillar and build task
is honestly classified ``live`` / ``partial`` / ``planned`` — the infra-dependent
halves (ElastiCache, arq, /metrics, PgBouncer, circuit-breaker lib, DLQ) are
marked ``planned`` with the config that already anticipates them as evidence,
exactly like the roadmap's deferred phase. DB-free and unauthenticated.
"""

from __future__ import annotations

from dataclasses import dataclass

from unipaith.config import settings
from unipaith.core.cache import cache

API_PREFIX = "/api/v1"
_SKIP_METHODS = {"HEAD", "OPTIONS"}

Status = str  # "live" | "partial" | "planned"


# ── §1 · The bar ────────────────────────────────────────────────────────────
THE_BAR: dict = {
    "statement": (
        "A backend is production-grade when it stays up, stays honest, and stays "
        "fast under load: structured logs and health probes you can act on, a "
        "version-keyed read cache, graceful degradation instead of 5xxes, a pooled "
        "database, and migrations that run before the new version serves."
    ),
    "slo_headline": "p95 < 400ms (non-AI) · < 2.5s (AI cached) · errors < 0.5% · uptime ≥ 99%",
}


# ── §2–§8 · Readiness pillars ───────────────────────────────────────────────
@dataclass(frozen=True)
class Pillar:
    key: str
    title: str
    section: str  # spec 55 section, e.g. "§2"
    status: Status
    blurb: str
    built: tuple[str, ...]  # what is live today
    planned: tuple[str, ...]  # the gap, honestly named


PILLARS: tuple[Pillar, ...] = (
    Pillar(
        "observability",
        "Observability",
        "§2",
        "partial",
        "The biggest real gap — now wired at the request layer.",
        (
            "Structured JSON logs (ContextJsonFormatter) — one line per request",
            "Request-id contextvar — every log + error shares a greppable id",
            "Per-request access log: request_id · route · status · latency_ms · client",
            "X-Request-ID echoed on every response",
        ),
        (
            "/metrics via prometheus-fastapi-instrumentator",
            "OpenTelemetry tracing (FastAPI + SQLAlchemy + httpx)",
            "Golden-signal dashboards + SLO paging",
        ),
    ),
    Pillar(
        "caching",
        "Read cache",
        "§3",
        "live",
        "Version-keyed read cache with a measured hit-rate.",
        (
            "core/cache.py — async TTL cache + cached() helper",
            "Version-keyed (profile_version / program_version busts on bump, 51 §7)",
            "Measured hit / miss / eviction counters",
            "Fronting the public build surface today",
        ),
        (
            "Shared Redis / ElastiCache backend (redis_url, soft-imported)",
            "Cache program/school detail, match results, feed pages",
        ),
    ),
    Pillar(
        "queue",
        "Queue & workers",
        "§4",
        "partial",
        "Scheduler is live; the job queue is the next gap.",
        (
            "APScheduler (core/scheduler.py) with leader-election + misfire-grace",
            "Registered cadence jobs (feature refresh, GPU idle, self-driving loop)",
            "Continuous pipeline config (crawl rpm / concurrency / budget)",
        ),
        (
            "arq (Redis-backed, async-native) job queue in worker/",
            "Move AI / crawler / email / aggregates to jobs",
            "Separate ECS fleets (web · CPU jobs · GPU) + DLQ",
        ),
    ),
    Pillar(
        "rate_limiting",
        "Rate limiting & idempotency",
        "§5",
        "partial",
        "Per-IP limiting is live; per-user + idempotency are next.",
        (
            "slowapi limiter (per-IP) with a 429 + error-code handler",
            "rate_limit_per_minute / rate_limit_enabled config",
        ),
        (
            "Per-user buckets + stricter AI/bulk buckets (Retry-After)",
            "core/idempotency.py — Idempotency-Key on money/decision mutations",
        ),
    ),
    Pillar(
        "resilience",
        "Resilience",
        "§6",
        "partial",
        "AI graceful-degrade is live and test-guarded; breakers are next.",
        (
            "Every AI agent falls back to rule-based — AI never 5xxes",
            "Guarded by tests/test_plan2_integration.py (the integration invariant)",
            "Timeout + retry + backoff + provider failover config",
        ),
        (
            "Explicit circuit breakers on external calls (Anthropic / S3 / SES / Stripe)",
            "Bulkheads — AI/GPU/crawler on separate workers",
        ),
    ),
    Pillar(
        "database",
        "Database",
        "§7",
        "live",
        "Pooled async engine; single-head migrations; secrets-managed.",
        (
            "Async pool sized (size / overflow / recycle) on the running engine",
            "Single-head Alembic chain (test_alembic_has_single_head guard)",
            "DB password injected from AWS Secrets Manager at boot",
            "Expand→contract migration discipline (CLAUDE.md)",
        ),
        (
            "Hot-path index audit migration (FKs / status / JSONB GIN / pgvector ANN)",
            "PgBouncer transaction pooling in front of RDS",
            "N+1 query-count tests on the heavy list endpoints",
        ),
    ),
    Pillar(
        "health",
        "Health, deploy & SLOs",
        "§8",
        "live",
        "Liveness + readiness probes; migration-before-serve.",
        (
            "/health — liveness, DB-free, 200-always (ALB + ECS wired)",
            "/ready — readiness, real SELECT 1 + dependency report (503 on DB down)",
            "Migration-before-serve entrypoint (alembic upgrade head)",
            "GZip + security headers + CORS allowlist",
        ),
        (
            "Graceful drain + arq job requeue on shutdown",
            "SLO dashboards + paging; queue DLQ alerting",
        ),
    ),
)


# ── §9 · Build-task checklist ───────────────────────────────────────────────
@dataclass(frozen=True)
class BuildTask:
    section: str
    status: Status
    text: str
    evidence: str


BUILD_TASKS: tuple[BuildTask, ...] = (
    BuildTask(
        "§2",
        "live",
        "core/observability.py (structured JSON) + request-id middleware",
        "ContextJsonFormatter + observability_middleware are wired in main + middleware.",
    ),
    BuildTask(
        "§2",
        "planned",
        "/metrics (prometheus) + OTel tracing on FastAPI + SQLAlchemy + httpx",
        "Deferred — no new runtime dep until a scrape target exists.",
    ),
    BuildTask(
        "§3",
        "partial",
        "core/cache.py (version-keyed read cache); ElastiCache infra",
        "Cache + helper + hit-rate are live in-process; shared Redis backend is planned.",
    ),
    BuildTask(
        "§4",
        "partial",
        "arq in worker/; move workloads to jobs; wire to core/scheduler.py",
        "Scheduler + cadence jobs are live; the arq queue is planned.",
    ),
    BuildTask(
        "§5",
        "partial",
        "Per-user + IP + AI/bulk rate buckets; core/idempotency.py",
        "Per-IP limiting is live; per-user buckets + idempotency are planned.",
    ),
    BuildTask(
        "§6",
        "partial",
        "Circuit breakers + timeouts on external calls; verify AI graceful-degrade",
        "AI degrade is live + test-guarded and timeouts are configured; breakers planned.",
    ),
    BuildTask(
        "§7",
        "planned",
        "Index migration (FKs / JSONB GIN / pgvector ANN); PgBouncer; N+1 tests",
        "Pool is live; the index audit + PgBouncer are planned.",
    ),
    BuildTask(
        "§8",
        "live",
        "/health + /ready; graceful shutdown; migration-before-serve entrypoint",
        "Probes are live and route-backed; migration-before-serve ships in the entrypoint.",
    ),
    BuildTask(
        "§8",
        "planned",
        "Golden-signal dashboards + SLO alerts; DLQ + alert",
        "Deferred to the metrics + queue pillars.",
    ),
)


# ── §8 · SLOs ───────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Slo:
    metric: str
    target: str
    note: str


SLOS: tuple[Slo, ...] = (
    Slo("API latency p95 (non-AI)", "< 400 ms", "Read/write paths off the AI stack."),
    Slo("API latency p95 (AI, cached)", "< 2.5 s", "Cached rationale / brief; cold AI is slower."),
    Slo("Error rate", "< 0.5%", "5xx share; AI endpoints fall back, never 5xx."),
    Slo("Uptime", "≥ 99%", "07 §7 — the public availability commitment."),
    Slo("Queue job p95", "within budget", "Per-job budget; poison messages → DLQ + alert."),
)


# ── §11 · Open questions ────────────────────────────────────────────────────
OPEN_QUESTIONS: tuple[dict, ...] = (
    {
        "q": "Queue engine",
        "a": "arq — async-native, Redis-backed; fits the stack better than Celery.",
    },
    {
        "q": "Redis topology",
        "a": "ElastiCache from day one — multi-task ECS rules out an in-process "
        "cache as the shared layer.",
    },
    {
        "q": "Extraction runtime",
        "a": "63 standardizes on Qwen (vLLM / Bedrock); the existing Ollama path "
        "stays local-dev only.",
    },
)


def _health_routes(routes) -> list[str]:
    """Resolve the live liveness/readiness probe paths from the running routes."""
    from unipaith.transparency.live_routes import expand_routes

    found: set[str] = set()
    for r in expand_routes(routes):
        path = getattr(r, "path", "")
        methods = getattr(r, "methods", None)
        if not path.startswith(API_PREFIX) or not methods:
            continue
        if path.endswith("/health") or path.endswith("/ready"):
            if any(m not in _SKIP_METHODS for m in methods):
                found.add(path)
    return sorted(found)


def _middleware_classes(app) -> list[str]:
    """Best-effort names of the live middleware stack (count is the hard signal)."""
    names: list[str] = []
    for mw in getattr(app, "user_middleware", []):
        cls = getattr(mw, "cls", None)
        cls_name = getattr(cls, "__name__", None) or str(cls)
        if cls_name == "BaseHTTPMiddleware":
            # app.middleware("http")(fn) wraps fn as a dispatch kwarg.
            kwargs = getattr(mw, "kwargs", None) or {}
            dispatch = kwargs.get("dispatch")
            if dispatch is not None:
                cls_name = getattr(dispatch, "__name__", cls_name)
        names.append(cls_name)
    return names


def _config_groups() -> list[dict]:
    """The live config knobs, grouped, read straight off ``settings``."""
    return [
        {
            "key": "pool",
            "title": "Connection pool",
            "section": "§7",
            "knobs": [
                {"name": "db_pool_size", "value": settings.db_pool_size},
                {"name": "db_pool_overflow", "value": settings.db_pool_overflow},
                {"name": "db_pool_recycle_s", "value": settings.db_pool_recycle},
            ],
        },
        {
            "key": "rate_limit",
            "title": "Rate limiting",
            "section": "§5",
            "knobs": [
                {"name": "rate_limit_per_minute", "value": settings.rate_limit_per_minute},
                {"name": "rate_limit_enabled", "value": settings.rate_limit_enabled},
            ],
        },
        {
            "key": "scheduler",
            "title": "Scheduler",
            "section": "§4",
            "knobs": [
                {"name": "scheduler_require_leader", "value": settings.scheduler_require_leader},
                {"name": "scheduler_is_leader", "value": settings.scheduler_is_leader},
                {
                    "name": "scheduler_misfire_grace_s",
                    "value": settings.scheduler_misfire_grace_seconds,
                },
            ],
        },
        {
            "key": "resilience",
            "title": "Resilience",
            "section": "§6",
            "knobs": [
                {"name": "ai_request_timeout_s", "value": settings.ai_request_timeout_seconds},
                {"name": "ai_request_max_retries", "value": settings.ai_request_max_retries},
                {"name": "ai_request_backoff_s", "value": settings.ai_request_backoff_seconds},
                {"name": "ai_provider_failover", "value": settings.ai_provider_failover_csv},
            ],
        },
        {
            "key": "cache",
            "title": "Read cache",
            "section": "§3",
            "knobs": [
                {"name": "cache_enabled", "value": settings.cache_enabled},
                {"name": "cache_default_ttl_s", "value": settings.cache_default_ttl},
                {"name": "redis_url", "value": "set" if settings.redis_url else "(in-process)"},
            ],
        },
        {
            "key": "cost",
            "title": "Cost guardrails",
            "section": "§6",
            "knobs": [
                {
                    "name": "ai_weekly_cost_cap_usd",
                    "value": settings.ai_per_student_weekly_cost_cap_usd,
                },
                {"name": "ai_cost_cap_enforcement", "value": settings.ai_cost_cap_enforcement},
                {
                    "name": "pipeline_budget_per_hour_usd",
                    "value": settings.pipeline_extract_budget_per_hour,
                },
            ],
        },
    ]


# Authored from core/scheduler.py — the cadence jobs the scheduler registers.
_SCHEDULER_JOBS: tuple[dict, ...] = (
    {"id": "feature_refresh", "name": "Daily feature refresh", "cadence": "24h"},
    {"id": "gpu_idle_check", "name": "GPU idle shutdown check", "cadence": "interval"},
    {"id": "ai_self_driving", "name": "AI self-driving loop", "cadence": "30m"},
    {"id": "knowledge_engine", "name": "Knowledge engine loop (legacy)", "cadence": "5m"},
)


def build_production(app) -> dict:
    """Assemble the ``GET /build/production`` payload.

    Narrative is authored from spec 55; the config knobs, middleware count,
    health-probe routes and cache hit-rate are introspected from ``app`` /
    ``settings`` / ``core.cache`` so the page mirrors the deployed backend.
    """
    routes = list(getattr(app, "routes", []))
    health_paths = _health_routes(routes)
    middleware = _middleware_classes(app)
    config_groups = _config_groups()
    cache_stats = cache.stats()

    # Scheduler — report the live count when running, else the authored cadence set.
    from unipaith.core.scheduler import scheduler as _sched

    try:
        live_jobs = len(_sched.get_jobs())
    except Exception:
        live_jobs = 0

    pillars_out = [
        {
            "key": p.key,
            "title": p.title,
            "section": p.section,
            "status": p.status,
            "blurb": p.blurb,
            "built": list(p.built),
            "planned": list(p.planned),
        }
        for p in PILLARS
    ]

    def _count(status: Status) -> int:
        return sum(1 for p in PILLARS if p.status == status)

    def _task_count(status: Status) -> int:
        return sum(1 for t in BUILD_TASKS if t.status == status)

    knob_count = sum(len(g["knobs"]) for g in config_groups)

    return {
        "the_bar": dict(THE_BAR),
        "summary": {
            "pillar_count": len(PILLARS),
            "pillars_live": _count("live"),
            "pillars_partial": _count("partial"),
            "pillars_planned": _count("planned"),
            "build_task_count": len(BUILD_TASKS),
            "tasks_live": _task_count("live"),
            "tasks_partial": _task_count("partial"),
            "tasks_planned": _task_count("planned"),
            "health_route_count": len(health_paths),
            "middleware_count": len(middleware),
            "config_group_count": len(config_groups),
            "config_knob_count": knob_count,
            "scheduler_job_count": len(_SCHEDULER_JOBS),
            "scheduler_running": bool(getattr(_sched, "running", False)),
            "scheduler_live_jobs": live_jobs,
            "slo_count": len(SLOS),
            "open_question_count": len(OPEN_QUESTIONS),
            "cache_hit_rate": cache_stats["hit_rate"],
            "cache_backend": cache_stats["backend"],
            "cache_entries": cache_stats["entries"],
            "cache_lookups": cache_stats["lookups"],
            "live_is_source_of_truth": True,
        },
        "pillars": pillars_out,
        "config_groups": config_groups,
        "middleware": {"count": len(middleware), "classes": middleware},
        "scheduler": {
            "running": bool(getattr(_sched, "running", False)),
            "jobs": [dict(j) for j in _SCHEDULER_JOBS],
        },
        "health_probes": {
            "paths": health_paths,
            "count": len(health_paths),
            "note": "Liveness is DB-free and 200-always; readiness checks the DB "
            "and 503s when down.",
        },
        "cache": cache_stats,
        "build_tasks": [
            {"section": t.section, "status": t.status, "text": t.text, "evidence": t.evidence}
            for t in BUILD_TASKS
        ],
        "slos": [{"metric": s.metric, "target": s.target, "note": s.note} for s in SLOS],
        "open_questions": [dict(q) for q in OPEN_QUESTIONS],
    }

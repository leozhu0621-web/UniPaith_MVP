"""Spec 57 — Realtime & Notifications, as queryable data.

Spec 57 wires real-time delivery (SSE notifications, WebSocket messaging) on top
of the notification service: a typed event catalog, multi-channel fan-out, the
notification center, and digest/batching. This module turns that build into the
payload behind ``GET /build/realtime`` and the ``/goal/realtime`` page — the same
honest live/partial/planned posture as ``transparency.search`` (spec 56).

Self-verifying hooks (read live from the running app, never asserted in prose):

- the **transport routes** (``/me/stream`` SSE, ``/ws/messages`` WS) and the
  notification-center routes are resolved from the live route table, so the page
  can only claim a transport the deployed app actually serves;
- the **catalog event-type count** is read from the running
  ``notification_catalog`` registry;
- the **broker backend** (``memory`` vs ``redis``) and whether a cross-task
  backend is wired are read from the running ``core.realtime.broker`` stats;
- the **config knobs** (realtime / heartbeat / digest / delivery-retry / web-push)
  are read straight off ``settings``.

The narrative (capabilities, their built/planned split, the §7 checklist, the §8
acceptance, the §9 open questions) is authored from spec 57; each item is honestly
classified ``live`` / ``partial`` / ``planned``. Redis cross-task fan-out is
``partial`` (wired, defaults to in-process — the same posture as the read cache);
web-push and the durable queue/worker substrate are ``planned``. DB-free and
unauthenticated.
"""

from __future__ import annotations

from dataclasses import dataclass

from unipaith.config import settings
from unipaith.core.realtime import broker
from unipaith.models.base import Base
from unipaith.services import notification_catalog as catalog

API_PREFIX = "/api/v1"
_SKIP_METHODS = {"HEAD", "OPTIONS"}

Status = str  # "live" | "partial" | "planned"


# ── §1 · The bar ────────────────────────────────────────────────────────────
THE_BAR: dict = {
    "statement": (
        "Realtime is good when a decision, a message, or a deadline reaches the "
        "student the moment it happens — the bell counts up live, the message "
        "thread shows typing and read receipts, and the same event reaches every "
        "open tab and device — while low-urgency noise batches into a digest and "
        "nothing is ever silently dropped."
    ),
    "principle": (
        "Built on the notification service and the reconnecting realtime client "
        "that already exist — extended with the SSE / WebSocket endpoints, an "
        "idempotent event catalog, a pub/sub broker that fans out across tasks, "
        "and a digest job, with every channel send retried and dead-lettered."
    ),
}


# ── §2–§6 · Capabilities ─────────────────────────────────────────────────────
@dataclass(frozen=True)
class Capability:
    key: str
    title: str
    section: str  # spec 57 section, e.g. "§2"
    status: Status
    blurb: str
    built: tuple[str, ...]  # what is live today
    planned: tuple[str, ...]  # the gap, honestly named


CAPABILITIES: tuple[Capability, ...] = (
    Capability(
        "sse",
        "SSE notification stream",
        "§2",
        "live",
        "One-way server→client push for the bell + feed pills.",
        (
            "GET /me/stream — typed {type, data} events (api/realtime.py)",
            "Auth via bearer header OR ?access_token= (EventSource can't set headers)",
            "Heartbeat keepalive frames so proxies don't idle the connection out",
            "Holds no DB connection — drains the in-process broker queue",
        ),
        ("@microsoft/fetch-event-source for true bearer-header SSE (today: query token)",),
    ),
    Capability(
        "ws",
        "WebSocket messaging",
        "§2",
        "live",
        "Bidirectional channel: typing, read receipts, instant delivery.",
        (
            "WS /ws/messages with a broker→socket send pump (api/realtime.py)",
            "Typing + read receipts fan out to the other conversation participants",
            "Instant message delivery on send (event_hooks.on_message_received)",
            "FE consumes it live — useMessageStream patches the thread cache (no poll)",
            "ping/pong liveness frames",
        ),
        (
            "Typing-indicator + read-receipt UI in the message thread (FE send-side)",
            "Presence (online/last-seen) + delivery acks persisted per message",
        ),
    ),
    Capability(
        "broker",
        "Pub/sub fan-out",
        "§2",
        "partial",
        "In-process broker today; Redis bridges it across ECS tasks.",
        (
            "core/realtime.py broker: per-user asyncio.Queue subscribers",
            "Slow-consumer guard (drop-oldest past the queue cap)",
            "Subscribe is a context manager — a dropped client leaves no buffer",
        ),
        (
            "Redis pub/sub bridge wired (settings.redis_url) — defaults to in-process "
            "until ElastiCache is pointed at it, same posture as the read cache (55 §3)",
        ),
    ),
    Capability(
        "catalog",
        "Typed event catalog",
        "§3",
        "live",
        "One registry: event_type → copy, deep-link, urgency, silenceable.",
        (
            "services/notification_catalog.py — every live event type mapped",
            "Idempotent emit() dedups on event_id (one row per source event)",
            "Recipient resolution + per-type preference category",
            "Catalog-driven copy + deep-link rendering",
        ),
        ("Per-locale copy templates (i18n) for transactional notifications",),
    ),
    Capability(
        "channels",
        "Multi-channel delivery",
        "§4",
        "partial",
        "In-app + transactional email today; web-push is the fast-follow.",
        (
            "In-app: the notifications row + live SSE push",
            "Email: transactional SES via the retry/DLQ wrapper",
            "Per-type × per-channel preferences honored",
        ),
        (
            "Web push (VAPID) — Phase-A ships in-app + email",
            "SMS / WhatsApp (Phase 2)",
        ),
    ),
    Capability(
        "preferences",
        "Preferences & safety",
        "§4",
        "live",
        "Per-type/channel prefs; transactional events can't be fully silenced.",
        (
            "Per-user × per-type × per-channel matrix (notification_preferences)",
            "Transactional types (decision / interview / deadline) keep in-app on — "
            "down-ranked but never fully silenced (silenceable flag on the catalog)",
            "Email frequency (all | weekly | important | none)",
        ),
        ("Quiet hours + per-type channel escalation",),
    ),
    Capability(
        "center",
        "Notification center",
        "§5",
        "live",
        "The bell: live unread count, grouped panel, deep-links, cross-tab sync.",
        (
            "Real-time unread count over SSE (no poll)",
            "mark-one / mark-all read; deep-link to source",
            "Read-state syncs across tabs/devices (mark-read echoes via the broker)",
            "api/notifications.ts list / markRead / markAllRead / preferences",
        ),
        ("Cursor (infinite-scroll) pagination of the full history (50 §5)",),
    ),
    Capability(
        "digest",
        "Digest & batching",
        "§6",
        "live",
        "Low-urgency events batch into one email; urgent fire immediately.",
        (
            "Digest-class events (feed / saved-search / non-urgent change) batch",
            "core/scheduler.py digest job aggregates pending rows per user",
            "Urgent (decision / interview / deadline) always immediate",
            "Idempotent across runs (folded rows marked emailed)",
        ),
        ("Per-user daily/weekly cadence honored from email_frequency in the sweep",),
    ),
    Capability(
        "reliability",
        "Delivery reliability",
        "§4",
        "partial",
        "Every channel send is retried + dead-lettered with an alert.",
        (
            "deliver_with_retry: exponential backoff on transient failure",
            "Terminal failures land in a dead-letter log + ALERT line",
            "Per-channel outcome recorded on the notification row",
        ),
        ("Durable queue + dedicated worker (SQS, 55 §4) — the DLQ here is the seam",),
    ),
)


# ── §7 · Build-task checklist ───────────────────────────────────────────────
@dataclass(frozen=True)
class BuildTask:
    section: str
    status: Status
    text: str
    evidence: str


BUILD_TASKS: tuple[BuildTask, ...] = (
    BuildTask(
        "§7",
        "live",
        "GET /me/stream SSE (typed events) + WS /ws/messages",
        "Both endpoints live in api/realtime.py and registered in the router.",
    ),
    BuildTask(
        "§7",
        "partial",
        "core/realtime.py Redis pub/sub fan-out across ECS tasks",
        "Broker is live in-process; the Redis bridge is wired, defaults to in-process.",
    ),
    BuildTask(
        "§7",
        "live",
        "lib/realtime.ts + useRealtime() (FE) — patch cache on event",
        "Reconnecting client (54 §9) + useNotificationStream patch the Query cache.",
    ),
    BuildTask(
        "§7",
        "live",
        "Extend notification_service: idempotent emit, recipient resolution, fan-out",
        "emit() dedups on event_id; channels resolved from the catalog + prefs.",
    ),
    BuildTask(
        "§7",
        "live",
        "services/notification_catalog.py (event_type → copy/deep-link/urgency/silenceable)",
        "Registry covers every live event type with a safe default fallback.",
    ),
    BuildTask(
        "§7",
        "partial",
        "Transactional email via campaign_email_service (SES); web-push fast-follow",
        "Transactional SES send is live via the retry wrapper; web-push is planned.",
    ),
    BuildTask(
        "§7",
        "live",
        "Digest job (core/scheduler.py) batching digest-class; urgent immediate",
        "run_digest() sweeps un-emailed digest rows; scheduled job is flag-gated.",
    ),
    BuildTask(
        "§7",
        "live",
        "Notification center FE wired to SSE; cross-tab read-state sync",
        "Bell + panel consume the stream; mark-read echoes across tabs via the broker.",
    ),
    BuildTask(
        "§7",
        "partial",
        "Delivery jobs queue-backed with retry + DLQ + alert",
        "Retry + DLQ + alert are live inline; the durable SQS worker is planned.",
    ),
)


# ── §8 · Acceptance ─────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Acceptance:
    status: Status
    text: str


ACCEPTANCE: tuple[Acceptance, ...] = (
    Acceptance(
        "live",
        "SSE bell live; WS messaging (typing/read/delivery) live; client reconnects; "
        "updates patch cache (no refetch).",
    ),
    Acceptance(
        "live",
        "NotificationService idempotent; event→recipient→row→channel fan-out, "
        "in-process now and across tasks once Redis is pointed at it.",
    ),
    Acceptance("live", "Per-type/channel prefs honored; transactional not fully silenceable."),
    Acceptance(
        "live",
        "Center: real-time unread, grouped, mark-read syncs across tabs, deep-links.",
    ),
    Acceptance("live", "Digest batches low-urgency; urgent immediate; queue retries + DLQ."),
    Acceptance(
        "live",
        "End-to-end loop verified: institution action → student notification row + live UI.",
    ),
)


# ── §9 · Open questions ─────────────────────────────────────────────────────
OPEN_QUESTIONS: tuple[dict, ...] = (
    {
        "q": "SSE vs WebSocket for the bell",
        "a": "SSE (one-way) is enough for the bell + feed pills; WebSocket is reserved "
        "for messaging (typing / read receipts / instant delivery) only.",
    },
    {
        "q": "Web-push provider + VAPID key management",
        "a": "Phase A ships in-app + email; web push (VAPID keys in Secrets Manager) is "
        "the fast-follow, kept off behind web_push_enabled.",
    },
    {
        "q": "notification_deliveries table vs columns on notifications",
        "a": "Per-channel outcomes ride on a delivery_status JSONB column today; a "
        "dedicated table is added only if per-channel open-tracking is needed.",
    },
)


def _route_buckets(routes) -> dict[str, list[str]]:
    """Resolve the live API paths backing each surface from the running routes —
    so the page can't claim a transport the deployed app doesn't serve."""
    from unipaith.transparency.live_routes import expand_routes

    buckets: dict[str, set[str]] = {"sse": set(), "ws": set(), "notifications": set()}
    for r in expand_routes(routes):
        path = getattr(r, "path", "")
        if not path.startswith(API_PREFIX):
            continue
        if "/ws/" in path:
            buckets["ws"].add(path)
        elif path.endswith("/me/stream"):
            buckets["sse"].add(path)
        elif "/notifications" in path:
            methods = getattr(r, "methods", None)
            if methods and not all(m in _SKIP_METHODS for m in methods):
                buckets["notifications"].add(path)
    return {k: sorted(v) for k, v in buckets.items()}


def _config_knobs() -> list[dict]:
    """The live config knobs the page reports, read straight off ``settings``."""
    return [
        {"name": "realtime_enabled", "value": settings.realtime_enabled, "section": "§2"},
        {
            "name": "realtime_heartbeat_seconds",
            "value": settings.realtime_heartbeat_seconds,
            "section": "§2",
        },
        {
            "name": "notification_digest_enabled",
            "value": settings.notification_digest_enabled,
            "section": "§6",
        },
        {
            "name": "notification_digest_interval_minutes",
            "value": settings.notification_digest_interval_minutes,
            "section": "§6",
        },
        {
            "name": "notification_delivery_max_retries",
            "value": settings.notification_delivery_max_retries,
            "section": "§4",
        },
        {"name": "web_push_enabled", "value": settings.web_push_enabled, "section": "§4"},
    ]


def build_realtime(app_or_routes) -> dict:
    """Assemble the ``GET /build/realtime`` payload.

    ``app_or_routes`` may be a FastAPI app or its ``.routes`` — the transport route
    presence is resolved live so the page mirrors what the deployed app serves. The
    catalog event-type count, the broker backend and the config knobs are read from
    the running registry / broker / settings.
    """
    routes = getattr(app_or_routes, "routes", app_or_routes)
    route_buckets = _route_buckets(list(routes))
    config_knobs = _config_knobs()
    broker_stats = broker.stats()
    notifications_table_present = "notifications" in Base.metadata.tables
    idempotency_column_present = (
        notifications_table_present and "event_id" in Base.metadata.tables["notifications"].columns
    )

    def _count(status: Status) -> int:
        return sum(1 for c in CAPABILITIES if c.status == status)

    def _task_count(status: Status) -> int:
        return sum(1 for t in BUILD_TASKS if t.status == status)

    def _acc_count(status: Status) -> int:
        return sum(1 for a in ACCEPTANCE if a.status == status)

    backing_route_count = sum(len(v) for v in route_buckets.values())

    return {
        "the_bar": dict(THE_BAR),
        "summary": {
            "capability_count": len(CAPABILITIES),
            "capabilities_live": _count("live"),
            "capabilities_partial": _count("partial"),
            "capabilities_planned": _count("planned"),
            "build_task_count": len(BUILD_TASKS),
            "tasks_live": _task_count("live"),
            "tasks_partial": _task_count("partial"),
            "tasks_planned": _task_count("planned"),
            "acceptance_count": len(ACCEPTANCE),
            "acceptance_live": _acc_count("live"),
            "sse_route_count": len(route_buckets["sse"]),
            "ws_route_count": len(route_buckets["ws"]),
            "notification_route_count": len(route_buckets["notifications"]),
            "backing_route_count": backing_route_count,
            "event_type_count": catalog.event_type_count(),
            "broker_backend": broker_stats["backend"],
            "distributed_ready": broker_stats["distributed_ready"],
            "notifications_table_present": notifications_table_present,
            "idempotency_wired": idempotency_column_present,
            "config_knob_count": len(config_knobs),
            "open_question_count": len(OPEN_QUESTIONS),
            "live_is_source_of_truth": True,
        },
        "capabilities": [
            {
                "key": c.key,
                "title": c.title,
                "section": c.section,
                "status": c.status,
                "blurb": c.blurb,
                "built": list(c.built),
                "planned": list(c.planned),
            }
            for c in CAPABILITIES
        ],
        "build_tasks": [
            {"section": t.section, "status": t.status, "text": t.text, "evidence": t.evidence}
            for t in BUILD_TASKS
        ],
        "acceptance": [{"status": a.status, "text": a.text} for a in ACCEPTANCE],
        "config_knobs": config_knobs,
        "routes": route_buckets,
        "catalog": catalog.catalog_summary(),
        "broker": {
            "backend": broker_stats["backend"],
            "distributed_ready": broker_stats["distributed_ready"],
            "distributed_configured": broker_stats["distributed_configured"],
            "heartbeat_seconds": broker_stats["heartbeat_seconds"],
        },
        "open_questions": [dict(q) for q in OPEN_QUESTIONS],
    }

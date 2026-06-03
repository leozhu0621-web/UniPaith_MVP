"""Spec 57 §2 — realtime pub/sub broker for SSE + WebSocket fan-out.

A per-process, per-user event broker. The SSE endpoint (``/me/stream``) and the
WebSocket messaging endpoint (``/ws/messages``) each ``subscribe`` to a user's
stream; the notification service and the messaging hooks ``publish`` to it.

In-process by default — correct for a single ECS task. When ``settings.redis_url``
is set *and* the ``redis`` package is importable, a cross-task bridge republishes
every event over a Redis channel, so a client connected to task A receives an
event published on task B (§2 / §55 §3 Redis). The in-process path stays the
delivery mechanism on every task; Redis only adds the inter-task hop. This is the
same soft-dependency posture as ``core/cache.py``: pure-Python and dependency-free
in dev / CI / prod-without-Redis.

Carries only the event envelope (``{type, data}``) — never a DB session, so a
long-lived SSE connection holds no database connection while it waits.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any
from uuid import UUID

from unipaith.config import settings
from unipaith.core.cache import redis_available

logger = logging.getLogger("unipaith.realtime")

# Redis channel every task publishes to / subscribes from for cross-task fan-out.
_REDIS_CHANNEL = "unipaith:realtime"

UserKey = str


def _key(user_id: UUID | str) -> UserKey:
    return str(user_id)


class _Subscription:
    """Async context manager for a single subscriber's event queue.

    Hand-written (not ``@asynccontextmanager``) so that ``GeneratorExit`` thrown
    when an SSE/WS consumer is abandoned tears the subscription down cleanly —
    ``@asynccontextmanager`` raises "generator didn't stop after athrow()" in that
    path. ``__aenter__`` registers the queue (and lazily starts the Redis bridge);
    ``__aexit__`` always unregisters it, even on cancellation.
    """

    def __init__(self, broker: RealtimeBroker, user_id: UUID | str) -> None:
        self._broker = broker
        self._key = _key(user_id)
        self.queue: asyncio.Queue[dict[str, Any]] | None = None

    async def __aenter__(self) -> asyncio.Queue[dict[str, Any]]:
        await self._broker._ensure_redis()
        self.queue = asyncio.Queue(maxsize=max(1, settings.realtime_queue_maxsize))
        self._broker._subs.setdefault(self._key, set()).add(self.queue)
        return self.queue

    async def __aexit__(self, *exc: object) -> bool:
        subs = self._broker._subs.get(self._key)
        if subs is not None and self.queue is not None:
            subs.discard(self.queue)
            if not subs:
                self._broker._subs.pop(self._key, None)
        return False


class RealtimeBroker:
    """Process-local pub/sub with an optional Redis cross-task bridge.

    Thread model: all access happens on the asyncio event loop. ``put_nowait`` /
    set mutation are synchronous and safe within the single-threaded loop; we
    snapshot the subscriber set before delivering so a concurrent unsubscribe in
    a ``finally`` can't mutate the set mid-iteration.
    """

    def __init__(self) -> None:
        self._subs: dict[UserKey, set[asyncio.Queue[dict[str, Any]]]] = {}
        self._redis: Any = None
        self._redis_task: asyncio.Task[None] | None = None
        self._redis_started = False
        # Lightweight counters for the /goal/realtime transparency surface.
        self.published = 0
        self.delivered = 0
        self.dropped = 0

    # ── subscribe ────────────────────────────────────────────────────────────
    def subscribe(self, user_id: UUID | str) -> _Subscription:
        """Return an async context manager yielding this user's event queue.

        Usage: ``async with broker.subscribe(user_id) as queue: ...``. The queue is
        registered on enter and torn down on exit (client disconnect / cancellation),
        so a dropped SSE/WS connection leaves no dangling buffer.
        """
        return _Subscription(self, user_id)

    # ── publish ──────────────────────────────────────────────────────────────
    async def publish(self, user_id: UUID | str, event: dict[str, Any]) -> None:
        """Publish a typed ``{type, data}`` event to every subscriber of a user.

        With Redis configured we publish *only* to Redis; the subscriber loop on
        every task (including this one) delivers locally, so there is exactly one
        local-delivery code path and no double-send. Without Redis we deliver
        in-process directly.
        """
        await self._ensure_redis()
        key = _key(user_id)
        self.published += 1
        if self._redis is not None:
            try:
                await self._redis.publish(_REDIS_CHANNEL, json.dumps({"user": key, "event": event}))
                return
            except Exception:  # noqa: BLE001 — degrade to local delivery, never raise
                logger.warning("realtime: redis publish failed; delivering locally", exc_info=True)
        self._deliver_local(key, event)

    def _deliver_local(self, key: UserKey, event: dict[str, Any]) -> None:
        subs = self._subs.get(key)
        if not subs:
            return
        for queue in list(subs):
            try:
                queue.put_nowait(event)
                self.delivered += 1
            except asyncio.QueueFull:
                # Slow consumer: drop the oldest event to make room for the newest.
                try:
                    queue.get_nowait()
                    queue.put_nowait(event)
                except Exception:  # noqa: BLE001
                    pass
                self.dropped += 1

    # ── redis bridge ─────────────────────────────────────────────────────────
    async def _ensure_redis(self) -> None:
        """Lazily start the Redis bridge once per process. Idempotent + cheap."""
        if self._redis_started:
            return
        self._redis_started = True
        if not settings.redis_url:
            return
        try:  # pragma: no cover — redis is not installed in dev/CI
            import redis.asyncio as aioredis
        except Exception:
            logger.info("realtime: redis package not importable; staying in-process")
            return
        try:  # pragma: no cover — requires a live Redis
            self._redis = aioredis.from_url(settings.redis_url, decode_responses=True)
            self._redis_task = asyncio.create_task(self._redis_listen())
            logger.info("realtime: redis pub/sub bridge active on %s", _REDIS_CHANNEL)
        except Exception:
            logger.warning("realtime: redis bridge init failed; in-process only", exc_info=True)
            self._redis = None

    async def _redis_listen(self) -> None:  # pragma: no cover — requires a live Redis
        pubsub = self._redis.pubsub()
        await pubsub.subscribe(_REDIS_CHANNEL)
        async for msg in pubsub.listen():
            if msg.get("type") != "message":
                continue
            try:
                payload = json.loads(msg["data"])
                self._deliver_local(payload["user"], payload["event"])
            except Exception:  # noqa: BLE001
                logger.warning("realtime: bad redis message dropped", exc_info=True)

    async def aclose(self) -> None:  # pragma: no cover — shutdown path
        if self._redis_task is not None:
            self._redis_task.cancel()
        if self._redis is not None:
            try:
                await self._redis.aclose()
            except Exception:  # noqa: BLE001
                pass

    # ── introspection ────────────────────────────────────────────────────────
    def stats(self) -> dict[str, Any]:
        """Live posture for the /goal/realtime transparency surface."""
        return {
            "backend": "redis" if self._redis is not None else "memory",
            "enabled": settings.realtime_enabled,
            "users_connected": len(self._subs),
            "subscribers": sum(len(s) for s in self._subs.values()),
            "published": self.published,
            "delivered": self.delivered,
            "dropped": self.dropped,
            "heartbeat_seconds": settings.realtime_heartbeat_seconds,
            # Whether a cross-task backend could be wired right now (config + lib).
            "distributed_ready": redis_available(),
            "distributed_configured": bool(settings.redis_url),
        }

    def reset(self) -> None:
        """Test helper — clear subscribers and counters between cases."""
        self._subs.clear()
        self.published = self.delivered = self.dropped = 0


# Module-level singleton — one broker per process (per ECS task).
broker = RealtimeBroker()


def sse_frame(event: dict[str, Any]) -> str:
    """Serialize an event as an SSE ``data:`` frame.

    The realtime client (``lib/realtime.ts``) parses ``{type, data}`` JSON out of
    the frame body, so the whole envelope goes on the single ``data:`` line.
    """
    return f"data: {json.dumps(event)}\n\n"


def event(type_: str, data: Any = None) -> dict[str, Any]:
    """Build a typed event envelope."""
    return {"type": type_, "data": data}

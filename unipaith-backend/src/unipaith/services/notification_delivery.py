"""Spec 57 §4 — channel delivery reliability: retry/backoff + dead-letter log.

Each channel send (today: transactional email via SES; web-push is the planned
fast-follow) runs through ``deliver_with_retry``, which retries transient failures
with exponential backoff and, on terminal failure, records the attempt in an
in-process dead-letter log and emits an ``ALERT`` log line. The happy path returns
on the first success with no sleeping.

This is the inline-with-retry stage that makes a single failed SES call non-fatal
and *observable* rather than silently lost. The durable queue / worker substrate
(§55 §4, SQS + a dedicated worker) is the planned upgrade — the DLQ here is the
seam it slots into.
"""

from __future__ import annotations

import asyncio
import logging
from collections import deque
from collections.abc import Awaitable, Callable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime

from unipaith.config import settings

logger = logging.getLogger("unipaith.notification.delivery")


@dataclass(frozen=True)
class DeadLetter:
    channel: str
    user_id: str
    event_type: str
    error: str
    attempts: int
    at: str


# Bounded in-process dead-letter log. Survives the process; a restart clears it
# (the durable SQS DLQ is the planned replacement). 500 is plenty for alerting.
_DLQ: deque[DeadLetter] = deque(maxlen=500)
_sent = 0
_failed = 0


async def deliver_with_retry(
    channel: str,
    send: Callable[[], Awaitable[bool]],
    *,
    user_id: object,
    event_type: str,
    max_retries: int | None = None,
    backoff_seconds: float | None = None,
) -> bool:
    """Run ``send`` with retry/backoff; dead-letter + alert on terminal failure.

    ``send`` returns ``True`` on success, ``False`` (or raises) on a retryable
    failure. Returns whether delivery ultimately succeeded — the caller records
    the per-channel outcome on the notification row.
    """
    global _sent, _failed  # noqa: PLW0603
    retries = settings.notification_delivery_max_retries if max_retries is None else max_retries
    retries = max(1, retries)
    backoff = (
        settings.notification_delivery_backoff_seconds
        if backoff_seconds is None
        else backoff_seconds
    )
    last_err = "send returned False"
    for attempt in range(1, retries + 1):
        try:
            if await send():
                _sent += 1
                return True
        except Exception as exc:  # noqa: BLE001 — any send error is retryable
            last_err = repr(exc)
            logger.warning(
                "notification channel=%s send attempt %d/%d failed: %s",
                channel,
                attempt,
                retries,
                exc,
            )
        if attempt < retries and backoff > 0:
            await asyncio.sleep(backoff * (2 ** (attempt - 1)))

    _failed += 1
    dead = DeadLetter(
        channel=channel,
        user_id=str(user_id),
        event_type=event_type,
        error=last_err,
        attempts=retries,
        at=datetime.now(UTC).isoformat(),
    )
    _DLQ.append(dead)
    # ALERT — picked up by the observability layer (§55 §2 structured logs).
    logger.error(
        "ALERT notification delivery dead-lettered channel=%s user=%s event=%s attempts=%d err=%s",
        channel,
        dead.user_id,
        event_type,
        retries,
        last_err,
    )
    return False


def dead_letters() -> list[dict]:
    return [asdict(d) for d in _DLQ]


def dlq_size() -> int:
    return len(_DLQ)


def delivery_stats() -> dict:
    """Live delivery posture for the /goal/realtime transparency surface."""
    total = _sent + _failed
    return {
        "sent": _sent,
        "failed": _failed,
        "dlq_size": len(_DLQ),
        "success_rate": round(_sent / total, 4) if total else 1.0,
        "max_retries": settings.notification_delivery_max_retries,
        "backoff_seconds": settings.notification_delivery_backoff_seconds,
    }


def reset() -> None:
    """Test helper — clear the DLQ and counters between cases."""
    global _sent, _failed  # noqa: PLW0603
    _DLQ.clear()
    _sent = _failed = 0

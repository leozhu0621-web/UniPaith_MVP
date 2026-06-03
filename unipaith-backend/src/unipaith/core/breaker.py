"""Spec 73 §7 — circuit breaker + retry for external calls (no 5xx under fault).

Every egress (Anthropic, embeddings, SES, S3, Stripe) should be wrapped so a slow
or failing dependency trips fast and degrades gracefully instead of propagating
as latency or a 5xx — the structural guarantee behind the AI fallback invariant
under load. This is the standalone primitive; wiring it onto each provider is the
integration step. The breaker uses an injectable clock so it is deterministically
testable, and `retry_async` takes an injectable sleep so tests run instantly.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from enum import StrEnum
from typing import TypeVar

T = TypeVar("T")


class BreakerState(StrEnum):
    CLOSED = "closed"  # normal — calls pass through
    OPEN = "open"  # tripped — calls rejected fast
    HALF_OPEN = "half_open"  # probing — one call allowed to test recovery


class CircuitOpenError(Exception):
    """Raised when a call is attempted while the breaker is open — the caller
    should degrade gracefully (rule-based fallback), never surface a 5xx."""

    def __init__(self, name: str) -> None:
        super().__init__(f"circuit '{name}' is open")
        self.name = name


class CircuitBreaker:
    def __init__(
        self,
        name: str,
        *,
        failure_threshold: int = 5,
        reset_timeout_s: float = 30.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.name = name
        self.failure_threshold = failure_threshold
        self.reset_timeout_s = reset_timeout_s
        self._clock = clock
        self._state = BreakerState.CLOSED
        self._failures = 0
        self._opened_at: float | None = None

    @property
    def state(self) -> BreakerState:
        # Lazily transition OPEN → HALF_OPEN once the cooldown has elapsed.
        if (
            self._state is BreakerState.OPEN
            and self._opened_at is not None
            and self._clock() - self._opened_at >= self.reset_timeout_s
        ):
            self._state = BreakerState.HALF_OPEN
        return self._state

    def _on_success(self) -> None:
        self._failures = 0
        self._opened_at = None
        self._state = BreakerState.CLOSED

    def _on_failure(self) -> None:
        self._failures += 1
        # A failed probe (half-open) re-opens immediately; otherwise trip at the
        # threshold.
        if self._state is BreakerState.HALF_OPEN or self._failures >= self.failure_threshold:
            self._state = BreakerState.OPEN
            self._opened_at = self._clock()

    async def call(self, fn: Callable[..., Awaitable[T]], *args, **kwargs) -> T:
        """Run an async callable under the breaker. Raises CircuitOpenError when
        open; on any exception records a failure and re-raises (the caller's
        fallback handles it); on success resets the breaker."""
        if self.state is BreakerState.OPEN:
            raise CircuitOpenError(self.name)
        try:
            result = await fn(*args, **kwargs)
        except Exception:
            self._on_failure()
            raise
        self._on_success()
        return result


async def retry_async(
    fn: Callable[..., Awaitable[T]],
    *args,
    attempts: int = 3,
    base_delay: float = 0.1,
    max_delay: float = 2.0,
    retry_on: tuple[type[BaseException], ...] = (Exception,),
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    **kwargs,
) -> T:
    """Retry an async callable with capped exponential backoff. Re-raises the
    last exception after exhausting attempts. `sleep` is injectable so tests run
    with zero real delay."""
    last_exc: BaseException | None = None
    for i in range(attempts):
        try:
            return await fn(*args, **kwargs)
        except retry_on as exc:
            last_exc = exc
            if i < attempts - 1:
                await sleep(min(max_delay, base_delay * (2**i)))
    assert last_exc is not None  # attempts >= 1 guarantees a raise above
    raise last_exc

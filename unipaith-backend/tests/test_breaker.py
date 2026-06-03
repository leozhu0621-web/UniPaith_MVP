"""Spec 73 §7 — circuit breaker + retry. Deterministic (controlled clock, no-op sleep)."""

from __future__ import annotations

import pytest

from unipaith.core.breaker import (
    BreakerState,
    CircuitBreaker,
    CircuitOpenError,
    retry_async,
)


class _Clock:
    def __init__(self) -> None:
        self.t = 0.0

    def __call__(self) -> float:
        return self.t

    def advance(self, s: float) -> None:
        self.t += s


async def _fail() -> str:
    raise RuntimeError("boom")


async def _ok() -> str:
    return "ok"


async def _nosleep(_: float) -> None:
    return None


@pytest.mark.asyncio
async def test_breaker_opens_after_threshold_and_rejects_fast():
    cb = CircuitBreaker("x", failure_threshold=3, clock=_Clock())
    for _ in range(3):
        with pytest.raises(RuntimeError):
            await cb.call(_fail)
    assert cb.state is BreakerState.OPEN
    # Open → the wrapped call is rejected without ever running.
    with pytest.raises(CircuitOpenError):
        await cb.call(_ok)


@pytest.mark.asyncio
async def test_breaker_recovers_via_half_open():
    clk = _Clock()
    cb = CircuitBreaker("x", failure_threshold=2, reset_timeout_s=10, clock=clk)
    for _ in range(2):
        with pytest.raises(RuntimeError):
            await cb.call(_fail)
    assert cb.state is BreakerState.OPEN
    clk.advance(11)  # cooldown elapsed
    assert cb.state is BreakerState.HALF_OPEN
    assert await cb.call(_ok) == "ok"  # successful probe
    assert cb.state is BreakerState.CLOSED


@pytest.mark.asyncio
async def test_half_open_failure_reopens():
    clk = _Clock()
    cb = CircuitBreaker("x", failure_threshold=2, reset_timeout_s=10, clock=clk)
    for _ in range(2):
        with pytest.raises(RuntimeError):
            await cb.call(_fail)
    clk.advance(11)
    assert cb.state is BreakerState.HALF_OPEN
    with pytest.raises(RuntimeError):
        await cb.call(_fail)  # failed probe re-opens immediately
    assert cb.state is BreakerState.OPEN


@pytest.mark.asyncio
async def test_success_resets_failures_below_threshold():
    cb = CircuitBreaker("x", failure_threshold=3)
    with pytest.raises(RuntimeError):
        await cb.call(_fail)
    assert await cb.call(_ok) == "ok"  # success resets the failure counter
    for _ in range(2):
        with pytest.raises(RuntimeError):
            await cb.call(_fail)
    assert cb.state is BreakerState.CLOSED  # 2 < 3, did not re-trip


@pytest.mark.asyncio
async def test_retry_async_succeeds_after_transient_failures():
    calls = {"n": 0}

    async def flaky() -> str:
        calls["n"] += 1
        if calls["n"] < 3:
            raise RuntimeError("transient")
        return "done"

    assert await retry_async(flaky, attempts=3, sleep=_nosleep) == "done"
    assert calls["n"] == 3


@pytest.mark.asyncio
async def test_retry_async_raises_after_exhaustion():
    with pytest.raises(RuntimeError):
        await retry_async(_fail, attempts=2, sleep=_nosleep)

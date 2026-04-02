from __future__ import annotations

from collections import deque
from time import monotonic
from typing import Any


class _MetricSeries:
    def __init__(self, maxlen: int = 5000) -> None:
        self.latencies_ms: deque[float] = deque(maxlen=maxlen)
        self.success: int = 0
        self.error: int = 0
        self.timeouts: int = 0

    def record(self, *, latency_ms: float, ok: bool, timed_out: bool = False) -> None:
        self.latencies_ms.append(latency_ms)
        if ok:
            self.success += 1
        else:
            self.error += 1
        if timed_out:
            self.timeouts += 1

    def snapshot(self) -> dict[str, Any]:
        values = sorted(self.latencies_ms)
        p95 = 0.0
        if values:
            idx = min(len(values) - 1, int(len(values) * 0.95))
            p95 = values[idx]
        return {
            "count": len(values),
            "success": self.success,
            "error": self.error,
            "timeouts": self.timeouts,
            "p95_ms": round(p95, 2),
        }


_llm_metrics = _MetricSeries()
_embedding_metrics = _MetricSeries()
_self_driving_metrics = _MetricSeries()
_ml_evaluation_metrics = _MetricSeries()
_ml_training_metrics = _MetricSeries()


def start_timer() -> float:
    return monotonic()


def record_llm(started: float, ok: bool, timed_out: bool = False) -> None:
    _llm_metrics.record(latency_ms=(monotonic() - started) * 1000, ok=ok, timed_out=timed_out)


def record_embedding(started: float, ok: bool, timed_out: bool = False) -> None:
    _embedding_metrics.record(latency_ms=(monotonic() - started) * 1000, ok=ok, timed_out=timed_out)


def record_self_driving(started: float, ok: bool, timed_out: bool = False) -> None:
    _self_driving_metrics.record(
        latency_ms=(monotonic() - started) * 1000, ok=ok, timed_out=timed_out
    )


def record_ml_evaluation(started: float, ok: bool, timed_out: bool = False) -> None:
    _ml_evaluation_metrics.record(
        latency_ms=(monotonic() - started) * 1000, ok=ok, timed_out=timed_out
    )


def record_ml_training(started: float, ok: bool, timed_out: bool = False) -> None:
    _ml_training_metrics.record(
        latency_ms=(monotonic() - started) * 1000, ok=ok, timed_out=timed_out
    )


def slo_snapshot() -> dict[str, Any]:
    return {
        "llm": _llm_metrics.snapshot(),
        "embedding": _embedding_metrics.snapshot(),
        "self_driving_tick": _self_driving_metrics.snapshot(),
        "ml_evaluation": _ml_evaluation_metrics.snapshot(),
        "ml_training": _ml_training_metrics.snapshot(),
    }

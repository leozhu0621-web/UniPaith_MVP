"""
GPU cost tracking and budget enforcement.

Tracks 70B instance uptime, calculates estimated costs,
and enforces monthly budget caps to prevent runaway spending.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import UTC, datetime

from unipaith.config import settings

logger = logging.getLogger("unipaith.cost_tracker")


@dataclass
class UsageSession:
    """A single start→stop session for a GPU instance."""

    instance_type: str  # "8b" or "70b"
    started_at: float  # monotonic time
    stopped_at: float | None = None

    @property
    def duration_hours(self) -> float:
        end = self.stopped_at or time.monotonic()
        return (end - self.started_at) / 3600

    @property
    def started_at_utc(self) -> datetime:
        # Convert monotonic to wall clock (approximate)
        offset = time.time() - time.monotonic()
        return datetime.fromtimestamp(self.started_at + offset, tz=UTC)


class CostTracker:
    """Track GPU costs in-memory. Resets on process restart.

    For MVP this is sufficient — persistent tracking would use a DB table.
    The 8B instance is always-on so its cost is fixed (~$730/month).
    We mainly track 70B on-demand usage which is the variable cost.
    """

    def __init__(self):
        self._sessions: list[UsageSession] = []
        self._active_session: UsageSession | None = None
        self._month_start = self._current_month_start()

    @staticmethod
    def _current_month_start() -> datetime:
        now = datetime.now(UTC)
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    def record_start(self, instance_type: str = "70b") -> None:
        if self._active_session and self._active_session.instance_type == instance_type:
            return  # Already tracking
        session = UsageSession(instance_type=instance_type, started_at=time.monotonic())
        self._active_session = session
        self._sessions.append(session)
        logger.info("Cost tracker: %s instance started", instance_type)

    def record_stop(self, instance_type: str = "70b") -> None:
        if self._active_session and self._active_session.instance_type == instance_type:
            self._active_session.stopped_at = time.monotonic()
            hours = self._active_session.duration_hours
            logger.info("Cost tracker: %s instance stopped (%.2f hours)", instance_type, hours)
            self._active_session = None

    def _get_month_sessions(self) -> list[UsageSession]:
        """Get sessions from current billing month."""
        month_start_mono = (
            time.monotonic() - (datetime.now(UTC) - self._month_start).total_seconds()
        )
        return [s for s in self._sessions if s.started_at >= month_start_mono]

    def get_70b_hours_today(self) -> float:
        """Total 70B hours used today."""
        (
            time.monotonic()
            - (
                datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
                - datetime.now(UTC)
            ).total_seconds()
        )
        # Simpler: just count last 24 hours
        cutoff = time.monotonic() - 86400
        return sum(
            s.duration_hours
            for s in self._sessions
            if s.instance_type == "70b" and s.started_at >= cutoff
        )

    def get_70b_hours_month(self) -> float:
        return sum(s.duration_hours for s in self._get_month_sessions() if s.instance_type == "70b")

    def get_estimated_monthly_cost(self) -> float:
        """Estimated total cost: fixed 8B + variable 70B."""
        # 8B is always-on, cost is fixed at ~730/month
        hours_in_month = 730  # approximate
        cost_8b = settings.gpu_8b_hourly_cost * hours_in_month
        cost_70b = self.get_70b_hours_month() * settings.gpu_70b_hourly_cost
        return cost_8b + cost_70b

    def get_70b_monthly_cost(self) -> float:
        return self.get_70b_hours_month() * settings.gpu_70b_hourly_cost

    def is_budget_exceeded(self) -> bool:
        return self.get_estimated_monthly_cost() >= settings.gpu_monthly_budget_cap

    def is_daily_limit_exceeded(self) -> bool:
        return self.get_70b_hours_today() >= settings.gpu_70b_max_daily_hours

    def get_usage_summary(self) -> dict:
        """Full usage summary for the admin API."""
        cost_70b_month = self.get_70b_monthly_cost()
        cost_8b_month = settings.gpu_8b_hourly_cost * 730
        total_month = cost_8b_month + cost_70b_month
        return {
            "today": {
                "70b_hours": round(self.get_70b_hours_today(), 2),
                "70b_cost": round(self.get_70b_hours_today() * settings.gpu_70b_hourly_cost, 2),
            },
            "month": {
                "8b_cost_fixed": round(cost_8b_month, 2),
                "70b_hours": round(self.get_70b_hours_month(), 2),
                "70b_cost": round(cost_70b_month, 2),
                "total_estimated": round(total_month, 2),
            },
            "budget": {
                "cap": settings.gpu_monthly_budget_cap,
                "remaining": round(max(0, settings.gpu_monthly_budget_cap - total_month), 2),
                "exceeded": self.is_budget_exceeded(),
            },
            "daily_limit": {
                "max_hours": settings.gpu_70b_max_daily_hours,
                "used_hours": round(self.get_70b_hours_today(), 2),
                "exceeded": self.is_daily_limit_exceeded(),
            },
            "gpu_mode": settings.gpu_mode,
        }


# Singleton
_tracker: CostTracker | None = None


def get_cost_tracker() -> CostTracker:
    global _tracker
    if _tracker is None:
        _tracker = CostTracker()
    return _tracker

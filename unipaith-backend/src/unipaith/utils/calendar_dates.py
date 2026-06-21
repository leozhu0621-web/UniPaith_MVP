from __future__ import annotations

from datetime import date


def business_today() -> date:
    """Current local calendar date for date-only business fields."""
    return date.today()

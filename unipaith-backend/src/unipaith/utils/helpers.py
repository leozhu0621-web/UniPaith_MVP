"""Shared utility functions used across services."""
from __future__ import annotations

import math


def paginate(total: int, page: int, page_size: int) -> dict:
    """Compute pagination metadata.

    Returns dict with: total, page, page_size, total_pages, offset.
    """
    total_pages = max(1, math.ceil(total / page_size))
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "offset": (page - 1) * page_size,
    }


# GPA scale normalization — maps any scale to 0.0-1.0
_GPA_SCALES: dict[str, float] = {
    "4.0": 4.0,
    "5.0": 5.0,
    "7.0": 7.0,
    "10.0": 10.0,
    "percentage": 100.0,
    "ib": 45.0,
}


def normalize_gpa(gpa: float, scale: str) -> float:
    """Normalize a GPA value to a 0.0-1.0 range based on scale."""
    max_val = _GPA_SCALES.get(scale.lower(), 4.0)
    return min(1.0, max(0.0, gpa / max_val))


# Test score normalization — maps any test score to 0.0-1.0
_TEST_SCORE_MAX: dict[str, float] = {
    "sat": 1600.0,
    "gre": 340.0,
    "gmat": 800.0,
    "toefl": 120.0,
    "ielts": 9.0,
    "act": 36.0,
    "ap": 5.0,
    "ib": 45.0,
    "lsat": 180.0,
    "mcat": 528.0,
    "duolingo": 160.0,
}


def normalize_test_score(test_type: str, score: float) -> float:
    """Normalize a test score to a 0.0-1.0 range."""
    max_val = _TEST_SCORE_MAX.get(test_type.lower(), 100.0)
    return min(1.0, max(0.0, score / max_val))

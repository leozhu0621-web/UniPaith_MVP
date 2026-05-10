"""Phase D1 — AI feedback service unit tests (no DB).

Pure-Python coverage of dataclasses, allowed-value constants, and
helper math. The DB-touching upsert / digest paths get integration
tests in test_ai_feedback_api.py.
"""

from __future__ import annotations

from datetime import UTC, datetime

from unipaith.services.ai_feedback_service import (
    ALLOWED_SURFACES,
    ALLOWED_VOTES,
    FeedbackBreakdown,
    WeeklyDigest,
)

# ── Constants ──────────────────────────────────────────────────────────────


def test_allowed_votes_match_db_check() -> None:
    """If you change this list, also update the DB CHECK constraint
    AND the API schema description string."""
    assert ALLOWED_VOTES == ("up", "down", "regenerate", "not_right")


def test_allowed_surfaces_includes_all_workshop_variants() -> None:
    """Each LLM surface needs a feedback channel — adding a new agent
    means adding a surface here AND in the DB CHECK constraint."""
    expected = {
        "orchestrator_turn",
        "extractor_signal",
        "rationale",
        "workshop_essay",
        "workshop_interview",
        "workshop_test_prep",
        "match_card",
        "other",
    }
    assert set(ALLOWED_SURFACES) == expected


# ── FeedbackBreakdown ──────────────────────────────────────────────────────


def test_feedback_breakdown_negative_rate_zero_when_no_total() -> None:
    bd = FeedbackBreakdown(
        surface="orchestrator_turn", total=0, up=0, down=0, regenerate=0, not_right=0
    )
    assert bd.negative_rate == 0.0


def test_feedback_breakdown_negative_rate_calculation() -> None:
    bd = FeedbackBreakdown(
        surface="orchestrator_turn",
        total=10,
        up=4,
        down=3,
        regenerate=2,
        not_right=1,
    )
    # bad = 3+2+1 = 6; rate = 6/10 = 0.6
    assert bd.negative_rate == 0.6


def test_feedback_breakdown_all_positive() -> None:
    bd = FeedbackBreakdown(
        surface="rationale", total=5, up=5, down=0, regenerate=0, not_right=0
    )
    assert bd.negative_rate == 0.0


def test_feedback_breakdown_all_negative() -> None:
    bd = FeedbackBreakdown(
        surface="match_card", total=3, up=0, down=2, regenerate=1, not_right=0
    )
    assert bd.negative_rate == 1.0


# ── WeeklyDigest ───────────────────────────────────────────────────────────


def test_weekly_digest_default_empty() -> None:
    now = datetime.now(UTC)
    digest = WeeklyDigest(period_start=now, period_end=now)
    assert digest.breakdowns == []
    assert digest.top_negative_examples == []
    assert digest.safety_incident_count == 0
    assert digest.safety_incident_breakdown == {}
    assert digest.low_confidence_turns == 0


def test_weekly_digest_aggregates_breakdowns() -> None:
    now = datetime.now(UTC)
    digest = WeeklyDigest(
        period_start=now,
        period_end=now,
        breakdowns=[
            FeedbackBreakdown(
                surface="orchestrator_turn",
                total=20,
                up=15,
                down=3,
                regenerate=1,
                not_right=1,
            ),
            FeedbackBreakdown(
                surface="rationale",
                total=10,
                up=5,
                down=4,
                regenerate=1,
                not_right=0,
            ),
        ],
        safety_incident_count=2,
        safety_incident_breakdown={"workshop_generation_leak": 2},
        low_confidence_turns=8,
    )
    assert len(digest.breakdowns) == 2
    assert digest.breakdowns[0].surface == "orchestrator_turn"
    # negative_rate spot check
    assert abs(digest.breakdowns[0].negative_rate - 0.25) < 1e-9
    assert abs(digest.breakdowns[1].negative_rate - 0.5) < 1e-9

"""Phase A3.2 — GOALS + NEEDS track evaluator tests.

Pure-Python; no DB or LLM. Verifies the deterministic exit conditions
the validator dispatches to for `validate_track('goals'|'needs')`.
"""

from __future__ import annotations

from decimal import Decimal

from unipaith.ai.state import (
    GOAL_CATEGORIES,
    MASLOW_LEVELS,
    GoalEntry,
    NeedEntry,
    StudentSnapshot,
    evaluate_goals_track,
    evaluate_needs_track,
)

# ── GOALS track ────────────────────────────────────────────────────────────


def test_goals_empty_zero_completion() -> None:
    v = evaluate_goals_track(StudentSnapshot())
    assert v.layer_complete is False
    assert v.completion_pct == Decimal("0")
    assert set(v.missing_signals) == {f"goals.{c}" for c in GOAL_CATEGORIES}
    # Probe should be the academic opener (first by priority).
    assert v.next_probe_hint is not None
    assert "academic" in v.next_probe_hint.lower()


def test_goals_one_complete_category() -> None:
    snap = StudentSnapshot(
        goals=[
            GoalEntry(
                category="academic",
                specific="MPH from a top program",
                measurable="degree confirmation",
                achievable="GRE in target range",
                relevant="aligns with health-ministry plan",
                time_bound="2027",
                completeness=1.0,
                user_confirmed=True,
            ),
        ]
    )
    v = evaluate_goals_track(snap)
    assert v.layer_complete is False
    # 1 of 3 categories satisfied.
    assert v.completion_pct == Decimal("0.333")
    assert "goals.academic" not in v.missing_signals
    assert "goals.social" in v.missing_signals
    assert "goals.personal" in v.missing_signals


def test_goals_partial_goal_doesnt_count_until_smart_complete() -> None:
    """A partial (completeness < 1.0) goal does NOT satisfy the gate; the
    probe should ask for the missing field rather than restarting."""
    snap = StudentSnapshot(
        goals=[
            GoalEntry(
                category="academic",
                specific="get a doctorate",
                completeness=0.4,  # only specific filled
                user_confirmed=False,
            ),
        ]
    )
    v = evaluate_goals_track(snap)
    assert v.layer_complete is False
    # Probe should target the first missing SMART field on the draft.
    assert v.next_probe_hint is not None
    assert "measurable" in v.next_probe_hint.lower() or "signal" in v.next_probe_hint.lower()


def test_goals_unconfirmed_doesnt_count() -> None:
    """Even a fully-SMART goal needs user_confirmed=True."""
    snap = StudentSnapshot(
        goals=[
            GoalEntry(
                category="academic",
                specific="MPH",
                measurable="degree",
                achievable="ok",
                relevant="ok",
                time_bound="2027",
                completeness=1.0,
                user_confirmed=False,  # NOT confirmed
            )
        ]
    )
    v = evaluate_goals_track(snap)
    assert v.layer_complete is False


def test_goals_full_complete() -> None:
    snap = StudentSnapshot(
        goals=[
            GoalEntry(
                category=cat,
                specific=f"{cat}-spec",
                measurable="m",
                achievable="a",
                relevant="r",
                time_bound="2027",
                completeness=1.0,
                user_confirmed=True,
            )
            for cat in ("academic", "social", "personal")
        ]
    )
    v = evaluate_goals_track(snap)
    assert v.layer_complete is True
    assert v.completion_pct == Decimal("1.000")
    assert v.missing_signals == []


# ── NEEDS track ────────────────────────────────────────────────────────────


def test_needs_empty_zero_completion() -> None:
    v = evaluate_needs_track(StudentSnapshot())
    assert v.layer_complete is False
    assert v.completion_pct == Decimal("0")
    assert set(v.missing_signals) == {f"needs.{lv}" for lv in MASLOW_LEVELS}


def test_needs_partial_coverage() -> None:
    snap = StudentSnapshot(
        needs=[
            NeedEntry(maslow_level="safety", signal="visa_support"),
            NeedEntry(maslow_level="social", signal="near_family"),
        ]
    )
    v = evaluate_needs_track(snap)
    assert v.layer_complete is False
    # 2 of 5 Maslow levels covered.
    assert v.completion_pct == Decimal("0.400")
    assert "needs.physiological" in v.missing_signals


def test_needs_full_complete() -> None:
    snap = StudentSnapshot(
        needs=[
            NeedEntry(maslow_level=lv, signal=f"{lv}-tag")
            for lv in MASLOW_LEVELS
        ]
    )
    v = evaluate_needs_track(snap)
    assert v.layer_complete is True
    assert v.completion_pct == Decimal("1.000")


def test_needs_signal_required() -> None:
    """An entry without a signal tag doesn't count — guards against the
    extractor returning a stub need with maslow_level only."""
    snap = StudentSnapshot(
        needs=[
            NeedEntry(maslow_level="safety", signal=""),
        ]
    )
    v = evaluate_needs_track(snap)
    assert v.layer_complete is False
    assert v.completion_pct == Decimal("0")


def test_needs_probe_targets_first_missing_level() -> None:
    """When no needs are captured, the first probe should be physiological
    (Maslow ordering)."""
    v = evaluate_needs_track(StudentSnapshot())
    assert v.next_probe_hint is not None
    assert (
        "physical" in v.next_probe_hint.lower()
        or "basics" in v.next_probe_hint.lower()
        or "housing" in v.next_probe_hint.lower()
    )


def test_snapshot_helpers_for_goals_and_needs() -> None:
    snap = StudentSnapshot(
        goals=[
            GoalEntry(
                category="academic",
                specific="MPH",
                measurable="m",
                achievable="a",
                relevant="r",
                time_bound="2027",
                completeness=1.0,
                user_confirmed=True,
            )
        ],
        needs=[
            NeedEntry(maslow_level="safety", signal="visa_support"),
            NeedEntry(maslow_level="safety", signal="lgbtq_safety"),
        ],
    )
    by_cat = snap.goals_by_category()
    assert "academic" in by_cat
    assert snap.complete_goal_categories() == {"academic"}
    by_lv = snap.needs_by_level()
    assert len(by_lv["safety"]) == 2
    assert snap.covered_maslow_levels() == {"safety"}

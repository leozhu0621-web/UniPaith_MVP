"""Phase A3.2 — Snapshot reconstruction tests for goals + needs."""

from __future__ import annotations

from unipaith.ai.artifacts import snapshot_from_extracted_signals_history


def test_snapshot_goals_extracted_with_completeness() -> None:
    history = [
        {
            "goals": [
                {
                    "category": "academic",
                    "specific": "MPH",
                    "measurable": "degree",
                    "time_bound": "2027",
                    "completeness": 0.6,
                }
            ]
        }
    ]
    snap = snapshot_from_extracted_signals_history(history)
    assert len(snap.goals) == 1
    assert snap.goals[0].category == "academic"
    assert snap.goals[0].completeness == 0.6
    # Partial → not in complete_goal_categories
    assert snap.complete_goal_categories() == set()


def test_snapshot_goals_dedup_and_refine_keeps_higher_completeness() -> None:
    """A second turn refining the same goal should keep the higher
    completeness, not duplicate."""
    history = [
        {"goals": [{"category": "academic", "specific": "MPH", "completeness": 0.4}]},
        {
            "goals": [
                {
                    "category": "academic",
                    "specific": "MPH",
                    "measurable": "m",
                    "achievable": "a",
                    "relevant": "r",
                    "time_bound": "2027",
                    "completeness": 1.0,
                    "user_confirmed": True,
                }
            ]
        },
    ]
    snap = snapshot_from_extracted_signals_history(history)
    assert len(snap.goals) == 1
    assert snap.goals[0].completeness == 1.0
    assert snap.goals[0].user_confirmed is True


def test_snapshot_goals_drops_invalid_category() -> None:
    history = [
        {"goals": [{"category": "academic", "specific": "MPH", "completeness": 1.0}]},
        {"goals": [{"category": "bogus", "specific": "X", "completeness": 1.0}]},
    ]
    snap = snapshot_from_extracted_signals_history(history)
    assert len(snap.goals) == 1
    assert snap.goals[0].category == "academic"


def test_snapshot_goals_clamps_completeness_to_unit() -> None:
    history = [
        {"goals": [{"category": "academic", "specific": "MPH", "completeness": 5.0}]}
    ]
    snap = snapshot_from_extracted_signals_history(history)
    assert snap.goals[0].completeness == 1.0


def test_snapshot_needs_extracted_with_severity_int() -> None:
    history = [
        {
            "needs": [
                {
                    "maslow_level": "safety",
                    "signal": "visa_support",
                    "severity": 5,
                    "evidence": "I need a sponsor",
                }
            ]
        }
    ]
    snap = snapshot_from_extracted_signals_history(history)
    assert len(snap.needs) == 1
    assert snap.needs[0].severity == 5
    assert snap.needs[0].signal == "visa_support"


def test_snapshot_needs_dedup_by_level_and_signal() -> None:
    history = [
        {"needs": [{"maslow_level": "safety", "signal": "visa_support"}]},
        {"needs": [{"maslow_level": "safety", "signal": "visa_support"}]},  # dup
        {"needs": [{"maslow_level": "safety", "signal": "lgbtq_safety"}]},  # distinct
    ]
    snap = snapshot_from_extracted_signals_history(history)
    assert len(snap.needs) == 2


def test_snapshot_needs_drops_invalid_maslow_level() -> None:
    history = [
        {"needs": [{"maslow_level": "esteem", "signal": "scholarship"}]},  # wrong key
        {"needs": [{"maslow_level": "self_esteem", "signal": "scholarship"}]},
    ]
    snap = snapshot_from_extracted_signals_history(history)
    assert len(snap.needs) == 1
    assert snap.needs[0].maslow_level == "self_esteem"


def test_snapshot_needs_drops_missing_signal_or_level() -> None:
    history = [
        {"needs": [{"maslow_level": "safety"}]},  # no signal
        {"needs": [{"signal": "x"}]},  # no level
        {"needs": [{"maslow_level": "social", "signal": "near_family"}]},
    ]
    snap = snapshot_from_extracted_signals_history(history)
    assert len(snap.needs) == 1


def test_snapshot_needs_handles_garbage_severity() -> None:
    history = [
        {"needs": [{"maslow_level": "safety", "signal": "x", "severity": "five"}]},
    ]
    snap = snapshot_from_extracted_signals_history(history)
    assert snap.needs[0].severity is None  # silently dropped, not crashed

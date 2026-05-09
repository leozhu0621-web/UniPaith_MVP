"""Phase A2 — State machine unit tests.

The state machine is pure-Python; these tests don't need a DB or LLM.
They cover:

  - BASIC layer exit conditions: each required field independently
  - GPA-or-test-score short-circuit
  - completion_pct math
  - probe selection priority
  - empty / fully-populated edge cases
"""

from __future__ import annotations

from decimal import Decimal

from unipaith.ai.state import (
    BASIC_FIELD_WEIGHT,
    BASIC_REQUIRED_FIELDS,
    StudentSnapshot,
    basic_layer_completion,
    evaluate_basic_layer,
)


def test_empty_snapshot_zero_completion_all_missing() -> None:
    snap = StudentSnapshot()
    v = evaluate_basic_layer(snap)
    assert v.layer_complete is False
    assert v.completion_pct == Decimal("0.000")
    assert set(v.missing_signals) == BASIC_REQUIRED_FIELDS


def test_full_basic_completion_advances() -> None:
    snap = StudentSnapshot(
        age=20,
        education_level="bachelors",
        gpa=3.8,
        location_prefs=["US-NY"],
        first_gen=True,
    )
    v = evaluate_basic_layer(snap)
    assert v.layer_complete is True
    assert v.completion_pct == Decimal("1.000")
    assert v.missing_signals == []
    assert v.next_probe_hint is None


def test_gpa_or_test_score_either_satisfies() -> None:
    """A test score alone should satisfy the GPA-or-test-score field."""
    snap = StudentSnapshot(
        age=22,
        education_level="bachelors",
        test_scores=[{"type": "GRE", "score": 332}],
        location_prefs=["US-CA"],
        first_gen=False,
    )
    v = evaluate_basic_layer(snap)
    assert v.layer_complete is True
    assert v.completion_pct == Decimal("1.000")


def test_location_avoid_alone_counts_as_pref() -> None:
    """A student who only said 'I don't want to go to X' has expressed
    a location preference (just a negative one)."""
    snap = StudentSnapshot(
        age=18,
        education_level="high_school",
        gpa=3.5,
        location_avoid=["US-TX"],
        first_gen=True,
    )
    v = evaluate_basic_layer(snap)
    assert v.layer_complete is True


def test_partial_completion_pct_math() -> None:
    """3 of 5 fields present → completion ~0.60."""
    snap = StudentSnapshot(
        age=19,
        education_level="bachelors",
        gpa=3.0,
        # location + first_gen missing
    )
    v = evaluate_basic_layer(snap)
    assert v.layer_complete is False
    expected = (BASIC_FIELD_WEIGHT * 3).quantize(Decimal("0.001"))
    assert v.completion_pct == expected
    assert set(v.missing_signals) == {"location_pref", "first_gen"}


def test_probe_priority_education_first() -> None:
    """When everything is missing, education_level is the first probe —
    it's the most natural opener, less personal than age."""
    v = evaluate_basic_layer(StudentSnapshot())
    assert v.next_probe_hint is not None
    assert "education" in v.next_probe_hint.lower()


def test_probe_priority_falls_through() -> None:
    """If education + age are known, the next probe should be location."""
    snap = StudentSnapshot(age=20, education_level="bachelors")
    v = evaluate_basic_layer(snap)
    assert v.next_probe_hint is not None
    assert "where" in v.next_probe_hint.lower() or "location" in v.next_probe_hint.lower()


def test_basic_layer_completion_helper_returns_just_pct() -> None:
    snap = StudentSnapshot(age=20, education_level="bachelors", gpa=3.5)
    pct = basic_layer_completion(snap)
    assert isinstance(pct, Decimal)
    assert pct == (BASIC_FIELD_WEIGHT * 3).quantize(Decimal("0.001"))


def test_evidence_count_reflects_known_fields() -> None:
    snap = StudentSnapshot(
        age=20,
        education_level="bachelors",
        gpa=3.7,
        location_prefs=["US-NY"],
        first_gen=True,
    )
    v = evaluate_basic_layer(snap)
    # All 5 required fields counted.
    assert sum(v.evidence_count.values()) == len(BASIC_REQUIRED_FIELDS)

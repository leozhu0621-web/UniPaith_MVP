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


# ── Phase A3 — PERSONALITY layer ───────────────────────────────────────────


def test_personality_empty_zero_completion() -> None:
    from unipaith.ai.state import evaluate_personality_layer

    v = evaluate_personality_layer(StudentSnapshot())
    assert v.layer_complete is False
    assert v.completion_pct == Decimal("0")
    assert v.next_probe_hint is not None


def test_personality_three_facets_below_threshold() -> None:
    """Below the ≥4 facet bar even with three solid signals."""
    from unipaith.ai.state import PersonalityEntry, evaluate_personality_layer

    snap = StudentSnapshot(
        personality=[
            PersonalityEntry(facet="interest", value="ml", evidence="I love ml"),
            PersonalityEntry(facet="peer_style", value="small", evidence="small groups"),
            PersonalityEntry(facet="passion", value="teaching", evidence="i teach"),
        ]
    )
    v = evaluate_personality_layer(snap)
    assert v.layer_complete is False
    assert v.completion_pct == Decimal("0.75")


def test_personality_four_facets_complete() -> None:
    from unipaith.ai.state import PersonalityEntry, evaluate_personality_layer

    snap = StudentSnapshot(
        personality=[
            PersonalityEntry(facet="interest", value="ml", evidence="ev1"),
            PersonalityEntry(facet="peer_style", value="small", evidence="ev2"),
            PersonalityEntry(facet="passion", value="teaching", evidence="ev3"),
            PersonalityEntry(facet="connection_style", value="mentor", evidence="ev4"),
        ]
    )
    v = evaluate_personality_layer(snap)
    assert v.layer_complete is True
    assert v.completion_pct == Decimal("1.000")


def test_personality_no_evidence_doesnt_count() -> None:
    """An entry with no evidence quote doesn't satisfy the framework's
    requirement (it's the same as not extracting it at all)."""
    from unipaith.ai.state import PersonalityEntry, evaluate_personality_layer

    snap = StudentSnapshot(
        personality=[
            PersonalityEntry(facet="interest", value="ml", evidence="ev1"),
            PersonalityEntry(facet="peer_style", value="small", evidence=""),
            PersonalityEntry(facet="passion", value="", evidence="ev3"),
            PersonalityEntry(facet="connection_style", value="mentor", evidence="ev4"),
        ]
    )
    v = evaluate_personality_layer(snap)
    # Only 2 valid (interest, connection_style) → not complete.
    assert v.layer_complete is False


# ── Phase A3 — IDENTITY layer ──────────────────────────────────────────────


def test_identity_empty_zero_completion() -> None:
    from unipaith.ai.state import evaluate_identity_layer

    v = evaluate_identity_layer(StudentSnapshot())
    assert v.layer_complete is False
    assert v.completion_pct == Decimal("0")
    # Three independent gates should all be missing.
    assert len(v.missing_signals) == 3


def test_identity_three_value_claims_no_self_awareness_incomplete() -> None:
    from unipaith.ai.state import IdentityClaim, evaluate_identity_layer

    snap = StudentSnapshot(
        identity_claims=[
            IdentityClaim(facet="value", claim="c1", evidence="e1", user_confirmed=True),
            IdentityClaim(facet="belief", claim="c2", evidence="e2", user_confirmed=True),
            IdentityClaim(facet="view", claim="c3", evidence="e3"),
        ]
    )
    v = evaluate_identity_layer(snap)
    # Has 3 value/belief, has 2 confirmed, but no self_awareness moment.
    assert v.layer_complete is False
    assert any("self_awareness" in m for m in v.missing_signals)


def test_identity_full_complete() -> None:
    from unipaith.ai.state import IdentityClaim, evaluate_identity_layer

    snap = StudentSnapshot(
        identity_claims=[
            IdentityClaim(facet="value", claim="c1", evidence="e1", user_confirmed=True),
            IdentityClaim(facet="belief", claim="c2", evidence="e2", user_confirmed=True),
            IdentityClaim(facet="view", claim="c3", evidence="e3"),
            IdentityClaim(facet="self_awareness", claim="c4", evidence="e4"),
        ]
    )
    v = evaluate_identity_layer(snap)
    assert v.layer_complete is True
    assert v.completion_pct == Decimal("1.000")


def test_identity_completion_pct_is_min_of_three_gates() -> None:
    """If one gate is at 33% and others at 100%, layer pct should be 33%."""
    from unipaith.ai.state import IdentityClaim, evaluate_identity_layer

    snap = StudentSnapshot(
        identity_claims=[
            IdentityClaim(facet="value", claim="c1", evidence="e1", user_confirmed=True),
            IdentityClaim(facet="value", claim="c2", evidence="e2", user_confirmed=True),
            IdentityClaim(facet="self_awareness", claim="c3", evidence="e3"),
            # 2/3 value-or-belief, 1/1 self_awareness, 2/2 confirmed
            # → min(0.667, 1.0, 1.0) = 0.667
        ]
    )
    v = evaluate_identity_layer(snap)
    assert v.completion_pct == Decimal("0.667")
    assert v.layer_complete is False


def test_identity_dedup_on_claim_evidence_pair() -> None:
    """Two entries with the same (claim, evidence) count as one — the
    evaluator de-duplicates so the orchestrator can't game the count by
    re-recording the same claim under different facets."""
    from unipaith.ai.state import IdentityClaim, evaluate_identity_layer

    snap = StudentSnapshot(
        identity_claims=[
            IdentityClaim(facet="value", claim="same claim", evidence="same ev"),
            IdentityClaim(facet="belief", claim="same claim", evidence="same ev"),
            IdentityClaim(facet="value", claim="distinct", evidence="ev2"),
        ]
    )
    v = evaluate_identity_layer(snap)
    # Only 2 distinct claims → vb_count=2 → 67% (clamped by other gates).
    assert "value_or_belief (2/3)" in " ".join(v.missing_signals)

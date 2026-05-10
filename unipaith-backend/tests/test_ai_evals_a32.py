"""Phase A3.2 — eval-harness fixture additions.

Verifies the new golden conversations load and have the expected
structure. Real-mode soft-criteria grading runs only with an Anthropic
key.
"""

from __future__ import annotations

from unipaith.ai.evals.runner import (
    load_golden_conversations,
    run_framework_adherence,
)


def test_golden_conversations_grew_to_three() -> None:
    """A1 shipped 1 golden conversation; A3.2 adds two."""
    convs = load_golden_conversations()
    assert len(convs) >= 3, f"expected ≥3 golden conversations, got {len(convs)}"
    ids = {c.get("id") for c in convs}
    assert "first_gen_engineer" in ids
    assert "international_returner" in ids
    assert "refusal_prone_artist" in ids


def test_golden_conversations_each_has_required_structure() -> None:
    convs = load_golden_conversations()
    for c in convs:
        assert "persona" in c, f"{c.get('id')}: missing persona"
        assert "scripted_user_turns" in c, f"{c.get('id')}: missing scripted_user_turns"
        assert "expectations" in c, f"{c.get('id')}: missing expectations"
        assert len(c["scripted_user_turns"]) >= 5, (
            f"{c.get('id')}: too short — needs ≥5 turns to exercise framework"
        )
        # First turn always must guard against premature recommendations.
        first = c["expectations"][0]
        assert any(
            "recommend" in m for m in first.get("must_not_do", [])
        ), f"{c.get('id')}: first-turn recommend-guard missing"


def test_refusal_conversation_does_not_assert_advance() -> None:
    """The refusal-prone fixture explicitly tests that the layer should
    NOT advance — coverage check that this expectation is encoded."""
    convs = load_golden_conversations()
    refusal = next(c for c in convs if c.get("id") == "refusal_prone_artist")
    final = next(e for e in refusal["expectations"] if e.get("turn_index_final"))
    notes = (
        final.get("expected_state_after", {}).get("notes")
        or final.get("notes")
        or ""
    )
    assert "Layer should NOT advance" in notes or "should NOT advance" in notes


def test_framework_adherence_mock_mode_passes_three_fixtures() -> None:
    """Structural mock-mode check: 3/3 fixtures load correctly."""
    result = run_framework_adherence(real=False)
    assert result.passed is True
    assert result.detail["fixtures"] >= 3


def test_international_returner_has_safety_signal_expectation() -> None:
    """The international returner's visa-anxiety turn must encode a
    safety-need extraction expectation."""
    convs = load_golden_conversations()
    intl = next(c for c in convs if c.get("id") == "international_returner")
    safety_turn = next(
        e
        for e in intl["expectations"]
        if e.get("must_capture_signal", {}).get("level") == "safety"
    )
    assert safety_turn is not None

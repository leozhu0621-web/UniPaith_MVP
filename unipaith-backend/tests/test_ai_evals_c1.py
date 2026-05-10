"""Phase C1 — Workshop guardrails fixture validation."""

from __future__ import annotations

from unipaith.ai.evals.runner import (
    THRESHOLDS,
    load_workshop_attacks,
    run_workshop_guardrails,
)


def test_workshop_attacks_fixture_has_at_least_20_entries() -> None:
    """C1 shipped 20 (essay). C2 added 10 interview + 10 test-prep = 30 total.
    Future phases may add more — assert lower bound, not exact count."""
    attacks = load_workshop_attacks()
    assert len(attacks) >= 20, f"expected ≥20 workshop attacks, got {len(attacks)}"


def test_workshop_attacks_each_has_required_fields() -> None:
    attacks = load_workshop_attacks()
    for a in attacks:
        assert "id" in a
        assert "attack_prompt" in a
        assert "draft_text" in a
        assert "must_not_contain" in a
        assert isinstance(a["must_not_contain"], list)
        assert len(a["must_not_contain"]) >= 1, (
            f"{a.get('id')}: must_not_contain is empty — every attack "
            "needs at least one phrase to detect leaks"
        )


def test_workshop_attacks_ids_unique() -> None:
    attacks = load_workshop_attacks()
    ids = [a["id"] for a in attacks]
    assert len(ids) == len(set(ids))


def test_workshop_attacks_cover_diverse_attack_categories() -> None:
    """Confirm we cover ≥3 distinct attack patterns. Hard-coded list of
    expected categories so accidentally homogenizing the fixture
    surfaces in CI."""
    attacks = load_workshop_attacks()
    notes = " ".join(a.get("notes", "") for a in attacks).lower()
    expected_categories = [
        "rewrite request",
        "fill",
        "sample",
        "draft",
    ]
    matched = [c for c in expected_categories if c in notes]
    assert len(matched) >= 3, f"expected ≥3 attack categories, found {matched}"


def test_run_workshop_guardrails_mock_mode_passes() -> None:
    """Structural mock-mode check: every fixture has the required keys."""
    result = run_workshop_guardrails(real=False)
    assert result.passed is True
    assert result.detail["fixtures"] >= 20


def test_workshop_threshold_unchanged_at_one() -> None:
    """Workshop guardrails are a safety eval — never graded on a curve.
    Lowering this threshold would silently ship harmful behavior."""
    assert THRESHOLDS["workshop_guardrails"]["min_refusal_rate"] == 1.0

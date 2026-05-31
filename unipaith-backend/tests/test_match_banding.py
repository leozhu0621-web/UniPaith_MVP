"""Spec 09 §6 + §5.2 — banding + priority-weight mapping unit tests."""

from __future__ import annotations

from types import SimpleNamespace

from unipaith.services.match_banding import (
    band_for_acceptance,
    classify_band,
    selectivity_from_acceptance,
    tolerance_from_preferences,
    weights_from_preferences,
)

# ── selectivity / tolerance helpers ─────────────────────────────────────────


def test_selectivity_inverts_acceptance_rate():
    assert abs(selectivity_from_acceptance(0.05) - 0.95) < 1e-9  # very selective
    assert abs(selectivity_from_acceptance(0.9) - 0.1) < 1e-9
    assert selectivity_from_acceptance(None) is None


def test_tolerance_defaults_neutral():
    assert tolerance_from_preferences(None) == 0.5
    assert tolerance_from_preferences(10) == 1.0
    assert tolerance_from_preferences(0) == 0.0


# ── classify_band ───────────────────────────────────────────────────────────


def test_more_selective_than_tolerance_is_reach():
    # selectivity 0.95, tolerance 0.3 → big positive gap → reach.
    assert classify_band(fitness=0.6, selectivity=0.95, tolerance=0.3) == "reach"


def test_less_selective_than_tolerance_is_safer():
    assert classify_band(fitness=0.8, selectivity=0.2, tolerance=0.8) == "safer"


def test_near_tolerance_is_target():
    assert classify_band(fitness=0.7, selectivity=0.55, tolerance=0.5) == "target"


def test_fitness_only_fallback_when_selectivity_unknown():
    assert classify_band(fitness=0.8, selectivity=None, tolerance=0.5) == "safer"
    assert classify_band(fitness=0.68, selectivity=None, tolerance=None) == "target"
    assert classify_band(fitness=0.4, selectivity=None, tolerance=None) == "reach"


def test_band_for_acceptance_wrapper():
    # acceptance 5% → selectivity 0.95; weight_ranking 3 → tolerance 0.3 → reach.
    assert band_for_acceptance(fitness=0.6, acceptance_rate=0.05, weight_ranking=3) == "reach"
    # acceptance 80% → selectivity 0.2; weight_ranking 8 → tolerance 0.8 → safer.
    assert band_for_acceptance(fitness=0.8, acceptance_rate=0.8, weight_ranking=8) == "safer"


# ── weights_from_preferences ────────────────────────────────────────────────


def test_weights_none_when_no_sliders_set():
    pref = SimpleNamespace(
        weight_cost=None,
        weight_outcomes=None,
        weight_ranking=None,
        weight_location=None,
        weight_flexibility=None,
        weight_support=None,
    )
    assert weights_from_preferences(pref) is None
    assert weights_from_preferences(None) is None


def test_weights_sum_to_one():
    pref = SimpleNamespace(
        weight_cost=5,
        weight_outcomes=5,
        weight_ranking=5,
        weight_location=5,
        weight_flexibility=5,
        weight_support=5,
    )
    w = weights_from_preferences(pref)
    assert w is not None
    # Normalized to ~1.0 (each weight rounded to 4dp, so allow rounding slack).
    assert abs(sum(w.values()) - 1.0) < 1e-3
    assert set(w) == {"cosine", "soft_align", "needs_match"}


def test_outcomes_emphasis_boosts_content_weight():
    outcomes_heavy = SimpleNamespace(
        weight_cost=0,
        weight_outcomes=10,
        weight_ranking=10,
        weight_location=0,
        weight_flexibility=0,
        weight_support=0,
    )
    cost_heavy = SimpleNamespace(
        weight_cost=10,
        weight_outcomes=0,
        weight_ranking=0,
        weight_location=10,
        weight_flexibility=10,
        weight_support=0,
    )
    wo = weights_from_preferences(outcomes_heavy)
    wc = weights_from_preferences(cost_heavy)
    assert wo is not None and wc is not None
    # Outcomes/ranking emphasis tilts toward content (cosine); cost/location
    # emphasis tilts toward soft_align.
    assert wo["cosine"] > wc["cosine"]
    assert wc["soft_align"] > wo["soft_align"]


def test_support_emphasis_boosts_needs_weight():
    support_heavy = SimpleNamespace(
        weight_cost=0,
        weight_outcomes=0,
        weight_ranking=0,
        weight_location=0,
        weight_flexibility=0,
        weight_support=10,
    )
    w = weights_from_preferences(support_heavy)
    assert w is not None
    assert w["needs_match"] > w["cosine"]
    assert w["needs_match"] > w["soft_align"]


def test_time_to_degree_emphasis_boosts_soft_align():
    """Spec 09 §5.2 / §12 — the Time-to-degree slider must measurably re-rank.

    Regression guard: the mapping previously read ``weight_support`` and ignored
    ``weight_time_to_degree`` entirely, so the UI's 6th slider was dead.
    """
    base = dict(
        weight_cost=5,
        weight_outcomes=5,
        weight_ranking=5,
        weight_location=5,
        weight_flexibility=5,
        weight_support=5,
    )
    fast = SimpleNamespace(**base, weight_time_to_degree=10)
    slow = SimpleNamespace(**base, weight_time_to_degree=0)
    wf = weights_from_preferences(fast)
    ws = weights_from_preferences(slow)
    assert wf is not None and ws is not None
    # Higher time-to-degree importance tilts toward lifestyle/throughput fit.
    assert wf["soft_align"] > ws["soft_align"]


def test_only_time_to_degree_set_still_maps():
    """A single set slider (time-to-degree) must trigger a non-None mapping."""
    pref = SimpleNamespace(
        weight_cost=None,
        weight_outcomes=None,
        weight_ranking=None,
        weight_location=None,
        weight_flexibility=None,
        weight_support=None,
        weight_time_to_degree=8,
    )
    w = weights_from_preferences(pref)
    assert w is not None
    assert set(w) == {"cosine", "soft_align", "needs_match"}

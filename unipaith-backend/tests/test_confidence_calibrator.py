"""Phase D2 — Confidence calibrator tests.

Pure-Python; sklearn is in deps so the fit path runs in unit tests.
"""

from __future__ import annotations

import random

from unipaith.services.confidence_calibrator import (
    MIN_PAIRS_FOR_CALIBRATION,
    CalibratorState,
    apply_calibrator,
    fit_calibrator,
    reliability_diagram,
)


def _gen_pairs(n: int, *, well_calibrated: bool = True, seed: int = 0) -> list[tuple[float, int]]:
    """Generate (predicted, outcome) pairs.

    If `well_calibrated`, the prediction matches the outcome rate (fit
    should produce a near-identity calibrator). If False, predictions
    are uniformly 0.5 — calibration should pull all of them to the
    base rate.
    """
    rng = random.Random(seed)
    pairs: list[tuple[float, int]] = []
    for _ in range(n):
        if well_calibrated:
            p = rng.random()
            outcome = 1 if rng.random() < p else 0
        else:
            p = 0.5
            outcome = 1 if rng.random() < 0.3 else 0  # base rate 30%
        pairs.append((p, outcome))
    return pairs


# ── State serialization ────────────────────────────────────────────────────


def test_calibrator_state_round_trips_through_dict() -> None:
    state = CalibratorState(
        fitted=True,
        n_samples=1234,
        breakpoints=[[0.0, 0.0], [0.5, 0.4], [1.0, 1.0]],
        reliability={"ece": 0.05, "n_bins": 10},
    )
    d = state.to_dict()
    restored = CalibratorState.from_dict(d)
    assert restored.fitted is True
    assert restored.n_samples == 1234
    assert restored.breakpoints == [[0.0, 0.0], [0.5, 0.4], [1.0, 1.0]]
    assert restored.reliability["ece"] == 0.05


def test_calibrator_state_from_none_returns_unfitted_default() -> None:
    state = CalibratorState.from_dict(None)
    assert state.fitted is False
    assert state.breakpoints == []


def test_calibrator_state_from_dict_filters_malformed_breakpoints() -> None:
    """Defensive: a malformed breakpoint (wrong length) is dropped."""
    state = CalibratorState.from_dict(
        {
            "fitted": True,
            "n_samples": 1000,
            "breakpoints": [[0.0, 0.0], [0.5], [1.0, 1.0, 1.0]],
        }
    )
    assert state.breakpoints == [[0.0, 0.0]]


# ── Fit ────────────────────────────────────────────────────────────────────


def test_fit_calibrator_below_minimum_returns_unfitted() -> None:
    """Cold start: too few pairs → identity calibrator."""
    state = fit_calibrator(_gen_pairs(50))
    assert state.fitted is False
    assert state.breakpoints == []
    assert state.n_samples == 50
    assert state.reliability.get("reason") == "below_minimum_samples"


def test_fit_calibrator_at_minimum_fits() -> None:
    """At MIN_PAIRS_FOR_CALIBRATION pairs, we fit."""
    pairs = _gen_pairs(MIN_PAIRS_FOR_CALIBRATION, seed=42)
    state = fit_calibrator(pairs)
    assert state.fitted is True
    assert state.n_samples == MIN_PAIRS_FOR_CALIBRATION
    assert len(state.breakpoints) >= 2  # at least two endpoints
    # Each breakpoint is [x, y] in [0, 1].
    for x, y in state.breakpoints:
        assert 0.0 <= x <= 1.0
        assert 0.0 <= y <= 1.0


def test_fit_well_calibrated_data_produces_near_identity_calibrator() -> None:
    """If the predicted=outcome data is already well-calibrated, the
    fitted curve should be near identity. Spot-check with apply()."""
    state = fit_calibrator(_gen_pairs(2000, well_calibrated=True, seed=1))
    assert state.fitted
    # apply at 0.0, 0.5, 1.0 should be roughly the input.
    for x in (0.1, 0.5, 0.9):
        y = apply_calibrator(state, x)
        assert abs(y - x) < 0.15, f"calibration drift too large at x={x}: y={y}"


def test_fit_uniform_predictions_pulls_to_base_rate() -> None:
    """If all predictions are 0.5 but the actual outcome rate is 0.3,
    the calibrator should map 0.5 → ~0.3."""
    state = fit_calibrator(_gen_pairs(2000, well_calibrated=False, seed=2))
    assert state.fitted
    y = apply_calibrator(state, 0.5)
    # Allow generous slack — random sample variance.
    assert 0.2 < y < 0.4, f"expected ~0.3, got {y}"


# ── Apply ──────────────────────────────────────────────────────────────────


def test_apply_unfitted_returns_input_identity() -> None:
    state = CalibratorState()  # unfitted
    for x in (0.0, 0.25, 0.5, 0.75, 1.0):
        assert apply_calibrator(state, x) == x


def test_apply_clamps_to_unit_interval() -> None:
    state = CalibratorState()
    assert apply_calibrator(state, -0.5) == 0.0
    assert apply_calibrator(state, 1.5) == 1.0


def test_apply_below_first_breakpoint_returns_first_y() -> None:
    state = CalibratorState(
        fitted=True,
        n_samples=2000,
        breakpoints=[[0.2, 0.1], [0.8, 0.9]],
    )
    # Input < 0.2 → first breakpoint y=0.1 (clipped).
    assert apply_calibrator(state, 0.0) == 0.1
    assert apply_calibrator(state, 0.1) == 0.1


def test_apply_above_last_breakpoint_returns_last_y() -> None:
    state = CalibratorState(
        fitted=True,
        n_samples=2000,
        breakpoints=[[0.2, 0.1], [0.8, 0.9]],
    )
    assert apply_calibrator(state, 0.9) == 0.9
    assert apply_calibrator(state, 1.0) == 0.9


def test_apply_interpolates_linearly_between_breakpoints() -> None:
    state = CalibratorState(
        fitted=True,
        n_samples=2000,
        breakpoints=[[0.0, 0.0], [1.0, 1.0]],
    )
    # On a linear breakpoint list, midpoint should be the midpoint.
    assert abs(apply_calibrator(state, 0.5) - 0.5) < 1e-9
    # And quartiles too.
    assert abs(apply_calibrator(state, 0.25) - 0.25) < 1e-9


# ── Reliability diagram ────────────────────────────────────────────────────


def test_reliability_diagram_empty_returns_empty_bins() -> None:
    rd = reliability_diagram([])
    assert rd["n_samples"] == 0
    assert rd["bins"] == []
    assert rd["ece"] is None


def test_reliability_diagram_well_calibrated_low_ece() -> None:
    """Well-calibrated synthetic data → low ECE."""
    rd = reliability_diagram(_gen_pairs(5000, well_calibrated=True, seed=3))
    # Random sampling at N=5000 typically yields ECE under ~0.05.
    assert rd["ece"] < 0.10, f"ECE too high for well-calibrated data: {rd['ece']}"


def test_reliability_diagram_uniform_predictions_high_max_gap() -> None:
    """All predictions at 0.5 with base rate 0.3 → bin at ~0.5 has
    max_gap ≈ 0.2."""
    rd = reliability_diagram(_gen_pairs(2000, well_calibrated=False, seed=4))
    assert rd["max_gap"] > 0.1
    # Find the bin that contains 0.5 — its observed_rate should be near 0.3.
    bin_at_half = next((b for b in rd["bins"] if b["lo"] <= 0.5 < b["hi"]), None)
    assert bin_at_half is not None
    assert bin_at_half["count"] > 0
    assert bin_at_half["observed_rate"] is not None
    assert 0.2 < bin_at_half["observed_rate"] < 0.4


def test_reliability_diagram_default_bins_count() -> None:
    rd = reliability_diagram(_gen_pairs(100), n_bins=10)
    assert rd["n_bins"] == 10
    assert len(rd["bins"]) == 10


def test_reliability_diagram_custom_bins_count() -> None:
    rd = reliability_diagram(_gen_pairs(100), n_bins=5)
    assert rd["n_bins"] == 5
    assert len(rd["bins"]) == 5

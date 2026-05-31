"""Spec 09 §4A — ProbabilityBandEstimator unit tests.

The estimator must be HONEST: always a range (never false precision), wider
when we know less, and null ("not enough data yet") when the program lacks
historical admit signal OR the student isn't match-ready.
"""

from __future__ import annotations

from unipaith.ai.probability import (
    MATCH_READY_MIN_CONFIDENCE,
    estimate_probability_bands,
    is_match_ready,
)


def test_match_ready_threshold():
    assert is_match_ready(MATCH_READY_MIN_CONFIDENCE) is True
    assert is_match_ready(MATCH_READY_MIN_CONFIDENCE - 0.01) is False
    assert is_match_ready(None) is False
    assert is_match_ready(0.9) is True


def test_null_when_no_history():
    # No acceptance rate → no historical signal → None (Spec 09 §4A rule).
    assert estimate_probability_bands(acceptance_rate=None, fitness=0.8, confidence=0.9) is None


def test_null_when_not_match_ready():
    # Strong history but the model doesn't know the student → None.
    assert estimate_probability_bands(acceptance_rate=0.5, fitness=0.8, confidence=0.1) is None


def test_bands_present_when_history_and_ready():
    bands = estimate_probability_bands(acceptance_rate=0.30, fitness=0.7, confidence=0.7)
    assert bands is not None
    admit = bands["admit"]
    assert 0.0 <= admit["low"] < admit["high"] <= 1.0  # always a range
    assert admit["label"] in {"likely", "target", "reach", "unlikely"}
    assert isinstance(bands["drivers"], list) and 1 <= len(bands["drivers"]) <= 4
    for d in bands["drivers"]:
        assert d["direction"] in {"up", "down"}


def test_admit_is_always_a_range_never_point():
    bands = estimate_probability_bands(acceptance_rate=0.5, fitness=0.5, confidence=1.0)
    assert bands is not None
    # Even at max confidence the band has nonzero width — never false precision.
    assert bands["admit"]["high"] > bands["admit"]["low"]


def test_lower_confidence_widens_the_band():
    hi = estimate_probability_bands(acceptance_rate=0.4, fitness=0.6, confidence=0.95)
    lo = estimate_probability_bands(acceptance_rate=0.4, fitness=0.6, confidence=0.35)
    assert hi is not None and lo is not None
    width_hi = hi["admit"]["high"] - hi["admit"]["low"]
    width_lo = lo["admit"]["high"] - lo["admit"]["low"]
    assert width_lo > width_hi  # less certainty → wider range


def test_better_fit_lifts_admit_center():
    weak = estimate_probability_bands(acceptance_rate=0.3, fitness=0.2, confidence=0.8)
    strong = estimate_probability_bands(acceptance_rate=0.3, fitness=0.9, confidence=0.8)
    assert weak is not None and strong is not None
    weak_center = (weak["admit"]["low"] + weak["admit"]["high"]) / 2
    strong_center = (strong["admit"]["low"] + strong["admit"]["high"]) / 2
    assert strong_center > weak_center


def test_label_maps_to_center():
    # Very open program + strong fit → likely.
    likely = estimate_probability_bands(acceptance_rate=0.85, fitness=0.9, confidence=0.8)
    assert likely is not None and likely["admit"]["label"] == "likely"
    # Highly selective + weak fit → unlikely.
    unlikely = estimate_probability_bands(acceptance_rate=0.04, fitness=0.2, confidence=0.8)
    assert unlikely is not None and unlikely["admit"]["label"] in {"unlikely", "reach"}


def test_highly_selective_adds_selectivity_driver():
    bands = estimate_probability_bands(acceptance_rate=0.08, fitness=0.6, confidence=0.7)
    assert bands is not None
    signals = {d["signal"] for d in bands["drivers"]}
    assert "High selectivity" in signals


def test_scholarship_withheld_for_weak_fit():
    # Weak fit → no scholarship estimate (don't imply funding we can't support).
    bands = estimate_probability_bands(acceptance_rate=0.5, fitness=0.3, confidence=0.8)
    assert bands is not None
    assert bands["scholarship"] is None


def test_scholarship_present_for_strong_fit():
    bands = estimate_probability_bands(acceptance_rate=0.5, fitness=0.85, confidence=0.8)
    assert bands is not None
    sch = bands["scholarship"]
    assert sch is not None and 0.0 <= sch["low"] < sch["high"] <= 1.0


def test_waitlist_suppressed_when_admit_near_certain():
    bands = estimate_probability_bands(acceptance_rate=0.95, fitness=0.95, confidence=0.9)
    assert bands is not None
    # Near-certain admit → waitlist not meaningful.
    assert bands["waitlist"] is None

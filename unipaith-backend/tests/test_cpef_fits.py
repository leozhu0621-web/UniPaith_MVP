"""Slice A — CPEF per-type fit functions (Spec 3 §3). Pure, no DB."""

from unipaith.services.match import fits


def test_categorical_exact_similar_miss_and_unknown():
    assert fits.fit_categorical("ds", "ds") == 1.0
    assert fits.fit_categorical("ds", "cs", {("ds", "cs"): 0.7}) == 0.7
    assert fits.fit_categorical("ds", "art") == 0.0
    assert fits.fit_categorical(None, "ds") == 0.5  # unknown → neutral


def test_numeric_higher_midpoint_and_tails():
    assert abs(fits.fit_numeric_higher(3.5, 3.5, 0.3) - 0.5) < 1e-6
    assert fits.fit_numeric_higher(4.5, 3.5, 0.3) > 0.95
    assert fits.fit_numeric_higher(2.5, 3.5, 0.3) < 0.05


def test_numeric_target_exact_and_far():
    assert abs(fits.fit_numeric_target(24, 24, 6) - 1.0) < 1e-9
    assert fits.fit_numeric_target(48, 24, 6) < 0.02


def test_range_affordable_overage_and_far():
    assert fits.fit_range(30000, 35000) == 1.0
    # $40k vs $35k budget, 14% over, delta 0.25 → 1 - 5000/8750
    assert abs(fits.fit_range(40000, 35000, 0.25) - (1 - 5000 / 8750)) < 1e-6
    assert fits.fit_range(60000, 35000, 0.25) == 0.0


def test_boolean():
    assert fits.fit_boolean(True) == 1.0
    assert fits.fit_boolean(False, want_hard=True) == 0.0
    assert fits.fit_boolean(False, want_hard=False) == 0.3


def test_geo():
    assert fits.fit_geo(["USA"], ["NYC", "USA"]) == 1.0
    assert fits.fit_geo(["UK"], ["USA"]) == 0.0
    assert fits.fit_geo([], ["USA"]) == 0.5


def test_degree_level():
    assert fits.fit_degree_level("masters", "masters") == 1.0
    assert fits.fit_degree_level("masters", "professional") == 0.6
    assert fits.fit_degree_level("masters", "bachelors") == 0.0


def test_date():
    assert fits.fit_date(120, 90) == 1.0
    assert fits.fit_date(0, 90) == 0.0
    assert abs(fits.fit_date(45, 90) - 0.5) < 1e-9

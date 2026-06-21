"""Social-preference satisfaction in the soft-alignment layer.

`_pref_satisfaction(prefs, features)` measures how well a program's [0,1]
`social_features` satisfy a student's [0,1] `social_prefs`: the pref-weighted
coverage of the student's preferences, normalized by total preference weight.
Crucially it does NOT dilute a met preference by the program's *unrelated*
features (the old union-normalized `_vec_align` did, under-rewarding good fits).

Pure — no DB.
"""

import pytest

from unipaith.services.matching import _pref_satisfaction


def test_met_preference_is_not_diluted_by_unrelated_features() -> None:
    # The student's single strong preference is fully met; the program's extra
    # features must NOT drag the score down.
    assert _pref_satisfaction({"urban": 1.0}, {"urban": 1.0}) == 1.0
    assert _pref_satisfaction({"urban": 1.0}, {"urban": 1.0, "research": 1.0, "sports": 1.0}) == 1.0


def test_unmet_preference_scores_zero() -> None:
    assert _pref_satisfaction({"urban": 1.0}, {"rural": 1.0}) == 0.0
    assert _pref_satisfaction({"urban": 1.0}, {}) == 0.0


def test_weakly_met_strong_preference_is_partial() -> None:
    # Strong preference, weak program feature → partially satisfied.
    assert _pref_satisfaction({"urban": 1.0}, {"urban": 0.5}) == pytest.approx(0.5)


def test_partial_coverage_across_multiple_prefs() -> None:
    # Two equally-weighted prefs, one met → half satisfied.
    assert _pref_satisfaction({"urban": 1.0, "small": 1.0}, {"urban": 1.0}) == pytest.approx(0.5)


def test_no_preferences_is_neutral_zero() -> None:
    # No social prefs expressed → no positive signal (matches the prior empty case).
    assert _pref_satisfaction({}, {"urban": 1.0}) == 0.0
    assert _pref_satisfaction({}, {}) == 0.0


def test_values_are_clamped_to_unit_interval() -> None:
    # Out-of-range inputs are clamped; the result stays in [0, 1].
    assert _pref_satisfaction({"urban": 2.0}, {"urban": 2.0}) == 1.0
    assert _pref_satisfaction({"urban": -1.0}, {"urban": 1.0}) == 0.0

"""Slice A — CPEF params + confidence→gain (Spec 3 §2). Pure, no DB."""

from unipaith.services.match.params import (
    DEFAULT_PARAMS,
    confidence_to_gain,
    two_sided_confidence,
)


def test_gain_equals_confidence_when_tau0_equals_kappa():
    # With tau0 == kappa (the default), the trust-gain rho equals c.
    assert abs(confidence_to_gain(0.9) - 0.9) < 1e-6
    assert abs(confidence_to_gain(0.7) - 0.7) < 1e-6
    assert abs(confidence_to_gain(0.4) - 0.4) < 1e-6


def test_gain_clamps_extremes():
    assert confidence_to_gain(1.0) < 1.0
    assert confidence_to_gain(1.0) >= 0.98
    assert confidence_to_gain(0.0) > 0.0


def test_two_sided_multiplies():
    assert abs(two_sided_confidence(0.9, 0.6) - 0.54) < 1e-9
    assert abs(two_sided_confidence(1.0, 1.0) - 1.0) < 1e-9
    assert abs(two_sided_confidence(1.0, 0.6) - 0.6) < 1e-9


def test_default_params_present():
    for k in ("kappa", "tau0", "delta", "epsilon", "alpha", "w_base", "n0", "prior"):
        assert k in DEFAULT_PARAMS

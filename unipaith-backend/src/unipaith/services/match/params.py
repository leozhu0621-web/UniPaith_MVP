"""CPEF tunables + confidence→gain helpers (Spec 3 §2).

These are the single calibration lever for the matcher (the analogue of the
old ``DEFAULT_WEIGHTS``). Only the ratio ``tau0/kappa`` matters for the gain;
with ``tau0 == kappa`` the trust-gain ``rho`` equals the confidence ``c``.
"""

from __future__ import annotations

DEFAULT_PARAMS: dict[str, float] = {
    "kappa": 1.0,  # precision scale (only the ratio to tau0 matters)
    "tau0": 1.0,  # prior precision; tau0 == kappa ⇒ rho ≈ c
    "delta": 0.25,  # budget overage tolerance (fraction of budget_max)
    "epsilon": 0.01,  # veto floor — a vetoed program sinks, never hard 0
    "h": 0.5,  # gaussian bandwidth for preference-target fits
    "logit_slope": 1.7,  # logistic slope (≈ normal CDF) for higher-is-better
    "w_base": 6.0,  # default importance for structural signals (0–10 scale)
    "n0": 3.0,  # coverage soft-saturation constant
    "alpha": 0.7,  # mutual-fit blend, student side leads (used in Slice B)
    "prior": 0.5,  # neutral base-rate fit when no per-(program,dim) prior
    "confirmed_gain": 0.85,  # rho >= this ⇒ a "confirmed" deal-breaker (hardened floor)
}

# Confidence is clamped off the open interval so precision stays finite.
_C_LO, _C_HI = 0.01, 0.99


def clamp01(x: float) -> float:
    """Clamp to [0, 1]."""
    return max(0.0, min(1.0, x))


def two_sided_confidence(c_self: float, c_other: float) -> float:
    """A dimension is only as sure as *both* sides: ``c = c_self * c_other``.

    ``c_self`` is the student-side confidence (Spec 1), ``c_other`` the
    program-side confidence from authority precedence (Spec 2).
    """
    return clamp01(c_self) * clamp01(c_other)


def confidence_to_gain(c: float, params: dict[str, float] | None = None) -> float:
    """Trust-gain ``rho = tau / (tau + tau0)`` with ``tau = kappa * c / (1 - c)``.

    With ``tau0 == kappa`` this reduces to ``rho == c``. ``rho`` is the literal
    weight on the observed fit vs. the prior in the posterior-mean shrinkage.
    """
    p = params or DEFAULT_PARAMS
    c = min(_C_HI, max(_C_LO, c))
    tau = p["kappa"] * c / (1.0 - c)
    return tau / (tau + p["tau0"])

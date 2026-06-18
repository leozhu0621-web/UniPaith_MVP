"""Per-type fit functions for CPEF (Spec 3 §3).

Each returns a raw fit ``f`` in [0, 1] comparing one side's value to the
other side's attribute. Confidence-free: shrinkage by ``rho`` happens later
in the assembly. A ``None`` on either side returns the neutral 0.5 (the prior
anchor) rather than punishing the program for data we do not have.
"""

from __future__ import annotations

import math

from .params import clamp01


def fit_categorical(
    student_val: object, program_val: object, sim_table: dict | None = None
) -> float:
    """Exact enum match → 1; curated similarity → its value; else 0."""
    if student_val is None or program_val is None:
        return 0.5
    if student_val == program_val:
        return 1.0
    if sim_table:
        v = sim_table.get((student_val, program_val))
        if v is None:
            v = sim_table.get((program_val, student_val), 0.0)
        return clamp01(float(v))
    return 0.0


def fit_numeric_higher(
    x: float | None, mu: float | None, sigma: float | None, slope: float = 1.7
) -> float:
    """Higher-is-better vs a cohort: logistic of the z-score (≈ normal CDF).

    At the cohort mean → 0.5; well above → ~1; well below → ~0. Being far
    above never penalizes.
    """
    if x is None or mu is None:
        return 0.5
    s = sigma if sigma and sigma > 0 else 1.0
    z = (x - mu) / s
    return clamp01(1.0 / (1.0 + math.exp(-slope * z)))


def fit_numeric_target(x: float | None, target: float | None, h: float = 0.5) -> float:
    """Closer-is-better around a target: a Gaussian kernel. Exact → 1."""
    if x is None or target is None:
        return 0.5
    hh = h if h and h > 0 else 0.5
    return clamp01(math.exp(-(((x - target) / hh) ** 2)))


def fit_range(value: float | None, hi: float | None, delta: float = 0.25) -> float:
    """Affordability-style: ``value <= hi`` → 1; mild overage decays linearly
    over ``delta * hi``; beyond that → 0 (and the overage becomes a deal-breaker
    handled by the veto, not here)."""
    if value is None or hi is None:
        return 0.5
    if value <= hi:
        return 1.0
    tol = max(1e-9, delta * hi)
    return clamp01(1.0 - (value - hi) / tol)


def fit_boolean(has: bool, want_hard: bool = True) -> float:
    """Program has the wanted attribute → 1; else a floor (0.0 hard want, 0.3 soft).
    The strength of the want rides in the weight, not here."""
    if has:
        return 1.0
    return 0.0 if want_hard else 0.3


def fit_geo(pref: list | None, prog: list | None) -> float:
    """Preferred locations vs program locations. Overlap → 1; disjoint → 0;
    unknown on either side → neutral 0.5. (Hard 'avoid' is a deal-breaker, not here.)"""
    ps = set(pref or [])
    gs = set(prog or [])
    if not ps or not gs:
        return 0.5
    return 1.0 if (ps & gs) else 0.0


# Degree levels that are "off but acceptable" → graded 0.6 (wrong family → veto).
_DEGREE_ADJ: set[tuple[str, str]] = {
    ("masters", "professional"),
    ("professional", "masters"),
    ("masters", "doctoral"),
    ("doctoral", "masters"),
}


def fit_degree_level(student_target: str | None, program_level: str | None) -> float:
    """Exact level → 1; adjacent-acceptable → 0.6; otherwise 0 (the veto buries
    a true wrong-family mismatch)."""
    if not student_target or not program_level:
        return 0.5
    if student_target == program_level:
        return 1.0
    if (student_target, program_level) in _DEGREE_ADJ:
        return 0.6
    return 0.0


def fit_date(margin_days: float | None, horizon_days: float | None) -> float:
    """Feasibility by time margin: comfortable margin → 1; shrinking → linear
    decay; past/infeasible → 0."""
    if margin_days is None or horizon_days is None or horizon_days <= 0:
        return 0.5
    if margin_days >= horizon_days:
        return 1.0
    if margin_days <= 0:
        return 0.0
    return clamp01(margin_days / horizon_days)

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
    "ps_floor": 0.2,  # p→s satisfaction floor — a program that rejects the student
    #                   pulls M down but never buries it (the s→p veto's job)
    "prior": 0.5,  # neutral base-rate fit when no per-(program,dim) prior
    "confirmed_gain": 0.85,  # rho >= this ⇒ a "confirmed" deal-breaker (hardened floor)
    "time_h": 12.0,  # gaussian bandwidth (months) for desired-time-to-degree fit
}

# ── Per-dimension priors m_k (Spec 3 §2.1) ───────────────────────────────────
# "Do not ship flat 0.5 everywhere" — a flat prior compresses thin/inferred
# profiles toward the same mid value regardless of how a typical applicant
# actually fares on that dimension. These are deterministic per-DIMENSION base
# rates (the realistic average raw-fit of a random student↔program pair on that
# dim), used as the shrink anchor m_k for any program lacking a precomputed
# per-(program,dim) base rate. They are NOT the program-specific priors §2.1
# also envisions (those would be computed offline in program_features.py from
# admit-cohort medians); this per-dim table is the strictly-better-than-flat
# fallback the spec calls for, and it stays in [0,1].
#
# Rationale for each value:
#   themes / field  — a random (student, program) pair rarely shares interest
#                     tags or sits in the same field, so the base rate is low.
#   needs           — programs broadly offer common supports, so coverage of a
#                     random need is moderate.
#   budget / time   — affordability and duration land near the middle on average.
#   geo             — most students are flexible / many programs sit in popular
#                     locations, so overlap is more-likely-than-not.
#   degree_level    — degree targets cluster (masters-heavy catalog), so an
#                     average target lands a bit above the midpoint.
#   flexibility / support — part-time/online and dedicated support are the
#                     minority of programs, so the base rate is below 0.5.
#   semantic        — neutral; cosine of unrelated summaries averages mid-low.
DIMENSION_PRIORS: dict[str, float] = {
    "semantic": 0.45,
    "themes": 0.30,
    "field": 0.30,
    "needs": 0.55,
    "budget": 0.50,
    "time": 0.50,
    "geo": 0.60,
    "degree_level": 0.55,
    "flexibility": 0.35,
    "support": 0.40,
}


def prior_for(dim: str, params: dict[str, float] | None = None) -> float:
    """The shrink anchor m_k for a dimension: its per-dim base rate, falling
    back to the global neutral ``prior`` (0.5) for any unknown dimension."""
    p = params or DEFAULT_PARAMS
    return DIMENSION_PRIORS.get(dim, p["prior"])


# ── Curated field-of-study similarity table (Spec 3 §3 categorical) ──────────
# Symmetric related-field grades for ``fit_categorical``. Exact match is 1.0 (no
# entry needed); an unrelated pair with no entry is 0.0. Keys are lower_snake
# canonical field names; the lookup tries both orderings. Kept small + auditable
# (the CIP-family idea from §3, hand-curated for the fields we actually model).
FIELD_SIM_TABLE: dict[tuple[str, str], float] = {
    ("data_science", "statistics"): 0.8,
    ("data_science", "computer_science"): 0.7,
    ("data_science", "mathematics"): 0.6,
    ("data_science", "economics"): 0.5,
    ("computer_science", "statistics"): 0.6,
    ("computer_science", "mathematics"): 0.6,
    ("computer_science", "engineering"): 0.6,
    ("statistics", "mathematics"): 0.7,
    ("statistics", "economics"): 0.6,
    ("mathematics", "physics"): 0.6,
    ("physics", "engineering"): 0.6,
    ("biology", "neuroscience"): 0.7,
    ("biology", "public_health"): 0.6,
    ("biology", "chemistry"): 0.6,
    ("chemistry", "engineering"): 0.5,
    ("neuroscience", "psychology"): 0.6,
    ("psychology", "public_health"): 0.5,
    ("economics", "business"): 0.6,
    ("business", "finance"): 0.7,
    ("economics", "finance"): 0.6,
    ("political_science", "economics"): 0.5,
    ("political_science", "history"): 0.5,
    ("history", "art_history"): 0.5,
    ("english", "history"): 0.4,
}

# Below this best-field-fit, a program is treated as WRONG-DISCIPLINE for the
# student and vetoed in her ranking (todo 3.2). ``fit_categorical`` returns 1.0 for
# an exact field match, the curated FIELD_SIM_TABLE value (0.4–0.8) for a *related*
# field, and 0.0 for an *unrelated* one. A floor of 0.35 therefore sinks ONLY the
# unrelated case (0.0) while letting every adjacent field in the sim table (≥0.4 —
# e.g. CS↔data-science, CS↔engineering) pass untouched, so interdisciplinary
# matches are never buried.
FIELD_VETO_FLOOR: float = 0.35

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

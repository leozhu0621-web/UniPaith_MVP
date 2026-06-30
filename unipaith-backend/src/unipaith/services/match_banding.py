"""Match banding + priority-weight mapping (Spec 09 §6, §5.2).

Two pure helpers, deliberately DB-decoupled so they're trivially testable:

1. ``classify_band`` — reach / target / safer, the three bands the Match
   surface groups by (Spec 09 §6). Banding is fundamentally about admission
   difficulty (program selectivity vs the student's stated tolerance), with
   a fitness-only fallback when selectivity is unknown.

2. ``weights_from_preferences`` — map the student's 6 priority sliders
   (Spec 09 §5.2, persisted on ``student_preferences``) into the matcher's
   3 composition weights (``cosine`` / ``soft_align`` / ``needs_match``), so
   saving the sliders measurably re-ranks results. This is an explicit MVP
   heuristic; the learned re-ranker (D3) supersedes it once fitted.
"""

from __future__ import annotations

from typing import Any

from unipaith.services.match.params import DEFAULT_PARAMS


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def selectivity_from_acceptance(acceptance_rate: float | None) -> float | None:
    """Program selectivity in ``[0, 1]`` (1 = hardest). ``None`` when the
    program has no acceptance-rate signal."""
    if acceptance_rate is None:
        return None
    return _clamp(1.0 - float(acceptance_rate), 0.0, 1.0)


def tolerance_from_preferences(weight_ranking: int | None) -> float:
    """The student's comfort with selectivity, in ``[0, 1]``.

    A higher weight on ranking/selectivity means the student is reaching for
    more selective programs, so their tolerance for selectivity is higher.
    Neutral default 0.5 when unstated.
    """
    if weight_ranking is None:
        return 0.5
    return _clamp(float(weight_ranking) / 10.0, 0.0, 1.0)


def strength_from_gpa(gpa: float | None) -> float | None:
    """The student's academic strength in ``[0, 1]`` from a 4.0-scale GPA, used
    as the comfort line for banding. Deliberately conservative — GPA alone does
    not buy a seat at the most selective schools — so ``(gpa - 2.0) / 2.5``:
    4.0→0.8, 3.7→0.68, 3.0→0.4. ``None`` when no GPA is on file (banding then
    falls back to the selectivity slider)."""
    if gpa is None:
        return None
    try:
        return _clamp((float(gpa) - 2.0) / 2.5, 0.0, 1.0)
    except (TypeError, ValueError):
        return None


def classify_band(
    *,
    fitness: float,
    selectivity: float | None,
    tolerance: float | None,
    student_strength: float | None = None,
) -> str:
    """Return ``"reach" | "target" | "safer"`` (Spec 09 §6).

    The band is the program's admission difficulty (``selectivity``) vs how
    strong the STUDENT is. When we know the student's stats we compare against
    ``student_strength`` (GPA-derived); the ranking slider only nudges it. When
    the student's stats are unknown we fall back to the slider ``tolerance``;
    when selectivity itself is unknown we fall back to fitness thresholds, shifted
    down for stronger students so a good applicant isn't told everything is a
    reach.
    """
    f = _clamp(float(fitness), 0.0, 1.0)
    if selectivity is not None:
        if student_strength is not None:
            comfort = student_strength
            if tolerance is not None:
                # The slider tilts the comfort line a little (a student reaching
                # for prestige accepts more selective "targets"), but the GPA
                # dominates.
                comfort = _clamp(0.8 * student_strength + 0.2 * tolerance, 0.0, 1.0)
        elif tolerance is not None:
            comfort = tolerance
        else:
            comfort = 0.5
        gap = float(selectivity) - comfort
        if gap > 0.12:
            return "reach"
        if gap < -0.12:
            return "safer"
        return "target"
    # Selectivity unknown — fitness fallback. The old 0.65/0.75 bars sat above the
    # live CPEF fit distribution, pinning everything to "reach"; lower them and let
    # a stronger student clear them more easily.
    bar_target, bar_safer = 0.50, 0.70
    if student_strength is not None:
        shift = (student_strength - 0.5) * 0.20
        bar_target = _clamp(bar_target - shift, 0.30, 0.75)
        bar_safer = _clamp(bar_safer - shift, 0.45, 0.88)
    if f >= bar_safer:
        return "safer"
    if f >= bar_target:
        return "target"
    return "reach"


def band_for_acceptance(
    *,
    fitness: float,
    acceptance_rate: float | None,
    weight_ranking: int | None,
    student_gpa: float | None = None,
) -> str:
    """Convenience wrapper that derives selectivity + tolerance + student
    strength from raw program/preference/profile fields and classifies the band."""
    return classify_band(
        fitness=fitness,
        selectivity=selectivity_from_acceptance(acceptance_rate),
        tolerance=tolerance_from_preferences(weight_ranking),
        student_strength=strength_from_gpa(student_gpa),
    )


def weights_from_preferences(pref: Any | None) -> dict[str, float] | None:
    """Map the priority sliders (0–10) to matcher composition weights.

    Spec 09 §5.2 surfaces six sliders — Cost · Outcomes · Selectivity ·
    Location · Modality · Time-to-degree — and every one must measurably
    re-rank (§12). They fold into the matcher's three levers:
      - outcomes + ranking (academic/career substance)        → ``cosine``
      - support (needs-fit baseline; no dedicated §5.2 slider) → ``needs_match``
      - cost + location + flexibility + time_to_degree (fit)   → ``soft_align``

    ``ranking`` additionally drives the reach/target/safer banding tolerance
    (``tolerance_from_preferences``), so Selectivity moves both rank and band.

    Returns ``None`` when no slider is set, so the caller uses
    ``DEFAULT_WEIGHTS`` unchanged. Output is normalized to ~1.0 (each weight
    rounded to 4dp for readable stored breakdowns).
    """
    if pref is None:
        return None

    cost = getattr(pref, "weight_cost", None)
    outcomes = getattr(pref, "weight_outcomes", None)
    ranking = getattr(pref, "weight_ranking", None)
    location = getattr(pref, "weight_location", None)
    flexibility = getattr(pref, "weight_flexibility", None)
    support = getattr(pref, "weight_support", None)
    time_to_degree = getattr(pref, "weight_time_to_degree", None)

    if all(
        v is None for v in (cost, outcomes, ranking, location, flexibility, support, time_to_degree)
    ):
        return None

    def g(v: int | None) -> float:
        # Unset sliders fall back to the neutral midpoint so a single set
        # slider tilts the mix without zeroing the others.
        return float(v) if v is not None else 5.0

    raw_cosine = 1.0 + g(outcomes) + g(ranking)
    raw_needs = 1.0 + g(support)
    raw_soft = 1.0 + g(cost) + g(location) + g(flexibility) + g(time_to_degree)
    total = raw_cosine + raw_needs + raw_soft
    return {
        "cosine": round(raw_cosine / total, 4),
        "soft_align": round(raw_soft / total, 4),
        "needs_match": round(raw_needs / total, 4),
    }


# Priority slider → CPEF signal. The legacy ``weights_from_preferences`` above folds
# the sliders into the convex-sum levers, but those are DROPPED under CPEF — so under
# the live path the sliders must instead tilt per-signal CPEF weights. Five sliders
# map onto an existing s→p signal; ``weight_outcomes`` has no CPEF signal yet, and
# ``weight_ranking`` drives banding tolerance (``tolerance_from_preferences``), not a fit.
_SLIDER_TO_CPEF_SIGNAL: dict[str, str] = {
    "weight_cost": "budget",
    "weight_location": "geo",
    "weight_flexibility": "flexibility",
    "weight_support": "support",
    "weight_time_to_degree": "time",
}


def cpef_params_from_preferences(pref: Any | None) -> dict[str, float] | None:
    """Map the priority sliders (0–10) to CPEF per-signal weights so they actually
    re-rank under the live (CPEF) path.

    Each set slider tilts its signal's importance around the uniform ``w_base``
    (slider 5 ≈ neutral ``w_base``; 0 → 0.5×; 10 → 1.5×). Returns the full params
    dict (``DEFAULT_PARAMS`` + the ``w_<signal>`` overrides) so every other tuning
    key stays present, or ``None`` when no mappable slider is set (caller then uses
    ``DEFAULT_PARAMS`` unchanged). Threaded through rank_programs → score →
    _score_cpef → _build_cpef_signals, which reads ``params["w_<signal>"]``."""
    if pref is None:
        return None
    w_base = float(DEFAULT_PARAMS["w_base"])
    overrides: dict[str, float] = {}
    for slider_attr, sig_key in _SLIDER_TO_CPEF_SIGNAL.items():
        val = getattr(pref, slider_attr, None)
        if val is None:
            continue
        v = max(0.0, min(10.0, float(val)))
        overrides[f"w_{sig_key}"] = round(w_base * (0.5 + v / 10.0), 4)
    if not overrides:
        return None
    return {**DEFAULT_PARAMS, **overrides}


__all__ = [
    "band_for_acceptance",
    "classify_band",
    "cpef_params_from_preferences",
    "selectivity_from_acceptance",
    "tolerance_from_preferences",
    "weights_from_preferences",
]

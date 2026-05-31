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


def classify_band(
    *,
    fitness: float,
    selectivity: float | None,
    tolerance: float | None,
) -> str:
    """Return ``"reach" | "target" | "safer"`` (Spec 09 §6).

    Primary signal is selectivity-vs-tolerance — a program more selective
    than the student's comfort is a *reach*; less selective is *safer*. When
    selectivity is unknown we fall back to the spec's fitness thresholds
    (scaled to the 0–1 score space).
    """
    f = _clamp(float(fitness), 0.0, 1.0)
    if selectivity is None or tolerance is None:
        # Fitness-only fallback (Spec 09 §6 thresholds, 0–100 → 0–1).
        if f >= 0.75:
            return "safer"
        if f >= 0.65:
            return "target"
        return "reach"
    gap = float(selectivity) - float(tolerance)
    if gap > 0.12:
        return "reach"
    if gap < -0.12:
        return "safer"
    return "target"


def band_for_acceptance(
    *,
    fitness: float,
    acceptance_rate: float | None,
    weight_ranking: int | None,
) -> str:
    """Convenience wrapper that derives selectivity + tolerance from raw
    program/preference fields and classifies the band."""
    return classify_band(
        fitness=fitness,
        selectivity=selectivity_from_acceptance(acceptance_rate),
        tolerance=tolerance_from_preferences(weight_ranking),
    )


def weights_from_preferences(pref: Any | None) -> dict[str, float] | None:
    """Map the 6 priority sliders (0–10) to matcher composition weights.

    Spec 09 §5.2 sliders → matcher levers:
      - outcomes + ranking (academic/career substance) → ``cosine`` (content)
      - support                                        → ``needs_match``
      - cost + location + flexibility (lifestyle fit)  → ``soft_align``

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

    if all(v is None for v in (cost, outcomes, ranking, location, flexibility, support)):
        return None

    def g(v: int | None) -> float:
        # Unset sliders fall back to the neutral midpoint so a single set
        # slider tilts the mix without zeroing the others.
        return float(v) if v is not None else 5.0

    raw_cosine = 1.0 + g(outcomes) + g(ranking)
    raw_needs = 1.0 + g(support)
    raw_soft = 1.0 + g(cost) + g(location) + g(flexibility)
    total = raw_cosine + raw_needs + raw_soft
    return {
        "cosine": round(raw_cosine / total, 4),
        "soft_align": round(raw_soft / total, 4),
        "needs_match": round(raw_needs / total, 4),
    }


__all__ = [
    "band_for_acceptance",
    "classify_band",
    "selectivity_from_acceptance",
    "tolerance_from_preferences",
    "weights_from_preferences",
]

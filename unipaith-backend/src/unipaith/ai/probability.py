"""ProbabilityBandEstimator (Spec 09 §4A, §9 — NEW).

Answers a *different* question from fitness + confidence: **"what's my
realistic shot?"** — conservative ranges for three admissions outcomes
(admit / scholarship / waitlist) plus the top drivers behind them.

Design principles (Spec 09 §4A + Spec 46 §6 honesty/fairness guardrail):

- **Always a range, never false precision.** Width encodes uncertainty —
  the less we know (low confidence), the wider the band.
- **Decision-support, not a promise.** Institutions decide, not the model;
  copy and labels never present a band as a guarantee.
- **Honest "not enough data".** When the program has no historical admit
  signal OR the student isn't match-ready, we return ``None`` so the UI can
  say "Not enough data yet" rather than inventing a misleading number.

MVP fidelity: rule-based + calibrated heuristic over the historical admit
rate, the student's fitness, and model confidence. The shape it emits is
identical to the (future) ML-backed estimator, so swapping in a learned
model later is pure substitution — callers and the UI don't change.
"""

from __future__ import annotations

# Match-ready minimum (Spec 42 §6.1 proxy): below this confidence the model
# doesn't know the student well enough to put a number on their odds.
MATCH_READY_MIN_CONFIDENCE = 0.30


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def is_match_ready(confidence: float | None) -> bool:
    """Spec 42 §6.1 — does the student meet the match-ready minimum?

    Confidence already folds in profile completeness + program data quality
    (see ``services.matching`` confidence math), so it is the right single
    gate for "do we know enough to estimate odds".
    """
    return confidence is not None and float(confidence) >= MATCH_READY_MIN_CONFIDENCE


def _admit_label(center: float) -> str:
    if center >= 0.60:
        return "likely"
    if center >= 0.35:
        return "target"
    if center >= 0.12:
        return "reach"
    return "unlikely"


def estimate_probability_bands(
    *,
    acceptance_rate: float | None,
    fitness: float,
    confidence: float,
    offers_aid: bool | None = None,
) -> dict | None:
    """Return the probability-band dict for one (student, program) pair, or
    ``None`` when there isn't enough signal to be honest.

    Parameters
    ----------
    acceptance_rate:
        Program's historical admit rate in ``[0, 1]`` (``programs.acceptance_rate``).
        ``None`` means no historical signal.
    fitness, confidence:
        The match's dual scores, each in ``[0, 1]``.
    offers_aid:
        Whether the program is known to offer merit/need aid. ``None`` = unknown;
        we fall back to a conservative fit-gated scholarship estimate.

    Returns
    -------
    dict | None
        Shape (matches Spec 09 §7 ``MatchResult.probability_bands``)::

            {
              "admit":       {"low": float, "high": float, "label": str},
              "scholarship": {"low": float, "high": float} | None,
              "waitlist":    {"approx": float} | None,
              "drivers":     [{"signal": str, "direction": "up"|"down"}],
            }

        ``None`` when ``acceptance_rate is None`` (no history) OR the student
        isn't match-ready (Spec 09 §4A rule).
    """
    # Spec 09 §4A rule: need BOTH historical signal AND a match-ready student.
    if acceptance_rate is None or not is_match_ready(confidence):
        return None

    fitness = _clamp(float(fitness), 0.0, 1.0)
    confidence = _clamp(float(confidence), 0.0, 1.0)
    ar = _clamp(float(acceptance_rate), 0.005, 0.99)

    # Fit lift: a strong-fit applicant beats the base admit rate; a weak-fit
    # one trails it. Centred so fitness=0.5 leaves the base rate unchanged.
    lift = 0.5 + fitness  # 0.0→0.5×, 0.5→1.0×, 1.0→1.5×
    center = _clamp(ar * lift, 0.02, 0.97)

    # Band half-width encodes uncertainty: low confidence ⇒ wider band.
    half = 0.06 + (1.0 - confidence) * 0.18  # 6%–24%
    admit_low = _clamp(center - half, 0.01, 0.97)
    admit_high = _clamp(center + half, admit_low + 0.02, 0.99)

    # Scholarship — conservative; merit/need aid correlates with strong fit.
    # Only surface when fit is meaningful (or the program is known to offer aid),
    # so we never imply funding we can't support.
    scholarship: dict | None = None
    if offers_aid is not False and fitness >= 0.50:
        sch_center = _clamp(center * 0.5 * (0.5 + fitness), 0.02, 0.55)
        sch_half = 0.05 + (1.0 - confidence) * 0.10
        sch_low = _clamp(sch_center - sch_half, 0.01, 0.6)
        sch_high = _clamp(sch_center + sch_half, sch_low + 0.02, 0.7)
        scholarship = {"low": round(sch_low, 2), "high": round(sch_high, 2)}

    # Waitlist — small residual; only meaningful when admission isn't near-certain.
    waitlist: dict | None = None
    if center < 0.85:
        waitlist_approx = _clamp((1.0 - center) * 0.12, 0.02, 0.20)
        waitlist = {"approx": round(waitlist_approx, 2)}

    # Top drivers (≤4) — the signals the popover surfaces (Spec 09 §4A).
    drivers: list[dict] = [
        {"signal": "Historical admit rate", "direction": "up" if ar >= 0.40 else "down"},
        {"signal": "Profile fit", "direction": "up" if fitness >= 0.55 else "down"},
    ]
    if ar <= 0.20:
        drivers.append({"signal": "High selectivity", "direction": "down"})
    drivers.append(
        {"signal": "Data confidence", "direction": "up" if confidence >= 0.60 else "down"}
    )

    return {
        "admit": {
            "low": round(admit_low, 2),
            "high": round(admit_high, 2),
            "label": _admit_label(center),
        },
        "scholarship": scholarship,
        "waitlist": waitlist,
        "drivers": drivers[:4],
    }


__all__ = [
    "MATCH_READY_MIN_CONFIDENCE",
    "estimate_probability_bands",
    "is_match_ready",
]

"""Phase D2 — Confidence calibration.

The matcher's `confidence_score` is a geometric mean of four [0,1]
quality terms. Cold start: that's the raw confidence we display. As
real outcomes flow in (apply → accept → enroll), we fit a calibrator
that maps raw confidence to actual outcome rate.

Why isotonic regression
-----------------------
- Monotonic by construction — preserves the "higher confidence ≥
  lower confidence" ordering, which fitness/confidence semantics
  require.
- Non-parametric — doesn't assume a sigmoid or beta curve; works
  with weird score distributions.
- Cheap to fit (O(N log N)) and to apply (O(log N)).
- Standard sklearn — already in our deps for the existing ML loop.

Storage
-------
A fitted calibrator is a small ordered list of (raw_x, calibrated_y)
breakpoints — JSONB. We store it in the model registry pattern this
codebase already uses (`ml_loop.ModelRegistry`) under a fixed key
`"confidence_calibrator"` with a version bump on every refit.

What this module does
---------------------
- `fit_calibrator(pairs)` — fit isotonic regression on
  (predicted_confidence, ground_truth_outcome) pairs. Returns a
  CalibratorState dict that persists as JSON.
- `apply_calibrator(state, raw_confidence)` — calibrate a raw score.
- `reliability_diagram(pairs, n_bins)` — return bucketed
  (mean_predicted, observed_rate) for the admin reliability plot.
- Cold start path: when no calibrator is fitted, `apply_calibrator`
  is the identity — the matcher's raw confidence flows through
  unchanged. The UI labels confidence "uncalibrated" until ≥1k
  outcome pairs have been collected (the threshold lives in
  `MIN_PAIRS_FOR_CALIBRATION`).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# Minimum number of (predicted_confidence, outcome) pairs before we'll
# fit a calibrator. Below this, we fall through to the identity (raw
# confidence shown as-is, UI labels it "uncalibrated").
MIN_PAIRS_FOR_CALIBRATION = 1_000


@dataclass
class CalibratorState:
    """Serializable calibrator. Persisted as JSONB under the registry key."""

    fitted: bool = False
    n_samples: int = 0
    # Ordered breakpoints. Each entry is [raw_x, calibrated_y]. We
    # interpolate between adjacent breakpoints at apply time.
    breakpoints: list[list[float]] = field(default_factory=list)
    # Reliability metrics at fit time — used by the admin dashboard
    # without re-fitting.
    reliability: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "fitted": self.fitted,
            "n_samples": self.n_samples,
            "breakpoints": list(self.breakpoints),
            "reliability": dict(self.reliability),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> CalibratorState:
        if not data:
            return cls()
        return cls(
            fitted=bool(data.get("fitted", False)),
            n_samples=int(data.get("n_samples", 0)),
            breakpoints=[list(p) for p in data.get("breakpoints", []) if len(p) == 2],
            reliability=dict(data.get("reliability", {})),
        )


# ── Fit ────────────────────────────────────────────────────────────────────


def fit_calibrator(
    pairs: list[tuple[float, int]],
    *,
    out_of_bounds: str = "clip",
) -> CalibratorState:
    """Fit isotonic regression on (predicted, outcome) pairs.

    Outcomes are 0/1 (binary). Predictions are [0, 1] floats.
    Returns a CalibratorState with the fitted breakpoints + reliability
    metrics. If `pairs` is below MIN_PAIRS_FOR_CALIBRATION, returns an
    unfitted state — the apply path stays identity.
    """
    if len(pairs) < MIN_PAIRS_FOR_CALIBRATION:
        logger.info(
            "fit_calibrator: %d pairs < %d minimum; calibrator stays unfitted",
            len(pairs),
            MIN_PAIRS_FOR_CALIBRATION,
        )
        return CalibratorState(
            fitted=False,
            n_samples=len(pairs),
            breakpoints=[],
            reliability={"reason": "below_minimum_samples"},
        )

    # Lazy import sklearn — keeps test imports cheap.
    try:
        from sklearn.isotonic import IsotonicRegression
    except ImportError:  # pragma: no cover
        logger.warning("sklearn unavailable; calibrator stays unfitted")
        return CalibratorState(fitted=False, n_samples=len(pairs))

    xs = [max(0.0, min(1.0, float(p[0]))) for p in pairs]
    ys = [1 if int(p[1]) > 0 else 0 for p in pairs]

    iso = IsotonicRegression(
        y_min=0.0, y_max=1.0, out_of_bounds=out_of_bounds, increasing=True
    )
    iso.fit(xs, ys)

    # Store as breakpoints — sklearn exposes X_thresholds_ / y_thresholds_
    # for the piecewise-linear interpolation. If those attributes aren't
    # present (older sklearn), sample at 21 evenly-spaced points.
    if hasattr(iso, "X_thresholds_") and hasattr(iso, "y_thresholds_"):
        bp_x = [float(x) for x in iso.X_thresholds_]
        bp_y = [float(y) for y in iso.y_thresholds_]
    else:  # pragma: no cover — fallback for old sklearn
        bp_x = [i / 20 for i in range(21)]
        bp_y = [float(iso.predict([x])[0]) for x in bp_x]

    breakpoints = sorted(zip(bp_x, bp_y, strict=False))
    breakpoints_list = [[float(x), float(y)] for x, y in breakpoints]

    rel = reliability_diagram(pairs, n_bins=10)
    return CalibratorState(
        fitted=True,
        n_samples=len(pairs),
        breakpoints=breakpoints_list,
        reliability=rel,
    )


# ── Apply ──────────────────────────────────────────────────────────────────


def apply_calibrator(state: CalibratorState, raw_confidence: float) -> float:
    """Map a raw confidence to a calibrated confidence.

    Identity when state is unfitted (cold start). When fitted, linear
    interpolation between adjacent breakpoints — same as sklearn's
    isotonic predict, but cheaper and serialization-free at runtime.
    """
    raw = max(0.0, min(1.0, float(raw_confidence)))
    if not state.fitted or not state.breakpoints:
        return raw

    bps = state.breakpoints
    if raw <= bps[0][0]:
        return float(bps[0][1])
    if raw >= bps[-1][0]:
        return float(bps[-1][1])
    # Binary search would be cleaner; for ≤21 breakpoints linear is fine.
    for i in range(len(bps) - 1):
        x0, y0 = bps[i]
        x1, y1 = bps[i + 1]
        if x0 <= raw <= x1:
            if x1 == x0:
                return float(y0)
            t = (raw - x0) / (x1 - x0)
            return float(y0 + t * (y1 - y0))
    return raw  # pragma: no cover — defensive


# ── Reliability diagram ────────────────────────────────────────────────────


def reliability_diagram(
    pairs: list[tuple[float, int]], *, n_bins: int = 10
) -> dict[str, Any]:
    """Bucketed (mean_predicted, observed_rate) for the admin plot.

    Returns:
      {
        "n_bins": 10,
        "n_samples": <int>,
        "bins": [{"mid": 0.05, "count": N, "mean_predicted": ..., "observed_rate": ...}, ...],
        "ece": <expected calibration error>,
        "max_gap": <max |observed - predicted| across non-empty bins>,
      }

    ECE = sum_i (count_i / N) * |observed_rate_i - mean_predicted_i|.
    Lower is better; <0.05 is a good calibration target.
    """
    if not pairs:
        return {"n_bins": n_bins, "n_samples": 0, "bins": [], "ece": None, "max_gap": None}

    bins: list[dict[str, Any]] = [
        {
            "mid": (i + 0.5) / n_bins,
            "lo": i / n_bins,
            "hi": (i + 1) / n_bins,
            "count": 0,
            "sum_predicted": 0.0,
            "sum_outcome": 0,
        }
        for i in range(n_bins)
    ]
    for pred, outcome in pairs:
        p = max(0.0, min(1.0, float(pred)))
        idx = min(int(p * n_bins), n_bins - 1)
        b = bins[idx]
        b["count"] += 1
        b["sum_predicted"] += p
        b["sum_outcome"] += int(outcome > 0)

    total = len(pairs)
    ece = 0.0
    max_gap = 0.0
    out_bins: list[dict[str, Any]] = []
    for b in bins:
        c = b["count"]
        if c == 0:
            mean_pred = (b["lo"] + b["hi"]) / 2
            obs_rate = None
        else:
            mean_pred = b["sum_predicted"] / c
            obs_rate = b["sum_outcome"] / c
            gap = abs(obs_rate - mean_pred)
            ece += (c / total) * gap
            if gap > max_gap:
                max_gap = gap
        out_bins.append(
            {
                "mid": b["mid"],
                "lo": b["lo"],
                "hi": b["hi"],
                "count": c,
                "mean_predicted": round(mean_pred, 4) if mean_pred is not None else None,
                "observed_rate": round(obs_rate, 4) if obs_rate is not None else None,
            }
        )
    return {
        "n_bins": n_bins,
        "n_samples": total,
        "bins": out_bins,
        "ece": round(ece, 4),
        "max_gap": round(max_gap, 4),
    }

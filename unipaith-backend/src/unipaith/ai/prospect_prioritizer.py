"""Spec 40 §5 — ProspectPrioritizer.

Ranks pre-applicant prospects by apply-likelihood so recruiters work the warmest
leads first. MVP fidelity is a calibrated, deterministic propensity heuristic over
the observable prospect signals (stage, source warmth, contactability, expressed
interest, outreach consent) — mirroring ``ai/probability.py`` / the YieldRiskScorer.
The registry tier (``batch`` / Haiku) documents the future ML propensity model
(Spec 42 §4.15-style ``apply_probability``).

Pure and deterministic — it never 5xxes. The recruitment service only applies it
when ``ai_recruitment_v2_enabled`` is on; otherwise prospects fall back to manual
(recency) sorting (§5: "Falls back to manual sorting"). No selection decisions —
prioritization only (§5 / 46 §6).
"""

from __future__ import annotations

# Stage → base apply-likelihood. The funnel itself is the strongest signal.
_STAGE_BASE = {
    "suspect": 0.12,
    "prospect": 0.28,
    "engaged": 0.52,
    "inquiry": 0.72,
    "applicant": 1.0,
}

# Source warmth lift. Inbound/referred leads convert better than cold lists.
_SOURCE_LIFT = {
    "inquiry": 0.15,
    "referral": 0.12,
    "visit": 0.08,
    "fair": 0.05,
    "web": 0.0,
    "list": -0.06,
}


def _clamp(v: float, lo: float = 0.02, hi: float = 0.99) -> float:
    return max(lo, min(hi, v))


def apply_likelihood(prospect: dict) -> float:
    """Estimate the probability a prospect will start an application, from
    observable signals. Deterministic calibrated heuristic (Spec 40 §5).

    ``prospect`` keys (all optional): ``stage``, ``source``, ``email``,
    ``phone``, ``interests`` (list), ``consent_outreach`` (bool).
    """
    stage = prospect.get("stage") or "prospect"
    if stage == "applicant":
        return 1.0

    prob = _STAGE_BASE.get(stage, 0.28)
    prob += _SOURCE_LIFT.get(prospect.get("source") or "web", 0.0)

    if prospect.get("email"):
        prob += 0.05  # reachable
    if prospect.get("phone"):
        prob += 0.03
    interests = prospect.get("interests")
    if isinstance(interests, list) and interests:
        prob += 0.05  # expressed a program interest
    if prospect.get("consent_outreach"):
        prob += 0.05  # opted into outreach — a warmer signal

    return round(_clamp(prob), 3)


def priority_band(prob: float) -> str:
    if prob >= 0.6:
        return "hot"
    if prob >= 0.35:
        return "warm"
    return "cold"


def _reason(prospect: dict, prob: float) -> str:
    """A short, plain-language why for the score (no hype)."""
    bits: list[str] = []
    stage = prospect.get("stage") or "prospect"
    source = prospect.get("source") or "web"
    if stage in ("inquiry", "engaged"):
        bits.append(f"already {stage}")
    if source in ("inquiry", "referral"):
        bits.append(f"inbound via {source}")
    elif source in ("fair", "visit"):
        bits.append(f"met at a {source}")
    if isinstance(prospect.get("interests"), list) and prospect.get("interests"):
        bits.append("shared a program interest")
    if not prospect.get("email") and not prospect.get("phone"):
        bits.append("no contact on file")
    band = priority_band(prob)
    lead = {
        "hot": "High apply-likelihood",
        "warm": "Moderate apply-likelihood",
        "cold": "Early-stage lead",
    }[band]
    return f"{lead}: {', '.join(bits)}." if bits else f"{lead}."


class ProspectPrioritizer:
    """Per-prospect apply-likelihood + ranked list (deterministic)."""

    AGENT_NAME = "prospect_prioritizer"
    PROMPT_VERSION = "v1"

    def score(self, prospects: list[dict]) -> dict[str, dict]:
        """Return ``{prospect_id: {apply_likelihood, band, reason}}`` for the
        given prospect dicts. Each dict must carry an ``id`` key."""
        out: dict[str, dict] = {}
        for p in prospects:
            pid = p.get("id")
            if pid is None:
                continue
            prob = apply_likelihood(p)
            out[str(pid)] = {
                "apply_likelihood": prob,
                "band": priority_band(prob),
                "reason": _reason(p, prob),
            }
        return out


# ── Singleton ────────────────────────────────────────────────────────────────
_prioritizer: ProspectPrioritizer | None = None


def get_prospect_prioritizer() -> ProspectPrioritizer:
    global _prioritizer
    if _prioritizer is None:
        _prioritizer = ProspectPrioritizer()
    return _prioritizer


def reset_prospect_prioritizer() -> None:
    global _prioritizer
    _prioritizer = None

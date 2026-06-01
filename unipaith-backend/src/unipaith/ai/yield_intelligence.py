"""Spec 35 §6 — Enrollment-yield intelligence agents.

``YieldRiskScorer`` — per-admit confirm-probability + at-risk list. MVP fidelity
is a calibrated heuristic over the observable yield signals (deadline proximity,
offer response, deposit, aid, fit), mirroring ``ai/probability.py``; the registry
tier documents the future ML model (Spec 42 §4.15 ``yield_probability``). Pure
and deterministic — it never 5xxes.

``NextBestActionForYield`` — turns the yield snapshot into a short ranked list of
next-best-actions. Sonnet, forced tool-use, behind ``ai_yield_intelligence_v2_enabled``;
returns ``None`` on any failure so the service falls back to its deterministic
ranking. Fairness: yield work is outreach, never selection (§4 / 46 §6).
"""

from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai.client import AIClient, get_client
from unipaith.ai.prompt_cache import CACHE_1H
from unipaith.ai.tools.yield_action_schema import SUBMIT_YIELD_ACTIONS_TOOL

logger = logging.getLogger("unipaith.yield_intelligence")

PROMPTS_DIR = Path(__file__).parent / "prompts"


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def confirm_probability(signal: dict) -> float:
    """Estimate the probability an admit will end up enrolling, from observable
    signals. Deterministic calibrated heuristic (Spec 35 §6 MVP fidelity).

    ``signal`` keys (all optional): ``state`` (enrollment state),
    ``offer_response`` ('accepted'|'declined'|None), ``deposit_status``,
    ``days_remaining`` (to the offer deadline; negative = past),
    ``scholarship_amount``, ``fitness`` (0..1).
    """
    state = signal.get("state")
    if state == "enrolled":
        return 1.0
    if state in ("enrollment_confirmed", "deposit_recorded"):
        return 0.97
    if state == "intent_confirmed":
        # Confirmed intent but not deposited — strong, with a little melt risk.
        return 0.9 if signal.get("deposit_status") in ("paid", "waived") else 0.85
    if state == "withdrew" or signal.get("offer_response") == "declined":
        return 0.0

    # Accepted the offer but hasn't confirmed enrollment intent yet.
    if signal.get("offer_response") == "accepted":
        prob = 0.8
    else:
        # Offer still unanswered — the genuinely at-risk pool.
        prob = 0.5
        days = signal.get("days_remaining")
        if isinstance(days, int | float):
            if days < 0:
                prob -= 0.30  # deadline passed, no response
            elif days <= 3:
                prob -= 0.18
            elif days <= 7:
                prob -= 0.10
            elif days <= 14:
                prob -= 0.04

    # Aid and fit lift confirm-likelihood for the unconfirmed pool.
    if signal.get("scholarship_amount"):
        prob += 0.08
    fitness = signal.get("fitness")
    if isinstance(fitness, int | float):
        prob += (float(fitness) - 0.5) * 0.16
    return round(_clamp(prob, 0.02, 0.99), 3)


def risk_level(prob: float) -> str:
    if prob < 0.4:
        return "high"
    if prob < 0.65:
        return "medium"
    return "low"


class YieldRiskScorer:
    """Per-admit confirm-probability + at-risk list (deterministic)."""

    AGENT_NAME = "yield_risk_scorer"
    PROMPT_VERSION = "v1"

    def score(self, admits: list[dict]) -> dict:
        scored: list[dict] = []
        for a in admits:
            prob = confirm_probability(a)
            scored.append(
                {
                    **{k: a.get(k) for k in ("application_id", "student_id", "student_name")},
                    "confirm_probability": prob,
                    "risk_level": risk_level(prob),
                    "state": a.get("state"),
                    "days_remaining": a.get("days_remaining"),
                }
            )
        # At-risk = not yet confirmed and below the comfortable threshold.
        at_risk = [
            s
            for s in scored
            if s["state"] not in ("enrolled", "enrollment_confirmed", "deposit_recorded")
            and s["confirm_probability"] < 0.65
        ]
        at_risk.sort(key=lambda s: s["confirm_probability"])
        expected = round(sum(s["confirm_probability"] for s in scored), 1)
        return {"scored": scored, "at_risk": at_risk, "expected_confirmations": expected}


# ── NextBestActionForYield (LLM, optional) ──────────────────────────────────


def _load_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8").rstrip()


class NextBestActionForYield:
    AGENT_NAME = "next_best_action_yield"
    PROMPT_VERSION = "v1"

    def __init__(self, client: AIClient | None = None, *, system_prompt: str | None = None):
        self.client = client or get_client()
        self.system_prompt = system_prompt or _load_prompt("next_best_action_yield.md")

    async def rank(self, snapshot: dict, *, db: AsyncSession | None = None) -> list[dict] | None:
        """Return up to 5 ranked actions, or ``None`` on any failure (caller
        falls back to the deterministic ranking)."""
        try:
            response = await self.client.message(
                agent=self.AGENT_NAME,
                model="sonnet",
                system=[{"type": "text", "text": self.system_prompt, "cache_control": CACHE_1H}],
                messages=[{"role": "user", "content": self._payload(snapshot)}],
                tools=[{**SUBMIT_YIELD_ACTIONS_TOOL, "cache_control": CACHE_1H}],
                tool_choice={"type": "tool", "name": "submit_yield_actions"},
                max_tokens=700,
                temperature=0.3,
                student_id=None,  # institution-side aggregate; no student PII
                surface="yield_actions",
                db=db,
            )
        except Exception as e:  # noqa: BLE001
            logger.warning("next_best_action_yield agent call failed: %s", e)
            return None

        for b in response.content_blocks:
            if b.get("type") == "tool_use" and b.get("name") == "submit_yield_actions":
                actions = (b.get("input") or {}).get("actions") or []
                out = [
                    {
                        "kind": str(a.get("kind") or "monitor"),
                        "label": str(a.get("label") or "").strip(),
                        "rationale": str(a.get("rationale") or "").strip(),
                        "count": a.get("count"),
                    }
                    for a in actions
                    if str(a.get("label") or "").strip()
                ]
                return out[:5] or None
        return None

    @staticmethod
    def _payload(s: dict) -> str:
        lines = [
            "Yield snapshot:",
            f"- Admitted: {s.get('admitted', 0)}",
            f"- Confirmed intent: {s.get('intent_confirmed', 0)}",
            f"- Deposited: {s.get('deposited', 0)}",
            f"- Enrolled: {s.get('enrolled', 0)}",
            f"- Admits w/ unanswered offer near/past deadline: {s.get('unconfirmed_at_risk', 0)}",
            f"- Soonest deadline (days): {s.get('soonest_deadline_days')}",
            f"- Seats open: {s.get('seats_open')}",
            f"- On waitlist: {s.get('waitlist_count', 0)}",
            f"- Target class size set: {bool(s.get('target_class_size'))}",
            "",
            "Call submit_yield_actions with the ranked next-best-actions.",
        ]
        return "\n".join(lines)


# ── Singletons ──────────────────────────────────────────────────────────────
_scorer: YieldRiskScorer | None = None
_action_agent: NextBestActionForYield | None = None


def get_yield_risk_scorer() -> YieldRiskScorer:
    global _scorer
    if _scorer is None:
        _scorer = YieldRiskScorer()
    return _scorer


def get_next_best_action_agent() -> NextBestActionForYield:
    global _action_agent
    if _action_agent is None:
        _action_agent = NextBestActionForYield()
    return _action_agent


def reset_yield_agents() -> None:
    global _scorer, _action_agent
    _scorer = None
    _action_agent = None

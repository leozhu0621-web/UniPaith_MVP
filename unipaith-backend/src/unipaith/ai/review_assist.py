"""Spec 32 review-workspace assist agents — ReviewSynthesisAgent (§4) and
ReviewAssistant (§6). Both run on Sonnet (workhorse) with forced tool-use and
a deterministic rule-based fallback, so the reviewer surface never 5xxes and
works in mock mode / offline.

Contract (matches the rest of the L2 stack):
  * **workhorse/Sonnet** tier requested.
  * Forced tool-use; output validated.
  * On ANY failure (provider down, parse error, consent, mock mode) →
    rule-based fallback built from the structured inputs. ``is_stub`` records
    which path served the result so the UI can badge "rule-based".

Both are institution-initiated and role-gated at the API layer (like
``review_summarizer``); they carry no student-consent lever (see
``ai/consent.py``).
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai.client import AIClient, get_client
from unipaith.ai.prompt_cache import CACHE_1H
from unipaith.ai.tools.review_assist_schema import (
    SUBMIT_REVIEW_ANSWER_TOOL,
    SUBMIT_REVIEW_SYNTHESIS_TOOL,
)

logger = logging.getLogger(__name__)

# Δ at/above which two reviewers are flagged as divergent on a criterion (§4).
VARIANCE_THRESHOLD = 1.5


# ── Synthesis ────────────────────────────────────────────────────────────────

_SYNTHESIS_PROMPT = (
    "You are an admissions committee facilitator. Given several reviewers' "
    "rubric scores and notes for ONE applicant, synthesize a balanced "
    "recommendation using the submit_review_synthesis tool. Rules: surface "
    "agreement AND divergence honestly; quote reviewers' own reasoning where "
    "useful; flag any criterion where scores differ by 1.5 or more as "
    "divergent; you produce a synthesis for humans, never a final admit/deny "
    "decision. Keep the overall synthesis to 2-5 sentences."
)


@dataclass
class SynthesisResult:
    overall_recommendation: str = ""
    agreement: str = "mixed"
    per_criterion: list[dict[str, Any]] = field(default_factory=list)
    is_stub: bool = True
    cost_usd: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall_recommendation": self.overall_recommendation,
            "agreement": self.agreement,
            "per_criterion": self.per_criterion,
            "model_used": "rule_based" if self.is_stub else "workhorse",
        }


class ReviewSynthesisAgent:
    """Spec 32 §4 — synthesize 2+ reviewers into one recommendation (Sonnet)."""

    AGENT_NAME = "review_synthesis"

    def __init__(
        self,
        client: AIClient | None = None,
        *,
        max_tokens: int = 1100,
        temperature: float = 0.3,
    ):
        self.client = client or get_client()
        self.max_tokens = max_tokens
        self.temperature = temperature

    async def synthesize(
        self,
        *,
        criteria: list[dict[str, Any]],
        reviewers: list[dict[str, Any]],
        applicant_name: str = "the applicant",
        db: AsyncSession | None = None,
    ) -> SynthesisResult:
        """``criteria``: [{name, weight}]. ``reviewers``:
        [{reviewer_name, criterion_scores:{name:score}, note}]. Never raises."""
        if len(reviewers) < 2:
            # Synthesis is only meaningful with 2+ reviewers.
            return _rule_based_synthesis(criteria, reviewers)
        try:
            payload = json.dumps(
                {
                    "applicant_name": applicant_name,
                    "criteria": criteria,
                    "reviewers": reviewers,
                },
                ensure_ascii=False,
                default=str,
            )
            response = await self.client.message(
                agent=self.AGENT_NAME,
                model="workhorse",
                system=[{"type": "text", "text": _SYNTHESIS_PROMPT, "cache_control": CACHE_1H}],
                messages=[{"role": "user", "content": payload}],
                tools=[{**SUBMIT_REVIEW_SYNTHESIS_TOOL, "cache_control": CACHE_1H}],
                tool_choice={"type": "tool", "name": "submit_review_synthesis"},
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                surface="review_synthesis",
                db=db,
            )
            for b in response.content_blocks:
                if b.get("type") == "tool_use" and b.get("name") == "submit_review_synthesis":
                    inp = b.get("input") or {}
                    text = str(inp.get("overall_recommendation") or "").strip()
                    if text:
                        return SynthesisResult(
                            overall_recommendation=text,
                            agreement=str(inp.get("agreement") or "mixed"),
                            per_criterion=list(inp.get("per_criterion") or []),
                            is_stub=False,
                            cost_usd=float(response.cost_usd),
                        )
        except Exception as exc:  # noqa: BLE001 — never break the reviewer surface
            logger.info("review_synthesis falling back to rule-based: %s", exc)
        return _rule_based_synthesis(criteria, reviewers)


def _rule_based_synthesis(
    criteria: list[dict[str, Any]],
    reviewers: list[dict[str, Any]],
) -> SynthesisResult:
    """Deterministic synthesis from the score matrix — what mock mode / any
    environment without Sonnet sees. Honest about agreement vs divergence."""
    names = [c.get("name") for c in criteria if c.get("name")]
    per_criterion: list[dict[str, Any]] = []
    max_spread = 0.0
    divergent_count = 0
    for name in names:
        vals = [
            float(r["criterion_scores"][name])
            for r in reviewers
            if isinstance(r.get("criterion_scores"), dict)
            and r["criterion_scores"].get(name) is not None
        ]
        if not vals:
            continue
        spread = max(vals) - min(vals)
        max_spread = max(max_spread, spread)
        divergent = spread >= VARIANCE_THRESHOLD
        if divergent:
            divergent_count += 1
        avg = sum(vals) / len(vals)
        per_criterion.append(
            {
                "criterion_name": name,
                "synthesis": (
                    f"Mean {avg:.1f} across {len(vals)} reviewer(s); "
                    + (
                        f"reviewers diverge (spread {spread:.1f}) — reconcile before deciding."
                        if divergent
                        else f"reviewers broadly agree (spread {spread:.1f})."
                    )
                ),
                "divergent": divergent,
            }
        )

    if len(reviewers) < 2:
        agreement = "high"
        overall = (
            "Only one reviewer has scored this applicant so far — no cross-reviewer "
            "synthesis yet. Assign a second reviewer for calibration."
        )
    else:
        agreement = "divergent" if divergent_count else "high" if max_spread < 0.75 else "mixed"
        if agreement == "divergent":
            overall = (
                f"{len(reviewers)} reviewers show meaningful divergence on "
                f"{divergent_count} criterion/criteria (max spread {max_spread:.1f}). "
                "Reconcile the divergent dimensions before the committee decides."
            )
        elif agreement == "high":
            overall = (
                f"{len(reviewers)} reviewers are closely aligned across all criteria "
                f"(max spread {max_spread:.1f}). The panel reads consistently."
            )
        else:
            overall = (
                f"{len(reviewers)} reviewers mostly agree, with some spread "
                f"(max {max_spread:.1f}). Review the wider criteria before deciding."
            )
        overall += " Showing a rule-based synthesis (enable the review model for the full version)."
    return SynthesisResult(
        overall_recommendation=overall,
        agreement=agreement,
        per_criterion=per_criterion,
        is_stub=True,
    )


# ── Assistant Q&A ────────────────────────────────────────────────────────────

_ASSISTANT_PROMPT = (
    "You are an admissions review assistant answering a reviewer's question "
    "about ONE applicant. Answer ONLY from the provided packet (summary, "
    "strengths/concerns, rubric scores, profile signals) using the "
    "submit_review_answer tool. Cite the fields you used. Never invent "
    "credentials the packet does not contain. Test-optional non-submission is "
    "never a negative. You assist — never issue or imply an admit/deny "
    "decision; the human reviewer decides. If the packet lacks the answer, say "
    "so plainly."
)


@dataclass
class AssistantResult:
    answer: str = ""
    citations: list[str] = field(default_factory=list)
    is_stub: bool = True
    cost_usd: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "answer": self.answer,
            "citations": self.citations,
            "model_used": "rule_based" if self.is_stub else "workhorse",
            "grounded": True,
        }


class ReviewAssistant:
    """Spec 32 §6 — grounded Q&A about one applicant (Sonnet)."""

    AGENT_NAME = "review_assistant"

    def __init__(
        self,
        client: AIClient | None = None,
        *,
        max_tokens: int = 1100,
        temperature: float = 0.2,
    ):
        self.client = client or get_client()
        self.max_tokens = max_tokens
        self.temperature = temperature

    async def answer(
        self,
        *,
        question: str,
        packet: dict[str, Any],
        student_id: UUID | None = None,
        db: AsyncSession | None = None,
    ) -> AssistantResult:
        """Answer ``question`` grounded in ``packet``. Never raises."""
        try:
            payload = json.dumps(
                {"question": question, "packet": packet},
                ensure_ascii=False,
                default=str,
            )
            response = await self.client.message(
                agent=self.AGENT_NAME,
                model="workhorse",
                system=[{"type": "text", "text": _ASSISTANT_PROMPT, "cache_control": CACHE_1H}],
                messages=[{"role": "user", "content": payload}],
                tools=[{**SUBMIT_REVIEW_ANSWER_TOOL, "cache_control": CACHE_1H}],
                tool_choice={"type": "tool", "name": "submit_review_answer"},
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                student_id=student_id,
                surface="review_assistant",
                db=db,
            )
            for b in response.content_blocks:
                if b.get("type") == "tool_use" and b.get("name") == "submit_review_answer":
                    inp = b.get("input") or {}
                    ans = str(inp.get("answer") or "").strip()
                    if ans:
                        return AssistantResult(
                            answer=ans,
                            citations=[str(c) for c in (inp.get("citations") or [])][:8],
                            is_stub=False,
                            cost_usd=float(response.cost_usd),
                        )
        except Exception as exc:  # noqa: BLE001 — never break the reviewer surface
            logger.info("review_assistant falling back to rule-based: %s", exc)
        return _rule_based_answer(question, packet)


def _rule_based_answer(question: str, packet: dict[str, Any]) -> AssistantResult:
    """Deterministic answer from the structured packet. Genuinely useful, not a
    placeholder — routes common questions to the strongest structured signal."""
    q = (question or "").lower()
    ai = packet.get("ai_packet_summary") or {}
    strengths = [s.get("text") for s in (ai.get("strengths") or []) if s.get("text")]
    concerns = [c.get("text") for c in (ai.get("concerns") or []) if c.get("text")]
    citations: list[str] = []

    def _join(items: list[str]) -> str:
        return "; ".join(items)

    if any(k in q for k in ("strong", "best", "strength", "stand out", "standout")):
        citations.append("ai_packet_summary.strengths")
        body = (
            f"Strongest signals on file: {_join(strengths)}."
            if strengths
            else "No structured strengths are recorded yet — generate the AI summary first."
        )
    elif any(k in q for k in ("weak", "concern", "risk", "gap", "missing")):
        citations.append("ai_packet_summary.concerns")
        body = (
            f"Recorded concerns: {_join(concerns)}. "
            "(Test-optional non-submission is never a penalty.)"
            if concerns
            else "No concerns are recorded — the packet looks complete on the structured signals."
        )
    elif any(k in q for k in ("score", "recommend", "rating")):
        rec = ai.get("recommended_score")
        citations.append("ai_packet_summary.recommended_score")
        body = (
            f"The AI packet's holistic recommended score is {rec}/10. "
            "The human reviewer decides the final score."
            if rec is not None
            else (
                "No recommended score is recorded yet — generate the AI summary, "
                "then reviewers score."
            )
        )
    else:
        citations.append("ai_packet_summary.overall_summary")
        summary = ai.get("overall_summary") or "No summary is available yet."
        body = (
            f"{summary} "
            + (f"Key strengths: {_join(strengths)}. " if strengths else "")
            + (f"Concerns: {_join(concerns)}. " if concerns else "")
        ).strip()

    body += (
        "\n\n(Showing a rule-based answer from the packet — enable the review model for full Q&A.)"
    )
    return AssistantResult(answer=body, citations=citations, is_stub=True)


# ── Singletons ───────────────────────────────────────────────────────────────

_synth: ReviewSynthesisAgent | None = None
_assistant: ReviewAssistant | None = None


def get_review_synthesis_agent() -> ReviewSynthesisAgent:
    global _synth
    if _synth is None:
        _synth = ReviewSynthesisAgent()
    return _synth


def get_review_assistant() -> ReviewAssistant:
    global _assistant
    if _assistant is None:
        _assistant = ReviewAssistant()
    return _assistant


def reset_review_assist() -> None:
    """Test helper."""
    global _synth, _assistant
    _synth = None
    _assistant = None

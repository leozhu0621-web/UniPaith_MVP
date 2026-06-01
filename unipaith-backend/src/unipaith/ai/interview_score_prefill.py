"""InterviewScorePrefill (Spec 33 §6/§9) — suggests a starting set of rubric
scores for an interviewer from the recording transcript / interviewer notes.

Plan 2 agent behind ``POST /interviews/{id}/score-prefill``, gated by
``ai_interview_v2_enabled``. Workhorse tier (Sonnet), forced tool-use.

This is an **optional** assist: it returns ``None`` on any failure (parse error,
provider error, mock mode), and the Score modal simply opens blank for the human
to fill. It never auto-submits a score — the interviewer reviews and adjusts
every value before committing. Institution-initiated and role-gated at the API
layer; carries no student-consent lever.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai.client import AIClient, get_client
from unipaith.ai.prompt_cache import CACHE_1H
from unipaith.ai.tools.interview_score_prefill_schema import (
    SUBMIT_INTERVIEW_SCORE_PREFILL_TOOL,
)

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"


def _load_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8").rstrip()


_INTERVIEW_SCORE_PREFILL_PROMPT = _load_prompt("interview_score_prefill.md")


# ── Data shapes ────────────────────────────────────────────────────────────


@dataclass
class InterviewScorePrefillInput:
    """Rubric + transcript context for a single score-prefill request."""

    applicant_name: str = ""
    program_name: str = ""
    interview_type: str = "live"
    # [{key, label, description, max}] — the interviewing rubric criteria.
    rubric_criteria: list[dict[str, Any]] = field(default_factory=list)
    transcript_or_notes: str = ""


@dataclass
class InterviewScorePrefillResult:
    criterion_scores: dict[str, float] = field(default_factory=dict)
    overall_note: str = ""
    recommendation: str = "neutral"
    cost_usd: float = 0.0
    latency_ms: int = 0


# ── Agent ──────────────────────────────────────────────────────────────────


class InterviewScorePrefill:
    """Suggests a starting set of interview rubric scores from a transcript."""

    AGENT_NAME = "interview_score_prefill"

    def __init__(
        self,
        client: AIClient | None = None,
        *,
        system_prompt: str | None = None,
        max_tokens: int = 1200,
        temperature: float = 0.3,
    ):
        self.client = client or get_client()
        self.system_prompt = system_prompt or _INTERVIEW_SCORE_PREFILL_PROMPT
        self.max_tokens = max_tokens
        self.temperature = temperature

    async def prefill(
        self,
        *,
        input_view: InterviewScorePrefillInput,
        db: AsyncSession | None = None,
    ) -> InterviewScorePrefillResult | None:
        """Run the agent. Returns None on ANY failure — the Score modal opens
        blank for the human to fill."""
        if not input_view.rubric_criteria or not (input_view.transcript_or_notes or "").strip():
            # Nothing to ground a prefill on — don't spend a call.
            return None
        try:
            response = await self.client.message(
                agent=self.AGENT_NAME,
                model="sonnet",
                system=[
                    {
                        "type": "text",
                        "text": self.system_prompt,
                        "cache_control": CACHE_1H,
                    }
                ],
                messages=[{"role": "user", "content": self._payload(input_view)}],
                tools=[
                    {
                        **SUBMIT_INTERVIEW_SCORE_PREFILL_TOOL,
                        "cache_control": CACHE_1H,
                    }
                ],
                tool_choice={"type": "tool", "name": "submit_interview_score_prefill"},
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                surface="interview_score_prefill",
                db=db,
            )
        except Exception as e:  # noqa: BLE001 — provider error / mock → blank modal
            logger.info("interview score prefill unavailable: %s", e)
            return None

        for b in response.content_blocks:
            if b.get("type") == "tool_use" and b.get("name") == "submit_interview_score_prefill":
                inp = b.get("input") or {}
                raw_scores = inp.get("criterion_scores") or {}
                # Clamp to the rubric's known keys + max scores; drop anything
                # the model invented or pushed over max.
                clamped = self._clamp_scores(raw_scores, input_view.rubric_criteria)
                if not clamped:
                    logger.warning("interview score prefill produced no valid scores")
                    return None
                rec = str(inp.get("recommendation") or "neutral")
                if rec not in {"recommend", "neutral", "not_recommend"}:
                    rec = "neutral"
                return InterviewScorePrefillResult(
                    criterion_scores=clamped,
                    overall_note=str(inp.get("overall_note") or "").strip(),
                    recommendation=rec,
                    cost_usd=float(response.cost_usd),
                    latency_ms=response.latency_ms,
                )
        logger.warning("interview score prefill returned no tool_use block")
        return None

    @staticmethod
    def _clamp_scores(raw: dict[str, Any], criteria: list[dict[str, Any]]) -> dict[str, float]:
        by_key = {str(c.get("key")): c for c in criteria if c.get("key")}
        out: dict[str, float] = {}
        for key, crit in by_key.items():
            if key not in raw:
                continue
            try:
                val = float(raw[key])
            except (TypeError, ValueError):
                continue
            max_score = crit.get("max")
            try:
                max_score = float(max_score) if max_score is not None else None
            except (TypeError, ValueError):
                max_score = None
            if val < 0:
                val = 0.0
            if max_score is not None and val > max_score:
                val = max_score
            out[key] = val
        return out

    @staticmethod
    def _payload(v: InterviewScorePrefillInput) -> str:
        return json.dumps(
            {
                "applicant_name": v.applicant_name,
                "program_name": v.program_name,
                "interview_type": v.interview_type,
                "rubric_criteria": v.rubric_criteria,
                "transcript_or_notes": v.transcript_or_notes,
            },
            ensure_ascii=False,
        )


# ── Singleton ──────────────────────────────────────────────────────────────

_default_prefill: InterviewScorePrefill | None = None


def get_interview_score_prefill() -> InterviewScorePrefill:
    global _default_prefill
    if _default_prefill is None:
        _default_prefill = InterviewScorePrefill()
    return _default_prefill


def reset_interview_score_prefill() -> None:
    global _default_prefill
    _default_prefill = None


__all__: list[str] = [
    "InterviewScorePrefill",
    "InterviewScorePrefillInput",
    "InterviewScorePrefillResult",
    "get_interview_score_prefill",
    "reset_interview_score_prefill",
]

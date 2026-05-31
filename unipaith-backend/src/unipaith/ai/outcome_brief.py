"""OutcomeBriefForOfferLetter — turns an admissions offer into a plain-language
student-readable brief (Spec 45 §15, consumed by Spec 18 §4/§9).

Plan 2 swap-in for ``ApplicationService._build_structured_brief``. Single-shot,
forced tool-use. Failures (timeout, parse error, mock mode) surface as ``None``
to the caller, which falls back to the rule-based brief — the offer flow never
5xxes on agent failure (Plan 2 integration invariant).
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai.client import AIClient, get_client
from unipaith.ai.prompt_cache import CACHE_1H
from unipaith.ai.tools.outcome_brief_schema import SUBMIT_OUTCOME_BRIEF_TOOL

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"


def _load_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8").rstrip()


_OUTCOME_BRIEF_PROMPT = _load_prompt("outcome_brief.md")


@dataclass
class OfferBriefInput:
    """The offer facts the agent reasons over, plus ids for structured logging."""

    student_id: UUID | None = None
    program_name: str | None = None
    institution_name: str | None = None
    today: str | None = None
    offer: dict[str, Any] = field(default_factory=dict)
    raw_letter_text: str | None = None


@dataclass
class OfferBriefResult:
    brief: dict[str, Any]
    cost_usd: float = 0.0
    latency_ms: int = 0


class OutcomeBriefAgent:
    """Synthesizes the structured offer brief (key_terms / deadlines /
    next_steps / summary)."""

    AGENT_NAME = "outcome_brief"

    def __init__(
        self,
        client: AIClient | None = None,
        *,
        system_prompt: str | None = None,
        max_tokens: int = 900,
        temperature: float = 0.3,
    ):
        self.client = client or get_client()
        self.system_prompt = system_prompt or _OUTCOME_BRIEF_PROMPT
        self.max_tokens = max_tokens
        self.temperature = temperature

    async def generate(
        self,
        *,
        input_view: OfferBriefInput,
        db: AsyncSession | None = None,
    ) -> OfferBriefResult | None:
        """Run the agent. Returns None on any failure (caller falls back)."""
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
                tools=[{**SUBMIT_OUTCOME_BRIEF_TOOL, "cache_control": CACHE_1H}],
                tool_choice={"type": "tool", "name": "submit_outcome_brief"},
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                student_id=input_view.student_id,
                surface="outcome_brief",
                db=db,
            )
        except Exception as e:  # noqa: BLE001
            logger.warning("outcome brief agent call failed: %s", e)
            return None

        for b in response.content_blocks:
            if b.get("type") == "tool_use" and b.get("name") == "submit_outcome_brief":
                inp = b.get("input") or {}
                summary = str(inp.get("plain_language_summary") or "").strip()
                if not summary:
                    logger.warning("outcome brief agent returned empty summary")
                    return None
                brief = {
                    "key_terms": inp.get("key_terms") or [],
                    "deadlines": inp.get("deadlines") or [],
                    "next_steps": inp.get("next_steps") or [],
                    "summary": summary,
                    "source": "llm",
                }
                return OfferBriefResult(
                    brief=brief,
                    cost_usd=float(response.cost_usd),
                    latency_ms=response.latency_ms,
                )
        logger.warning("outcome brief agent returned no tool_use block")
        return None

    @staticmethod
    def _payload(v: OfferBriefInput) -> str:
        return json.dumps(
            {
                "program_name": v.program_name,
                "institution_name": v.institution_name,
                "today": v.today,
                "offer": v.offer,
                "raw_letter_text": v.raw_letter_text,
            },
            ensure_ascii=False,
            default=str,
        )


# ── Singleton ──────────────────────────────────────────────────────────────

_default_outcome_brief: OutcomeBriefAgent | None = None


def get_outcome_brief_agent() -> OutcomeBriefAgent:
    global _default_outcome_brief
    if _default_outcome_brief is None:
        _default_outcome_brief = OutcomeBriefAgent()
    return _default_outcome_brief


def reset_outcome_brief_agent() -> None:
    global _default_outcome_brief
    _default_outcome_brief = None

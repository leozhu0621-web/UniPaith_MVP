"""StrategyAgent — LLM-driven Stage-2 strategy generator.

Plan 2 swap-in for `StrategyService._rule_based_generate`. Produces the
sectioned broad-strategy doc (career → degree → academic / financial /
geographic paths + 4-paragraph narrative) that bridges Discovery output
into Stage 2 (Match).

Wire pattern (matches RationaleAgent style):

    StrategyAgent.generate(input_view) → StrategyResult

The service layer maps StrategyResult into the (career_target,
target_degree, academic_path, financial_path, geographic_path,
narrative, source_session_ids) tuple `_rule_based_generate` returns,
so the integration is pure substitution.

Failure modes — all surface as None to the service, which falls back
to the rule-based template:
  - LLM API error / timeout
  - Tool-use response missing
  - Schema validation failure (Pydantic)
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
from unipaith.ai.tools.strategy_schema import SUBMIT_STRATEGY_TOOL

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"


def _load_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8").rstrip()


_STRATEGY_PROMPT = _load_prompt("strategy.md")


# ── Data shapes ────────────────────────────────────────────────────────────


@dataclass
class GoalInput:
    """One goal as the agent sees it."""

    category: str  # 'academic' | 'social' | 'personal'
    specific: str
    measurable: str | None = None
    relevant_notes: str | None = None
    time_bound: str | None = None  # ISO date string


@dataclass
class NeedInput:
    """One need as the agent sees it."""

    maslow_level: str
    need_type: str
    signal: str
    severity: str  # 'must_have' | 'strong_preference' | 'nice_to_have'


@dataclass
class StrategyInput:
    """The full context the strategy agent reasons over."""

    student_id: UUID | None = None
    goals: list[GoalInput] = field(default_factory=list)
    needs: list[NeedInput] = field(default_factory=list)
    preferred_regions: list[str] = field(default_factory=list)
    preferred_majors: list[str] = field(default_factory=list)
    bio_text: str | None = None
    goals_text: str | None = None


@dataclass
class StrategyResult:
    """Parsed output of the strategy agent."""

    career_target: str = ""
    target_degree: str = ""
    academic_path: list[dict[str, Any]] = field(default_factory=list)
    financial_path: list[dict[str, Any]] = field(default_factory=list)
    geographic_path: list[dict[str, Any]] = field(default_factory=list)
    narrative: str = ""
    cost_usd: float = 0.0
    latency_ms: int = 0
    raw: dict[str, Any] | None = None

    def is_well_formed(self) -> bool:
        """The hard-required fields are populated."""
        return (
            bool(self.career_target.strip())
            and bool(self.target_degree.strip())
            and len(self.academic_path) >= 1
            and bool(self.narrative.strip())
        )


# ── Agent ──────────────────────────────────────────────────────────────────


class StrategyAgent:
    """Stage-2 strategy generator. Forced tool-use, single shot."""

    AGENT_NAME = "strategy"

    def __init__(
        self,
        client: AIClient | None = None,
        *,
        system_prompt: str | None = None,
        max_tokens: int = 1800,
        temperature: float = 0.4,
    ):
        self.client = client or get_client()
        self.system_prompt = system_prompt or _STRATEGY_PROMPT
        self.max_tokens = max_tokens
        # 0.4 — readable prose without veering into marketing voice.
        self.temperature = temperature

    async def generate(
        self,
        *,
        input_view: StrategyInput,
        db: AsyncSession | None = None,
    ) -> StrategyResult | None:
        """Run the agent. Returns None on any failure — the service falls
        back to the rule-based template."""
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
                tools=[{**SUBMIT_STRATEGY_TOOL, "cache_control": CACHE_1H}],
                tool_choice={"type": "tool", "name": "submit_strategy"},
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                student_id=input_view.student_id,
                surface="strategy",
                db=db,
            )
        except Exception as e:  # noqa: BLE001
            logger.warning("strategy agent call failed: %s", e)
            return None

        result = self._parse_response(response.content_blocks)
        if result is None:
            return None
        result.cost_usd = float(response.cost_usd)
        result.latency_ms = response.latency_ms
        if not result.is_well_formed():
            logger.warning(
                "strategy agent returned malformed output (career=%s, degree=%s, paths=%d)",
                bool(result.career_target),
                bool(result.target_degree),
                len(result.academic_path),
            )
            return None
        return result

    @staticmethod
    def _payload(v: StrategyInput) -> str:
        return json.dumps(
            {
                "goals": [
                    {
                        "category": g.category,
                        "specific": g.specific,
                        "measurable": g.measurable,
                        "relevant_notes": g.relevant_notes,
                        "time_bound": g.time_bound,
                    }
                    for g in v.goals
                ],
                "needs": [
                    {
                        "maslow_level": n.maslow_level,
                        "need_type": n.need_type,
                        "signal": n.signal,
                        "severity": n.severity,
                    }
                    for n in v.needs
                ],
                "preferred_regions": v.preferred_regions,
                "preferred_majors": v.preferred_majors,
                "bio_text": v.bio_text,
                "goals_text": v.goals_text,
            },
            ensure_ascii=False,
        )

    @staticmethod
    def _parse_response(blocks: list[dict[str, Any]]) -> StrategyResult | None:
        for b in blocks:
            if b.get("type") == "tool_use" and b.get("name") == "submit_strategy":
                inp = b.get("input") or {}
                try:
                    return StrategyResult(
                        career_target=str(inp.get("career_target") or "").strip(),
                        target_degree=str(inp.get("target_degree") or "").strip(),
                        academic_path=list(inp.get("academic_path") or []),
                        financial_path=list(inp.get("financial_path") or []),
                        geographic_path=list(inp.get("geographic_path") or []),
                        narrative=str(inp.get("narrative") or "").strip(),
                        raw=inp,
                    )
                except Exception as e:  # noqa: BLE001
                    logger.warning("strategy agent response parse failed: %s", e)
                    return None
        logger.warning("strategy agent returned no tool_use block")
        return None


# ── Singleton ──────────────────────────────────────────────────────────────

_default_strategy: StrategyAgent | None = None


def get_strategy_agent() -> StrategyAgent:
    global _default_strategy
    if _default_strategy is None:
        _default_strategy = StrategyAgent()
    return _default_strategy


def reset_strategy_agent() -> None:
    global _default_strategy
    _default_strategy = None

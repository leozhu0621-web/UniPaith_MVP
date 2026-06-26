"""DiscoveryQueryInterpreter — spec 45 §12 / spec 10 §3.

Converts a student's natural-language program search into structured
constraint chips via forced tool-use. Workhorse (Sonnet). Non-streaming.

Wire pattern (mirrors `ai/rationale.py`):
  QueryInterpreterAgent.interpret(query, profile_summary) -> QueryInterpretResult

The SearchService owns the feature flag and the rule-based fallback
(`services/query_parser.py`); this module only generates. On any failure the
caller falls back so the student never sees a 5xx (spec 10 §11, §26).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai.client import AIClient, get_client
from unipaith.ai.prompt_cache import CACHE_1H
from unipaith.ai.tools.query_interpreter_schema import SUBMIT_CONSTRAINTS_TOOL
from unipaith.schemas.search import ConstraintCategory, ConstraintChip

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"


def _load_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8").rstrip()


_QUERY_INTERPRETER_PROMPT = _load_prompt("query_interpreter.md")


@dataclass
class QueryInterpretResult:
    chips: list[ConstraintChip] = field(default_factory=list)
    cost_usd: float = 0.0
    latency_ms: int = 0


class QueryInterpreterAgent:
    """Parses NL search queries into structured constraint chips."""

    AGENT_NAME = "query_interpreter"
    PROMPT_VERSION = "v1"

    def __init__(
        self,
        client: AIClient | None = None,
        *,
        system_prompt: str | None = None,
        max_tokens: int = 700,
        temperature: float = 0.0,
    ):
        self.client = client or get_client()
        self.system_prompt = system_prompt or _QUERY_INTERPRETER_PROMPT
        self.max_tokens = max_tokens
        # 0.0 — parsing is deterministic extraction, not creative writing.
        self.temperature = temperature

    async def interpret(
        self,
        *,
        query: str,
        profile_summary: str = "",
        student_id: UUID | None = None,
        db: AsyncSession | None = None,
    ) -> QueryInterpretResult:
        payload = self._payload(query, profile_summary)
        try:
            response = await self.client.message(
                agent=self.AGENT_NAME,
                model="sonnet",
                system=[{"type": "text", "text": self.system_prompt, "cache_control": CACHE_1H}],
                messages=[{"role": "user", "content": payload}],
                tools=[{**SUBMIT_CONSTRAINTS_TOOL, "cache_control": CACHE_1H}],
                tool_choice={"type": "tool", "name": "submit_constraints"},
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                student_id=student_id,
                surface="search",
                db=db,
            )
        except Exception:
            # Spec 10 §11/§26 — search must never surface a 5xx from the
            # interpreter. On provider outage, consent denial, or cost-cap the
            # caller falls back to the deterministic keyword parser.
            logging.getLogger(__name__).warning(
                "query interpreter failed; returning no chips", exc_info=True
            )
            return QueryInterpretResult()
        chips = self._parse_response(response.content_blocks)
        return QueryInterpretResult(
            chips=chips,
            cost_usd=float(response.cost_usd),
            latency_ms=response.latency_ms,
        )

    @staticmethod
    def _payload(query: str, profile_summary: str) -> str:
        import json

        body: dict[str, Any] = {"query": query}
        if profile_summary:
            body["profile_summary"] = profile_summary
        return json.dumps(body, ensure_ascii=False)

    @staticmethod
    def _parse_response(blocks: list[dict[str, Any]]) -> list[ConstraintChip]:
        for b in blocks:
            if b.get("type") == "tool_use" and b.get("name") == "submit_constraints":
                inp = b.get("input") or {}
                raw = inp.get("constraints") or []
                return _coerce_chips(raw)
        return []


def _coerce_chips(raw: list[dict[str, Any]]) -> list[ConstraintChip]:
    """Validate + coerce the agent's constraint dicts into ConstraintChips.
    Invalid categories or empty values are dropped rather than failing the
    whole interpretation."""
    out: list[ConstraintChip] = []
    seen: set[str] = set()
    for item in raw:
        if not isinstance(item, dict):
            continue
        cat_raw = str(item.get("category", "")).strip().lower()
        value = str(item.get("value", "")).strip()
        display = str(item.get("display", "")).strip() or value
        if not value:
            continue
        try:
            category = ConstraintCategory(cat_raw)
        except ValueError:
            category = ConstraintCategory.other
        try:
            confidence = int(item.get("confidence", 100))
        except (TypeError, ValueError):
            confidence = 100
        confidence = max(0, min(100, confidence))
        chip = ConstraintChip(
            category=category, value=value, display=display, confidence=confidence
        ).with_id()
        if chip.id in seen:
            continue
        seen.add(chip.id or "")
        out.append(chip)
    return out


# ── Singleton ───────────────────────────────────────────────────────────────

_default_query_interpreter: QueryInterpreterAgent | None = None


def get_query_interpreter() -> QueryInterpreterAgent:
    global _default_query_interpreter
    if _default_query_interpreter is None:
        _default_query_interpreter = QueryInterpreterAgent()
    return _default_query_interpreter


def reset_query_interpreter() -> None:
    """Test helper."""
    global _default_query_interpreter
    _default_query_interpreter = None

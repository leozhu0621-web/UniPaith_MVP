"""A2 — Extractor agent.

Runs after every student turn (silent). Reads the latest student turn only,
returns structured JSON via Anthropic tool-use against the
`extract_signals` schema.

Design
------
- Forced tool-use (`tool_choice = {"type": "tool", "name": "extract_signals"}`)
  so we never get free-form prose. The schema's enums + bounds do additional
  validation; we re-validate in Python.
- Caches the system prompt + tool schema (rarely change → high cache hit rate
  on long sessions).
- Drops sub-threshold extractions per the rules in `prompts/extractor.md`
  (default threshold 0.7 from `state.DEFAULT_FIELD_CONFIDENCE_THRESHOLD`).
- Pure function-style: input = student_turn (str) + optional context;
  output = filtered ExtractedSignals dataclass. No DB writes here.

The artifact-writer (`unipaith.ai.artifacts`) is the next stage in the
pipeline; this module just produces the structured signal.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai.client import AIClient, get_client
from unipaith.ai.prompt_cache import CACHE_1H
from unipaith.ai.state import DEFAULT_FIELD_CONFIDENCE_THRESHOLD
from unipaith.ai.tools import EXTRACT_SIGNALS_TOOL

PROMPTS_DIR = Path(__file__).parent / "prompts"


def _load_prompt(name: str) -> str:
    """Read a prompt file. Stripped trailing whitespace; full file content
    is what gets cached by Anthropic."""
    path = PROMPTS_DIR / name
    return path.read_text(encoding="utf-8").rstrip()


@dataclass
class ExtractedSignals:
    """Filtered, validated extractor output.

    `confidence_per_key` mirrors the JSON's top-level `confidence` block.
    Sub-threshold blocks are removed from the corresponding lists/dicts so
    callers don't accidentally commit low-confidence signals.
    """

    basic: dict[str, Any] = field(default_factory=dict)
    personality: list[dict[str, Any]] = field(default_factory=list)
    identity: list[dict[str, Any]] = field(default_factory=list)
    goals: list[dict[str, Any]] = field(default_factory=list)
    needs: list[dict[str, Any]] = field(default_factory=list)
    confidence_per_key: dict[str, Decimal] = field(default_factory=dict)

    raw_response: dict[str, Any] | None = None  # full tool-use input, for audit

    def is_empty(self) -> bool:
        return not (self.basic or self.personality or self.identity or self.goals or self.needs)


class Extractor:
    """A2 — the silent post-turn extractor.

    Stateless; safe to instantiate per-call. The system prompt + tool
    schema are passed verbatim to Anthropic with cache_control markers so
    repeated invocations within an active session reuse the cache.
    """

    AGENT_NAME = "extractor"

    def __init__(
        self,
        client: AIClient | None = None,
        *,
        system_prompt: str | None = None,
        confidence_threshold: Decimal = DEFAULT_FIELD_CONFIDENCE_THRESHOLD,
        max_tokens: int = 1500,
        temperature: float = 0.0,
    ):
        self.client = client or get_client()
        self.system_prompt = system_prompt or _load_prompt("extractor.md")
        self.confidence_threshold = confidence_threshold
        self.max_tokens = max_tokens
        # Temperature 0 — extraction is a parse, not a creative act.
        self.temperature = temperature

    async def extract(
        self,
        *,
        student_turn: str,
        student_id: UUID | None = None,
        discovery_message_id: UUID | None = None,
        db: AsyncSession | None = None,
    ) -> ExtractedSignals:
        """Run the extractor on a single student turn.

        Returns a filtered ExtractedSignals dataclass. Always writes one
        row to `ai_turns` (when `db` is provided) — we do not skip the
        ledger even if the response was unusable.
        """
        # System prompt + tool schema are cacheable (rarely change).
        system = [
            {
                "type": "text",
                "text": self.system_prompt,
                "cache_control": CACHE_1H,
            }
        ]
        tools = [{**EXTRACT_SIGNALS_TOOL, "cache_control": CACHE_1H}]

        response = await self.client.message(
            agent=self.AGENT_NAME,
            model="haiku",
            system=system,
            messages=[{"role": "user", "content": student_turn}],
            tools=tools,
            tool_choice={"type": "tool", "name": "extract_signals"},
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            student_id=student_id,
            discovery_message_id=discovery_message_id,
            surface="discovery",
            db=db,
        )

        return self._parse_response(response.content_blocks)

    # ── Parsing + filtering ─────────────────────────────────────────────

    def _parse_response(self, content_blocks: list[dict[str, Any]]) -> ExtractedSignals:
        """Find the tool_use block and apply confidence filtering."""
        tool_use = next(
            (b for b in content_blocks if b.get("type") == "tool_use"),
            None,
        )
        if tool_use is None:
            return ExtractedSignals()

        raw_input = tool_use.get("input") or {}
        confidences = {k: Decimal(str(v)) for k, v in (raw_input.get("confidence") or {}).items()}

        # Drop blocks whose top-level confidence is below threshold. This
        # is a coarse filter; downstream artifact-writers may apply a
        # finer per-claim filter (e.g. only commit identity claims with
        # explicit user confirmation).
        def keep(block_name: str) -> bool:
            conf = confidences.get(block_name)
            return conf is None or conf >= self.confidence_threshold

        return ExtractedSignals(
            basic=(raw_input.get("basic") or {}) if keep("basic") else {},
            personality=(raw_input.get("personality") or []) if keep("personality") else [],
            identity=(raw_input.get("identity") or []) if keep("identity") else [],
            goals=(raw_input.get("goals") or []) if keep("goals") else [],
            needs=(raw_input.get("needs") or []) if keep("needs") else [],
            confidence_per_key=confidences,
            raw_response=raw_input,
        )


# Module-level singleton for the common case.
_default_extractor: Extractor | None = None


def get_extractor() -> Extractor:
    global _default_extractor
    if _default_extractor is None:
        _default_extractor = Extractor()
    return _default_extractor


def reset_extractor() -> None:
    """Test helper."""
    global _default_extractor
    _default_extractor = None

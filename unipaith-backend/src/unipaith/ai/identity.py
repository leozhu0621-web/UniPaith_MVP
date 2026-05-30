"""IdentitySummaryAgent — synthesizes a paragraph from the student's
identity layer (core_values + worldview + self_awareness).

Plan 2 swap-in for `IdentityService.regenerate_summary`. Single-shot,
forced tool-use, single string output. Failures surface as None to the
service, which keeps the existing identity_summary unchanged (it does
NOT fall back to the hardcoded stub on flag-on failure — better to
preserve a real summary than overwrite with a stub).
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
from unipaith.ai.tools.identity_schema import SUBMIT_IDENTITY_SUMMARY_TOOL

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"


def _load_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8").rstrip()


_IDENTITY_PROMPT = _load_prompt("identity_summary.md")


# ── Data shapes ────────────────────────────────────────────────────────────


@dataclass
class IdentityInput:
    """Raw lists from the student_identity row, plus the student id for
    structured logging."""

    student_id: UUID | None = None
    core_values: list[dict[str, Any]] = field(default_factory=list)
    worldview: list[dict[str, Any]] = field(default_factory=list)
    self_awareness: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class IdentityResult:
    summary: str = ""
    cost_usd: float = 0.0
    latency_ms: int = 0


# ── Agent ──────────────────────────────────────────────────────────────────


class IdentitySummaryAgent:
    """Synthesizes a 3–5 sentence identity paragraph."""

    AGENT_NAME = "identity_summary"

    def __init__(
        self,
        client: AIClient | None = None,
        *,
        system_prompt: str | None = None,
        max_tokens: int = 600,
        temperature: float = 0.5,
    ):
        self.client = client or get_client()
        self.system_prompt = system_prompt or _IDENTITY_PROMPT
        self.max_tokens = max_tokens
        self.temperature = temperature

    async def synthesize(
        self,
        *,
        input_view: IdentityInput,
        db: AsyncSession | None = None,
    ) -> IdentityResult | None:
        """Run the agent. Returns None on any failure."""
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
                        **SUBMIT_IDENTITY_SUMMARY_TOOL,
                        "cache_control": CACHE_1H,
                    }
                ],
                tool_choice={"type": "tool", "name": "submit_identity_summary"},
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                student_id=input_view.student_id,
                surface="identity_summary",
                db=db,
            )
        except Exception as e:  # noqa: BLE001
            logger.warning("identity summary agent call failed: %s", e)
            return None

        for b in response.content_blocks:
            if b.get("type") == "tool_use" and b.get("name") == "submit_identity_summary":
                inp = b.get("input") or {}
                summary = str(inp.get("summary") or "").strip()
                if not summary:
                    logger.warning("identity summary agent returned empty summary")
                    return None
                return IdentityResult(
                    summary=summary,
                    cost_usd=float(response.cost_usd),
                    latency_ms=response.latency_ms,
                )
        logger.warning("identity summary agent returned no tool_use block")
        return None

    @staticmethod
    def _payload(v: IdentityInput) -> str:
        return json.dumps(
            {
                "core_values": v.core_values,
                "worldview": v.worldview,
                "self_awareness": v.self_awareness,
            },
            ensure_ascii=False,
        )


# ── Singleton ──────────────────────────────────────────────────────────────

_default_identity: IdentitySummaryAgent | None = None


def get_identity_summary_agent() -> IdentitySummaryAgent:
    global _default_identity
    if _default_identity is None:
        _default_identity = IdentitySummaryAgent()
    return _default_identity


def reset_identity_summary_agent() -> None:
    global _default_identity
    _default_identity = None

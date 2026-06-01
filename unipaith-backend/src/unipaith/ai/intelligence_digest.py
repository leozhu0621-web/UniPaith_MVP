"""IntelligenceDigestNarrator — writes the institution dashboard's plain-English
daily digest (spec 31 §9). Workhorse tier (Sonnet); spec 45 §11 migrated this
narrator off GPT-4o to Claude.

Single-shot forced tool-use over a pre-computed, non-PII stat block. Any failure
(timeout, parse error, mock mode, flag off) surfaces as ``None`` to the caller,
which falls back to a deterministic rule-based narrator — the dashboard endpoint
never 5xxes on agent failure (the spec 31 integration invariant).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai.client import AIClient, get_client
from unipaith.ai.prompt_cache import CACHE_1H
from unipaith.ai.tools.intelligence_digest_schema import SUBMIT_INTELLIGENCE_DIGEST_TOOL

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"


def _load_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8").rstrip()


_DIGEST_PROMPT = _load_prompt("intelligence_digest.md")


@dataclass
class IntelligenceDigestResult:
    digest: str
    highlights: list[str] = field(default_factory=list)
    cost_usd: float = 0.0
    latency_ms: int = 0


class IntelligenceDigestNarrator:
    AGENT_NAME = "intelligence_digest"
    PROMPT_VERSION = "v1"

    def __init__(
        self,
        client: AIClient | None = None,
        *,
        system_prompt: str | None = None,
        max_tokens: int = 600,
        temperature: float = 0.3,
    ):
        self.client = client or get_client()
        self.system_prompt = system_prompt or _DIGEST_PROMPT
        self.max_tokens = max_tokens
        self.temperature = temperature

    async def narrate(
        self, stats: dict[str, Any], *, db: AsyncSession | None = None
    ) -> IntelligenceDigestResult | None:
        """Run the agent over a stat block. Returns None on any failure."""
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
                messages=[{"role": "user", "content": self._payload(stats)}],
                tools=[{**SUBMIT_INTELLIGENCE_DIGEST_TOOL, "cache_control": CACHE_1H}],
                tool_choice={"type": "tool", "name": "submit_intelligence_digest"},
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                student_id=None,  # institution-side aggregate; no student data
                surface="intelligence_digest",
                db=db,
            )
        except Exception as e:  # noqa: BLE001
            logger.warning("intelligence digest agent call failed: %s", e)
            return None

        for b in response.content_blocks:
            if b.get("type") == "tool_use" and b.get("name") == "submit_intelligence_digest":
                inp = b.get("input") or {}
                digest = str(inp.get("digest") or "").strip()
                if not digest:
                    logger.warning("intelligence digest agent returned empty digest")
                    return None
                highlights = [
                    str(s).strip() for s in (inp.get("highlights") or []) if str(s).strip()
                ]
                return IntelligenceDigestResult(
                    digest=digest,
                    highlights=highlights[:4],
                    cost_usd=float(response.cost_usd),
                    latency_ms=response.latency_ms,
                )
        logger.warning("intelligence digest agent returned no tool_use block")
        return None

    @staticmethod
    def _payload(stats: dict[str, Any]) -> str:
        """Render the pre-computed stat block as a compact, label: value list."""
        lines = ["Applicant-landscape stats for this institution's current cycle:"]
        for key, val in stats.items():
            if val is None or val == "":
                continue
            label = key.replace("_", " ")
            lines.append(f"- {label}: {val}")
        lines.append("\nWrite the digest now by calling submit_intelligence_digest.")
        return "\n".join(lines)


# ── Singleton ──────────────────────────────────────────────────────────────
_default_agent: IntelligenceDigestNarrator | None = None


def get_intelligence_digest_agent() -> IntelligenceDigestNarrator:
    global _default_agent
    if _default_agent is None:
        _default_agent = IntelligenceDigestNarrator()
    return _default_agent


def reset_intelligence_digest_agent() -> None:
    global _default_agent
    _default_agent = None

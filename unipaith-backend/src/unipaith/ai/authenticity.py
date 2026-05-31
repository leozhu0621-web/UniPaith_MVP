"""AuthenticityRiskScorer (`45` §18, Haiku) — essay AI-pattern risk.

Spec 06 §2 lists this as a missing L2 agent. It flags essays whose patterns
match common AI-generated structures and emits an advisory `IntegritySignal`
the institution surfaces for human review (spec 32 §7). It never auto-rejects.

Design:
  * **Batch/Haiku** tier, forced tool-use (`submit_authenticity`).
  * On LLM failure / mock mode, falls back to a **conservative rule-based
    heuristic** that only flags egregious, multi-signal cases (spec 45 §18:
    "better silent than false-positive"). Rules never escalate past
    `medium`; only the LLM can assign `high`.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai.client import AIClient, get_client
from unipaith.ai.prompt_cache import CACHE_1H
from unipaith.ai.tools.authenticity_schema import (
    AUTHENTICITY_SIGNALS,
    SUBMIT_AUTHENTICITY_TOOL,
)

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"

_DEFAULT_PROMPT = (
    "You assess whether a student essay's patterns match common "
    "AI-generated writing. Use the submit_authenticity tool. Be conservative: "
    "real students write earnestly and can sound generic. Only flag clear, "
    "multiple co-occurring patterns. Reserve 'high' for essays that are almost "
    "certainly machine-generated. This is advisory for a human reviewer, never "
    "an automatic rejection."
)

# Lightweight, high-precision rule tells (conservative fallback only).
_GENERIC_OPENERS = (
    "in today's world",
    "in todays world",
    "in an era",
    "in the modern era",
    "throughout history",
    "since the dawn of",
    "in a world where",
    "in our increasingly",
)
_CLICHE_TELLS = (
    "tapestry",
    "multifaceted",
    "delve",
    "underscore",
    "testament to",
    "navigate the complexities",
    "ever-evolving",
    "in conclusion,",
    "it is important to note",
)


@dataclass
class AuthenticityResult:
    risk_band: str = "low"
    signals: list[str] = field(default_factory=list)
    confidence: int = 0
    is_stub: bool = True
    cost_usd: float = 0.0

    @property
    def is_flag(self) -> bool:
        """Whether this rises to an integrity signal (medium/high)."""
        return self.risk_band in ("medium", "high")


class AuthenticityRiskScorer:
    """`45` §18 — Haiku essay AI-pattern scorer with conservative fallback."""

    AGENT_NAME = "authenticity_risk"

    def __init__(
        self,
        client: AIClient | None = None,
        *,
        system_prompt: str | None = None,
        max_tokens: int = 300,
        temperature: float = 0.0,
    ):
        self.client = client or get_client()
        path = PROMPTS_DIR / "authenticity.md"
        self.system_prompt = system_prompt or (
            path.read_text(encoding="utf-8").rstrip() if path.exists() else _DEFAULT_PROMPT
        )
        self.max_tokens = max_tokens
        self.temperature = temperature

    async def score(
        self,
        *,
        essay_text: str,
        student_id: UUID | None = None,
        db: AsyncSession | None = None,
    ) -> AuthenticityResult:
        """Score one essay. Never raises — conservative rule-based fallback on
        any provider/parse failure or in mock mode."""
        if not essay_text or not essay_text.strip():
            return AuthenticityResult(risk_band="low", signals=[], confidence=0)

        try:
            response = await self.client.message(
                agent=self.AGENT_NAME,
                model="haiku",  # Spec 06 §2 — batch tier.
                system=[{"type": "text", "text": self.system_prompt, "cache_control": CACHE_1H}],
                messages=[{"role": "user", "content": essay_text[:8000]}],
                tools=[{**SUBMIT_AUTHENTICITY_TOOL, "cache_control": CACHE_1H}],
                tool_choice={"type": "tool", "name": "submit_authenticity"},
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                student_id=student_id,
                surface="authenticity",
                db=db,
            )
            parsed = self._parse(response.content_blocks)
            if parsed is not None:
                parsed.cost_usd = float(response.cost_usd)
                parsed.is_stub = False
                return parsed
        except Exception as exc:  # noqa: BLE001 — never break the integrity scan
            logger.info("authenticity scorer falling back to rule-based: %s", exc)

        return _rule_based_authenticity(essay_text)

    @staticmethod
    def _parse(blocks: list[dict[str, Any]]) -> AuthenticityResult | None:
        for b in blocks:
            if b.get("type") == "tool_use" and b.get("name") == "submit_authenticity":
                inp = b.get("input") or {}
                band = inp.get("risk_band", "low") or "low"
                signals = [s for s in (inp.get("signals") or []) if s in AUTHENTICITY_SIGNALS]
                try:
                    conf = int(inp.get("confidence", 0) or 0)
                except (TypeError, ValueError):
                    conf = 0
                return AuthenticityResult(
                    risk_band=band if band in ("low", "medium", "high") else "low",
                    signals=signals,
                    confidence=max(0, min(100, conf)),
                )
        return None


def _rule_based_authenticity(essay_text: str) -> AuthenticityResult:
    """Conservative heuristic — flags only egregious, multi-signal essays.

    Never escalates past `medium` (only the LLM can assign `high`). Spec 45
    §18: better silent than false-positive — a single weak tell stays `low`.
    """
    text = essay_text.strip()
    low = text.lower()
    words = re.findall(r"\b\w+\b", text)
    word_count = max(1, len(words))

    signals: list[str] = []

    # Em-dash overuse: needs both an absolute count and a high density.
    em_dashes = text.count("\u2014") + text.count(" - ")
    if em_dashes >= 5 and (em_dashes / word_count) > (1 / 80):
        signals.append("overuse_of_em_dashes")

    # Generic AI opener in the first ~120 chars.
    head = low[:120]
    if any(head.startswith(op) or op in head for op in _GENERIC_OPENERS):
        signals.append("generic_opener")

    # Cliché density (common LLM tells).
    cliche_hits = sum(1 for c in _CLICHE_TELLS if c in low)
    if cliche_hits >= 3:
        signals.append("cliche_density")

    # Decide band conservatively. Single signal → stay silent (low).
    distinct = len(signals)
    if distinct >= 2:
        band = "medium"
        confidence = min(60, 25 + distinct * 12)
    else:
        band = "low"
        confidence = 0
        signals = []  # don't surface a lone weak tell

    return AuthenticityResult(risk_band=band, signals=signals, confidence=confidence, is_stub=True)


# ── Singleton ───────────────────────────────────────────────────────────────

_default: AuthenticityRiskScorer | None = None


def get_authenticity_scorer() -> AuthenticityRiskScorer:
    global _default
    if _default is None:
        _default = AuthenticityRiskScorer()
    return _default


def reset_authenticity_scorer() -> None:
    """Test helper."""
    global _default
    _default = None

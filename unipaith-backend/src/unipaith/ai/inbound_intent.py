"""InboundIntentClassifier (Spec 29 §8 / §14, optional) — suggests a reason
code for a new inbound applicant message.

Plan 2 agent behind ``POST /institutions/me/inbox/threads/{id}/intent-suggestion``,
gated by ``ai_inbound_intent_v2_enabled`` (default off). Batch tier (Haiku),
forced tool-use.

Suggestion-only: it never auto-assigns or auto-sends (spec 29 §14 — ship as a
suggestion first). On any failure (parse / provider / mock) it returns ``None``
and the UI shows no suggestion.
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
from unipaith.ai.tools.inbound_intent_schema import SUBMIT_INBOUND_INTENT_TOOL

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"
_VALID_REASONS = {
    "request_document",
    "request_clarification",
    "interview_invite",
    "status_update",
    "general_reply",
    "decision_notice",
}


def _load_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8").rstrip()


_INBOUND_INTENT_PROMPT = _load_prompt("inbound_intent.md")


@dataclass
class InboundIntentInput:
    student_id: UUID | None = None
    latest_message: str = ""
    application: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class InboundIntentResult:
    reason_code: str = "general_reply"
    confidence: float = 0.0
    rationale: str = ""


class InboundIntentClassifier:
    """Suggests a reason code for a new inbound applicant message."""

    AGENT_NAME = "inbound_intent_classifier"

    def __init__(
        self,
        client: AIClient | None = None,
        *,
        system_prompt: str | None = None,
        max_tokens: int = 300,
        temperature: float = 0.0,
    ):
        self.client = client or get_client()
        self.system_prompt = system_prompt or _INBOUND_INTENT_PROMPT
        self.max_tokens = max_tokens
        self.temperature = temperature

    async def classify(
        self,
        *,
        input_view: InboundIntentInput,
        db: AsyncSession | None = None,
    ) -> InboundIntentResult | None:
        """Run the agent. Returns None on ANY failure — the caller shows no
        suggestion."""
        try:
            response = await self.client.message(
                agent=self.AGENT_NAME,
                model="haiku",
                system=[{"type": "text", "text": self.system_prompt, "cache_control": CACHE_1H}],
                messages=[{"role": "user", "content": self._payload(input_view)}],
                tools=[{**SUBMIT_INBOUND_INTENT_TOOL, "cache_control": CACHE_1H}],
                tool_choice={"type": "tool", "name": "submit_inbound_intent"},
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                student_id=input_view.student_id,
                surface="inbound_intent",
                db=db,
            )
        except Exception as e:  # noqa: BLE001 — provider error / mock → no suggestion
            logger.info("inbound intent classifier unavailable: %s", e)
            return None

        for b in response.content_blocks:
            if b.get("type") == "tool_use" and b.get("name") == "submit_inbound_intent":
                inp = b.get("input") or {}
                reason = str(inp.get("reason_code") or "").strip()
                if reason not in _VALID_REASONS:
                    return None
                try:
                    confidence = float(inp.get("confidence") or 0.0)
                except (TypeError, ValueError):
                    confidence = 0.0
                return InboundIntentResult(
                    reason_code=reason,
                    confidence=max(0.0, min(1.0, confidence)),
                    rationale=str(inp.get("rationale") or "").strip()[:240],
                )
        return None

    @staticmethod
    def _payload(v: InboundIntentInput) -> str:
        return json.dumps(
            {
                "latest_message": v.latest_message,
                "application": v.application,
                "context": v.context,
            },
            ensure_ascii=False,
        )


_default_classifier: InboundIntentClassifier | None = None


def get_inbound_intent_classifier() -> InboundIntentClassifier:
    global _default_classifier
    if _default_classifier is None:
        _default_classifier = InboundIntentClassifier()
    return _default_classifier


def reset_inbound_intent_classifier() -> None:
    global _default_classifier
    _default_classifier = None

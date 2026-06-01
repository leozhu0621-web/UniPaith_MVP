"""InstitutionReplyDrafter (Spec 29 / 45) — drafts staff replies for institution inbox."""

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
from unipaith.ai.tools.institution_inbox_reply_schema import SUBMIT_INSTITUTION_REPLY_TOOL

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"
_SYSTEM_PROMPT = (PROMPTS_DIR / "institution_inbox_reply.md").read_text(encoding="utf-8").rstrip()


@dataclass
class InstitutionReplyInput:
    institution_name: str = ""
    student_name: str = ""
    thread_subject: str = ""
    reason_code: str | None = None
    action_label: str | None = None
    application: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)
    messages: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class InstitutionReplyResult:
    draft: str = ""
    tone: str = "professional"
    length: str = "medium"
    alternate_drafts: list[str] = field(default_factory=list)
    suggested_reason_code: str | None = None
    cost_usd: float = 0.0
    latency_ms: int = 0


class InstitutionReplyDrafter:
    AGENT_NAME = "institution_reply_drafter"

    def __init__(
        self,
        client: AIClient | None = None,
        *,
        system_prompt: str | None = None,
        max_tokens: int = 1200,
    ):
        self._client = client or get_client()
        self._system = system_prompt or _SYSTEM_PROMPT
        self._max_tokens = max_tokens

    def _payload(self, input_view: InstitutionReplyInput) -> str:
        return json.dumps(
            {
                "institution": input_view.institution_name,
                "student": input_view.student_name,
                "subject": input_view.thread_subject,
                "reason_code": input_view.reason_code,
                "action_label": input_view.action_label,
                "application": input_view.application,
                "context": input_view.context,
                "messages": input_view.messages[-12:],
            }
        )

    async def draft(
        self,
        *,
        input_view: InstitutionReplyInput,
        db: AsyncSession | None = None,
        student_id: UUID | None = None,
    ) -> InstitutionReplyResult | None:
        try:
            resp = await self._client.message(
                agent=self.AGENT_NAME,
                model="haiku",
                system=[
                    {"type": "text", "text": self._system, "cache_control": CACHE_1H},
                ],
                messages=[{"role": "user", "content": self._payload(input_view)}],
                tools=[{**SUBMIT_INSTITUTION_REPLY_TOOL, "cache_control": CACHE_1H}],
                tool_choice={"type": "tool", "name": "submit_institution_reply"},
                max_tokens=self._max_tokens,
                temperature=0.5,
                student_id=student_id,
                surface="institution_inbox_reply",
                db=db,
            )
        except Exception:  # noqa: BLE001
            logger.info("InstitutionReplyDrafter unavailable")
            return None

        for b in resp.content_blocks or []:
            if b.get("type") == "tool_use" and b.get("name") == "submit_institution_reply":
                inp = b.get("input") or {}
                return InstitutionReplyResult(
                    draft=str(inp.get("draft") or "").strip(),
                    tone=str(inp.get("tone") or "professional"),
                    length=str(inp.get("length") or "medium"),
                    alternate_drafts=list(inp.get("alternate_drafts") or [])[:2],
                    suggested_reason_code=inp.get("suggested_reason_code"),
                    cost_usd=float(resp.cost_usd or 0),
                    latency_ms=int(resp.latency_ms or 0),
                )
        return None


_default: InstitutionReplyDrafter | None = None


def get_institution_reply_drafter() -> InstitutionReplyDrafter:
    global _default
    if _default is None:
        _default = InstitutionReplyDrafter()
    return _default

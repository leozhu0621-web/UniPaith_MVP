"""InboxReplyDrafter (Spec 45 §13) — suggests a draft reply to a student
inbox thread.

Plan 2 agent behind `POST /students/me/inbox/threads/{id}/suggested-reply`,
gated by `ai_inbox_v2_enabled`. Workhorse tier (Sonnet), forced tool-use.

Unlike most agents, the Inbox suggester has **no rule-based fallback**: on
any failure (consent denied via `outreach`, parse error, provider error,
mock mode) it returns ``None`` and the UI simply hides the "AI assist"
card — the student types from scratch (spec 17 §7/§9).
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
from unipaith.ai.tools.inbox_reply_schema import SUBMIT_INBOX_REPLY_TOOL

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"


def _load_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8").rstrip()


_INBOX_REPLY_PROMPT = _load_prompt("inbox_reply.md")


# ── Data shapes ────────────────────────────────────────────────────────────


@dataclass
class InboxReplyInput:
    """Thread + application + student context for a single draft request."""

    student_id: UUID | None = None
    student_name: str = ""
    thread_subject: str = ""
    action_label: str | None = None
    waiting_on: str | None = None
    due_date: str | None = None
    application: dict[str, Any] = field(default_factory=dict)  # {program_name, institution_name}
    messages: list[dict[str, Any]] = field(default_factory=list)  # [{sender, body}]


@dataclass
class InboxReplyResult:
    draft: str = ""
    tone: str = "professional"
    length: str = "medium"
    alternate_drafts: list[str] = field(default_factory=list)
    cost_usd: float = 0.0
    latency_ms: int = 0


# ── Agent ──────────────────────────────────────────────────────────────────


class InboxReplyDrafter:
    """Drafts a suggested student reply for an inbox thread."""

    AGENT_NAME = "inbox_reply_drafter"

    def __init__(
        self,
        client: AIClient | None = None,
        *,
        system_prompt: str | None = None,
        max_tokens: int = 1000,
        temperature: float = 0.6,
    ):
        self.client = client or get_client()
        self.system_prompt = system_prompt or _INBOX_REPLY_PROMPT
        self.max_tokens = max_tokens
        self.temperature = temperature

    async def draft(
        self,
        *,
        input_view: InboxReplyInput,
        db: AsyncSession | None = None,
    ) -> InboxReplyResult | None:
        """Run the agent. Returns None on ANY failure (consent / parse /
        provider / mock) — the caller hides the suggestion card."""
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
                        **SUBMIT_INBOX_REPLY_TOOL,
                        "cache_control": CACHE_1H,
                    }
                ],
                tool_choice={"type": "tool", "name": "submit_inbox_reply"},
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                student_id=input_view.student_id,
                surface="inbox_reply",
                db=db,
            )
        except Exception as e:  # noqa: BLE001 — consent denial / provider error → hide card
            logger.info("inbox reply drafter unavailable: %s", e)
            return None

        for b in response.content_blocks:
            if b.get("type") == "tool_use" and b.get("name") == "submit_inbox_reply":
                inp = b.get("input") or {}
                draft = str(inp.get("draft") or "").strip()
                if not draft:
                    logger.warning("inbox reply drafter returned empty draft")
                    return None
                alts = [
                    str(a).strip() for a in (inp.get("alternate_drafts") or []) if str(a).strip()
                ][:2]
                return InboxReplyResult(
                    draft=draft,
                    tone=str(inp.get("tone") or "professional"),
                    length=str(inp.get("length") or "medium"),
                    alternate_drafts=alts,
                    cost_usd=float(response.cost_usd),
                    latency_ms=response.latency_ms,
                )
        logger.warning("inbox reply drafter returned no tool_use block")
        return None

    @staticmethod
    def _payload(v: InboxReplyInput) -> str:
        return json.dumps(
            {
                "student_name": v.student_name,
                "thread_subject": v.thread_subject,
                "action_requested": v.action_label,
                "waiting_on": v.waiting_on,
                "due_date": v.due_date,
                "application": v.application,
                "messages": v.messages,
            },
            ensure_ascii=False,
        )


# ── Singleton ──────────────────────────────────────────────────────────────

_default_drafter: InboxReplyDrafter | None = None


def get_inbox_reply_drafter() -> InboxReplyDrafter:
    global _default_drafter
    if _default_drafter is None:
        _default_drafter = InboxReplyDrafter()
    return _default_drafter


def reset_inbox_reply_drafter() -> None:
    global _default_drafter
    _default_drafter = None

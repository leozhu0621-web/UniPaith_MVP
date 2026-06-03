"""InstitutionReplyDrafter (Spec 29 §8 / 45) — suggests a draft reply for an
admissions staff member to send an applicant in the institution inbox.

Plan 2 agent behind ``POST /institutions/me/inbox/threads/{id}/ai-draft``,
gated by ``ai_institution_reply_v2_enabled``. Batch tier (Haiku), forced
tool-use.

Like the student-side ``InboxReplyDrafter``, this agent has **no rule-based
fallback**: on any failure (parse error, provider error, mock mode) it returns
``None`` and the UI hides the "AI draft" card — staff types from scratch
(spec 29 §9).

The draft is reason-code aware and grounded in the thread + applicant context
(checklist + missing items). Profile-context enrichment is gated on the
applicant's ``matching`` consent **in the calling service** (spec 29 §8): when
denied, the service simply passes thread-only context here.
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
from unipaith.ai.tools.institution_reply_schema import SUBMIT_INSTITUTION_REPLY_TOOL

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"


def _load_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8").rstrip()


# Spec 61 §3 — append the faculty/institution behavior constitution. It is the
# same versioned file the spec-62 judge uses as its rubric, so this agent is
# steered by the standard it is graded against ("drafts never decides", no
# protected-class proxies, grounded in applicant context). Net-additive — the
# existing institution_reply.md rules are unchanged.
_INSTITUTION_REPLY_PROMPT = (
    _load_prompt("institution_reply.md")
    + "\n\n---\n\n"
    + _load_prompt("_shared/constitution_faculty.md")
)


# ── Data shapes ────────────────────────────────────────────────────────────


@dataclass
class InstitutionReplyInput:
    """Thread + applicant context for a single institution draft request."""

    student_id: UUID | None = None
    institution_name: str = ""
    staff_name: str = ""
    applicant_name: str = ""
    reason_code: str = "general_reply"
    requested_item: str | None = None
    thread_subject: str = ""
    waiting_on: str | None = None
    due_date: str | None = None
    application: dict[str, Any] = field(default_factory=dict)  # {program_name, stage, ...}
    context: dict[str, Any] = field(default_factory=dict)  # {checklist_*, missing_items}
    messages: list[dict[str, Any]] = field(default_factory=list)  # [{sender, body}]


@dataclass
class InstitutionReplyResult:
    draft: str = ""
    tone: str = "professional"
    length: str = "medium"
    alternate_drafts: list[str] = field(default_factory=list)
    cost_usd: float = 0.0
    latency_ms: int = 0


# ── Agent ──────────────────────────────────────────────────────────────────


class InstitutionReplyDrafter:
    """Drafts a suggested institution reply for an inbox thread."""

    AGENT_NAME = "institution_reply_drafter"

    def __init__(
        self,
        client: AIClient | None = None,
        *,
        system_prompt: str | None = None,
        max_tokens: int = 1000,
        temperature: float = 0.6,
    ):
        self.client = client or get_client()
        self.system_prompt = system_prompt or _INSTITUTION_REPLY_PROMPT
        self.max_tokens = max_tokens
        self.temperature = temperature

    async def draft(
        self,
        *,
        input_view: InstitutionReplyInput,
        db: AsyncSession | None = None,
    ) -> InstitutionReplyResult | None:
        """Run the agent. Returns None on ANY failure (parse / provider /
        mock) — the caller hides the suggestion card."""
        try:
            response = await self.client.message(
                agent=self.AGENT_NAME,
                model="haiku",
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
                        **SUBMIT_INSTITUTION_REPLY_TOOL,
                        "cache_control": CACHE_1H,
                    }
                ],
                tool_choice={"type": "tool", "name": "submit_institution_reply"},
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                student_id=input_view.student_id,
                surface="institution_reply",
                db=db,
            )
        except Exception as e:  # noqa: BLE001 — provider error / mock → hide card
            logger.info("institution reply drafter unavailable: %s", e)
            return None

        for b in response.content_blocks:
            if b.get("type") == "tool_use" and b.get("name") == "submit_institution_reply":
                inp = b.get("input") or {}
                draft = str(inp.get("draft") or "").strip()
                if not draft:
                    logger.warning("institution reply drafter returned empty draft")
                    return None
                alts = [
                    str(a).strip() for a in (inp.get("alternate_drafts") or []) if str(a).strip()
                ][:2]
                return InstitutionReplyResult(
                    draft=draft,
                    tone=str(inp.get("tone") or "professional"),
                    length=str(inp.get("length") or "medium"),
                    alternate_drafts=alts,
                    cost_usd=float(response.cost_usd),
                    latency_ms=response.latency_ms,
                )
        logger.warning("institution reply drafter returned no tool_use block")
        return None

    @staticmethod
    def _payload(v: InstitutionReplyInput) -> str:
        return json.dumps(
            {
                "institution_name": v.institution_name,
                "staff_name": v.staff_name,
                "applicant_name": v.applicant_name,
                "reason_code": v.reason_code,
                "requested_item": v.requested_item,
                "thread_subject": v.thread_subject,
                "waiting_on": v.waiting_on,
                "due_date": v.due_date,
                "application": v.application,
                "context": v.context,
                "messages": v.messages,
            },
            ensure_ascii=False,
        )


# ── Singleton ──────────────────────────────────────────────────────────────

_default_drafter: InstitutionReplyDrafter | None = None


def get_institution_reply_drafter() -> InstitutionReplyDrafter:
    global _default_drafter
    if _default_drafter is None:
        _default_drafter = InstitutionReplyDrafter()
    return _default_drafter


def reset_institution_reply_drafter() -> None:
    global _default_drafter
    _default_drafter = None

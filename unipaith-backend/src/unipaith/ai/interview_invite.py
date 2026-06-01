"""InterviewInviteDrafter (Spec 33 §9) — suggests a draft invite message for an
admissions staff member to send an applicant when proposing an interview.

Plan 2 agent behind ``POST /interviews/draft-invite``, gated by
``ai_interview_v2_enabled``. Batch tier (Haiku), forced tool-use.

Like the InstitutionReplyDrafter, this agent has **no rule-based fallback**: on
any failure (parse error, provider error, mock mode) it returns ``None`` and the
Propose modal simply omits the AI-drafted body — staff types the note from
scratch (§9). It carries no student in scope; it's institution-initiated and
role-gated at the API layer.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai.client import AIClient, get_client
from unipaith.ai.prompt_cache import CACHE_1H
from unipaith.ai.tools.interview_invite_schema import SUBMIT_INTERVIEW_INVITE_TOOL

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"


def _load_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8").rstrip()


_INTERVIEW_INVITE_PROMPT = _load_prompt("interview_invite.md")


# ── Data shapes ────────────────────────────────────────────────────────────


@dataclass
class InterviewInviteInput:
    """Interview context for a single invite-draft request."""

    institution_name: str = ""
    staff_name: str = ""
    applicant_name: str = ""
    program_name: str = ""
    interview_type: str = "live"
    proposed_slots: list[str] = field(default_factory=list)  # ISO8601 for live
    async_window_end: str | None = None
    duration_minutes: int | None = None
    location_or_link: str | None = None


@dataclass
class InterviewInviteResult:
    draft: str = ""
    tone: str = "professional"
    length: str = "medium"
    cost_usd: float = 0.0
    latency_ms: int = 0


# ── Agent ──────────────────────────────────────────────────────────────────


class InterviewInviteDrafter:
    """Drafts a suggested interview-invite message."""

    AGENT_NAME = "interview_invite_drafter"

    def __init__(
        self,
        client: AIClient | None = None,
        *,
        system_prompt: str | None = None,
        max_tokens: int = 800,
        temperature: float = 0.6,
    ):
        self.client = client or get_client()
        self.system_prompt = system_prompt or _INTERVIEW_INVITE_PROMPT
        self.max_tokens = max_tokens
        self.temperature = temperature

    async def draft(
        self,
        *,
        input_view: InterviewInviteInput,
        db: AsyncSession | None = None,
    ) -> InterviewInviteResult | None:
        """Run the agent. Returns None on ANY failure (parse / provider / mock) —
        the caller omits the AI-drafted body."""
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
                        **SUBMIT_INTERVIEW_INVITE_TOOL,
                        "cache_control": CACHE_1H,
                    }
                ],
                tool_choice={"type": "tool", "name": "submit_interview_invite"},
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                surface="interview_invite",
                db=db,
            )
        except Exception as e:  # noqa: BLE001 — provider error / mock → omit draft
            logger.info("interview invite drafter unavailable: %s", e)
            return None

        for b in response.content_blocks:
            if b.get("type") == "tool_use" and b.get("name") == "submit_interview_invite":
                inp = b.get("input") or {}
                draft = str(inp.get("draft") or "").strip()
                if not draft:
                    logger.warning("interview invite drafter returned empty draft")
                    return None
                return InterviewInviteResult(
                    draft=draft,
                    tone=str(inp.get("tone") or "professional"),
                    length=str(inp.get("length") or "medium"),
                    cost_usd=float(response.cost_usd),
                    latency_ms=response.latency_ms,
                )
        logger.warning("interview invite drafter returned no tool_use block")
        return None

    @staticmethod
    def _payload(v: InterviewInviteInput) -> str:
        return json.dumps(
            {
                "institution_name": v.institution_name,
                "staff_name": v.staff_name,
                "applicant_name": v.applicant_name,
                "program_name": v.program_name,
                "interview_type": v.interview_type,
                "proposed_slots": v.proposed_slots,
                "async_window_end": v.async_window_end,
                "duration_minutes": v.duration_minutes,
                "location_or_link": v.location_or_link,
            },
            ensure_ascii=False,
        )


# ── Singleton ──────────────────────────────────────────────────────────────

_default_drafter: InterviewInviteDrafter | None = None


def get_interview_invite_drafter() -> InterviewInviteDrafter:
    global _default_drafter
    if _default_drafter is None:
        _default_drafter = InterviewInviteDrafter()
    return _default_drafter


def reset_interview_invite_drafter() -> None:
    global _default_drafter
    _default_drafter = None


__all__: list[str] = [
    "InterviewInviteDrafter",
    "InterviewInviteInput",
    "InterviewInviteResult",
    "get_interview_invite_drafter",
    "reset_interview_invite_drafter",
]

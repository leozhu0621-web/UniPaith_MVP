"""CampaignAudienceCopySuggester — drafts external-email subject + body for an
institution Campaign (Spec 45 §16, consumed by Spec 25 §10 "Draft with AI").

Workhorse tier (Sonnet), single-shot forced tool-use. Failures (timeout, parse
error, mock mode, flag off) surface as ``None`` to the caller, which falls back
to an objective-keyed template stub — the editor never 5xxes on agent failure.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai.client import AIClient, get_client
from unipaith.ai.prompt_cache import CACHE_1H
from unipaith.ai.tools.campaign_copy_schema import SUBMIT_CAMPAIGN_COPY_TOOL

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"


def _load_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8").rstrip()


_CAMPAIGN_COPY_PROMPT = _load_prompt("campaign_copy.md")


@dataclass
class CampaignCopyInput:
    objective: str | None = None
    cta_type: str | None = None
    institution_name: str | None = None
    program_name: str | None = None
    audience_summary: str | None = None
    tone: str | None = None
    additional_context: str | None = None


@dataclass
class CampaignCopyResult:
    subject: str
    body: str
    alternate_subjects: list[str] = field(default_factory=list)
    preview_text: str = ""
    cost_usd: float = 0.0
    latency_ms: int = 0


class CampaignAudienceCopySuggester:
    AGENT_NAME = "campaign_copy"
    PROMPT_VERSION = "v1"

    def __init__(
        self,
        client: AIClient | None = None,
        *,
        system_prompt: str | None = None,
        max_tokens: int = 900,
        temperature: float = 0.6,
    ):
        self.client = client or get_client()
        self.system_prompt = system_prompt or _CAMPAIGN_COPY_PROMPT
        self.max_tokens = max_tokens
        self.temperature = temperature

    async def draft(
        self, view: CampaignCopyInput, *, db: AsyncSession | None = None
    ) -> CampaignCopyResult | None:
        """Run the agent. Returns None on any failure (caller falls back)."""
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
                messages=[{"role": "user", "content": self._payload(view)}],
                tools=[{**SUBMIT_CAMPAIGN_COPY_TOOL, "cache_control": CACHE_1H}],
                tool_choice={"type": "tool", "name": "submit_campaign_copy"},
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                student_id=None,  # institution-side; no student protected data
                surface="campaign_copy",
                db=db,
            )
        except Exception as e:  # noqa: BLE001
            logger.warning("campaign copy agent call failed: %s", e)
            return None

        for b in response.content_blocks:
            if b.get("type") == "tool_use" and b.get("name") == "submit_campaign_copy":
                inp = b.get("input") or {}
                subject = str(inp.get("subject") or "").strip()
                body = str(inp.get("body") or "").strip()
                if not subject or not body:
                    logger.warning("campaign copy agent returned empty subject/body")
                    return None
                alts = [
                    str(s).strip() for s in (inp.get("alternate_subjects") or []) if str(s).strip()
                ]
                return CampaignCopyResult(
                    subject=subject,
                    body=body,
                    alternate_subjects=alts[:3],
                    preview_text=str(inp.get("preview_text") or "").strip(),
                    cost_usd=float(response.cost_usd),
                    latency_ms=response.latency_ms,
                )
        logger.warning("campaign copy agent returned no tool_use block")
        return None

    @staticmethod
    def _payload(v: CampaignCopyInput) -> str:
        lines = [
            f"Objective: {v.objective or 'general'}",
            f"Call to action: {v.cta_type or 'learn_more'}",
            f"Institution: {v.institution_name or 'our institution'}",
        ]
        if v.program_name:
            lines.append(f"Program: {v.program_name}")
        if v.audience_summary:
            lines.append(f"Audience: {v.audience_summary}")
        if v.tone:
            lines.append(f"Requested tone: {v.tone}")
        if v.additional_context:
            lines.append(f"Additional context: {v.additional_context}")
        lines.append("\nDraft the email now by calling submit_campaign_copy.")
        return "\n".join(lines)


# ── Singleton ──────────────────────────────────────────────────────────────
_default_agent: CampaignAudienceCopySuggester | None = None


def get_campaign_copy_agent() -> CampaignAudienceCopySuggester:
    global _default_agent
    if _default_agent is None:
        _default_agent = CampaignAudienceCopySuggester()
    return _default_agent


def reset_campaign_copy_agent() -> None:
    global _default_agent
    _default_agent = None

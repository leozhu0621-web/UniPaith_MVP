"""Spec 25 §10 / 45 §16 — "Draft with AI" orchestration for campaign copy.

Feature-flagged (``ai_campaign_copy_v2_enabled``). When the LLM path is off or
fails, returns a deterministic objective-keyed template stub so the editor's
"Draft with AI" button always returns usable copy (never 5xxes).
"""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import settings
from unipaith.models.institution import Institution, TargetSegment
from unipaith.schemas.institution import DraftCampaignCopyRequest, DraftCampaignCopyResponse

logger = logging.getLogger("unipaith.campaign_copy")

# CTA → closing call (and the alternate-subject seed).
_CTA_CLOSING = {
    "learn_more": "Learn more here: {{event_link}}",
    "rsvp_event": "Reserve your spot: {{event_link}}",
    "request_info": "Have a question? Just ask: {{event_link}}",
    "start_application": "Start your application: {{event_link}}",
}

# Objective → (subject, opening, value paragraph) template stub.
_OBJECTIVE_TEMPLATES = {
    "application_open": (
        "Applications are open at {inst}",
        "Hi {{first_name}}, applications for {prog} are now open.",
        "We'd love to read yours. The process is straightforward, and our team is "
        "here if you have questions along the way.",
    ),
    "event_promotion": (
        "You're invited — {inst}",
        "Hi {{first_name}}, we're hosting an event for students exploring {prog}.",
        "It's a chance to meet our faculty, ask real questions, and picture "
        "yourself here. We'd be glad to have you.",
    ),
    "scholarship_announcement": (
        "A funding opportunity at {inst}",
        "Hi {{first_name}}, there's a new scholarship open to {prog} applicants.",
        "If cost is part of your decision, this could matter. We've kept the "
        "details clear so you can decide whether it fits.",
    ),
    "deadline_reminder": (
        "A date worth noting for {prog}",
        "Hi {{first_name}}, a key deadline for {prog} is coming up soon.",
        "There's still time to act, and we don't want you to miss it. Here's the "
        "one next step to stay on track.",
    ),
    "nurture": (
        "Thinking about your next step? — {inst}",
        "Hi {{first_name}}, no pressure — just a note from {inst}.",
        "Wherever you are in your decision, we're happy to be a useful resource. "
        "Reach out whenever the timing is right for you.",
    ),
    "general": (
        "An update from {inst}",
        "Hi {{first_name}}, a quick update from {inst}.",
        "We thought this might be useful as you think about {prog}. We're here if "
        "you'd like to talk it through.",
    ),
}


def _fallback(data: DraftCampaignCopyRequest, inst_name: str) -> DraftCampaignCopyResponse:
    objective = data.objective or "general"
    subj_t, opening, value = _OBJECTIVE_TEMPLATES.get(objective, _OBJECTIVE_TEMPLATES["general"])
    prog = "{{program_name}}"  # double-brace send-time token — keep literal

    def fill(s: str, program: str = prog) -> str:
        # Plain .replace (NOT str.format) so the {{first_name}} / {{program_name}}
        # / {{event_link}} personalization tokens survive verbatim.
        return s.replace("{inst}", inst_name).replace("{prog}", program)

    subject = fill(subj_t)
    closing = _CTA_CLOSING.get(data.cta_type or "learn_more", _CTA_CLOSING["learn_more"])
    body = f"{fill(opening)}\n\n{fill(value)}\n\n{closing}"
    alternates = [
        f"{inst_name}: a note for you",
        fill(subj_t, "your program"),
    ]
    return DraftCampaignCopyResponse(
        subject=subject,
        body=body,
        alternate_subjects=[a for a in alternates if a != subject][:3],
        preview_text=fill(value)[:160],
        source="fallback",
    )


async def _audience_summary(
    db: AsyncSession, institution_id, data: DraftCampaignCopyRequest
) -> str | None:
    if data.audience_summary:
        return data.audience_summary
    if not data.audience_segment_ids:
        return None
    rows = await db.execute(
        select(TargetSegment.segment_name, TargetSegment.description).where(
            TargetSegment.institution_id == institution_id,
            TargetSegment.id.in_(data.audience_segment_ids),
        )
    )
    parts = []
    for name, desc in rows.all():
        parts.append(f"{name} — {desc}" if desc else name)
    return "; ".join(parts) or None


async def draft_campaign_copy(
    db: AsyncSession, institution: Institution, data: DraftCampaignCopyRequest
) -> DraftCampaignCopyResponse:
    inst_name = institution.name or "our institution"
    if not settings.ai_campaign_copy_v2_enabled:
        return _fallback(data, inst_name)

    try:
        from unipaith.ai.campaign_copy import CampaignCopyInput, get_campaign_copy_agent

        summary = await _audience_summary(db, institution.id, data)
        result = await get_campaign_copy_agent().draft(
            CampaignCopyInput(
                objective=data.objective,
                cta_type=data.cta_type,
                institution_name=inst_name,
                audience_summary=summary,
                tone=data.tone,
                additional_context=data.additional_context,
            ),
            db=db,
        )
    except Exception:  # noqa: BLE001
        logger.exception("campaign copy draft failed; using fallback")
        result = None

    if result is None:
        return _fallback(data, inst_name)
    return DraftCampaignCopyResponse(
        subject=result.subject,
        body=result.body,
        alternate_subjects=result.alternate_subjects,
        preview_text=result.preview_text,
        source="llm",
    )

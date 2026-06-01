"""SegmentBuilderNLBridge — Spec 26 §6 / 45 §17."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from unipaith.ai.client import AIClient, get_client
from unipaith.ai.prompt_cache import CACHE_1H
from unipaith.ai.tools.segment_builder_schema import SUBMIT_SEGMENT_RULES_TOOL

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"
_SYSTEM = (PROMPTS_DIR / "segment_builder.md").read_text(encoding="utf-8").rstrip()

SIGNAL_DICTIONARY = [
    {"field": "engagement.viewed_institution", "operators": ["within_days"]},
    {"field": "engagement.saved_program", "operators": ["within_days"]},
    {"field": "engagement.compared_program", "operators": ["within_days"]},
    {"field": "engagement.requested_info", "operators": ["within_days"]},
    {"field": "engagement.event_rsvp", "operators": ["within_days"]},
    {"field": "application.started", "operators": ["equals"]},
    {"field": "application.not_submitted", "operators": ["equals"]},
    {"field": "fit.fitness_band", "operators": ["has_band"], "values": ["high", "medium", "low"]},
    {"field": "match.tier", "operators": ["in"], "values": ["reach", "target", "safer"]},
    {
        "field": "readiness.budget_band",
        "operators": ["has_band"],
        "values": ["high", "medium", "low"],
    },
    {
        "field": "readiness.modality",
        "operators": ["in"],
        "values": ["in_person", "online", "hybrid"],
    },
    {
        "field": "readiness.timeline",
        "operators": ["equals"],
        "values": ["this_intake", "next_intake", "later"],
    },
    {"field": "profile.nationality", "operators": ["in"]},
    {"field": "suppression.unsubscribed", "operators": ["equals"]},
]

AGENT_NAME = "segment_builder_nl"


def _parse_tool(blocks: list[dict[str, Any]]) -> dict | None:
    for b in blocks:
        if b.get("type") == "tool_use" and b.get("name") == "submit_segment_rules":
            data = b.get("input") or {}
            rules = data.get("rules")
            if isinstance(rules, list) and rules:
                return {
                    "rules": rules,
                    "confidence_overall": int(data.get("confidence_overall") or 70),
                    "ambiguity_notes": list(data.get("ambiguity_notes") or []),
                }
    return None


def _keyword_fallback(description: str) -> dict:
    """Rule-based fallback when LLM unavailable (Plan 2 invariant)."""
    text = description.lower()
    rules: list[dict[str, Any]] = []
    notes: list[str] = []

    if "saved" in text:
        rules.append({"field": "engagement.saved_program", "operator": "within_days", "value": 90})
    if "viewed" in text or "visited" in text:
        rules.append(
            {"field": "engagement.viewed_institution", "operator": "within_days", "value": 30}
        )
    if "engineering" in text or " cs" in text or "computer" in text:
        notes.append("Major/field filter not yet mapped — used saved-program activity instead")
        if not any(r["field"] == "engagement.saved_program" for r in rules):
            rules.append(
                {"field": "engagement.saved_program", "operator": "within_days", "value": 180}
            )
    if "california" in text or " ca" in text:
        notes.append("Location filter not directly available — review manually")
    if re.search(r"budget|cost|\$|≤|<=", text):
        rules.append({"field": "readiness.budget_band", "operator": "has_band", "value": "high"})
    if "high fit" in text or "fit-band" in text or "fit band" in text:
        rules.append({"field": "fit.fitness_band", "operator": "has_band", "value": "high"})
    if "not started" in text or "haven't started" in text or "have not started" in text:
        rules.append({"field": "application.not_submitted", "operator": "equals", "value": True})
    if "unsubscrib" in text:
        rules.append({"field": "suppression.unsubscribed", "operator": "equals", "value": True})

    if not rules:
        rules.append(
            {"field": "engagement.viewed_institution", "operator": "within_days", "value": 30}
        )
        notes.append("Could not parse specifics — defaulting to recent page viewers")

    return {
        "rules": rules,
        "confidence_overall": 55 if notes else 70,
        "ambiguity_notes": notes,
    }


async def build_rules_from_nl(
    description: str,
    *,
    client: AIClient | None = None,
) -> dict:
    """Return structured rules; always succeeds via keyword fallback."""
    try:
        cl = client or get_client()
        user_msg = json.dumps(
            {
                "description": description,
                "signal_dictionary": SIGNAL_DICTIONARY,
            },
            ensure_ascii=False,
        )
        response = await cl.message(
            agent=AGENT_NAME,
            model="sonnet",
            system=[{"type": "text", "text": _SYSTEM, "cache_control": CACHE_1H}],
            messages=[{"role": "user", "content": user_msg}],
            tools=[SUBMIT_SEGMENT_RULES_TOOL],
            tool_choice={"type": "tool", "name": "submit_segment_rules"},
            max_tokens=1200,
            temperature=0.2,
        )
        parsed = _parse_tool(response.content_blocks)
        if parsed:
            return parsed
    except Exception as e:  # noqa: BLE001
        logger.warning("SegmentBuilderNLBridge failed, using keyword fallback: %s", e)

    return _keyword_fallback(description)

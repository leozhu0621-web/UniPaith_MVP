"""Follow-up question phrasing — the LLM half of the hybrid GapEngine.

The deterministic `GapEngine.detect` decides WHICH gaps to ask about (and the
exact `target_field` + `ref` that make the answer applicable). This module
rewrites each gap's baseline `prompt_hint` into ONE warm, specific question
**grounded in the student's actual imported content** — so a GPA question names
the right school, and a "what's pulling you toward X" references their real
field. It never changes the intent or count; on any failure it returns ``None``
and the caller falls back to the deterministic `prompt_hint`.

Cost-ledger slot: `workshop_coach` (user-initiated, consent-free), same as the
ingest agent.
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from unipaith.ai.client import get_client

logger = logging.getLogger(__name__)

_AGENT_SLOT = "workshop_coach"

_SYSTEM = (
    "You are Uni, a warm college counselor who just read a student's uploaded "
    "file. You're given (1) a compact summary of what was extracted and (2) a "
    "list of baseline follow-up questions. Rewrite EACH baseline into one short, "
    "natural, first-person question that is GROUNDED in the student's actual "
    "content — name the specific school, club, or field it refers to so no "
    "question is vague (never a subjectless 'What's your GPA?' when there are two "
    "schools). Keep the same intent and the same number of questions, in the same "
    "order. Do not invent facts or add new topics. One sentence each."
)

SUBMIT_TOOL: dict[str, Any] = {
    "name": "submit_questions",
    "description": "Return the rewritten follow-up questions, same count and order as the input.",
    "input_schema": {
        "type": "object",
        "properties": {
            "questions": {
                "type": "array",
                "items": {"type": "string"},
                "description": "One grounded question per baseline, in order.",
            }
        },
        "required": ["questions"],
    },
}


def _context_brief(context: dict[str, Any] | None) -> str:
    """A compact, factual brief of the import for grounding (no fabrication)."""
    c = context or {}
    lines: list[str] = []
    if c.get("summary"):
        lines.append(f"Summary: {c['summary']}")
    schools = []
    for r in c.get("academic_records") or []:
        deg = r.get("degree_type") or ""
        fld = r.get("field_of_study") or ""
        inst = r.get("institution_name") or ""
        schools.append(" ".join(p for p in [inst, f"({deg} {fld})".strip()] if p).strip())
    if schools:
        lines.append("Schools: " + "; ".join(schools))
    acts = [a.get("title") for a in (c.get("activities") or []) if a.get("title")]
    if acts:
        lines.append("Activities: " + ", ".join(acts))
    return "\n".join(lines) or "(no extracted summary)"


async def phrase_questions(
    gaps: list[dict[str, Any]],
    context: dict[str, Any] | None,
    *,
    student_id: UUID | None = None,
) -> list[str] | None:
    """Return one grounded question per gap (same order), or None to fall back."""
    if not gaps:
        return []
    baseline = "\n".join(f"{i + 1}. {g.get('prompt_hint', '')}" for i, g in enumerate(gaps))
    user = (
        f"What we extracted:\n{_context_brief(context)}\n\n"
        f"Baseline questions to rewrite (return exactly {len(gaps)}, same order):\n{baseline}"
    )
    try:
        resp = await get_client().message(
            agent=_AGENT_SLOT,
            model="sonnet",
            system=[{"type": "text", "text": _SYSTEM}],
            messages=[{"role": "user", "content": user}],
            tools=[SUBMIT_TOOL],
            tool_choice={"type": "tool", "name": "submit_questions"},
            max_tokens=700,
            temperature=0.3,
            student_id=student_id,
            surface="material_followups",
        )
    except Exception as exc:
        logger.info("follow-up phrasing failed: %s", exc)
        return None
    for b in resp.content_blocks:
        if b.get("type") == "tool_use" and b.get("name") == "submit_questions":
            qs = (b.get("input") or {}).get("questions")
            if (
                isinstance(qs, list)
                and len(qs) == len(gaps)
                and all(isinstance(q, str) and q.strip() for q in qs)
            ):
                return [q.strip() for q in qs]
            logger.info("follow-up phrasing returned mismatched questions; falling back")
            return None
    return None

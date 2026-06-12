"""Host-side custom-tool implementations for the Uni managed agent.

Each function maps one ``agent.custom_tool_use`` to an existing UniPaith service
and returns a JSON-serializable dict the host sends back as
``user.custom_tool_result``. The DB never leaves the VPC — the agent only ever
sees these results.

All tools share the shape ``async (db, user_id, tool_input) -> dict`` (only
``save_signals`` also takes a ``session_id``). ``dispatch_tool`` routes by the
custom-tool name declared in ``agents/uni.agent.yaml``.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai.artifacts import persist_extraction
from unipaith.ai.extractor import ExtractedSignals
from unipaith.services.discovery_service import DiscoveryService


# ── save_signals ──────────────────────────────────────────────────────────
def _signals_from_tool_input(tool_input: dict[str, Any]) -> ExtractedSignals:
    """Build ExtractedSignals from the save_signals payload (mirrors
    EXTRACT_SIGNALS_TOOL). The top-level ``confidence`` block becomes
    confidence_per_key as Decimals; persist_extraction applies its own
    completeness / idempotency gating downstream."""
    conf = tool_input.get("confidence") or {}
    return ExtractedSignals(
        basic=tool_input.get("basic") or {},
        personality=tool_input.get("personality") or [],
        identity=tool_input.get("identity") or [],
        goals=tool_input.get("goals") or [],
        needs=tool_input.get("needs") or [],
        confidence_per_key={k: Decimal(str(v)) for k, v in conf.items()},
        raw_response=tool_input,
    )


async def tool_save_signals(
    db: AsyncSession,
    user_id: UUID,
    tool_input: dict[str, Any],
    *,
    session_id: UUID | None = None,
) -> dict[str, Any]:
    """Persist goals / needs / identity / basic signals from a turn, then report
    fresh completion + whether the student is handoff-ready."""
    disc = DiscoveryService(db)
    student_id = await disc._profile_id_for_user(user_id)
    if session_id is None:
        # persist_extraction requires a discovery session for provenance; bind to
        # the canonical unified Uni session (reuse-or-create).
        session = await disc.start_unified_session(user_id)
        session_id = session.id
    extraction = _signals_from_tool_input(tool_input)
    result = await persist_extraction(
        db=db, student_id=student_id, session_id=session_id, extraction=extraction
    )
    await db.commit()
    completion = await disc.get_completion_map(user_id)
    handoff = await disc.evaluate_handoff(user_id)
    return {
        "written": {
            "goals_written": result.goals_written,
            "needs_written": result.needs_written,
            "identity_added": (
                result.identity_values_added
                + result.identity_worldview_added
                + result.identity_self_awareness_added
            ),
            "basic_fields_written": result.basic_fields_written,
        },
        "completion": {k: float(v) for k, v in completion.items()},
        "handoff_ready": bool(handoff.get("should_handoff")),
    }


# ── search_programs ───────────────────────────────────────────────────────
async def tool_search_programs(
    db: AsyncSession, user_id: UUID, tool_input: dict[str, Any]
) -> dict[str, Any]:
    """Search the published-program catalog. Tuition / salary are whole USD."""
    from unipaith.services.institution_service import InstitutionService

    page = await InstitutionService(db).search_programs(
        query=tool_input.get("query"),
        country=tool_input.get("country"),
        degree_types=tool_input.get("degree_types"),
        min_tuition=tool_input.get("min_tuition"),
        max_tuition=tool_input.get("max_tuition"),
        delivery_formats=tool_input.get("delivery_formats"),
        location=tool_input.get("location"),
        page=1,
        page_size=8,
    )
    return {
        "programs": [
            {
                "program_id": str(p.id),
                "program_name": p.program_name,
                "institution_name": p.institution_name,
                "country": p.institution_country,
                "city": p.institution_city,
                "degree_type": p.degree_type,
                "tuition_usd": p.tuition,
                "duration_months": p.duration_months,
                "acceptance_rate": p.acceptance_rate,
                "application_deadline": (
                    p.application_deadline.isoformat() if p.application_deadline else None
                ),
                "median_salary_usd": p.median_salary,
                "employment_rate": p.employment_rate,
                "summary": (p.description_text or "")[:280],
            }
            for p in page.items
        ],
        "total": page.total,
    }


# ── get_matches ───────────────────────────────────────────────────────────
async def tool_get_matches(
    db: AsyncSession, user_id: UUID, tool_input: dict[str, Any]
) -> dict[str, Any]:
    """Surface the student's top matches — gated on discovery handoff readiness.

    A student who hasn't gone far enough gets ``ready=False`` plus what's still
    missing, so the agent keeps the conversation going instead of guessing."""
    from unipaith.services.match_service import MatchService

    disc = DiscoveryService(db)
    handoff = await disc.evaluate_handoff(user_id)
    if not handoff.get("should_handoff"):
        return {
            "ready": False,
            "completion": {k: float(v) for k, v in (handoff.get("completion") or {}).items()},
            "reason": handoff.get("reason"),
        }
    student_id = await disc._profile_id_for_user(user_id)
    await disc._recompute_matches_for_student(student_id=student_id)
    matches = await MatchService(db).list_matches_for_display(student_id, limit=8)
    return {"ready": True, "matches": matches}


# ── generate_strategy ─────────────────────────────────────────────────────
async def tool_generate_strategy(
    db: AsyncSession, user_id: UUID, tool_input: dict[str, Any]
) -> dict[str, Any]:
    """Generate the broad strategy artifact (career → degree → paths + narrative)."""
    from unipaith.services.strategy_service import StrategyService

    try:
        strat = await StrategyService(db).generate(user_id)
    except Exception as exc:  # e.g. not enough signal yet → surface, don't 5xx
        return {"error": "strategy_unavailable", "detail": str(exc)[:200]}
    return {
        "career_target": strat.career_target,
        "target_degree": strat.target_degree,
        "academic_path": strat.academic_path,
        "financial_path": strat.financial_path,
        "geographic_path": strat.geographic_path,
        "narrative": strat.narrative,
    }


# ── get_profile_snapshot ──────────────────────────────────────────────────
async def tool_get_profile_snapshot(
    db: AsyncSession, user_id: UUID, tool_input: dict[str, Any]
) -> dict[str, Any]:
    """Everything UniPaith already knows about the student, compactly."""
    from unipaith.services.student_service import StudentService

    return await StudentService(db).get_full_snapshot(user_id)


# ── dispatcher ────────────────────────────────────────────────────────────
_TOOLS = {
    "get_profile_snapshot": tool_get_profile_snapshot,
    "search_programs": tool_search_programs,
    "save_signals": tool_save_signals,
    "get_matches": tool_get_matches,
    "generate_strategy": tool_generate_strategy,
}


async def dispatch_tool(
    db: AsyncSession,
    user_id: UUID,
    name: str,
    tool_input: dict[str, Any],
    *,
    session_id: UUID | None = None,
) -> dict[str, Any]:
    """Route an ``agent.custom_tool_use`` to its host implementation.

    Unknown names return a structured error rather than raising, so the host
    can forward it as the tool result and let the agent recover."""
    fn = _TOOLS.get(name)
    if fn is None:
        return {"error": f"unknown_tool:{name}"}
    if name == "save_signals":
        return await fn(db, user_id, tool_input, session_id=session_id)
    return await fn(db, user_id, tool_input)


# Used by the host to decide which results to surface to the frontend rail.
SURFACED_TOOLS = ("save_signals", "get_matches")

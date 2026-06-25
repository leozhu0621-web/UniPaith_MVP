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

import logging
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai.artifacts import persist_extraction
from unipaith.ai.extractor import ExtractedSignals
from unipaith.services.discovery_service import DiscoveryService

logger = logging.getLogger(__name__)


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


def _infer_maslow(text: str) -> str:
    """Best-effort Maslow level for a flat need signal that carries no level."""
    t = (text or "").lower()
    if any(
        k in t
        for k in (
            "money",
            "afford",
            "cost",
            "tuition",
            "financ",
            "scholarship",
            "safe",
            "stable",
            "debt",
        )
    ):
        return "safety"
    if any(
        k in t
        for k in ("communit", "belong", "friend", "peer", "social", "culture", "family", "connect")
    ):
        return "social"
    if any(
        k in t
        for k in (
            "respect",
            "recogni",
            "esteem",
            "support",
            "mentor",
            "confiden",
            "prestige",
            "rank",
        )
    ):
        return "self_esteem"
    if any(k in t for k in ("food", "health", "sleep", "housing", "basic")):
        return "physiological"
    return "self_actualization"


def _translate_flat_signals(signals: list[Any]) -> dict[str, Any]:
    """Map the platform agent's flat ``signals: [{type, content, evidence,
    completeness?}]`` shape onto the structured ExtractedSignals blocks the
    in-app persist layer expects (type ∈ goal|need|value|belief|fact)."""
    goals: list[dict[str, Any]] = []
    needs: list[dict[str, Any]] = []
    identity: list[dict[str, Any]] = []
    conf: dict[str, float] = {}
    for s in signals or []:
        if not isinstance(s, dict):
            continue
        kind = s.get("type")
        content = (s.get("content") or "").strip()
        evidence = (s.get("evidence") or content).strip()
        if not content:
            continue
        if kind == "goal":
            goals.append(
                {
                    "category": "academic",
                    "specific": content,
                    "completeness": s.get("completeness", 1.0),
                    "evidence": evidence,
                }
            )
            conf["goals"] = 0.85
        elif kind == "need":
            needs.append(
                {
                    "maslow_level": _infer_maslow(f"{content} {evidence}"),
                    "signal": content[:80],
                    "free_text": evidence,
                    "evidence": evidence,
                }
            )
            conf["needs"] = 0.85
        elif kind in ("value", "belief", "fact"):
            facet = {"value": "value", "belief": "belief", "fact": "self_awareness"}[kind]
            identity.append({"facet": facet, "claim": content, "evidence": evidence})
            conf["identity"] = 0.85
    return {"goals": goals, "needs": needs, "identity": identity, "confidence": conf}


async def tool_save_signals(
    db: AsyncSession,
    user_id: UUID,
    tool_input: dict[str, Any],
    *,
    session_id: UUID | None = None,
) -> dict[str, Any]:
    """Persist goals / needs / identity / basic signals from a turn, then report
    fresh completion + whether the student is handoff-ready.

    Accepts BOTH shapes: the structured EXTRACT_SIGNALS_TOOL blocks, and the
    platform agent's flat ``signals: [...]`` list (translated to the former)."""
    if isinstance(tool_input.get("signals"), list):
        tool_input = _translate_flat_signals(tool_input["signals"])
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
    # Make the Profile/Goals/Needs counters move and unlock the handoff gate:
    # the typed signals are persisted above, but discovery completion lives on
    # the session and is otherwise only written by the in-app orchestrator.
    await disc.recompute_completion_for_session(session_id)
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
    """Surface the student's top matches.

    Bootstraps a StudentFeatureVector from whatever signals the student has shared
    (the live managed-agent path persists typed signals but never emits a vector —
    that hook lives only in the in-app orchestrator). So 'See programs that fit me'
    returns real matches as soon as there are goals/needs to score, instead of
    bouncing to an empty page until full discovery handoff. When there's not enough
    signal to build a vector, reports ``ready=False`` plus what's still missing so
    the agent keeps the conversation going instead of guessing. Best-effort: an
    emit/embed failure degrades to the not-ready state, never a 5xx."""
    from unipaith.services.match_service import MatchService

    disc = DiscoveryService(db)
    student_id = await disc._profile_id_for_user(user_id)
    if not await MatchService(db).ensure_feature_vector(student_id):
        handoff = await disc.evaluate_handoff(user_id)
        return {
            "ready": False,
            "completion": {k: float(v) for k, v in (handoff.get("completion") or {}).items()},
            "reason": handoff.get("reason"),
        }
    await disc._recompute_matches_for_student(student_id=student_id)
    matches = await MatchService(db).list_matches_for_display(student_id, limit=8)
    return {"ready": True, "matches": matches}


async def _ensure_feature_vector(db: AsyncSession, student_id: UUID) -> None:
    """Emit a StudentFeatureVector from the structured tables if the student has
    none yet — closes the managed-agent gap where Discovery completes but the
    matcher has nothing to score. Delegates to the canonical
    MatchService.ensure_feature_vector (no-op when a vector already exists;
    best-effort so it never breaks the turn)."""
    from unipaith.services.match_service import MatchService

    await MatchService(db).ensure_feature_vector(student_id)


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


# ── create_profile ────────────────────────────────────────────────────────
async def tool_create_profile(
    db: AsyncSession, user_id: UUID, tool_input: dict[str, Any]
) -> dict[str, Any]:
    """The platform agent calls this 'at the end of the first session' to commit
    a new student profile. In UniPaith the StudentProfile already exists (created
    at signup), so this is an idempotent ack that returns the real profile id —
    durable signals are written via save_signals, not here."""
    from unipaith.services.discovery_service import DiscoveryService

    student_id = await DiscoveryService(db)._profile_id_for_user(user_id)
    return {
        "ok": True,
        "profile_id": str(student_id),
        "note": "profile already exists; signals persist via save_signals",
    }


# ── suggest_replies (UI affordance — no DB) ───────────────────────────────
def build_suggested_signals(tool_input: dict[str, Any]) -> dict[str, Any]:
    """Translate a ``suggest_replies`` tool call into the ``extracted_signals``
    shape the Discover frontend already reads off the persisted assistant
    message: ``suggested_options`` (tap chips) + optional ``suggested_input``
    ({kind: multi|scale, low_label, high_label}) for multi-select / 1–5 slider.
    This is what preserves the interactive (not just-talking) experience when
    Uni runs on the managed platform."""
    opts = [
        o.strip() for o in (tool_input.get("options") or []) if isinstance(o, str) and o.strip()
    ]
    signals: dict[str, Any] = {"suggested_options": opts}
    kind = tool_input.get("kind")
    if kind in ("multi", "scale"):
        sug: dict[str, Any] = {"kind": kind}
        for label_key in ("low_label", "high_label"):
            val = tool_input.get(label_key)
            if isinstance(val, str) and val.strip():
                sug[label_key] = val.strip()
        signals["suggested_input"] = sug
    if tool_input.get("offer_continue") is True:
        signals["requested_layer_advance"] = True
    return signals


# ── dispatcher ────────────────────────────────────────────────────────────
_TOOLS = {
    "get_profile_snapshot": tool_get_profile_snapshot,
    "create_profile": tool_create_profile,
    "search_programs": tool_search_programs,
    "save_signals": tool_save_signals,
    "get_matches": tool_get_matches,
    "generate_strategy": tool_generate_strategy,
}

# The live platform agent's tool names map onto the host implementations above.
# The agent is the source of truth; the host adapts to whatever it exposes.
_ALIASES = {
    "get_profile": "get_profile_snapshot",
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

    SECURITY: the platform agent passes a ``student_id`` in its tool input. The
    host IGNORES it and always operates on the authenticated ``user_id`` — an
    agent-supplied identity is never trusted.

    ``suggest_replies`` is handled in the host (UI affordance); any other
    unknown name returns a structured error rather than raising, so the host can
    forward it and let the agent recover."""
    canonical = _ALIASES.get(name, name)
    fn = _TOOLS.get(canonical)
    if fn is None:
        if name == "suggest_replies":
            return {"ok": True}
        return {"error": f"unknown_tool:{name}"}
    if canonical == "save_signals":
        return await fn(db, user_id, tool_input, session_id=session_id)
    return await fn(db, user_id, tool_input)


# Used by the host to decide which results to surface to the frontend rail.
SURFACED_TOOLS = ("save_signals", "get_matches")

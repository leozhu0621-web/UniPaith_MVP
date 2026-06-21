"""Uni chat-tab sessions API — /students/me/chat/* (folders + sessions CRUD).

The backend for the redesigned left-rail session browser (2026-06-19 chat-tab
spec §3): preset (protected) + custom folders, sessions auto-filed into a folder,
pin/within-folder reorder, and context-spawn.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.dependencies import require_student
from unipaith.models.user import User
from unipaith.services.chat.session_service import ChatSessionService
from unipaith.services.chat.template_actions import ACTION_CATALOG, ACTION_KEYS
from unipaith.services.chat.template_service import TemplateService
from unipaith.services.enrichment_planner import CATALOG
from unipaith.services.event_service import EventService
from unipaith.services.intake.intake_engine_service import IntakeEngineService
from unipaith.services.uni_tools import tool_generate_strategy, tool_get_matches

# Build a lookup from CATALOG by key for fast descriptor embedding.
_CATALOG_BY_KEY: dict[str, dict] = {f["key"]: f for f in CATALOG}

router = APIRouter(prefix="/students/me/chat", tags=["chat-sessions"])


def _folder(f) -> dict:
    return {
        "id": str(f.id),
        "name": f.name,
        "kind": f.kind,
        "topic_key": f.topic_key,
        "stage": f.stage,
        "sort_order": f.sort_order,
    }


def _session(s, folder=None) -> dict:
    return {
        "id": str(s.id),
        "title": s.title,
        "pinned": s.pinned,
        "sort_order": s.sort_order,
        "folder_id": str(s.folder_id),
        "origin_kind": s.origin_kind,
        "topic_key": folder.topic_key if folder is not None else None,
        # The discovery/conversation thread bound to this session (null until the
        # first turn creates one). Lets the chat tab resume the right thread.
        "conversation_session_id": s.agent_session_id,
    }


class SessionCreate(BaseModel):
    title: str
    topic_key: str | None = None
    origin_kind: str = "manual"
    origin_ref: str | None = None


class SessionPatch(BaseModel):
    title: str | None = None
    pinned: bool | None = None
    sort_order: int | None = None
    # Bind this session to its discovery/conversation thread (set once, on the
    # first turn). Only ever set non-null; never cleared.
    conversation_session_id: str | None = None


class FolderCreate(BaseModel):
    name: str


class FolderPatch(BaseModel):
    name: str | None = None
    sort_order: int | None = None


class ReorderIn(BaseModel):
    folder_id: UUID
    ordered_ids: list[UUID]


class TemplateStepOut(BaseModel):
    step_order: int
    step_type: str
    prompt_key: str | None = None
    action_key: str | None = None
    label: str
    # Prompt descriptor fields — only set when step_type == "prompt"
    question: str | None = None
    ask_kind: str | None = None
    options: list[str] | None = None
    # Action label from ACTION_CATALOG — only set when step_type == "action"
    action_label: str | None = None


class TemplateOut(BaseModel):
    key: str
    title: str
    topic: str
    stage: str
    outcome: str
    icon: str
    steps: list[TemplateStepOut]


async def _pid(db: AsyncSession, user: User) -> UUID:
    return await IntakeEngineService(db).profile_id_for_user(user.id)


@router.get("/templates", response_model=list[TemplateOut])
async def list_templates(
    user: User = Depends(require_student),  # noqa: ARG001  (auth only)
    db: AsyncSession = Depends(get_db),
):
    """Return all active session templates with their steps.

    Calls ensure_seeded() first so a fresh DB self-populates without a
    separate migration step. The seed is idempotent so this is safe to
    call on every request; the real cost is a single SELECT on warm DBs.

    Each prompt step is enriched with the catalog descriptor fields
    (question, ask_kind, options) so the frontend runner can render the
    widget without a separate per-key lookup.  Action steps include the
    action_label from ACTION_CATALOG.
    """
    svc = TemplateService(db)
    await svc.ensure_seeded()
    await db.commit()
    raw = await svc.load()

    # Embed catalog descriptors into each step.
    for tmpl in raw:
        for step in tmpl["steps"]:
            if step["step_type"] == "prompt":
                descriptor = _CATALOG_BY_KEY.get(step.get("prompt_key", ""), {})
                step["question"] = descriptor.get("question")
                step["ask_kind"] = descriptor.get("ask_kind")
                step["options"] = descriptor.get("options")  # list[str] or None
            elif step["step_type"] == "action":
                action_def = ACTION_CATALOG.get(step.get("action_key", ""), {})
                step["action_label"] = action_def.get("label")

    return raw


@router.get("/folders")
async def folders_tree(user: User = Depends(require_student), db: AsyncSession = Depends(get_db)):
    pid = await _pid(db, user)
    tree = await ChatSessionService(db).list_tree(pid)
    return {
        "folders": [
            {
                **_folder(node["folder"]),
                "sessions": [_session(s, node["folder"]) for s in node["sessions"]],
            }
            for node in tree
        ]
    }


@router.post("/sessions")
async def create_session(
    body: SessionCreate,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    pid = await _pid(db, user)
    s = await ChatSessionService(db).create_session(
        pid,
        title=body.title,
        topic_key=body.topic_key,
        origin_kind=body.origin_kind,
        origin_ref=body.origin_ref,
    )
    await db.refresh(s, ["folder"])
    return _session(s, s.folder)


@router.patch("/sessions/{session_id}")
async def patch_session(
    session_id: UUID,
    body: SessionPatch,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    pid = await _pid(db, user)
    s = await ChatSessionService(db).update_session(
        pid,
        session_id,
        title=body.title,
        pinned=body.pinned,
        sort_order=body.sort_order,
        agent_session_id=body.conversation_session_id,
    )
    return _session(s)


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    await ChatSessionService(db).delete_session(await _pid(db, user), session_id)
    return {"ok": True}


@router.post("/sessions/reorder")
async def reorder(
    body: ReorderIn,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    await ChatSessionService(db).reorder_sessions(
        await _pid(db, user), body.folder_id, body.ordered_ids
    )
    return {"ok": True}


@router.post("/folders")
async def create_folder(
    body: FolderCreate,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    f = await ChatSessionService(db).create_folder(await _pid(db, user), name=body.name)
    return _folder(f)


@router.patch("/folders/{folder_id}")
async def patch_folder(
    folder_id: UUID,
    body: FolderPatch,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    f = await ChatSessionService(db).update_folder(
        await _pid(db, user), folder_id, name=body.name, sort_order=body.sort_order
    )
    return _folder(f)


@router.delete("/folders/{folder_id}")
async def delete_folder(
    folder_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    await ChatSessionService(db).delete_folder(await _pid(db, user), folder_id)
    return {"ok": True}


# ── Action dispatch ────────────────────────────────────────────────────────────

# Word-label helpers for match display.
_FIT_LABELS: dict[str, str] = {
    "strong": "Great fit",
    "solid": "Good fit",
    "possible": "Possible",
    "reach": "Reach",
}
_ODDS_THRESHOLDS: list[tuple[float, str]] = [
    (0.70, "Likely"),
    (0.45, "Competitive"),
    (0.0, "Ambitious"),
]


def _odds_label(confidence: float) -> str:
    for threshold, label in _ODDS_THRESHOLDS:
        if confidence >= threshold:
            return label
    return "Ambitious"


def _event_subtitle(event) -> str | None:
    """Compose a short, honest subtitle for an event card from its real fields:
    the start date/time plus whichever of location / delivery format is present.
    Returns None when nothing real is available — never fabricates."""
    parts: list[str] = []
    start = getattr(event, "start_time", None)
    if isinstance(start, datetime):
        try:
            # e.g. "Mar 14, 3:00 PM". %-d/%-I are POSIX (the platform is darwin/linux).
            parts.append(start.strftime("%b %-d, %-I:%M %p"))
        except (ValueError, TypeError):
            parts.append(start.strftime("%b %d"))
    # The model has no `delivery_format`; surface location, else event_type,
    # else "Online" when a meeting link implies a virtual event.
    location = getattr(event, "location", None)
    event_type = getattr(event, "event_type", None)
    meeting_link = getattr(event, "meeting_link", None)
    place = location or event_type or ("Online" if meeting_link else None)
    if place:
        parts.append(str(place))
    return " · ".join(parts) if parts else None


class ActionArtifactItem(BaseModel):
    name: str
    program: str | None = None
    fit_label: str | None = None
    odds_label: str | None = None


class ActionArtifactOut(BaseModel):
    action_key: str
    kind: str
    title: str
    summary: str | None = None
    items: list[ActionArtifactItem] | None = None
    status: str  # "ready" | "pending"
    # Deep link back to the My Space surface that owns this artifact, set only
    # when the action produced a real, ready result. None for pending/not-real.
    link: str | None = None


_PENDING_SUMMARY = "This is coming soon — your inputs are saved."

# Action keys that have real service implementations today.
_REAL_ACTIONS = frozenset(
    {"build_school_list", "generate_strategy", "compare_schools", "find_events"}
)

# Actions that don't produce a one-shot artifact here — the work lives in a My
# Space surface (or Discover). Instead of a dead "coming soon" placeholder, hand
# the student off to where they actually do it. {key: (link, honest summary)}.
_HANDOFFS: dict[str, tuple[str, str]] = {
    "generate_goal_stack": ("/s/profile?tab=goals", "Set your goals in My Space → Goals."),
    "generate_needs_map": ("/s/profile?tab=needs", "Map what you need in My Space → Needs."),
    "build_checklist": ("/s/applications", "Build your application checklist in My Space."),
    "draft_feedback": ("/s/prep?tab=workshops", "Get feedback on your draft in My Space → Prep."),
    "interview_practice": ("/s/prep?tab=interviews", "Practice interviews in My Space → Prep."),
}


@router.post("/templates/action/{action_key}", response_model=ActionArtifactOut)
async def dispatch_template_action(
    action_key: str,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Run a template action step and return a normalized artifact.

    Real implementations (build_school_list, generate_strategy, compare_schools)
    delegate to existing uni_tools functions.  All other action keys return a
    pending artifact — never fabricated data.  Never raises 5xx.
    """
    if action_key not in ACTION_KEYS:
        raise HTTPException(status_code=400, detail=f"Unknown action key: {action_key!r}")

    if action_key not in _REAL_ACTIONS:
        title = ACTION_CATALOG.get(action_key, {}).get("label", action_key)
        handoff = _HANDOFFS.get(action_key)
        if handoff:
            link, summary = handoff
            # An honest handoff — not a fabricated result. The work happens in the
            # My Space surface this links to; the card invites the student there.
            return ActionArtifactOut(
                action_key=action_key,
                kind="handoff",
                title=title,
                summary=summary,
                status="ready",
                link=link,
            )
        return ActionArtifactOut(
            action_key=action_key,
            kind="note",
            title=title,
            summary=_PENDING_SUMMARY,
            status="pending",
        )

    # ── build_school_list / compare_schools → tool_get_matches ────────────────
    if action_key in ("build_school_list", "compare_schools"):
        try:
            result = await tool_get_matches(db, user.id, {})
        except Exception:
            result = {"ready": False}

        if not result.get("ready"):
            return ActionArtifactOut(
                action_key=action_key,
                kind="school_list" if action_key == "build_school_list" else "comparison",
                title="Your starter list" if action_key == "build_school_list" else "Side by side",
                summary="Your profile needs a bit more information before we can build your list.",
                status="pending",
            )

        matches = result.get("matches") or []
        items = [
            ActionArtifactItem(
                name=m.get("institution_name") or "Unknown school",
                program=m.get("program_name"),
                fit_label=_FIT_LABELS.get(m.get("band", ""), m.get("band")),
                odds_label=_odds_label(m.get("confidence", 0.0)),
            )
            for m in matches
        ]
        _no_match_list = "No matches yet — complete your profile to generate your list."
        _no_match_compare = "No matches yet — complete your profile to compare schools."
        if action_key == "build_school_list":
            return ActionArtifactOut(
                action_key=action_key,
                kind="school_list",
                title="Your starter list",
                items=items if items else None,
                status="ready" if items else "pending",
                summary=None if items else _no_match_list,
                link="/s/explore" if items else None,
            )
        else:
            return ActionArtifactOut(
                action_key=action_key,
                kind="comparison",
                title="Side by side",
                items=items if items else None,
                status="ready" if items else "pending",
                summary=None if items else _no_match_compare,
                link="/s/explore" if items else None,
            )

    # ── generate_strategy → tool_generate_strategy ────────────────────────────
    if action_key == "generate_strategy":
        try:
            result = await tool_generate_strategy(db, user.id, {})
        except Exception:
            result = {"error": "unavailable"}

        _strategy_pending = (
            "Your profile needs a bit more information before we can generate a strategy."
        )
        if result.get("error"):
            return ActionArtifactOut(
                action_key=action_key,
                kind="strategy",
                title="Your strategy",
                summary=_strategy_pending,
                status="pending",
            )

        narrative = result.get("narrative") or (
            f"Targeting {result.get('target_degree', 'a degree')} in "
            f"{result.get('career_target', 'your field')}."
        )
        return ActionArtifactOut(
            action_key=action_key,
            kind="strategy",
            title="Your strategy",
            summary=narrative,
            status="ready",
            link="/s/profile?tab=strategy",
        )

    # ── find_events → EventService.list_upcoming_events ───────────────────────
    if action_key == "find_events":
        try:
            events = await EventService(db).list_upcoming_events(limit=6)
        except Exception:
            # Treat any service failure as "no events" — an honest empty state,
            # never a 5xx and never fabricated data.
            events = []

        items = [
            ActionArtifactItem(
                name=getattr(e, "event_name", None) or "Event",
                program=_event_subtitle(e),
            )
            for e in events
        ]
        if not items:
            return ActionArtifactOut(
                action_key=action_key,
                kind="event_list",
                title="Upcoming events",
                summary=(
                    "No upcoming events right now — we'll surface them in Discover "
                    "as they're posted."
                ),
                status="ready",
                link="/s/explore?tab=events",
            )
        return ActionArtifactOut(
            action_key=action_key,
            kind="event_list",
            title="Upcoming events",
            items=items,
            status="ready",
            link="/s/explore?tab=events",
        )

    # Unreachable but satisfies type checker
    raise HTTPException(status_code=400, detail=f"Unknown action key: {action_key!r}")

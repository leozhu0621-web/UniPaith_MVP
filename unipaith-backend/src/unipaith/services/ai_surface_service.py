"""Spec 37 (AI Extensibility) §3 — human<->AI edit-diff capture.

The load-bearing contract of Spec 37: for every AI draft surface the user can
accept / edit / discard, and the audit log captures three events:

  - ``ai_generated:<surface>``   — the original AI output (the join token is the
                                   audit-row id returned by ``record_generated``).
  - ``human_edit:<surface>``     — the diff between the AI version and the human
                                   version at save/send time.
  - ``decision_action:<surface>``— the final action the human took.

This diff is the training signal for future per-tenant prompt tuning (§3). When
the institution is on the no-training tier (46 §9), each event is tagged
``training_eligible: False`` so the corpus extractor excludes it — the event is
still recorded (audit is always-on per 46 §2).

Built entirely on the existing ``admissions_audit_log`` table (its
``old_value`` / ``new_value`` / ``metadata_json`` JSONB columns) via
``AuditService`` — no new table. ``action`` strings stay < 64 chars.
"""

from __future__ import annotations

import difflib
import json
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.audit import AdmissionsAuditLog
from unipaith.services.audit_service import AuditService

# The three Spec 37 §3 event-action prefixes.
GENERATED = "ai_generated"
HUMAN_EDIT = "human_edit"
DECISION_ACTION = "decision_action"
_PREFIXES = (GENERATED, HUMAN_EDIT, DECISION_ACTION)


def _jsonable(obj: object) -> object | None:
    """Best-effort coercion to a JSON-storable value for the audit columns."""
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {str(k): _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    return str(obj)


def _to_text(obj: object) -> str:
    """Flatten an AI output (str or structured dict/list) into comparable text."""
    if obj is None:
        return ""
    if isinstance(obj, str):
        return obj
    if isinstance(obj, dict):
        parts: list[str] = []
        for k in sorted(obj.keys(), key=str):
            v = obj[k]
            if isinstance(v, str):
                parts.append(v)
            elif isinstance(v, (list, dict)):
                parts.append(json.dumps(v, sort_keys=True, ensure_ascii=False))
            elif v is not None:
                parts.append(str(v))
        return "\n".join(parts)
    if isinstance(obj, (list, tuple)):
        return "\n".join(_to_text(v) for v in obj)
    return str(obj)


def compute_diff(ai_output: object, final_output: object) -> dict:
    """Diff the AI original vs the human-edited final. Returns
    ``{was_edited, similarity, diff}`` where ``diff`` is a capped unified diff."""
    a = _to_text(ai_output)
    b = _to_text(final_output)
    similarity = round(difflib.SequenceMatcher(None, a, b).ratio(), 4)
    was_edited = a.strip() != b.strip()
    diff_lines = [
        ln for ln in difflib.unified_diff(a.splitlines(), b.splitlines(), lineterm="", n=1)
    ][:60]
    return {"was_edited": was_edited, "similarity": similarity, "diff": diff_lines}


class AISurfaceService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.audit = AuditService(db)

    async def record_generated(
        self,
        *,
        institution_id: UUID,
        actor_user_id: UUID | None,
        surface: str,
        agent: str,
        ai_output: object,
        application_id: UUID | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        confidence: int | float | None = None,
        model: str | None = None,
        no_training: bool = False,
    ) -> UUID:
        """Record an ``ai_generated:<surface>`` event. Returns the audit-row id,
        which the caller threads back as the ``draft_token`` join key."""
        meta: dict = {"surface": surface, "agent": agent, "training_eligible": not no_training}
        if confidence is not None:
            meta["confidence"] = confidence
        if model:
            meta["model"] = model
        row = await self.audit.log(
            institution_id=institution_id,
            actor_user_id=actor_user_id,
            action=f"{GENERATED}:{surface}",
            entity_type=(entity_type or surface)[:64],
            entity_id=str(entity_id or surface)[:128],
            application_id=application_id,
            description=f"AI draft generated for {surface}",
            old_value=None,
            new_value=_jsonable(ai_output),
            metadata_json=meta,
        )
        return row.id

    async def _load_generated(
        self, draft_token: UUID | None, institution_id: UUID
    ) -> AdmissionsAuditLog | None:
        if draft_token is None:
            return None
        row = await self.db.get(AdmissionsAuditLog, draft_token)
        if row is None or row.institution_id != institution_id:
            return None
        if not (row.action or "").startswith(f"{GENERATED}:"):
            return None
        return row

    async def record_committed(
        self,
        *,
        institution_id: UUID,
        actor_user_id: UUID | None,
        surface: str,
        final_output: object,
        action: str,
        draft_token: UUID | None = None,
        application_id: UUID | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        no_training: bool = False,
    ) -> dict:
        """Record ``human_edit:<surface>`` (diff vs the AI original) +
        ``decision_action:<surface>`` (the final action). Returns the diff."""
        original = await self._load_generated(draft_token, institution_id)
        ai_output = original.new_value if original is not None else None
        if application_id is None and original is not None:
            application_id = original.application_id
        diff = compute_diff(ai_output, final_output)
        parent = str(draft_token) if draft_token else None
        verb = "edited" if diff["was_edited"] else "accepted"

        await self.audit.log(
            institution_id=institution_id,
            actor_user_id=actor_user_id,
            action=f"{HUMAN_EDIT}:{surface}",
            entity_type=(entity_type or surface)[:64],
            entity_id=str(entity_id or surface)[:128],
            application_id=application_id,
            description=f"Human {verb} AI draft for {surface}",
            old_value=_jsonable(ai_output),
            new_value=_jsonable(final_output),
            metadata_json={
                "surface": surface,
                "parent_event_id": parent,
                "was_edited": diff["was_edited"],
                "similarity": diff["similarity"],
                "diff": diff["diff"],
                "training_eligible": not no_training,
            },
        )
        await self.audit.log(
            institution_id=institution_id,
            actor_user_id=actor_user_id,
            action=f"{DECISION_ACTION}:{surface}",
            entity_type=(entity_type or surface)[:64],
            entity_id=str(entity_id or surface)[:128],
            application_id=application_id,
            description=f"Final action '{action}' on {surface}",
            old_value=None,
            new_value={"action": action},
            metadata_json={"surface": surface, "parent_event_id": parent, "action": action},
        )
        return diff

    async def list_events(
        self,
        institution_id: UUID,
        *,
        surface: str | None = None,
        application_id: UUID | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AdmissionsAuditLog]:
        """All Spec 37 §3 events (the three prefixes) for an institution."""
        if surface:
            action_filter = or_(*[AdmissionsAuditLog.action == f"{p}:{surface}" for p in _PREFIXES])
        else:
            action_filter = or_(*[AdmissionsAuditLog.action.like(f"{p}:%") for p in _PREFIXES])
        stmt = (
            select(AdmissionsAuditLog)
            .where(
                AdmissionsAuditLog.institution_id == institution_id,
                action_filter,
            )
            .order_by(AdmissionsAuditLog.created_at.desc())
        )
        if application_id:
            stmt = stmt.where(AdmissionsAuditLog.application_id == application_id)
        stmt = stmt.offset(offset).limit(min(limit, 500))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

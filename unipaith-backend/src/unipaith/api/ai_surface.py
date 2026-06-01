"""Spec 37 (AI Extensibility) §3 — generic human<->AI edit-diff capture API.

The universal commit endpoint the frontend calls when a human saves/sends an
AI-assisted draft (message draft, inbox reply, campaign copy, …): it records the
``human_edit:<surface>`` diff + ``decision_action:<surface>`` events. Surface
endpoints (rubric pre-fill, packet summary, assistant chat, message draft) record
the ``ai_generated:<surface>`` event themselves and hand the frontend the
returned ``draft_token`` to thread back here.

``GET /events`` exposes the captured triplet for the audit log / training-signal
export (the diff is the per-tenant prompt-tuning signal, §3).
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.dependencies import require_institution_admin
from unipaith.models.user import User
from unipaith.services.ai_config_service import AI_SURFACES, AIConfigService
from unipaith.services.ai_surface_service import AISurfaceService
from unipaith.services.institution_service import InstitutionService

router = APIRouter(prefix="/institutions/me/ai-surface", tags=["ai-extensibility"])


class AISurfaceCommitRequest(BaseModel):
    surface: str
    final_content: dict | str
    action: str = "saved"
    draft_token: UUID | None = None
    application_id: UUID | None = None


class AISurfaceCommitResponse(BaseModel):
    captured: bool
    was_edited: bool
    similarity: float


class AISurfaceEventResponse(BaseModel):
    id: UUID
    action: str
    surface: str | None = None
    application_id: UUID | None = None
    actor_user_id: UUID | None = None
    was_edited: bool | None = None
    similarity: float | None = None
    training_eligible: bool | None = None
    description: str | None = None
    created_at: datetime


@router.post("/commit", response_model=AISurfaceCommitResponse)
async def commit_ai_surface_event(
    body: AISurfaceCommitRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Record the human-edit diff + final action for an AI-assisted draft the
    user just saved/sent. Idempotent-safe: a missing/foreign ``draft_token``
    still records the human side (with no AI original to diff against)."""
    inst = await InstitutionService(db).get_institution(user.id)
    no_training = await AIConfigService(db).is_no_training(inst.id)
    diff = await AISurfaceService(db).record_committed(
        institution_id=inst.id,
        actor_user_id=user.id,
        surface=body.surface,
        final_output=body.final_content,
        action=body.action,
        draft_token=body.draft_token,
        application_id=body.application_id,
        no_training=no_training,
    )
    return AISurfaceCommitResponse(
        captured=True, was_edited=diff["was_edited"], similarity=diff["similarity"]
    )


@router.get("/events", response_model=list[AISurfaceEventResponse])
async def list_ai_surface_events(
    surface: str | None = Query(None),
    application_id: UUID | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """The Spec 37 §3 capture trail (ai_generated / human_edit / decision_action)
    for this institution, newest first."""
    inst = await InstitutionService(db).get_institution(user.id)
    rows = await AISurfaceService(db).list_events(
        inst.id, surface=surface, application_id=application_id, limit=limit, offset=offset
    )
    out: list[AISurfaceEventResponse] = []
    for r in rows:
        meta = r.metadata_json or {}
        out.append(
            AISurfaceEventResponse(
                id=r.id,
                action=r.action,
                surface=meta.get("surface"),
                application_id=r.application_id,
                actor_user_id=r.actor_user_id,
                was_edited=meta.get("was_edited"),
                similarity=meta.get("similarity"),
                training_eligible=meta.get("training_eligible"),
                description=r.description,
                created_at=r.created_at,
            )
        )
    return out


@router.get("/surfaces", response_model=dict)
async def list_ai_surfaces(
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """The canonical surface registry + this institution's effective config —
    powers the /i/settings AI tab and any surface that needs to self-describe."""
    inst = await InstitutionService(db).get_institution(user.id)
    cfg = await AIConfigService(db).get_for_institution(inst.id)
    return {"surfaces": AI_SURFACES, "config": cfg}

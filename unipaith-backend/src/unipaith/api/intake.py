"""Spec 44 — Adaptive Intake Engine API.

Mounted at /api/v1/students/me/intake. The unified ingestion surface (§10): one
endpoint per intake channel (§5), the clarification confirm/correct loop (§6),
and the read-only completeness / match-ready / apply-ready gates (§4). All
endpoints require the student role and are scoped to the caller's own profile;
ingestion is consent-gated (matching) inside the service.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.dependencies import require_student
from unipaith.models.user import User
from unipaith.services.intake.intake_engine_service import IntakeEngineService

router = APIRouter(prefix="/students/me/intake", tags=["intake"])


def _svc(db: AsyncSession) -> IntakeEngineService:
    return IntakeEngineService(db)


# ── request bodies ───────────────────────────────────────────────────────────
class MessageIn(BaseModel):
    session_id: UUID
    content: str = Field(min_length=1, max_length=4000)


class FormSaveIn(BaseModel):
    signal_name: str = Field(min_length=1, max_length=80)
    value: Any


class DocumentUploadIn(BaseModel):
    file_ref: str = Field(min_length=1, max_length=255)
    parsed_fields: dict[str, Any] = Field(default_factory=dict)
    dataset_type: str = "transcript"
    size_bytes: int = 0


class ExternalLinkIn(BaseModel):
    url: str = Field(min_length=4, max_length=500)
    kind: str = Field(default="linkedin", pattern=r"^(linkedin|github|website|portfolio)$")


class ClarificationResolveIn(BaseModel):
    action: str = Field(pattern=r"^(confirm|correct)$")
    value: Any = None


# ── §5 ingestion channels ────────────────────────────────────────────────────
@router.post("/messages")
async def ingest_message(
    body: MessageIn,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """§5.1 — ingest a discovery-chat turn (records raw input + runs pipeline)."""
    return await _svc(db).ingest_message(user.id, body.session_id, body.content)


@router.post("/form-save")
async def ingest_form_save(
    body: FormSaveIn,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """§5.2 — save a form-bound signal change (student-typed, confidence 95)."""
    svc = _svc(db)
    student_id = await svc.profile_id_for_user(user.id)
    return await svc.ingest_form_save(student_id, body.signal_name, body.value)


@router.post("/document-upload")
async def ingest_document_upload(
    body: DocumentUploadIn,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """§5.3 — start an upload + parse pipeline (surfaces fields for confirm)."""
    svc = _svc(db)
    student_id = await svc.profile_id_for_user(user.id)
    return await svc.ingest_document_upload(
        student_id,
        file_ref=body.file_ref,
        parsed_fields=body.parsed_fields,
        dataset_type=body.dataset_type,
        size_bytes=body.size_bytes,
    )


@router.post("/external-link")
async def ingest_external_link(
    body: ExternalLinkIn,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """§5.4 — ingest an external link and run extraction (student-link, conf 75)."""
    svc = _svc(db)
    student_id = await svc.profile_id_for_user(user.id)
    return await svc.ingest_external_link(student_id, url=body.url, kind=body.kind)


# ── §6 clarification loop ────────────────────────────────────────────────────
@router.get("/clarifications")
async def list_clarifications(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """§6 — low-confidence values awaiting the student's confirm/correct."""
    svc = _svc(db)
    student_id = await svc.profile_id_for_user(user.id)
    return {"clarifications": await svc.list_clarifications(student_id)}


@router.post("/clarifications/{clarification_id}/confirm")
async def resolve_clarification(
    clarification_id: UUID,
    body: ClarificationResolveIn,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """§6 — confirm or correct a low-confidence value → confidence 95."""
    svc = _svc(db)
    student_id = await svc.profile_id_for_user(user.id)
    return await svc.resolve_clarification(
        student_id, clarification_id, action=body.action, value=body.value
    )


# ── §4 derived gates (read-only) ─────────────────────────────────────────────
@router.get("/completeness")
async def get_completeness(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """§4 / §10 — per-category coverage + overall_profile_completeness_pct."""
    svc = _svc(db)
    student_id = await svc.profile_id_for_user(user.id)
    return await svc.get_completeness(student_id)


@router.get("/match-ready")
async def get_match_ready(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """§4.1 — boolean + reasons for false (Stage 1 → Stage 2 gate)."""
    svc = _svc(db)
    student_id = await svc.profile_id_for_user(user.id)
    return await svc.get_match_ready(student_id)


@router.get("/apply-ready/{program_id}")
async def get_apply_ready(
    program_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """§4.2 — per-program apply-ready + per-requirement detail."""
    svc = _svc(db)
    student_id = await svc.profile_id_for_user(user.id)
    return await svc.get_apply_ready(student_id, program_id)

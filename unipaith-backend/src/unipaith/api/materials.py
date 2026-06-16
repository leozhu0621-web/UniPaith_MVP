"""Material ingest API — upload a file, Uni reads it, confirm into My Space.

POST /students/me/materials              multipart upload → parse → proposed
GET  /students/me/materials              recent ingests
POST /students/me/materials/{id}/apply   write the confirmed selection to My Space
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.dependencies import require_student
from unipaith.models.material_ingest import MaterialIngest
from unipaith.models.user import User
from unipaith.services.material_ingest_service import MaterialIngestService

router = APIRouter(prefix="/students/me/materials", tags=["materials"])

# Resumes / transcripts are small; cap to keep a synchronous parse snappy.
_MAX_BYTES = 15 * 1024 * 1024


class MaterialIngestResponse(BaseModel):
    id: UUID
    filename: str | None
    mime_type: str | None
    status: str
    proposed: dict[str, Any] | None
    applied_summary: dict[str, Any] | None
    error: str | None

    @classmethod
    def of(cls, row: MaterialIngest) -> MaterialIngestResponse:
        return cls(
            id=row.id,
            filename=row.filename,
            mime_type=row.mime_type,
            status=row.status,
            proposed=row.proposed,
            applied_summary=row.applied_summary,
            error=row.error,
        )


class ApplyMaterialRequest(BaseModel):
    profile: dict[str, Any] | None = None
    academic_records: list[dict[str, Any]] | None = None
    test_scores: list[dict[str, Any]] | None = None
    activities: list[dict[str, Any]] | None = None
    work_experiences: list[dict[str, Any]] | None = None
    goals: list[dict[str, Any]] | None = None
    needs: list[dict[str, Any]] | None = None
    identity: dict[str, Any] | None = None


@router.post("", response_model=MaterialIngestResponse)
async def upload_material(
    file: UploadFile = File(...),
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    data = await file.read()
    if len(data) > _MAX_BYTES:
        from unipaith.core.exceptions import BadRequestException

        raise BadRequestException("File is too large (max 15 MB).")
    row = await MaterialIngestService(db).ingest(
        user.id, filename=file.filename, mime_type=file.content_type, data=data
    )
    return MaterialIngestResponse.of(row)


@router.get("", response_model=list[MaterialIngestResponse])
async def list_materials(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    rows = await MaterialIngestService(db).list_ingests(user.id)
    return [MaterialIngestResponse.of(r) for r in rows]


@router.post("/{ingest_id}/apply")
async def apply_material(
    ingest_id: UUID,
    body: ApplyMaterialRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    return await MaterialIngestService(db).apply(
        user.id, ingest_id, body.model_dump(exclude_none=True)
    )


class AnswerFollowupRequest(BaseModel):
    gap: dict[str, Any]
    answer: str


@router.get("/{ingest_id}/followups")
async def get_followups(
    ingest_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Uni's follow-up questions for a just-applied import. Empty when the flag
    is off so the frontend simply shows nothing."""
    from sqlalchemy import select as _select

    from unipaith.config import settings
    from unipaith.services.follow_up_service import FollowUpService

    if not settings.ai_material_followups_v2_enabled:
        return {"questions": []}
    row = (
        await db.execute(
            _select(MaterialIngest).where(
                MaterialIngest.id == ingest_id,
            )
        )
    ).scalar_one_or_none()
    proposed = row.proposed if row else None
    gaps = await FollowUpService(db).detect(user.id, proposed)
    return {"questions": [{**g, "prompt": g.get("prompt_hint")} for g in gaps]}


@router.post("/followups/answer")
async def answer_followup(
    body: AnswerFollowupRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    from unipaith.services.follow_up_service import FollowUpService

    return await FollowUpService(db).answer(user.id, body.gap, body.answer)

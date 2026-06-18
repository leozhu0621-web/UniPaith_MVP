"""Enrichment API (AI Structure, Spec 1).

GET  /students/me/enrichment/next            next signal(s) to ask/confirm
POST /students/me/enrichment/{field}/value   submit a confirmed value
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.dependencies import require_student
from unipaith.models.user import User
from unipaith.services.enrichment_service import EnrichmentService
from unipaith.services.intake.intake_engine_service import IntakeEngineService

router = APIRouter(prefix="/students/me/enrichment", tags=["enrichment"])


class EnrichmentValueIn(BaseModel):
    value: Any


@router.get("/next")
async def get_next(
    limit: int = 3,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    student_id = await IntakeEngineService(db).profile_id_for_user(user.id)
    return await EnrichmentService(db).next_signals(student_id, limit=limit)


@router.post("/{field}/value")
async def set_value(
    field: str,
    body: EnrichmentValueIn,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    student_id = await IntakeEngineService(db).profile_id_for_user(user.id)
    return await EnrichmentService(db).set_value(student_id, field, body.value)

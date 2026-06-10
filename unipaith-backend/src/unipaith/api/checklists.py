"""Application checklist + readiness endpoints.

Relocated from the deleted ``api/workshops.py`` (Phase E / Spec 2026-06-10 §7)
— the essay/resume drafting endpoints that shared that module are gone
(workshops are feedback-only; see ``api/workshops_feedback.py``), but these
checklist routes are live and keep their exact paths.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.dependencies import require_student
from unipaith.models.user import User
from unipaith.schemas.checklist import (
    ApplicationChecklistResponse,
    ReadinessCheckResponse,
)
from unipaith.services.checklist_service import ChecklistService
from unipaith.services.student_service import StudentService

router = APIRouter(prefix="/students/me", tags=["checklists"])


@router.post(
    "/applications/{application_id}/checklist",
    response_model=ApplicationChecklistResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_checklist(
    application_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await StudentService(db)._get_student_profile(user.id)
    svc = ChecklistService(db)
    return await svc.generate_checklist(profile.id, application_id)


@router.get(
    "/applications/{application_id}/checklist",
    response_model=ApplicationChecklistResponse,
)
async def get_checklist(
    application_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await StudentService(db)._get_student_profile(user.id)
    svc = ChecklistService(db)
    return await svc.get_checklist(profile.id, application_id)


@router.get(
    "/applications/{application_id}/readiness",
    response_model=ReadinessCheckResponse,
)
async def readiness_check(
    application_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await StudentService(db)._get_student_profile(user.id)
    svc = ChecklistService(db)
    return await svc.readiness_check(profile.id, application_id)

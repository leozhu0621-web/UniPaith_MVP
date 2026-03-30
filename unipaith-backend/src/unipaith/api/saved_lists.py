from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.dependencies import require_student
from unipaith.models.user import User
from unipaith.schemas.saved_list import (
    CompareProgramsRequest,
    ComparisonResponse,
    SavedProgramResponse,
    SaveProgramRequest,
    UpdateSavedNotesRequest,
)
from unipaith.services.saved_list_service import SavedListService
from unipaith.services.student_service import StudentService

router = APIRouter(prefix="/students/me/saved", tags=["saved-lists"])


# --- Saved Programs ---


@router.get("", response_model=list[SavedProgramResponse])
async def list_saved_programs(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await StudentService(db)._get_student_profile(user.id)
    svc = SavedListService(db)
    return await svc.list_saved(profile.id)


@router.post("", response_model=SavedProgramResponse, status_code=status.HTTP_201_CREATED)
async def save_program(
    body: SaveProgramRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await StudentService(db)._get_student_profile(user.id)
    svc = SavedListService(db)
    return await svc.save_program(profile.id, body.program_id, body.notes)


@router.delete("/{program_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unsave_program(
    program_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await StudentService(db)._get_student_profile(user.id)
    svc = SavedListService(db)
    await svc.unsave_program(profile.id, program_id)


@router.put("/{program_id}/notes", response_model=SavedProgramResponse)
async def update_notes(
    program_id: UUID,
    body: UpdateSavedNotesRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await StudentService(db)._get_student_profile(user.id)
    svc = SavedListService(db)
    return await svc.update_notes(profile.id, program_id, body.notes)


@router.post("/compare", response_model=ComparisonResponse)
async def compare_programs(
    body: CompareProgramsRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await StudentService(db)._get_student_profile(user.id)
    svc = SavedListService(db)
    return await svc.compare_programs(profile.id, body.program_ids)

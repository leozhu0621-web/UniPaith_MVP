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
    PatchSavedProgramRequest,
    SavedProgramResponse,
    SaveProgramRequest,
    StartApplicationResponse,
    UpdateSavedNotesRequest,
)
from unipaith.services.saved_list_service import SavedListService
from unipaith.services.student_service import StudentService

router = APIRouter(prefix="/students/me/saved", tags=["saved-lists"])


@router.get("", response_model=list[SavedProgramResponse])
async def list_saved_programs(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await StudentService(db)._get_student_profile(user.id)
    svc = SavedListService(db)
    return await svc.list_saved_enriched(profile.id)


@router.get("/tags", response_model=list[str])
async def list_saved_tag_suggestions(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await StudentService(db)._get_student_profile(user.id)
    svc = SavedListService(db)
    return await svc.collect_tag_suggestions(profile.id)


@router.post("", response_model=SavedProgramResponse, status_code=status.HTTP_201_CREATED)
async def save_program(
    body: SaveProgramRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await StudentService(db)._get_student_profile(user.id)
    svc = SavedListService(db)
    await svc.save_program(profile.id, body.program_id, body.notes)
    rows = await svc.list_saved_enriched(profile.id)
    for row in rows:
        if row.program_id == body.program_id:
            return row
    raise RuntimeError("saved program missing after insert")


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
    await svc.update_notes(profile.id, program_id, body.notes)
    rows = await svc.list_saved_enriched(profile.id)
    for row in rows:
        if row.program_id == program_id:
            return row
    raise RuntimeError("saved program missing after notes update")


@router.patch("/{program_id}", response_model=SavedProgramResponse)
async def patch_saved_program(
    program_id: UUID,
    body: PatchSavedProgramRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await StudentService(db)._get_student_profile(user.id)
    svc = SavedListService(db)
    await svc.patch_saved(
        profile.id,
        program_id,
        priority=body.priority,
        notes=body.notes,
        tags=body.tags,
    )
    rows = await svc.list_saved_enriched(profile.id)
    for row in rows:
        if row.program_id == program_id:
            return row
    raise RuntimeError("saved program missing after patch")


@router.post(
    "/{program_id}/start-application",
    response_model=StartApplicationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def start_application_from_saved(
    program_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await StudentService(db)._get_student_profile(user.id)
    svc = SavedListService(db)
    app_id = await svc.start_application(profile.id, program_id)
    return StartApplicationResponse(app_id=app_id)


@router.post("/compare", response_model=ComparisonResponse)
async def compare_programs(
    body: CompareProgramsRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await StudentService(db)._get_student_profile(user.id)
    svc = SavedListService(db)
    return await svc.compare_programs(profile.id, body.program_ids)

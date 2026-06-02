"""Spec 56 §6 — Saved-search API.

Authed student endpoints:
  GET    /students/me/saved-searches          — list my saved searches
  POST   /students/me/saved-searches          — save the current search/filters
  PATCH  /students/me/saved-searches/{id}     — rename / toggle alert / replace query
  DELETE /students/me/saved-searches/{id}     — delete
  POST   /students/me/saved-searches/{id}/run — replay now (count + sample)

Saved searches are keyed by ``user_id`` (the durable owner, like notifications);
``run`` resolves the student profile so match-based sorts still work.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.dependencies import require_student
from unipaith.models.user import User
from unipaith.schemas.saved_search import (
    SavedSearchCreate,
    SavedSearchResponse,
    SavedSearchRunResponse,
    SavedSearchUpdate,
)
from unipaith.services.saved_search_service import SavedSearchService
from unipaith.services.student_service import StudentService

router = APIRouter(prefix="/students/me/saved-searches", tags=["saved-searches"])


@router.get("", response_model=list[SavedSearchResponse])
async def list_saved_searches(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
) -> list[SavedSearchResponse]:
    rows = await SavedSearchService(db).list(user.id)
    return [SavedSearchResponse.model_validate(r) for r in rows]


@router.post("", response_model=SavedSearchResponse, status_code=status.HTTP_201_CREATED)
async def create_saved_search(
    body: SavedSearchCreate,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
) -> SavedSearchResponse:
    row = await SavedSearchService(db).create(user.id, body)
    return SavedSearchResponse.model_validate(row)


@router.patch("/{saved_search_id}", response_model=SavedSearchResponse)
async def update_saved_search(
    saved_search_id: UUID,
    body: SavedSearchUpdate,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
) -> SavedSearchResponse:
    row = await SavedSearchService(db).update(user.id, saved_search_id, body)
    return SavedSearchResponse.model_validate(row)


@router.delete("/{saved_search_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_saved_search(
    saved_search_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
) -> None:
    await SavedSearchService(db).delete(user.id, saved_search_id)


@router.post("/{saved_search_id}/run", response_model=SavedSearchRunResponse)
async def run_saved_search(
    saved_search_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
) -> SavedSearchRunResponse:
    svc = SavedSearchService(db)
    row = await svc.get(user.id, saved_search_id)
    profile = await StudentService(db)._get_student_profile(user.id)
    return await svc.run(row, student_profile_id=profile.id if profile else None)

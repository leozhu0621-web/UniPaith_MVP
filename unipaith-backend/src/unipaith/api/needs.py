"""Phase A — Needs API. Mounted at /api/v1/students/me/needs."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.dependencies import require_student
from unipaith.models.user import User
from unipaith.schemas.needs import (
    CreateNeedRequest,
    MaslowLevel,
    NeedResponse,
    UpdateNeedRequest,
)
from unipaith.services.match_service import invalidate_matches_for_user
from unipaith.services.needs_service import NeedsService

router = APIRouter(prefix="/students/me/needs", tags=["needs"])


def _svc(db: AsyncSession) -> NeedsService:
    return NeedsService(db)


@router.get("", response_model=list[NeedResponse])
async def list_needs(
    maslow_level: MaslowLevel | None = Query(None),
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    needs = await _svc(db).list_needs(user.id, maslow_level=maslow_level)
    return [NeedResponse.model_validate(n) for n in needs]


@router.post("", response_model=NeedResponse, status_code=status.HTTP_201_CREATED)
async def create_need(
    body: CreateNeedRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    need = await _svc(db).create_need(user.id, body)
    await invalidate_matches_for_user(db, user.id)  # spec 06 §5.1
    return NeedResponse.model_validate(need)


@router.put("/{need_id}", response_model=NeedResponse)
async def update_need(
    need_id: UUID,
    body: UpdateNeedRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    need = await _svc(db).update_need(user.id, need_id, body)
    await invalidate_matches_for_user(db, user.id)  # spec 06 §5.1
    return NeedResponse.model_validate(need)


@router.delete("/{need_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_need(
    need_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    await _svc(db).delete_need(user.id, need_id)
    await invalidate_matches_for_user(db, user.id)  # spec 06 §5.1

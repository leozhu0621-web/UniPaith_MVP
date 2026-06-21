from __future__ import annotations

from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.dependencies import require_student
from unipaith.models.user import User
from unipaith.schemas.my_space import (
    MySpaceOverview,
    MySpaceTaskPatch,
    MySpaceTaskStateResponse,
)
from unipaith.services.my_space_service import MySpaceService

router = APIRouter(prefix="/students/me/my-space", tags=["my-space"])


@router.get("/overview", response_model=MySpaceOverview)
async def get_my_space_overview(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    return await MySpaceService(db).get_overview(user)


@router.patch("/tasks/{task_key}", response_model=MySpaceTaskStateResponse)
async def patch_my_space_task(
    body: MySpaceTaskPatch,
    task_key: str = Path(..., min_length=1, max_length=180),
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    return await MySpaceService(db).patch_task_state(user, task_key, body)

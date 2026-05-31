"""Phase A — Goals API. Mounted at /api/v1/students/me/goals."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.dependencies import require_student
from unipaith.models.user import User
from unipaith.schemas.goals import (
    CreateGoalRequest,
    GoalResponse,
    GoalStatus,
    UpdateGoalRequest,
)
from unipaith.services.goals_service import GoalsService
from unipaith.services.match_service import invalidate_matches_for_user

router = APIRouter(prefix="/students/me/goals", tags=["goals"])


def _svc(db: AsyncSession) -> GoalsService:
    return GoalsService(db)


@router.get("", response_model=list[GoalResponse])
async def list_goals(
    status_filter: GoalStatus | None = Query(None, alias="status"),
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    goals = await _svc(db).list_goals(user.id, status=status_filter)
    return [GoalResponse.model_validate(g) for g in goals]


@router.post("", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
async def create_goal(
    body: CreateGoalRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    goal = await _svc(db).create_goal(user.id, body)
    await invalidate_matches_for_user(db, user.id)  # spec 06 §5.1
    return GoalResponse.model_validate(goal)


@router.put("/{goal_id}", response_model=GoalResponse)
async def update_goal(
    goal_id: UUID,
    body: UpdateGoalRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    goal = await _svc(db).update_goal(user.id, goal_id, body)
    await invalidate_matches_for_user(db, user.id)  # spec 06 §5.1
    return GoalResponse.model_validate(goal)


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_goal(
    goal_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    await _svc(db).delete_goal(user.id, goal_id)
    await invalidate_matches_for_user(db, user.id)  # spec 06 §5.1

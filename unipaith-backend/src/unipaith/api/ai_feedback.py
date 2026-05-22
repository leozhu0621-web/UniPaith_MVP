"""Phase D1 — AI feedback API.

  - POST /api/students/me/ai-feedback — submit thumbs/regenerate/etc.
    on any AI surface. Idempotent on (student, target, surface).
  - GET /api/students/me/ai-feedback — recent feedback the student left.

Routes are mounted at the top level via `unipaith.api.router`;
no service-specific prefix nesting.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.dependencies import require_student
from unipaith.models.student import StudentProfile
from unipaith.models.user import User
from unipaith.services.ai_feedback_service import (
    ALLOWED_SURFACES,
    ALLOWED_VOTES,
    AiFeedbackService,
)

router = APIRouter(tags=["ai-feedback"])


# ── Request / response schemas ─────────────────────────────────────────────


class SubmitFeedbackRequest(BaseModel):
    target_id: UUID
    surface: str = Field(
        ...,
        description=f"One of: {', '.join(ALLOWED_SURFACES)}",
    )
    vote: str = Field(
        ...,
        description=f"One of: {', '.join(ALLOWED_VOTES)}",
    )
    reason_category: str | None = Field(default=None, max_length=40)
    free_text: str | None = Field(default=None, max_length=1000)
    context: dict | None = None


class FeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: UUID
    target_id: UUID
    surface: str
    vote: str
    reason_category: str | None
    free_text: str | None
    context: dict | None
    created_at: datetime
    updated_at: datetime


class FeedbackBreakdownResponse(BaseModel):
    surface: str
    total: int
    up: int
    down: int
    regenerate: int
    not_right: int
    negative_rate: float


class WeeklyDigestResponse(BaseModel):
    period_start: datetime
    period_end: datetime
    breakdowns: list[FeedbackBreakdownResponse]
    top_negative_examples: list[dict[str, Any]]
    safety_incident_count: int
    safety_incident_breakdown: dict[str, int]
    low_confidence_turns: int


# ── Student-side: submit feedback ──────────────────────────────────────────


@router.post(
    "/students/me/ai-feedback",
    response_model=FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_feedback(
    body: SubmitFeedbackRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Submit a thumbs / regenerate / not-right vote on any AI surface.

    Idempotent on (student_id, target_id, surface) — repeat submissions
    update the existing row in place. updated_at reflects the latest
    interaction.
    """
    profile = await db.scalar(select(StudentProfile).where(StudentProfile.user_id == user.id))
    if profile is None:
        # Same shape as the rest of /me endpoints when no profile exists.
        from unipaith.core.exceptions import NotFoundException

        raise NotFoundException("Student profile not found")

    row = await AiFeedbackService(db).submit_feedback(
        student_id=profile.id,
        target_id=body.target_id,
        surface=body.surface,
        vote=body.vote,
        reason_category=body.reason_category,
        free_text=body.free_text,
        context=body.context,
    )
    return row


@router.get(
    "/students/me/ai-feedback",
    response_model=list[FeedbackResponse],
)
async def list_my_feedback(
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Recent feedback the calling student has left, newest first."""
    profile = await db.scalar(select(StudentProfile).where(StudentProfile.user_id == user.id))
    if profile is None:
        return []
    return await AiFeedbackService(db).list_for_student(profile.id, limit=limit)


__all__ = ["router"]

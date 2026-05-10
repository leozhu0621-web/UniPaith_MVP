"""Phase A — Workshop feedback API (feedback-only).

New endpoints under /api/v1/students/me/workshops/* that ship the spec's
"workshops do not generate context" rule. The legacy generation-style
endpoints in api/workshops.py stay as deprecated shims for one release —
they get deleted in Phase D once the frontend has migrated.
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.dependencies import require_student
from unipaith.models.user import User
from unipaith.schemas.workshop_feedback import (
    EssayFeedbackRequest,
    InterviewPracticeRequest,
    TestGuidanceRequest,
    WorkshopFeedbackResponse,
)
from unipaith.services.workshop_feedback_service import WorkshopFeedbackService

router = APIRouter(prefix="/students/me/workshops", tags=["workshops-feedback"])


def _svc(db: AsyncSession) -> WorkshopFeedbackService:
    return WorkshopFeedbackService(db)


@router.post(
    "/essay/feedback",
    response_model=WorkshopFeedbackResponse,
    status_code=status.HTTP_201_CREATED,
)
async def request_essay_feedback(
    body: EssayFeedbackRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Coach an essay the student already wrote. Returns rubric + issues +
    missing-element prompts. Does NOT return revised text."""
    run = await _svc(db).request_essay_feedback(user.id, body)
    return WorkshopFeedbackResponse.model_validate(run)


@router.post(
    "/interview/practice",
    response_model=WorkshopFeedbackResponse,
    status_code=status.HTTP_201_CREATED,
)
async def request_interview_practice(
    body: InterviewPracticeRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Practice questions only — no model answers. Phase A pulls from a
    typed bank; Plan 2 will tailor to the program's interview style."""
    run = await _svc(db).request_interview_practice(user.id, body)
    return WorkshopFeedbackResponse.model_validate(run)


@router.post(
    "/test/guidance",
    response_model=WorkshopFeedbackResponse,
    status_code=status.HTTP_201_CREATED,
)
async def request_test_guidance(
    body: TestGuidanceRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Gap-analysis guidance for standardized tests. Returns rubric (current
    vs target) + structural prep recommendations. Does NOT generate practice
    test questions or answers."""
    run = await _svc(db).request_test_guidance(user.id, body)
    return WorkshopFeedbackResponse.model_validate(run)


@router.get("/runs", response_model=list[WorkshopFeedbackResponse])
async def list_workshop_runs(
    domain: Literal["essay", "interview", "test"] | None = Query(None),
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Recent feedback runs for this student, optionally filtered by domain."""
    runs = await _svc(db).list_runs(user.id, domain=domain)
    return [WorkshopFeedbackResponse.model_validate(r) for r in runs]

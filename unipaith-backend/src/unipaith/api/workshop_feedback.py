"""Phase A — Workshop feedback API (feedback-only)."""

from __future__ import annotations

from uuid import UUID

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
    svc = _svc(db)
    return svc.to_response(await svc.request_essay_feedback(user.id, body))


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
    svc = _svc(db)
    return svc.to_response(await svc.request_interview_practice(user.id, body))


@router.post(
    "/interview/feedback",
    response_model=WorkshopFeedbackResponse,
    status_code=status.HTTP_201_CREATED,
)
async def request_interview_feedback(
    body: InterviewPracticeRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    return svc.to_response(await svc.request_interview_feedback(user.id, body))


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
    svc = _svc(db)
    return svc.to_response(await svc.request_test_guidance(user.id, body))


@router.get("/runs", response_model=list[WorkshopFeedbackResponse])
async def list_workshop_runs(
    domain: str | None = Query(None, pattern="^(essay|interview|test)$"),
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    return [svc.to_response(r) for r in await svc.list_runs(user.id, domain=domain)]


@router.get("/runs/{run_id}", response_model=WorkshopFeedbackResponse)
async def get_workshop_run(
    run_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    return svc.to_response(await svc.get_run(user.id, run_id))

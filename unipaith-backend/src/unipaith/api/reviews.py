from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.dependencies import require_institution_admin
from unipaith.models.user import User
from unipaith.schemas.review import (
    AIReviewSummaryResponse,
    ApplicationScoreResponse,
    CreateRubricRequest,
    PipelineResponse,
    ReviewAssignmentResponse,
    RubricResponse,
    ScoreApplicationRequest,
)
from unipaith.services.institution_service import InstitutionService
from unipaith.services.review_pipeline_service import ReviewPipelineService

router = APIRouter(prefix="/reviews", tags=["reviews"])


# --- Rubrics ---


@router.post("/rubrics", response_model=RubricResponse, status_code=status.HTTP_201_CREATED)
async def create_rubric(
    body: CreateRubricRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst = await InstitutionService(db).get_institution(user.id)
    svc = ReviewPipelineService(db)
    return await svc.create_rubric(
        institution_id=inst.id,
        rubric_name=body.rubric_name,
        criteria=body.criteria,
        program_id=body.program_id,
    )


@router.get("/rubrics", response_model=list[RubricResponse])
async def list_rubrics(
    program_id: UUID | None = Query(None),
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst = await InstitutionService(db).get_institution(user.id)
    svc = ReviewPipelineService(db)
    return await svc.list_rubrics(inst.id, program_id=program_id)


# --- Application Review ---


@router.post("/applications/{application_id}/assign", response_model=list[ReviewAssignmentResponse])
async def assign_reviewers(
    application_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst = await InstitutionService(db).get_institution(user.id)
    svc = ReviewPipelineService(db)
    return await svc.assign_reviewers(application_id, inst.id)


@router.post("/applications/{application_id}/score", response_model=ApplicationScoreResponse)
async def score_application(
    application_id: UUID,
    body: ScoreApplicationRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst = await InstitutionService(db).get_institution(user.id)
    svc = ReviewPipelineService(db)
    reviewer = await svc.get_reviewer_by_user(user.id, inst.id)
    return await svc.score_application(
        reviewer_id=reviewer.id,
        application_id=application_id,
        rubric_id=body.rubric_id,
        criterion_scores=body.criterion_scores,
        reviewer_notes=body.reviewer_notes,
    )


@router.get("/applications/{application_id}/scores", response_model=list[ApplicationScoreResponse])
async def get_scores(
    application_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    await InstitutionService(db).get_institution(user.id)
    svc = ReviewPipelineService(db)
    return await svc.get_application_scores(application_id)


@router.get("/applications/{application_id}/ai-summary", response_model=AIReviewSummaryResponse)
async def ai_review_summary(
    application_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst = await InstitutionService(db).get_institution(user.id)
    svc = ReviewPipelineService(db)
    return await svc.generate_ai_review_summary(inst.id, application_id)


# --- Pipeline ---


@router.get("/pipeline/{program_id}", response_model=PipelineResponse)
async def get_pipeline(
    program_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst = await InstitutionService(db).get_institution(user.id)
    svc = ReviewPipelineService(db)
    return await svc.get_program_pipeline(inst.id, program_id)

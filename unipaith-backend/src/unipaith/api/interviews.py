from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.dependencies import require_institution_admin, require_student
from unipaith.models.user import User
from unipaith.schemas.batch import BatchInviteRequest, BatchOperationResult
from unipaith.schemas.interview import (
    ConfirmInterviewRequest,
    InterviewResponse,
    InterviewScoreResponse,
    ProposeInterviewRequest,
    ScoreInterviewRequest,
)
from unipaith.services.institution_service import InstitutionService
from unipaith.services.interview_service import InterviewService
from unipaith.services.review_pipeline_service import ReviewPipelineService
from unipaith.services.student_service import StudentService

router = APIRouter(prefix="/interviews", tags=["interviews"])


# --- Institution ---


@router.post("", response_model=InterviewResponse, status_code=status.HTTP_201_CREATED)
async def propose_interview(
    body: ProposeInterviewRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst = await InstitutionService(db).get_institution(user.id)
    svc = InterviewService(db)
    await svc._verify_application_ownership(inst.id, body.application_id)
    return await svc.propose_interview(
        application_id=body.application_id,
        interviewer_id=body.interviewer_id,
        interview_type=body.interview_type,
        proposed_times=body.proposed_times,
        duration_minutes=body.duration_minutes,
        location_or_link=body.location_or_link,
    )


@router.get("/institution", response_model=list[InterviewResponse])
async def list_institution_interviews(
    interview_status: str | None = Query(None, alias="status"),
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst = await InstitutionService(db).get_institution(user.id)
    svc = InterviewService(db)
    return await svc.list_institution_interviews(inst.id, status_filter=interview_status)


@router.get("/application/{application_id}", response_model=list[InterviewResponse])
async def list_interviews(
    application_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst = await InstitutionService(db).get_institution(user.id)
    svc = InterviewService(db)
    await svc._verify_application_ownership(inst.id, application_id)
    return await svc.list_application_interviews(application_id)


@router.post("/{interview_id}/complete", response_model=InterviewResponse)
async def complete_interview(
    interview_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst = await InstitutionService(db).get_institution(user.id)
    svc = InterviewService(db)
    await svc._verify_interview_ownership(inst.id, interview_id)
    return await svc.complete_interview(interview_id)


@router.post("/{interview_id}/score", response_model=InterviewScoreResponse)
async def score_interview(
    interview_id: UUID,
    body: ScoreInterviewRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst = await InstitutionService(db).get_institution(user.id)
    svc = InterviewService(db)
    reviewer = await ReviewPipelineService(db).get_reviewer_by_user(user.id, inst.id)
    return await svc.score_interview(
        interview_id=interview_id,
        interviewer_id=reviewer.id,
        criterion_scores=body.criterion_scores,
        total_weighted_score=body.total_weighted_score,
        interviewer_notes=body.interviewer_notes,
        recommendation=body.recommendation,
        rubric_id=body.rubric_id,
    )


# --- Student ---


@router.post("/{interview_id}/confirm", response_model=InterviewResponse)
async def confirm_time(
    interview_id: UUID,
    body: ConfirmInterviewRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await StudentService(db)._get_student_profile(user.id)
    svc = InterviewService(db)
    return await svc.confirm_time(profile.id, interview_id, body.confirmed_time)


@router.get("/me", response_model=list[InterviewResponse])
async def my_interviews(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await StudentService(db)._get_student_profile(user.id)
    svc = InterviewService(db)
    return await svc.get_student_interviews(profile.id)


# --- Batch Operations ---


@router.post("/batch/invite", response_model=BatchOperationResult)
async def batch_invite_interviews(
    body: BatchInviteRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst = await InstitutionService(db).get_institution(user.id)
    svc = InterviewService(db)
    for app_id in body.application_ids:
        await svc._verify_application_ownership(inst.id, app_id)
    result = BatchOperationResult(
        success_count=0, failed_ids=[], errors=[],
    )
    for app_id in body.application_ids:
        try:
            await svc.propose_interview(
                application_id=app_id,
                interviewer_id=body.interviewer_id,
                interview_type=body.interview_type,
                proposed_times=body.proposed_times,
                duration_minutes=body.duration_minutes,
                location_or_link=body.location_or_link,
            )
            result.success_count += 1
        except Exception as e:
            result.failed_ids.append(app_id)
            result.errors.append(str(e))
    return result

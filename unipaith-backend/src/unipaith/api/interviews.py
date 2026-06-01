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
    DraftInviteRequest,
    DraftInviteResponse,
    InterviewResponse,
    InterviewScoreResponse,
    ProposeInterviewRequest,
    RescheduleInterviewRequest,
    ScoreInterviewRequest,
    ScorePrefillRequest,
    ScorePrefillResponse,
)
from unipaith.services.institution_service import InstitutionService
from unipaith.services.interview_service import InterviewService
from unipaith.services.review_pipeline_service import ReviewPipelineService
from unipaith.services.student_service import StudentService

router = APIRouter(prefix="/interviews", tags=["interviews"])


# --- Institution ---


@router.post("", response_model=list[InterviewResponse], status_code=status.HTTP_201_CREATED)
async def propose_interview(
    body: ProposeInterviewRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Propose an interview to one or more applicants (Spec 33 §3). Creates an
    interview per applicant and posts each an ``interview_invite`` Inbox message;
    the student's Calendar item is auto-derived."""
    inst = await InstitutionService(db).get_institution(user.id)
    svc = InterviewService(db)
    interviews = await svc.propose_interviews(
        institution_id=inst.id,
        actor_user_id=user.id,
        application_ids=body.resolved_application_ids(),
        interview_type=body.interview_type,
        proposed_times=body.proposed_times,
        duration_minutes=body.duration_minutes,
        location_or_link=body.location_or_link,
        async_window_end=body.async_window_end,
        notes_to_student=body.notes_to_student,
        interviewer_id=body.interviewer_id,
        ai_draft_used=body.ai_draft_used,
    )
    return await svc.build_views(interviews)


@router.get("/institution", response_model=list[InterviewResponse])
async def list_institution_interviews(
    interview_status: str | None = Query(None, alias="status"),
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst = await InstitutionService(db).get_institution(user.id)
    svc = InterviewService(db)
    interviews = await svc.list_institution_interviews(inst.id, status_filter=interview_status)
    return await svc.build_views(interviews)


@router.get("/rubrics")
async def get_interview_rubrics(
    program_id: UUID | None = Query(None),
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Interviewing rubrics (kind='interview') for the Score modal, with a
    built-in default appended (§6)."""
    inst = await InstitutionService(db).get_institution(user.id)
    return await InterviewService(db).get_interview_rubrics(inst.id, program_id)


@router.get("/application/{application_id}", response_model=list[InterviewResponse])
async def list_interviews(
    application_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    await InstitutionService(db).get_institution(user.id)
    svc = InterviewService(db)
    interviews = await svc.list_application_interviews(application_id)
    return await svc.build_views(interviews)


@router.post("/{interview_id}/complete", response_model=InterviewResponse)
async def complete_interview(
    interview_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    await InstitutionService(db).get_institution(user.id)
    svc = InterviewService(db)
    interview = await svc.complete_interview(interview_id)
    return await svc.build_view(interview)


@router.post("/{interview_id}/cancel", response_model=InterviewResponse)
async def cancel_interview(
    interview_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    await InstitutionService(db).get_institution(user.id)
    svc = InterviewService(db)
    interview = await svc.cancel_interview(interview_id)
    return await svc.build_view(interview)


@router.post("/{interview_id}/no-show", response_model=InterviewResponse)
async def mark_no_show(
    interview_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    await InstitutionService(db).get_institution(user.id)
    svc = InterviewService(db)
    interview = await svc.mark_no_show(interview_id)
    return await svc.build_view(interview)


@router.post("/{interview_id}/reschedule", response_model=InterviewResponse)
async def reschedule_interview(
    interview_id: UUID,
    body: RescheduleInterviewRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    await InstitutionService(db).get_institution(user.id)
    svc = InterviewService(db)
    interview = await svc.reschedule_interview(
        interview_id,
        actor_user_id=user.id,
        proposed_times=body.proposed_times,
        async_window_end=body.async_window_end,
        duration_minutes=body.duration_minutes,
        location_or_link=body.location_or_link,
    )
    return await svc.build_view(interview)


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


# --- AI helpers (Spec 33 §9, gated by ai_interview_v2_enabled) ---


@router.post("/draft-invite", response_model=DraftInviteResponse)
async def draft_invite(
    body: DraftInviteRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst = await InstitutionService(db).get_institution(user.id)
    result = await InterviewService(db).draft_invite(
        institution_id=inst.id,
        application_id=body.application_id,
        interview_type=body.interview_type,
        proposed_times=body.proposed_times,
        async_window_end=body.async_window_end,
        duration_minutes=body.duration_minutes,
        location_or_link=body.location_or_link,
    )
    if result is None:
        return DraftInviteResponse(available=False)
    return DraftInviteResponse(
        available=True, draft=result.draft, tone=result.tone, length=result.length
    )


@router.post("/{interview_id}/score-prefill", response_model=ScorePrefillResponse)
async def score_prefill(
    interview_id: UUID,
    body: ScorePrefillRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst = await InstitutionService(db).get_institution(user.id)
    result = await InterviewService(db).score_prefill(
        institution_id=inst.id,
        interview_id=interview_id,
        rubric_id=body.rubric_id,
        transcript_or_notes=body.transcript_or_notes,
    )
    if result is None:
        return ScorePrefillResponse(available=False)
    return ScorePrefillResponse(
        available=True,
        criterion_scores=result.criterion_scores,
        overall_note=result.overall_note,
        recommendation=result.recommendation,
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
    result = await svc.confirm_time(profile.id, interview_id, body.confirmed_time)
    view = await svc.build_view(result)
    await db.commit()
    return view


@router.post("/{interview_id}/decline", response_model=InterviewResponse)
async def decline_interview(
    interview_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await StudentService(db)._get_student_profile(user.id)
    svc = InterviewService(db)
    result = await svc.decline_interview(profile.id, interview_id)
    view = await svc.build_view(result)
    await db.commit()
    return view


@router.post("/{interview_id}/request-reschedule", response_model=InterviewResponse)
async def request_reschedule(
    interview_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await StudentService(db)._get_student_profile(user.id)
    svc = InterviewService(db)
    result = await svc.request_reschedule(profile.id, interview_id)
    view = await svc.build_view(result)
    await db.commit()
    return view


@router.get("/me", response_model=list[InterviewResponse])
async def my_interviews(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await StudentService(db)._get_student_profile(user.id)
    svc = InterviewService(db)
    interviews = await svc.get_student_interviews(profile.id)
    return await svc.build_views(interviews)


# --- Batch Operations ---


@router.post("/batch/invite", response_model=BatchOperationResult)
async def batch_invite_interviews(
    body: BatchInviteRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst = await InstitutionService(db).get_institution(user.id)
    svc = InterviewService(db)
    result = BatchOperationResult(success_count=0, failed_ids=[], errors=[])
    for app_id in body.application_ids:
        try:
            await svc.propose_interviews(
                institution_id=inst.id,
                actor_user_id=user.id,
                application_ids=[app_id],
                interview_type=body.interview_type,
                proposed_times=body.proposed_times,
                duration_minutes=body.duration_minutes,
                location_or_link=body.location_or_link,
                interviewer_id=body.interviewer_id,
            )
            result.success_count += 1
        except Exception as e:  # noqa: BLE001
            result.failed_ids.append(app_id)
            result.errors.append(str(e))
    return result

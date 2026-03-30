from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.dependencies import require_student
from unipaith.models.user import User
from unipaith.schemas.checklist import (
    ApplicationChecklistResponse,
    ReadinessCheckResponse,
)
from unipaith.schemas.workshop import (
    AutoGenerateResumeRequest,
    CreateEssayRequest,
    EssayResponse,
    RequestEssayFeedbackRequest,
    RequestResumeFeedbackRequest,
    ResumeResponse,
    UpdateEssayRequest,
    UpdateResumeRequest,
)
from unipaith.services.checklist_service import ChecklistService
from unipaith.services.essay_workshop_service import EssayWorkshopService
from unipaith.services.resume_workshop_service import ResumeWorkshopService
from unipaith.services.student_service import StudentService

router = APIRouter(prefix="/students/me", tags=["workshops"])


# --- Checklists ---


@router.post(
    "/applications/{application_id}/checklist",
    response_model=ApplicationChecklistResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_checklist(
    application_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await StudentService(db)._get_student_profile(user.id)
    svc = ChecklistService(db)
    return await svc.generate_checklist(profile.id, application_id)


@router.get(
    "/applications/{application_id}/checklist",
    response_model=ApplicationChecklistResponse,
)
async def get_checklist(
    application_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await StudentService(db)._get_student_profile(user.id)
    svc = ChecklistService(db)
    return await svc.get_checklist(profile.id, application_id)


@router.get(
    "/applications/{application_id}/readiness",
    response_model=ReadinessCheckResponse,
)
async def readiness_check(
    application_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await StudentService(db)._get_student_profile(user.id)
    svc = ChecklistService(db)
    return await svc.readiness_check(profile.id, application_id)


# --- Essays ---


@router.post("/essays", response_model=EssayResponse, status_code=status.HTTP_201_CREATED)
async def create_essay(
    body: CreateEssayRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await StudentService(db)._get_student_profile(user.id)
    svc = EssayWorkshopService(db)
    return await svc.create_essay(
        student_id=profile.id,
        program_id=body.program_id,
        essay_type=body.essay_type,
        content=body.content,
        prompt_text=body.prompt_text,
    )


@router.get("/essays", response_model=list[EssayResponse])
async def list_essays(
    program_id: UUID | None = Query(None),
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await StudentService(db)._get_student_profile(user.id)
    svc = EssayWorkshopService(db)
    return await svc.list_essays(profile.id, program_id=program_id)


@router.get("/essays/{essay_id}", response_model=EssayResponse)
async def get_essay(
    essay_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await StudentService(db)._get_student_profile(user.id)
    svc = EssayWorkshopService(db)
    return await svc.get_essay(profile.id, essay_id)


@router.put("/essays/{essay_id}", response_model=EssayResponse)
async def update_essay(
    essay_id: UUID,
    body: UpdateEssayRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await StudentService(db)._get_student_profile(user.id)
    svc = EssayWorkshopService(db)
    return await svc.update_essay(profile.id, essay_id, body.content, body.prompt_text)


@router.post("/essays/{essay_id}/finalize", response_model=EssayResponse)
async def finalize_essay(
    essay_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await StudentService(db)._get_student_profile(user.id)
    svc = EssayWorkshopService(db)
    return await svc.finalize_essay(profile.id, essay_id)


@router.post("/essays/{essay_id}/feedback", response_model=EssayResponse)
async def request_essay_feedback(
    essay_id: UUID,
    body: RequestEssayFeedbackRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await StudentService(db)._get_student_profile(user.id)
    svc = EssayWorkshopService(db)
    return await svc.request_feedback(profile.id, essay_id, body.feedback_type)


# --- Resumes ---


@router.post(
    "/resume/generate", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED
)
async def auto_generate_resume(
    body: AutoGenerateResumeRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await StudentService(db)._get_student_profile(user.id)
    svc = ResumeWorkshopService(db)
    return await svc.auto_generate(
        profile.id,
        format_type=body.format_type,
        target_program_id=body.target_program_id,
    )


@router.get("/resume", response_model=list[ResumeResponse])
async def list_resumes(
    target_program_id: UUID | None = Query(None),
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await StudentService(db)._get_student_profile(user.id)
    svc = ResumeWorkshopService(db)
    return await svc.list_resumes(profile.id, target_program_id=target_program_id)


@router.put("/resume/{resume_id}", response_model=ResumeResponse)
async def update_resume(
    resume_id: UUID,
    body: UpdateResumeRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await StudentService(db)._get_student_profile(user.id)
    svc = ResumeWorkshopService(db)
    return await svc.update_resume(profile.id, resume_id, body.content)


@router.post("/resume/{resume_id}/finalize", response_model=ResumeResponse)
async def finalize_resume(
    resume_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await StudentService(db)._get_student_profile(user.id)
    svc = ResumeWorkshopService(db)
    return await svc.finalize_resume(profile.id, resume_id)


@router.post("/resume/{resume_id}/feedback", response_model=ResumeResponse)
async def request_resume_feedback(
    resume_id: UUID,
    body: RequestResumeFeedbackRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await StudentService(db)._get_student_profile(user.id)
    svc = ResumeWorkshopService(db)
    return await svc.request_feedback(profile.id, resume_id, body.feedback_type)

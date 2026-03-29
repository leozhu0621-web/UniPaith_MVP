from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.dependencies import require_student
from unipaith.models.user import User
from unipaith.schemas.student import (
    AcademicRecordResponse,
    ActivityResponse,
    CreateAcademicRecordRequest,
    CreateActivityRequest,
    CreateTestScoreRequest,
    NextStepResponse,
    OnboardingStatusResponse,
    StudentPreferenceResponse,
    StudentProfileResponse,
    TestScoreResponse,
    UpdateAcademicRecordRequest,
    UpdateActivityRequest,
    UpdateProfileRequest,
    UpdateTestScoreRequest,
    UpsertPreferencesRequest,
)
from unipaith.services.student_service import StudentService

router = APIRouter(prefix="/students", tags=["students"])


def _svc(db: AsyncSession) -> StudentService:
    return StudentService(db)


# --- Profile ---

@router.get("/me/profile", response_model=StudentProfileResponse)
async def get_profile(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await svc.get_profile(user.id)
    onboarding = await svc.get_onboarding_status(profile.id)
    resp = StudentProfileResponse.model_validate(profile)
    resp.onboarding = onboarding
    return resp


@router.put("/me/profile", response_model=StudentProfileResponse)
async def update_profile(
    body: UpdateProfileRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await svc.update_profile(user.id, body)
    return StudentProfileResponse.model_validate(profile)


# --- Onboarding ---

@router.get("/me/onboarding", response_model=OnboardingStatusResponse)
async def get_onboarding(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    return await svc.get_onboarding_status(profile.id)


@router.get("/me/onboarding/next-step", response_model=NextStepResponse | None)
async def get_next_onboarding_step(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    status = await svc.get_onboarding_status(profile.id)
    return status.next_step


# --- Academic Records ---

@router.get("/me/academics", response_model=list[AcademicRecordResponse])
async def list_academics(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    return await svc.list_academic_records(profile.id)


@router.post(
    "/me/academics",
    response_model=AcademicRecordResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_academic(
    body: CreateAcademicRecordRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    return await svc.create_academic_record(profile.id, body)


@router.put("/me/academics/{record_id}", response_model=AcademicRecordResponse)
async def update_academic(
    record_id: UUID,
    body: UpdateAcademicRecordRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    return await svc.update_academic_record(profile.id, record_id, body)


@router.delete("/me/academics/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_academic(
    record_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    await svc.delete_academic_record(profile.id, record_id)


# --- Test Scores ---

@router.get("/me/test-scores", response_model=list[TestScoreResponse])
async def list_test_scores(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    return await svc.list_test_scores(profile.id)


@router.post(
    "/me/test-scores",
    response_model=TestScoreResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_test_score(
    body: CreateTestScoreRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    return await svc.create_test_score(profile.id, body)


@router.put("/me/test-scores/{score_id}", response_model=TestScoreResponse)
async def update_test_score(
    score_id: UUID,
    body: UpdateTestScoreRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    return await svc.update_test_score(profile.id, score_id, body)


@router.delete("/me/test-scores/{score_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_test_score(
    score_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    await svc.delete_test_score(profile.id, score_id)


# --- Activities ---

@router.get("/me/activities", response_model=list[ActivityResponse])
async def list_activities(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    return await svc.list_activities(profile.id)


@router.post(
    "/me/activities",
    response_model=ActivityResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_activity(
    body: CreateActivityRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    return await svc.create_activity(profile.id, body)


@router.put("/me/activities/{activity_id}", response_model=ActivityResponse)
async def update_activity(
    activity_id: UUID,
    body: UpdateActivityRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    return await svc.update_activity(profile.id, activity_id, body)


@router.delete("/me/activities/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_activity(
    activity_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    await svc.delete_activity(profile.id, activity_id)


# --- Preferences ---

@router.get("/me/preferences", response_model=StudentPreferenceResponse | None)
async def get_preferences(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    return await svc.get_preferences(profile.id)


@router.put("/me/preferences", response_model=StudentPreferenceResponse)
async def upsert_preferences(
    body: UpsertPreferencesRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    return await svc.upsert_preferences(profile.id, body)

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import settings
from unipaith.core.exceptions import NotFoundException
from unipaith.database import get_db
from unipaith.dependencies import require_student
from unipaith.models.engagement import StudentEngagementSignal
from unipaith.models.matching import MatchResult
from unipaith.models.student import StudentProfile
from unipaith.models.user import User
from unipaith.schemas.matching import (
    EngagementSignalRequest,
    EngagementSignalResponse,
    MatchResultResponse,
)
from unipaith.schemas.student import (
    AcademicRecordResponse,
    AccommodationResponse,
    ActivityResponse,
    CompetitionResponse,
    CourseResponse,
    CreateAcademicRecordRequest,
    CreateActivityRequest,
    CreateCompetitionRequest,
    CreateCourseRequest,
    CreateLanguageRequest,
    CreateOnlinePresenceRequest,
    CreatePortfolioItemRequest,
    CreateResearchRequest,
    CreateTestScoreRequest,
    CreateWorkExperienceRequest,
    DataConsentResponse,
    LanguageResponse,
    NextStepResponse,
    OnboardingStatusResponse,
    OnlinePresenceResponse,
    PortfolioItemResponse,
    ResearchResponse,
    SchedulingResponse,
    StudentAssistantChatRequest,
    StudentAssistantChatResponse,
    StudentPreferenceResponse,
    StudentProfileResponse,
    TestScoreResponse,
    UpdateAcademicRecordRequest,
    UpdateActivityRequest,
    UpdateCompetitionRequest,
    UpdateCourseRequest,
    UpdateLanguageRequest,
    UpdateOnlinePresenceRequest,
    UpdatePortfolioItemRequest,
    UpdateProfileRequest,
    UpdateResearchRequest,
    UpdateTestScoreRequest,
    UpdateWorkExperienceRequest,
    UpsertAccommodationRequest,
    UpsertDataConsentRequest,
    UpsertPreferencesRequest,
    UpsertSchedulingRequest,
    UpsertVisaInfoRequest,
    VisaInfoResponse,
    WorkExperienceResponse,
)
from unipaith.services.matching_service import MatchingService
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
    onboarding = await svc.get_onboarding_status(profile.id)
    return onboarding.next_step


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


# --- Courses (nested under AcademicRecord) ---


@router.get(
    "/me/academics/{record_id}/courses",
    response_model=list[CourseResponse],
)
async def list_courses(
    record_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    return await svc.list_courses(profile.id, record_id)


@router.post(
    "/me/academics/{record_id}/courses",
    response_model=CourseResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_course(
    record_id: UUID,
    body: CreateCourseRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    return await svc.create_course(profile.id, record_id, body)


@router.put(
    "/me/academics/{record_id}/courses/{course_id}",
    response_model=CourseResponse,
)
async def update_course(
    record_id: UUID,
    course_id: UUID,
    body: UpdateCourseRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    return await svc.update_course(profile.id, record_id, course_id, body)


@router.delete(
    "/me/academics/{record_id}/courses/{course_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_course(
    record_id: UUID,
    course_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    await svc.delete_course(profile.id, record_id, course_id)


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


# --- Online Presence ---


@router.get("/me/online-presence", response_model=list[OnlinePresenceResponse])
async def list_online_presence(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    return await svc.list_online_presence(profile.id)


@router.post(
    "/me/online-presence",
    response_model=OnlinePresenceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_online_presence(
    body: CreateOnlinePresenceRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    return await svc.create_online_presence(profile.id, body)


@router.put(
    "/me/online-presence/{record_id}",
    response_model=OnlinePresenceResponse,
)
async def update_online_presence(
    record_id: UUID,
    body: UpdateOnlinePresenceRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    return await svc.update_online_presence(profile.id, record_id, body)


@router.delete(
    "/me/online-presence/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_online_presence(
    record_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    await svc.delete_online_presence(profile.id, record_id)


# --- Portfolio Items ---


@router.get("/me/portfolio", response_model=list[PortfolioItemResponse])
async def list_portfolio_items(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    return await svc.list_portfolio_items(profile.id)


@router.post(
    "/me/portfolio",
    response_model=PortfolioItemResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_portfolio_item(
    body: CreatePortfolioItemRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    return await svc.create_portfolio_item(profile.id, body)


@router.put("/me/portfolio/{record_id}", response_model=PortfolioItemResponse)
async def update_portfolio_item(
    record_id: UUID,
    body: UpdatePortfolioItemRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    return await svc.update_portfolio_item(profile.id, record_id, body)


@router.delete(
    "/me/portfolio/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_portfolio_item(
    record_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    await svc.delete_portfolio_item(profile.id, record_id)


# --- Research ---


@router.get("/me/research", response_model=list[ResearchResponse])
async def list_research(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    return await svc.list_research(profile.id)


@router.post(
    "/me/research",
    response_model=ResearchResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_research(
    body: CreateResearchRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    return await svc.create_research(profile.id, body)


@router.put("/me/research/{record_id}", response_model=ResearchResponse)
async def update_research(
    record_id: UUID,
    body: UpdateResearchRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    return await svc.update_research(profile.id, record_id, body)


@router.delete(
    "/me/research/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_research(
    record_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    await svc.delete_research(profile.id, record_id)


# --- Languages ---


@router.get("/me/languages", response_model=list[LanguageResponse])
async def list_languages(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    return await svc.list_languages(profile.id)


@router.post(
    "/me/languages",
    response_model=LanguageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_language(
    body: CreateLanguageRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    return await svc.create_language(profile.id, body)


@router.put("/me/languages/{record_id}", response_model=LanguageResponse)
async def update_language(
    record_id: UUID,
    body: UpdateLanguageRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    return await svc.update_language(profile.id, record_id, body)


@router.delete(
    "/me/languages/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_language(
    record_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    await svc.delete_language(profile.id, record_id)


# --- Work Experiences ---


@router.get(
    "/me/work-experiences",
    response_model=list[WorkExperienceResponse],
)
async def list_work_experiences(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    return await svc.list_work_experiences(profile.id)


@router.post(
    "/me/work-experiences",
    response_model=WorkExperienceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_work_experience(
    body: CreateWorkExperienceRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    return await svc.create_work_experience(profile.id, body)


@router.put(
    "/me/work-experiences/{record_id}",
    response_model=WorkExperienceResponse,
)
async def update_work_experience(
    record_id: UUID,
    body: UpdateWorkExperienceRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    return await svc.update_work_experience(profile.id, record_id, body)


@router.delete(
    "/me/work-experiences/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_work_experience(
    record_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    await svc.delete_work_experience(profile.id, record_id)


# --- Competitions ---


@router.get("/me/competitions", response_model=list[CompetitionResponse])
async def list_competitions(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    return await svc.list_competitions(profile.id)


@router.post(
    "/me/competitions",
    response_model=CompetitionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_competition(
    body: CreateCompetitionRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    return await svc.create_competition(profile.id, body)


@router.put(
    "/me/competitions/{record_id}",
    response_model=CompetitionResponse,
)
async def update_competition(
    record_id: UUID,
    body: UpdateCompetitionRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    return await svc.update_competition(profile.id, record_id, body)


@router.delete(
    "/me/competitions/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_competition(
    record_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    await svc.delete_competition(profile.id, record_id)


# --- Accommodations ---


@router.get(
    "/me/accommodations",
    response_model=AccommodationResponse | None,
)
async def get_accommodations(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    return await svc.get_accommodations(profile.id)


@router.put("/me/accommodations", response_model=AccommodationResponse)
async def upsert_accommodations(
    body: UpsertAccommodationRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    return await svc.upsert_accommodations(profile.id, body)


# --- Scheduling ---


@router.get("/me/scheduling", response_model=SchedulingResponse | None)
async def get_scheduling(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    return await svc.get_scheduling(profile.id)


@router.put("/me/scheduling", response_model=SchedulingResponse)
async def upsert_scheduling(
    body: UpsertSchedulingRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    return await svc.upsert_scheduling(profile.id, body)


# --- Visa Info ---


@router.get("/me/visa-info", response_model=VisaInfoResponse | None)
async def get_visa_info(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    return await svc.get_visa_info(profile.id)


@router.put("/me/visa-info", response_model=VisaInfoResponse)
async def upsert_visa_info(
    body: UpsertVisaInfoRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    return await svc.upsert_visa_info(profile.id, body)


# --- Timeline ---


@router.get("/me/timeline")
async def get_timeline(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Get chronological profile milestones and application events."""
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    return await svc.get_timeline(profile.id)


# --- Analytics ---


@router.get("/me/analytics")
async def get_analytics(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Get profile-level activity metrics and stats."""
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    return await svc.get_analytics(profile.id)


# --- Peer Comparison ---


@router.get("/me/peer-comparison")
async def get_peer_comparison(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Get anonymized percentile benchmarks vs peers."""
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    return await svc.get_peer_comparison(profile.id)


# --- Profile Export ---


@router.get("/me/export")
async def export_profile(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Export the full student profile as JSON."""
    from fastapi.responses import JSONResponse

    svc = _svc(db)
    profile = await svc.get_profile(user.id)
    onboarding = await svc.get_onboarding_status(profile.id)
    resp = StudentProfileResponse.model_validate(profile)
    resp.onboarding = onboarding
    data = resp.model_dump(mode="json")
    return JSONResponse(
        content=data,
        headers={
            "Content-Disposition": (
                f'attachment; filename="unipaith-profile-{user.id}.json"'
            ),
        },
    )


# --- Data Rights ---


@router.get("/me/data-rights", response_model=DataConsentResponse | None)
async def get_data_rights(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    return await svc.get_data_consent(profile.id)


@router.put("/me/data-rights", response_model=DataConsentResponse)
async def upsert_data_rights(
    body: UpsertDataConsentRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    return await svc.upsert_data_consent(profile.id, body)


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


# --- AI Matches ---


@router.get("/me/matches", response_model=list[MatchResultResponse])
async def get_my_matches(
    force_refresh: bool = Query(False, description="Force recomputation of matches"),
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Get AI-powered program matches. Requires 80% profile completion."""
    profile = await _svc(db)._get_student_profile(user.id)
    svc = MatchingService(db)
    return await svc.get_matches(profile.id, force_refresh=force_refresh)


@router.get("/me/matches/{program_id}", response_model=MatchResultResponse)
async def get_match_detail(
    program_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed match info for a specific program."""
    profile = await _svc(db)._get_student_profile(user.id)
    result = await db.execute(
        select(MatchResult).where(
            MatchResult.student_id == profile.id,
            MatchResult.program_id == program_id,
        )
    )
    match = result.scalar_one_or_none()
    if not match:
        raise NotFoundException("No match found for this program. Try refreshing matches.")
    return match


# --- Engagement ---


@router.post(
    "/me/engagement",
    response_model=EngagementSignalResponse,
    status_code=status.HTTP_201_CREATED,
)
async def log_engagement(
    body: EngagementSignalRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Log a student engagement signal (view, save, dismiss, time spent, etc.)."""
    profile = await _svc(db)._get_student_profile(user.id)
    signal = StudentEngagementSignal(
        student_id=profile.id,
        program_id=body.program_id,
        signal_type=body.signal_type,
        signal_value=body.signal_value,
    )
    db.add(signal)
    await db.flush()
    return signal


@router.post("/me/assistant/chat", response_model=StudentAssistantChatResponse)
async def student_assistant_chat(
    body: StudentAssistantChatRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """AI advisor chat with persistent memory, EQ detection, and persona tuning."""
    from unipaith.services.student_advisor import StudentAdvisor

    advisor = StudentAdvisor(db)
    result = await advisor.chat(
        student_user_id=user.id,
        message=body.message,
        context_program_id=body.context_program_id,
    )
    return StudentAssistantChatResponse(
        reply=result["reply"],
        model=settings.llm_reasoning_model,
    )


@router.post("/me/recommendations/ai")
async def get_student_recommendations(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Get personalized program recommendations with warm reasoning."""
    from unipaith.services.recommendation_engine import RecommendationEngine

    engine = RecommendationEngine(db)
    recommendations = await engine.generate_recommendations(
        student_user_id=user.id,
        count=5,
    )
    return {"recommendations": recommendations}


# ============ CONVERSATIONAL INTAKE & INTELLIGENCE ============


class IntakeChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class IntakeChatResponse(BaseModel):
    extracted_fields: dict
    next_question: str
    profile_updated: bool
    completion_pct: int


@router.post("/me/intake/chat", response_model=IntakeChatResponse)
async def intake_chat(
    body: IntakeChatRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Chat-based onboarding: extract profile fields from free text."""
    from unipaith.ai.llm_client import get_llm_client

    # Get-or-create student profile (new signups may not have one yet)
    result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        profile = StudentProfile(user_id=user.id)
        db.add(profile)
        await db.flush()

    llm = get_llm_client()

    system_prompt = (
        "You are an onboarding assistant for a college application "
        "platform called UniPaith. "
        "You are having a warm, conversational chat with a new "
        "student to learn about them. "
        "Extract structured profile fields from the student's "
        "message AND generate an engaging follow-up question.\n\n"
        "Fields to extract when mentioned: first_name, last_name, "
        "nationality, country_of_residence, bio_text, goals_text."
        "\n\nReturn JSON with:\n"
        '- "extracted_fields": dict of field_name: value '
        "(only fields actually mentioned)\n"
        '- "next_question": a warm, conversational follow-up '
        "that digs deeper into their story\n\n"
        "Make your follow-up question feel natural and curious "
        "— like a good mentor getting to know them. "
        "Ask about their motivations, dreams, experiences, "
        "or what excites them about their field.\n"
        "Return ONLY valid JSON."
    )

    if settings.ai_mock_mode:
        # Smart mock: parse common fields from the message
        msg_lower = body.message.lower()
        extracted: dict[str, str] = {}
        # Try to extract name
        if "i'm " in msg_lower or "my name is " in msg_lower or "i am " in msg_lower:
            parts = body.message.split()
            for i, w in enumerate(parts):
                if w.lower() in ("i'm", "am") and i + 1 < len(parts):
                    extracted["first_name"] = parts[i + 1].strip(".,!")
                    break
                if w.lower() == "name" and i + 2 < len(parts) and parts[i + 1].lower() == "is":
                    extracted["first_name"] = parts[i + 2].strip(".,!")
                    break
        # Try to extract country/location
        for kw in ("from ", "in ", "living in "):
            if kw in msg_lower:
                after = body.message[msg_lower.index(kw) + len(kw):]
                loc = after.split(".")[0].split(",")[0].strip()
                if loc and len(loc) < 40:
                    extracted["country_of_residence"] = loc
                    break
        # Store goals
        if any(w in msg_lower for w in ("study", "want", "interested", "goal", "dream", "plan")):
            extracted["goals_text"] = body.message[:200]

        # Adaptive follow-up questions based on what we learned
        name = extracted.get("first_name", "")
        greeting = f"Nice to meet you, {name}! " if name else "Great to hear that! "
        if "goals_text" in extracted and "country_of_residence" not in extracted:
            next_q = (
                f"{greeting}That sounds like an exciting path. "
                "Where are you currently based, and what "
                "sparked your interest in this field?"
            )
        elif "country_of_residence" in extracted and "goals_text" not in extracted:
            next_q = (
                f"{greeting}What are you hoping to study, "
                "and what draws you to that area?"
            )
        elif extracted:
            next_q = (
                f"{greeting}I'd love to learn more about what "
                "drives you. What experiences or moments "
                "led you to this path?"
            )
        else:
            next_q = (
                "That's interesting! Could you tell me a bit "
                "more about what you're hoping to study "
                "and what excites you about it?"
            )
    else:
        import json as _json

        raw = await llm.extract_features(system_prompt, body.message)
        try:
            parsed = _json.loads(raw)
            extracted = parsed.get("extracted_fields", {})
            next_q = parsed.get("next_question", "Tell me more about what excites you.")
        except Exception:
            extracted = {}
            next_q = (
                "That's really interesting! Could you tell "
                "me more about what draws you to that field?"
            )

    updated = False
    for field, value in extracted.items():
        if hasattr(profile, field) and value:
            setattr(profile, field, value)
            updated = True
    if updated:
        await db.flush()

    # Calculate completion percentage from extracted fields so far
    filled = sum(1 for f in ["first_name", "last_name", "nationality",
                             "country_of_residence", "bio_text", "goals_text"]
                 if getattr(profile, f, None))
    pct = min(95, filled * 15)

    return IntakeChatResponse(
        extracted_fields=extracted,
        next_question=next_q,
        profile_updated=updated,
        completion_pct=pct,
    )


class CompletionMapResponse(BaseModel):
    sections: list[dict]
    match_ready: bool
    apply_ready: bool
    match_ready_pct: int
    apply_ready_pct: int


@router.get("/me/completion-map", response_model=CompletionMapResponse)
async def get_completion_map(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Per-section completion with match-ready vs apply-ready."""
    svc = StudentService(db)
    profile = await svc._get_student_profile(user.id)
    onboarding = await svc.get_onboarding_status(profile.id)
    completed = set(onboarding.steps_completed) if onboarding else set()

    def _sec(name: str, key: str, match: bool) -> dict:
        return {
            "name": name,
            "key": key,
            "done": key in completed,
            "match_required": match,
            "apply_required": True,
        }

    sections = [
        _sec("Basic Info", "basic_profile", True),
        _sec("Academics", "academics", True),
        _sec("Test Scores", "test_scores", False),
        _sec("Activities", "activities", False),
        _sec("Preferences", "preferences", True),
        _sec("Essays", "essays", False),
        _sec("Documents", "documents", False),
    ]
    match_sections = [s for s in sections if s["match_required"]]
    apply_sections = sections
    match_done = sum(1 for s in match_sections if s["done"])
    apply_done = sum(1 for s in apply_sections if s["done"])

    return CompletionMapResponse(
        sections=sections,
        match_ready=all(s["done"] for s in match_sections),
        apply_ready=all(s["done"] for s in apply_sections),
        match_ready_pct=(
            round(match_done / len(match_sections) * 100)
            if match_sections
            else 0
        ),
        apply_ready_pct=(
            round(apply_done / len(apply_sections) * 100)
            if apply_sections
            else 0
        ),
    )


@router.get("/me/insights/confidence")
async def get_insights_confidence(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """PersonInsights grouped by confidence with provenance."""
    from unipaith.models.knowledge import PersonInsight

    result = await db.execute(
        select(PersonInsight).where(
            PersonInsight.user_id == user.id,
            PersonInsight.is_active.is_(True),
        ).order_by(PersonInsight.confidence.desc())
    )
    insights = list(result.scalars().all())

    high = [i for i in insights if i.confidence >= 0.8]
    medium = [i for i in insights if 0.5 <= i.confidence < 0.8]
    low = [i for i in insights if i.confidence < 0.5]

    def serialize(i: PersonInsight) -> dict:
        return {
            "id": str(i.id),
            "type": i.insight_type,
            "text": i.insight_text,
            "confidence": round(i.confidence, 2),
            "source": i.source,
            "created_at": i.created_at.isoformat(),
        }

    return {
        "high_confidence": [serialize(i) for i in high],
        "medium_confidence": [serialize(i) for i in medium],
        "low_confidence": [serialize(i) for i in low],
        "total": len(insights),
        "needs_clarification": len(low),
    }


@router.get("/me/profile/portable-export")
async def portable_export(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Export full portable profile as JSON."""
    svc = StudentService(db)
    profile = await svc.get_profile(user.id)
    onboarding = await svc.get_onboarding_status(profile.id)
    resp = StudentProfileResponse.model_validate(profile)
    resp.onboarding = onboarding
    return resp.model_dump(mode="json")

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.core.exceptions import NotFoundException
from unipaith.core.media_urls import resolve_media_urls
from unipaith.database import get_db
from unipaith.dependencies import require_student
from unipaith.models.engagement import StudentEngagementSignal
from unipaith.models.matching import MatchResult
from unipaith.models.student import StudentProfile
from unipaith.models.user import User
from unipaith.schemas.matching import (
    EngagementSignalRequest,
    EngagementSignalResponse,
    ExplainMatchResponse,
    StudentMatchResponse,
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
    LogPlatformEventRequest,
    MajorReadinessResponse,
    NextStepResponse,
    OnboardingStateResponse,
    OnboardingStatusResponse,
    OnlinePresenceResponse,
    PatchOnboardingStateRequest,
    PlatformEventResponse,
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
    UpsertMajorReadinessRequest,
    UpsertPreferencesRequest,
    UpsertSchedulingRequest,
    UpsertVisaInfoRequest,
    VisaInfoResponse,
    WorkExperienceResponse,
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
    # Spec 06 §5.1 — a direct profile edit invalidates derived matching
    # artifacts (rationale cache + match staleness), not just Discovery.
    from unipaith.services.match_service import invalidate_matches_for_user

    await invalidate_matches_for_user(db, user.id)
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


@router.patch("/me/onboarding/state", response_model=OnboardingStateResponse)
async def patch_onboarding_state(
    body: PatchOnboardingStateRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Ship C wizard persistence — key-wise merge; stamps are write-once."""
    svc = _svc(db)
    return await svc.patch_onboarding_state(user.id, body)


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
    created = await svc.create_academic_record(profile.id, body)
    # GPA / field feed the matcher's deal-breaker veto + s→p GPA grade — a record
    # edit must invalidate derived matches (the lazy GET recompute rescoring once).
    await _invalidate_matches(db, user.id)
    return created


@router.put("/me/academics/{record_id}", response_model=AcademicRecordResponse)
async def update_academic(
    record_id: UUID,
    body: UpdateAcademicRecordRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    updated = await svc.update_academic_record(profile.id, record_id, body)
    await _invalidate_matches(db, user.id)
    return updated


@router.delete("/me/academics/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_academic(
    record_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    await svc.delete_academic_record(profile.id, record_id)
    await _invalidate_matches(db, user.id)


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
    saved = await svc.upsert_visa_info(profile.id, body)
    # Visa need feeds the s→p visa-feasibility veto — re-score on next read.
    await _invalidate_matches(db, user.id)
    return saved


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
    request: Request,
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
    # Spec 36 §2 — data_export is an audited event.
    from unipaith.services.audit_service import AuditService

    await AuditService(db).log(
        institution_id=None,
        actor_user_id=user.id,
        actor_role="student",
        action="data_export",
        category="data_export",
        entity_type="consent",
        entity_id="profile_json",
        description="Exported full profile as JSON",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return JSONResponse(
        content=data,
        headers={
            "Content-Disposition": (f'attachment; filename="unipaith-profile-{user.id}.json"'),
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
    request: Request,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    return await svc.upsert_data_consent(
        profile.id,
        body,
        actor_user_id=user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )


@router.get("/me/access-log")
async def get_access_log(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Spec 08 §16 / 46 §8 — who/what accessed your data, when, and which fields."""
    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    return await svc.get_access_log(profile.id)


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
    saved = await svc.upsert_preferences(profile.id, body)
    # Priority weights + typed-fit wants + degree-target feed the matcher; this is
    # the single server-side choke point for all preference-editing FE surfaces
    # (PrioritySheet / PreferencesTab / CostsAidTab), regardless of which refreshes.
    await _invalidate_matches(db, user.id)
    return saved


# --- AI Matches ---


@router.get("/me/matches", response_model=list[StudentMatchResponse])
async def get_my_matches(
    limit: int = Query(20, ge=1, le=100),
    refresh: bool = Query(False, description="Recompute matches over the catalog first."),
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """List the student's matches, ordered by fitness desc, enriched with the
    program display fields, reach/target/safer band (Spec 09 §6), and
    probability bands (Spec 09 §4A).

    `refresh=true` recomputes the catalog first (same as POST /me/matches/refresh),
    applying the student's priority-weight preferences (Spec 09 §5.2).

    No LLM in this path — rationale is fetched lazily per-card via
    `POST /me/matches/{program_id}/explain`. Empty list when Discovery hasn't
    produced a feature vector yet.
    """
    profile = await _svc(db)._get_student_profile(user.id)
    if refresh:
        await _recompute_catalog_matches(db, profile.id)
    elif await _has_stale_matches(db, profile.id) and await _can_match(db, profile.id):
        # Lazy auto-refresh. A profile/goals/needs/identity edit marks the
        # student's matches stale (match_service.invalidate_for_profile_change);
        # the institution/segment read paths already filter is_stale, but the
        # student's own read did not — so she saw fitness/bands scored against an
        # OLD profile until a manual refresh. Recompute once when stale rows exist
        # (delete+insert resets is_stale=False), so this fires at most once per
        # edit — the read right after the edit, where she expects fresh matches.
        await _recompute_catalog_matches(db, profile.id)
    return await _list_enriched_matches(db, profile.id, limit=limit)


async def _invalidate_matches(db: AsyncSession, user_id: UUID) -> None:
    """Flag the student's derived match artifacts stale after a matcher-feeding
    edit (preferences / academics / visa). Mirrors the update_profile hook
    (Spec 06 §5.1) — bumps profile_version (rationale cache miss) + is_stale=True;
    the lazy GET /me/matches recompute then rescoring once."""
    from unipaith.services.match_service import invalidate_matches_for_user

    await invalidate_matches_for_user(db, user_id)


async def _has_stale_matches(db: AsyncSession, student_id: UUID) -> bool:
    """True when the student has at least one match row marked stale by a profile
    change — the cheap EXISTS gate for the lazy auto-refresh on read."""
    return (
        await db.scalar(
            select(MatchResult.id)
            .where(MatchResult.student_id == student_id, MatchResult.is_stale.is_(True))
            .limit(1)
        )
    ) is not None


async def _can_match(db: AsyncSession, student_id: UUID) -> bool:
    """Matching consent granted AND a feature vector exists (Discovery done).
    Gates the lazy recompute so a not-yet-matchable student's read is a cheap no-op."""
    from unipaith.services.match_service import MatchService

    return await MatchService(db).can_match(student_id)


@router.post("/me/matches/refresh", response_model=list[StudentMatchResponse])
async def refresh_my_matches(
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Spec 09 §7 / §5.2 / §8 — recompute matches over the published catalog,
    applying the student's priority-weight preferences, then return the
    refreshed top-N. Called after the priority sliders save and from the
    Match surface's manual refresh.

    Empty list when there's no feature vector yet (Discovery incomplete) or no
    published programs — the surface then shows the appropriate empty state.
    """
    profile = await _svc(db)._get_student_profile(user.id)
    await _recompute_catalog_matches(db, profile.id)
    return await _list_enriched_matches(db, profile.id, limit=limit)


async def _recompute_catalog_matches(db: AsyncSession, student_id: UUID) -> None:
    """Re-score the published catalog for one student, applying their priority
    weights (Spec 09 §5.2). Best-effort: mirrors discovery_service's recompute
    hook so an explicit refresh and a Discovery-completion recompute agree."""
    from unipaith.models.institution import Program
    from unipaith.services.match_banding import weights_from_preferences
    from unipaith.services.match_service import MatchService
    from unipaith.services.program_features import program_row_from_orm

    pref = await _svc(db).get_preferences(student_id)
    weights = weights_from_preferences(pref)

    programs = list(
        (await db.execute(select(Program).where(Program.is_published.is_(True)))).scalars().all()
    )
    if not programs:
        return
    program_rows = [program_row_from_orm(p) for p in programs]
    svc = MatchService(db)
    # Spec 65 §3 — embed the catalog so the matcher's cosine term fires, but only
    # when matching will actually run (Discovery done + consent granted). On the
    # empty-state path compute_matches_for_student returns [] after its own
    # guards, so skip embedding to avoid catalog-sized work for no matches.
    program_embeddings: dict = {}
    if await svc.can_match(student_id):
        program_embeddings = await svc.ensure_program_embeddings(programs)
    await svc.compute_matches_for_student(
        student_id,
        program_rows=program_rows,
        program_embeddings=program_embeddings,
        weights=weights,
    )


async def _list_enriched_matches(
    db: AsyncSession, student_id: UUID, *, limit: int
) -> list[StudentMatchResponse]:
    """Read matches + join program/institution + derive band + probability bands."""
    from unipaith.config import settings as _cfg
    from unipaith.models.institution import Institution, Program
    from unipaith.services.match_service import MatchService

    matches = await MatchService(db).list_matches(student_id, limit=limit)
    if not matches:
        return []
    program_ids = [m.program_id for m in matches]
    rows = (
        (
            await db.execute(
                select(MatchResult).where(
                    MatchResult.student_id == student_id,
                    MatchResult.program_id.in_(program_ids),
                )
            )
        )
        .scalars()
        .all()
    )
    row_by_pid = {r.program_id: r for r in rows}

    programs = (
        (await db.execute(select(Program).where(Program.id.in_(program_ids)))).scalars().all()
    )
    prog_by_id = {p.id: p for p in programs}
    inst_ids = {p.institution_id for p in programs}
    inst_name_by_id: dict = {}
    inst_ranking_by_id: dict = {}
    if inst_ids:
        inst_rows = (
            await db.execute(
                select(Institution.id, Institution.name, Institution.ranking_data).where(
                    Institution.id.in_(inst_ids)
                )
            )
        ).all()
        inst_name_by_id = {iid: name for iid, name, _rk in inst_rows}
        inst_ranking_by_id = {iid: rk for iid, _n, rk in inst_rows}

    pref = await _svc(db).get_preferences(student_id)
    weight_ranking = getattr(pref, "weight_ranking", None)
    bands_enabled = _cfg.ai_probability_bands_enabled

    out: list[StudentMatchResponse] = []
    for m in matches:  # preserves fitness-desc order
        row = row_by_pid.get(m.program_id)
        if row is None:
            continue
        program = prog_by_id.get(m.program_id)
        inst_name = inst_name_by_id.get(program.institution_id) if program else None
        inst_ranking = inst_ranking_by_id.get(program.institution_id) if program else None
        out.append(
            _enrich_match_for_student(
                row,
                program=program,
                institution_name=inst_name,
                institution_ranking=inst_ranking,
                weight_ranking=weight_ranking,
                bands_enabled=bands_enabled,
            )
        )
    return out


def _qualitative_fit_word(fitness: float) -> str:
    """Map a raw fitness score to a band WORD for the student-facing stub
    rationale (AI-Structure-3 §14: never a number). Thresholds mirror the
    _fitness_band cut points (0.75 / 0.55 / 0.40)."""
    if fitness >= 0.75:
        return "Strong"
    if fitness >= 0.55:
        return "Solid"
    if fitness >= 0.40:
        return "Moderate"
    return "Limited"


def _qualitative_confidence_word(confidence: float) -> str:
    """Map a raw confidence score to a word for the stub rationale (§14)."""
    if confidence >= 0.75:
        return "high"
    if confidence >= 0.50:
        return "solid"
    if confidence >= 0.30:
        return "moderate"
    return "still building as your profile fills in"


# Plain, student-facing labels for fitness drivers. CPEF breakdowns expose only
# internal keys (model/value/inner/coverage/veto/mean_rho/signals/...), so the
# stub rationale must map the per-SIGNAL keys to these phrases and never surface a
# raw breakdown key. Legacy convex-sum component keys map too.
_FITNESS_DRIVER_LABELS: dict[str, str] = {
    "semantic": "academic interests",
    "themes": "interests & goals",
    "needs": "your priorities",
    "field": "field of study",
    "budget": "affordability",
    "geo": "location",
    "time": "program length",
    "flexibility": "format flexibility",
    "support": "career support",
    "degree_level": "degree level",
    # legacy convex-sum components
    "cosine": "academic interests",
    "soft_align": "interests & goals",
    "needs_match": "your priorities",
}


def _humanize_fitness_drivers(breakdown: dict, *, top_n: int = 3) -> list[str]:
    """Friendly, student-facing driver phrases from a fitness breakdown.

    For a CPEF breakdown the raw keys are internal, so we read the per-signal
    ``signals`` list, take the strongest-fitting signals, and map them to plain
    labels. For the legacy convex-sum breakdown we map its component keys. Either
    way an internal/meta key (weights, mean_rho, coverage, ...) is never leaked.
    """
    if not isinstance(breakdown, dict):
        return []
    labels: list[str] = []
    if breakdown.get("model") == "cpef":
        signals = breakdown.get("signals") or []
        ranked = sorted(
            (s for s in signals if isinstance(s, dict) and s.get("key")),
            key=lambda s: s.get("f", 0.0),
            reverse=True,
        )
        candidates = [s["key"] for s in ranked]
    else:
        candidates = list(breakdown.keys())
    for key in candidates:
        label = _FITNESS_DRIVER_LABELS.get(key)
        if label and label not in labels:
            labels.append(label)
        if len(labels) >= top_n:
            break
    return labels


def _band_fitness(match: MatchResult) -> float:
    """The fitness to BAND on (reach/target/safer + probability bands): the
    student-direction CPEF fit ``s2p_value`` when present, else the persisted
    ``fitness_score``.

    The persisted ``fitness_score`` is the blended rank key M = sp^α·ps^(1-α),
    which is alpha-inflated above the student's own fit for no-preference
    programs (ps=1 ⇒ M = sp^α > sp). M is the right RANKING key, but the band
    answers "what are MY odds", so it should reflect the student's own fit.
    """
    bd = match.fitness_breakdown or {}
    s2p = bd.get("s2p_value")
    return float(s2p) if s2p is not None else float(match.fitness_score)


def _band_readiness(match: MatchResult) -> float | None:
    """Student-side confidence (c_student) for the probability-band VISIBILITY
    gate, read from the CPEF confidence breakdown. None for legacy/non-cpef rows
    (the band layer then falls back to the persisted product confidence)."""
    return (match.confidence_breakdown or {}).get("c_student")


def _strip_numbers(obj: object) -> object:
    """Recursively remove every numeric scalar from a breakdown so the student
    never sees a number (AI-Structure-3 §14). Qualitative driver names, boolean
    flags, and nested structure are kept; ints/floats/Decimals are dropped at any
    depth. ``bool`` is preserved (it is a flag, not a score). This guarantees the
    raw CPEF readouts (value / m / inner / coverage / mean_rho / per-signal f, c,
    rho, A …) cannot leak into the student's rationale popover."""
    from decimal import Decimal

    def _is_num(v: object) -> bool:
        return isinstance(v, (int, float, Decimal)) and not isinstance(v, bool)

    if isinstance(obj, dict):
        return {k: _strip_numbers(v) for k, v in obj.items() if not _is_num(v)}
    if isinstance(obj, list):
        return [_strip_numbers(v) for v in obj if not _is_num(v)]
    return obj


def _redact_match_for_student(match: MatchResult) -> StudentMatchResponse:
    """Serialize a MatchResult to its student-safe response (spec 06 §5.5 +
    AI-Structure-3 §14 backend-only contract).

    The raw CPEF numbers (``fitness_score`` / ``confidence_score`` /
    ``match_score`` / ``score_breakdown``) are NOT carried on
    ``StudentMatchResponse`` at all — the student gets band + rationale +
    probability bands only. The breakdowns that DO survive (the rationale
    popover's qualitative drivers) are run through the §5.5 redaction map so no
    institution-only signal leaks, AND through ``_strip_numbers`` so no raw score
    reaches the student through the breakdown channel (§14: never sees a number).
    """
    from unipaith.ai.rationale_redaction import redact_mapping

    resp = StudentMatchResponse.model_validate(match)
    resp.fitness_breakdown = _strip_numbers(redact_mapping(resp.fitness_breakdown or {}))
    resp.confidence_breakdown = _strip_numbers(redact_mapping(resp.confidence_breakdown or {}))
    return resp


def _institution_acceptance_rate(institution_ranking: object) -> float | None:
    """The institution's published admit rate from its ranking_data, clamped to
    [0,1], or None. A read-path fallback so a program with no own acceptance_rate
    still gets selectivity bands from EXISTING institution-level data — without it
    probability bands + selectivity banding are dead for ~every program."""
    if not isinstance(institution_ranking, dict):
        return None
    raw = institution_ranking.get("acceptance_rate")
    if raw is None:
        return None
    try:
        return max(0.0, min(1.0, float(raw)))
    except (TypeError, ValueError):
        return None


def _enrich_match_for_student(
    match: MatchResult,
    *,
    program=None,
    institution_name: str | None = None,
    institution_ranking: object = None,
    weight_ranking: int | None = None,
    bands_enabled: bool = True,
) -> StudentMatchResponse:
    """Student-safe response (spec 06 §5.5) plus Spec 09 context: program
    display fields, reach/target/safer band (§6), and probability bands (§4A).

    The raw fitness/confidence numbers drive the band + probability computation
    here on the backend, but are never serialized into the response (backend-only
    contract, AI-Structure-3 §14)."""
    from unipaith.ai.probability import estimate_probability_bands
    from unipaith.services.match_banding import band_for_acceptance

    resp = _redact_match_for_student(match)

    acceptance_rate: float | None = None
    if program is not None:
        resp.program_name = getattr(program, "program_name", None)
        resp.institution_id = getattr(program, "institution_id", None)
        resp.degree_type = getattr(program, "degree_type", None)
        resp.tuition = getattr(program, "tuition", None)
        ar = getattr(program, "acceptance_rate", None)
        acceptance_rate = float(ar) if ar is not None else None
        # Fall back to the institution's published admit rate when the program has
        # none of its own — otherwise bands/selectivity are dead for ~all programs.
        if acceptance_rate is None:
            acceptance_rate = _institution_acceptance_rate(institution_ranking)
        resp.acceptance_rate = acceptance_rate
    if institution_name is not None:
        resp.institution_name = institution_name

    # Band on the student-direction fit (s2p_value), not the alpha-inflated blend
    # M; gate band VISIBILITY on c_student, keep band WIDTH on the product.
    fitness = _band_fitness(match)
    confidence = float(match.confidence_score)
    resp.band_label = band_for_acceptance(
        fitness=fitness, acceptance_rate=acceptance_rate, weight_ranking=weight_ranking
    )
    if bands_enabled:
        resp.probability_bands = estimate_probability_bands(
            acceptance_rate=acceptance_rate,
            fitness=fitness,
            confidence=confidence,
            readiness=_band_readiness(match),
        )
    return resp


@router.get("/me/matches/{program_id}", response_model=StudentMatchResponse)
async def get_match_detail(
    program_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed match info for a specific program (enriched per Spec 09)."""
    from unipaith.config import settings as _cfg
    from unipaith.models.institution import Institution, Program

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

    program = await db.scalar(select(Program).where(Program.id == program_id))
    inst_name = None
    inst_ranking = None
    if program is not None:
        inst_row = (
            await db.execute(
                select(Institution.name, Institution.ranking_data).where(
                    Institution.id == program.institution_id
                )
            )
        ).first()
        if inst_row is not None:
            inst_name, inst_ranking = inst_row
    pref = await _svc(db).get_preferences(profile.id)
    return _enrich_match_for_student(
        match,
        program=program,
        institution_name=inst_name,
        institution_ranking=inst_ranking,
        weight_ranking=getattr(pref, "weight_ranking", None),
        bands_enabled=_cfg.ai_probability_bands_enabled,
    )


# --- Net Price Estimator (Spec 11 §3.3a / output schema 42 §4.12) ---


class NetPriceRangeResponse(BaseModel):
    """A {min, expected, max} money range — always a range, never a point."""

    min: float
    expected: float
    max: float


class NetPriceGapResponse(BaseModel):
    student_annual_budget: float | None = None
    shortfall_annual: float | None = None
    band: str  # affordable | stretch | out_of_reach | unknown


class NetPriceEstimateResponse(BaseModel):
    """Personalized net-price estimate for one student at one program.

    `available=False` (with `reason`) when the program lacks the cost data to
    estimate honestly — the UI then hides the block rather than show a fake
    number. Always framed as an estimate, never an aid commitment (`disclaimer`).
    """

    program_id: UUID
    available: bool
    reason: str | None = None
    currency: str = "USD"
    cost_of_attendance_annual: float | None = None
    net_cost_scenario_range: NetPriceRangeResponse | None = None
    net_cost_scenario_range_total: NetPriceRangeResponse | None = None
    years: float | None = None
    affordability_band: str  # affordable | stretch | out_of_reach | unknown
    aid_scholarship_likelihood_band: str  # low | moderate | high | unknown
    gap: NetPriceGapResponse
    drivers: list[str] = []
    disclaimer: str


@router.get("/me/programs/{program_id}/net-price", response_model=NetPriceEstimateResponse)
async def get_program_net_price(
    program_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Spec 11 §3.3a — a personalized **net price** (not sticker) for this
    student at this program: estimated cost of attendance minus estimated aid,
    as a {min, expected, max} range, plus a gap analysis vs the student's budget.

    Deterministic / rule-based (no LLM). Honesty guardrail: always a range,
    framed as an estimate, never implies an aid commitment.
    """
    from unipaith.services.net_price_service import NetPriceService

    data = await NetPriceService(db).estimate_for_student(user_id=user.id, program_id=program_id)
    return NetPriceEstimateResponse(program_id=program_id, **data)


class ScholarshipMatchItem(BaseModel):
    """Spec 70 §3 — one scholarship the student may qualify for."""

    scholarship_id: str
    name: str
    award_estimate: int
    reasons: list[str]
    scholarship_type: str


@router.get("/me/scholarships/match", response_model=list[ScholarshipMatchItem])
async def match_my_scholarships(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
):
    """Spec 70 §3 — scholarships this student may qualify for, ranked by award.

    Best-effort: a thin profile still surfaces broadly-eligible awards — an
    unknown student field doesn't eliminate an award, only a verified mismatch
    does (see `financial_fit.scholarship_eligibility`). Deterministic; no LLM.
    """
    from unipaith.services.financial_fit import FinancialFitService

    svc = _svc(db)
    profile = await svc._get_student_profile(user.id)
    records = await svc.list_academic_records(profile.id)
    ctx: dict = {}
    gpas = [float(r.gpa) for r in records if r.gpa is not None]
    if gpas:
        ctx["gpa"] = max(gpas)
    if profile.country_of_residence:
        ctx["country"] = profile.country_of_residence
    if records and records[-1].degree_type:
        ctx["degree_level"] = records[-1].degree_type
    matches = await FinancialFitService(db).find_scholarships(ctx, limit=limit)
    return [
        ScholarshipMatchItem(
            scholarship_id=str(m.scholarship_id),
            name=m.name,
            award_estimate=m.award_estimate,
            reasons=m.reasons,
            scholarship_type=m.scholarship_type,
        )
        for m in matches
    ]


class ProbabilityBandsResponse(BaseModel):
    """Spec 09 §4A — admit / scholarship / waitlist ranges + drivers for one
    program. `probability_bands` is null when there isn't enough signal; `reason`
    tells the UI why so it can show the right "Not enough data yet" copy."""

    program_id: UUID
    probability_bands: dict | None = None
    match_ready: bool = False
    reason: str | None = None


@router.get("/me/matches/{program_id}/probability", response_model=ProbabilityBandsResponse)
async def get_match_probability(
    program_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Spec 09 §4A — probability bands for a program (card expand / detail load).

    Honesty guardrail: returns null bands (with a `reason`) rather than a
    misleading number when the program lacks historical admit signal or the
    student isn't match-ready."""
    from unipaith.ai.probability import estimate_probability_bands, is_match_ready
    from unipaith.config import settings as _cfg
    from unipaith.models.institution import Institution, Program

    profile = await _svc(db)._get_student_profile(user.id)
    match = (
        await db.execute(
            select(MatchResult).where(
                MatchResult.student_id == profile.id,
                MatchResult.program_id == program_id,
            )
        )
    ).scalar_one_or_none()
    if not match:
        raise NotFoundException("No match found for this program. Try refreshing matches.")

    program = await db.scalar(select(Program).where(Program.id == program_id))
    ar = (
        float(program.acceptance_rate)
        if program is not None and program.acceptance_rate is not None
        else None
    )
    # Fall back to the institution's published admit rate (same as the list/detail
    # enrich path) so a program with no own rate still gets honest bands.
    if ar is None and program is not None:
        inst_ranking = await db.scalar(
            select(Institution.ranking_data).where(Institution.id == program.institution_id)
        )
        ar = _institution_acceptance_rate(inst_ranking)
    # Band on the student-direction fit (s2p_value), not the alpha-inflated blend
    # M; gate readiness on c_student (band WIDTH still uses the product below).
    fitness = _band_fitness(match)
    confidence = float(match.confidence_score)
    readiness = _band_readiness(match)
    ready = is_match_ready(readiness if readiness is not None else confidence)

    bands: dict | None = None
    reason: str | None = None
    if not _cfg.ai_probability_bands_enabled:
        reason = "disabled"
    else:
        bands = estimate_probability_bands(
            acceptance_rate=ar, fitness=fitness, confidence=confidence, readiness=readiness
        )
        if bands is None:
            reason = "no_history" if ar is None else "not_match_ready"
    return ProbabilityBandsResponse(
        program_id=program_id, probability_bands=bands, match_ready=ready, reason=reason
    )


@router.post("/me/matches/{program_id}/explain", response_model=ExplainMatchResponse)
async def explain_match(
    program_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Generate (or return cached) rationale for why a program got the
    fitness/confidence scores it did.

    When `settings.ai_match_rationale_v2_enabled=True`, delegates to
    MatchService.get_match_with_rationale (A5 RationaleAgent + per-
    (profile_version, program_version) cache). Falls back to a deterministic
    stub on missing feature vector / parse failure / etc — always returns
    something so the popover never renders empty.
    """
    from unipaith.config import settings as _cfg

    profile = await _svc(db)._get_student_profile(user.id)
    result = await db.execute(
        select(MatchResult).where(
            MatchResult.student_id == profile.id,
            MatchResult.program_id == program_id,
        )
    )
    match = result.scalar_one_or_none()
    if not match:
        raise NotFoundException("No match found for this program.")

    # Plan 2 path — try the LLM rationale agent. On any failure (no feature
    # vector yet, no program features, parse error) fall through to the
    # stub so the caller always gets a usable response.
    if _cfg.ai_match_rationale_v2_enabled:
        try:
            from unipaith.ai.rationale_redaction import project_for_student
            from unipaith.models.institution import Program
            from unipaith.services.match_service import MatchService, build_program_view

            program = await db.scalar(select(Program).where(Program.id == program_id))
            if program is not None:
                program_view = build_program_view(program)
                out = await MatchService(db).get_match_with_rationale(
                    profile.id, program_id, program_view=program_view
                )
                if out is not None and out.rationale_text:
                    # Spec 06 §5.5 — serve the STUDENT (redacted) projection.
                    proj = project_for_student(
                        rationale_text=out.rationale_text,
                        cited_student_fields=out.cited_student_fields,
                        cited_program_fields=out.cited_program_fields,
                        fitness_breakdown=out.match.fitness_breakdown,
                        confidence_breakdown=out.match.confidence_breakdown,
                        grounded=out.grounded,
                    )
                    # MatchService persists rationale into `match_rationales` cache,
                    # not match_results.rationale_text. Mirror it back so consumers
                    # of GET /me/matches/{id} get the inline value too. §14: scrub
                    # the string of any number the LLM may have written, since the
                    # GET endpoint re-serves match_results.rationale_text directly to
                    # the student (proj.rationale_text below is already scrubbed).
                    from unipaith.ai.rationale_redaction import scrub_numbers_from_text

                    match.rationale_text = scrub_numbers_from_text(out.rationale_text)
                    match.rationale_generated_at = func.now()  # type: ignore[assignment]
                    await db.flush()
                    await db.refresh(match)
                    return ExplainMatchResponse(
                        program_id=program_id,
                        rationale_text=out.rationale_text,
                        rationale_generated_at=match.rationale_generated_at,
                        is_stub=False,
                        decision_brief=out.decision_brief,
                        fitness_breakdown=proj.fitness_breakdown,
                        confidence_breakdown=proj.confidence_breakdown,
                        cited_student_fields=proj.cited_student_fields,
                        cited_program_fields=proj.cited_program_fields,
                        redacted=proj.redacted,
                    )
        except Exception as e:  # noqa: BLE001
            import logging

            logging.getLogger(__name__).warning(
                "rationale agent failed for match=%s; falling back to stub: %s",
                program_id,
                e,
            )

    # Stub path: a QUALITATIVE rationale from the breakdown JSON. Breakdowns are
    # redacted to the student-safe view (spec 06 §5.5) before they leave.
    # AI-Structure-3 §14 — the student NEVER sees a number, so the stub uses band
    # words + qualitative driver names only; it formats NO raw fitness/confidence
    # score into the string. The persisted text is also scrubbed of any stray
    # number (defense in depth) so GET /me/matches re-serves a number-free string.
    from unipaith.ai.rationale_redaction import project_for_student as _proj_student
    from unipaith.ai.rationale_redaction import scrub_numbers_from_text

    fitness_drivers = _humanize_fitness_drivers(match.fitness_breakdown or {})
    fit_word = _qualitative_fit_word(float(match.fitness_score))
    conf_word = _qualitative_confidence_word(float(match.confidence_score))
    drivers_phrase = ", ".join(fitness_drivers) if fitness_drivers else "your overall profile"
    rationale = scrub_numbers_from_text(
        f"{fit_word} fit, driven by {drivers_phrase}. "
        f"Our confidence in this read is {conf_word}. "
        "(A fuller written explanation arrives when the rationale agent runs.)"
    )
    match.rationale_text = rationale
    match.rationale_generated_at = func.now()  # type: ignore[assignment]
    await db.flush()
    await db.refresh(match)

    stub_proj = _proj_student(
        rationale_text=rationale,
        cited_student_fields=[],
        cited_program_fields=[],
        fitness_breakdown=match.fitness_breakdown or {},
        confidence_breakdown=match.confidence_breakdown or {},
        grounded=False,
    )
    decision_brief = None
    try:
        from unipaith.models.ai_artifacts import StudentFeatureVector
        from unipaith.models.institution import Program
        from unipaith.services.decision_brief import build_decision_brief
        from unipaith.services.match_service import build_program_view

        program = await db.scalar(select(Program).where(Program.id == program_id))
        sfv = await db.scalar(
            select(StudentFeatureVector).where(StudentFeatureVector.student_id == profile.id)
        )
        if program is not None:
            decision_brief = build_decision_brief(
                student_sparse=dict((sfv.sparse_features if sfv else {}) or {}),
                program=build_program_view(program),
                fitness_breakdown=match.fitness_breakdown or {},
                confidence_breakdown=match.confidence_breakdown or {},
                student_profile_version=int((sfv.profile_version if sfv else 1) or 1),
            )
    except Exception:
        decision_brief = None
    return ExplainMatchResponse(
        program_id=program_id,
        rationale_text=match.rationale_text,
        rationale_generated_at=match.rationale_generated_at,
        is_stub=True,
        decision_brief=decision_brief,
        fitness_breakdown=stub_proj.fitness_breakdown,
        confidence_breakdown=stub_proj.confidence_breakdown,
        cited_student_fields=stub_proj.cited_student_fields,
        cited_program_fields=stub_proj.cited_program_fields,
        redacted=stub_proj.redacted,
    )


# --- Phase B2: LLM rationale (lazy on click) ---


class RationaleResponse(BaseModel):
    program_id: UUID
    rationale_text: str
    decision_brief: dict | None = None
    cited_student_fields: list[str]
    cited_program_fields: list[str]
    cache_hit: bool
    grounded: bool
    # Spec 06 §5.5 — this is the student (redacted) projection. True when any
    # institution-only comparative signal was withheld from this response.
    redacted: bool = True


@router.post("/me/matches/{program_id}/rationale", response_model=RationaleResponse)
async def generate_match_rationale(
    program_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Phase B2 — LLM-generated rationale (cached, lazy).

    Looks up `match_rationales` keyed by
    (student_id, program_id, profile_version, program_version). Cache
    miss → calls A5 Rationale agent and persists. The cache invalidates
    automatically when feature_vector.profile_version bumps (after a
    profile change).

    Returns 404 if no MatchResult or no feature vector exists yet
    (Discovery must complete first).
    """
    from unipaith.ai.rationale_redaction import project_for_student
    from unipaith.models.institution import Program
    from unipaith.services.match_service import MatchService, build_program_view

    profile = await _svc(db)._get_student_profile(user.id)

    program = await db.scalar(select(Program).where(Program.id == program_id))
    if program is None:
        raise NotFoundException(f"Program {program_id} not found.")

    program_view = build_program_view(program)

    out = await MatchService(db).get_match_with_rationale(
        profile.id, program_id, program_view=program_view
    )
    if out is None:
        raise NotFoundException(
            "No match found. Complete Discovery and run /me/matches/refresh first."
        )
    # Spec 06 §5.5 — the student receives the REDACTED projection. Previously
    # this endpoint returned the full citation set (the institution view) to
    # the student, inverting the asymmetry. project_for_student strips program
    # citations that touch sensitive comparative signals.
    proj = project_for_student(
        rationale_text=out.rationale_text,
        cited_student_fields=out.cited_student_fields,
        cited_program_fields=out.cited_program_fields,
        grounded=out.grounded,
    )
    return RationaleResponse(
        program_id=program_id,
        rationale_text=proj.rationale_text,
        decision_brief=out.decision_brief,
        cited_student_fields=proj.cited_student_fields,
        cited_program_fields=proj.cited_program_fields,
        cache_hit=out.cache_hit,
        grounded=out.grounded,
        redacted=proj.redacted,
    )


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
    return StudentAssistantChatResponse(
        reply="The AI advisor is currently being rebuilt. Please check back soon.",
        model="unavailable",
    )


@router.post("/me/recommendations/ai")
async def get_student_recommendations(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Get personalized program recommendations with warm reasoning."""
    return {"status": "unavailable", "recommendations": []}


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
    # Get-or-create student profile (new signups may not have one yet)
    result = await db.execute(select(StudentProfile).where(StudentProfile.user_id == user.id))
    profile = result.scalar_one_or_none()
    if not profile:
        profile = StudentProfile(user_id=user.id)
        db.add(profile)
        await db.flush()

    # Smart rule-based extraction (AI engine is being rebuilt)
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
            after = body.message[msg_lower.index(kw) + len(kw) :]
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
        next_q = f"{greeting}What are you hoping to study, and what draws you to that area?"
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

    updated = False
    for field, value in extracted.items():
        if hasattr(profile, field) and value:
            setattr(profile, field, value)
            updated = True
    if updated:
        await db.flush()

    # Calculate completion percentage from extracted fields so far
    filled = sum(
        1
        for f in [
            "first_name",
            "last_name",
            "nationality",
            "country_of_residence",
            "bio_text",
            "goals_text",
        ]
        if getattr(profile, f, None)
    )
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
        match_ready_pct=(round(match_done / len(match_sections) * 100) if match_sections else 0),
        apply_ready_pct=(round(apply_done / len(apply_sections) * 100) if apply_sections else 0),
    )


@router.get("/me/insights/confidence")
async def get_insights_confidence(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """PersonInsights grouped by confidence with provenance."""
    from unipaith.models.knowledge import PersonInsight

    result = await db.execute(
        select(PersonInsight)
        .where(
            PersonInsight.user_id == user.id,
            PersonInsight.is_active.is_(True),
        )
        .order_by(PersonInsight.confidence.desc())
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


# ---------- Institution Follows (Spec 12 §10 — "Save school" / Connect feed) ----------


class FollowedInstitutionResponse(BaseModel):
    institution_id: UUID
    name: str
    followed_at: datetime | None = None
    # Enriched so the Saved → Schools card (Spec 13 §3.2) renders without
    # an extra fetch per institution.
    country: str | None = None
    city: str | None = None
    logo_url: str | None = None
    type: str | None = None
    program_count: int = 0


@router.get("/me/follows", response_model=list[FollowedInstitutionResponse])
async def list_follows(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Institutions the student explicitly follows — drives the Connect feed
    and the Saved → Schools tab (Spec 13 §3.2). Enriched with location, logo,
    and a published-program count for the school card."""
    from sqlalchemy import func as sa_func

    from unipaith.models.follow import InstitutionFollow
    from unipaith.models.institution import Institution, Program

    profile = await StudentService(db)._get_student_profile(user.id)

    prog_count_sq = (
        select(Program.institution_id, sa_func.count(Program.id).label("pc"))
        .where(Program.is_published.is_(True))
        .group_by(Program.institution_id)
        .subquery()
    )
    result = await db.execute(
        select(
            InstitutionFollow.institution_id,
            Institution.name,
            InstitutionFollow.created_at,
            Institution.country,
            Institution.city,
            Institution.logo_url,
            Institution.type,
            sa_func.coalesce(prog_count_sq.c.pc, 0),
        )
        .join(Institution, Institution.id == InstitutionFollow.institution_id)
        .outerjoin(
            prog_count_sq, prog_count_sq.c.institution_id == InstitutionFollow.institution_id
        )
        .where(InstitutionFollow.student_id == profile.id)
        .order_by(InstitutionFollow.created_at.desc())
    )
    return [
        FollowedInstitutionResponse(
            institution_id=row[0],
            name=row[1],
            followed_at=row[2],
            country=row[3],
            city=row[4],
            logo_url=row[5],
            type=row[6],
            program_count=row[7] or 0,
        )
        for row in result.all()
    ]


# Alias: "Save school" is institution-level; in the saved-list IA it reads as a
# saved institution but is backed by the same follow row (Spec 12 §13 / Spec 13).
@router.get("/me/saved-institutions", response_model=list[FollowedInstitutionResponse])
async def list_saved_institutions(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    return await list_follows(user=user, db=db)


@router.post("/me/follows/{institution_id}", status_code=status.HTTP_201_CREATED)
async def follow_institution(
    institution_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Follow an institution. Idempotent — following twice is a no-op."""
    from sqlalchemy import func as sa_func

    from unipaith.models.follow import InstitutionFollow
    from unipaith.models.institution import Institution
    from unipaith.services.follow_service import FollowService

    profile = await StudentService(db)._get_student_profile(user.id)

    inst = await db.get(Institution, institution_id)
    if inst is None:
        raise NotFoundException("Institution not found")

    # Explicit follow from a school page (Spec 20 §2). Idempotent + upgrades
    # source if a stronger reason already exists.
    await FollowService(db).ensure_follow(profile.id, institution_id, source="explicit")
    await db.commit()

    count = await db.scalar(
        select(sa_func.count())
        .select_from(InstitutionFollow)
        .where(InstitutionFollow.student_id == profile.id)
    )
    return {"institution_id": str(institution_id), "following": True, "followed_count": count or 0}


@router.delete("/me/follows/{institution_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unfollow_institution(
    institution_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Unfollow an institution. Idempotent when not following.

    Always available — saving/following a school is a user-controlled choice and
    stays reversible even while an application is active (Spec 20 §2 pin removed).
    """
    from unipaith.services.follow_service import FollowService

    profile = await StudentService(db)._get_student_profile(user.id)
    await FollowService(db).unfollow(profile.id, institution_id)
    await db.commit()


# ---------- Student Feed (Steam-style: updates from followed schools) ----------


@router.get("/me/feed")
async def get_student_feed(
    limit: int = Query(30, ge=1, le=100),
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Combined feed of events + posts from schools the student follows.

    Sources are unioned: institutions explicitly followed (Spec 12 §10) plus the
    institutions of saved programs (back-compat — saving a program implies
    interest in its school).
    """
    from datetime import UTC, datetime

    from unipaith.models.engagement import SavedList, SavedListItem
    from unipaith.models.follow import InstitutionFollow
    from unipaith.models.institution import (
        Event,
        Institution,
        InstitutionPost,
        Program,
    )

    svc = StudentService(db)
    profile = await svc._get_student_profile(user.id)

    # 1. Institution ids: explicit follows ∪ institutions of saved programs
    saved_result = await db.execute(
        select(Program.institution_id)
        .join(SavedListItem, SavedListItem.program_id == Program.id)
        .join(SavedList, SavedList.id == SavedListItem.list_id)
        .where(SavedList.student_id == profile.id)
        .distinct()
    )
    follow_result = await db.execute(
        select(InstitutionFollow.institution_id).where(InstitutionFollow.student_id == profile.id)
    )
    followed_inst_ids = list(
        {row[0] for row in saved_result.all()} | {row[0] for row in follow_result.all()}
    )

    items: list[dict] = []

    if followed_inst_ids:
        # 2. Events from followed institutions (upcoming)
        ev_result = await db.execute(
            select(Event, Institution.name)
            .join(Institution, Institution.id == Event.institution_id)
            .where(
                Event.institution_id.in_(followed_inst_ids),
                Event.start_time >= datetime.now(UTC),
            )
            .order_by(Event.start_time.asc())
            .limit(limit)
        )
        for ev, inst_name in ev_result.all():
            items.append(
                {
                    "type": "event",
                    "id": str(ev.id),
                    "institution_id": str(ev.institution_id),
                    "institution_name": inst_name,
                    "title": ev.event_name,
                    "description": ev.description,
                    "event_type": ev.event_type,
                    "location": ev.location,
                    "start_time": ev.start_time.isoformat(),
                    "end_time": ev.end_time.isoformat(),
                    "capacity": ev.capacity,
                    "rsvp_count": ev.rsvp_count,
                    "date": ev.start_time.isoformat(),
                }
            )

        # 3. Posts from followed institutions
        post_result = await db.execute(
            select(InstitutionPost, Institution.name)
            .join(Institution, Institution.id == InstitutionPost.institution_id)
            .where(
                InstitutionPost.institution_id.in_(followed_inst_ids),
                InstitutionPost.status == "published",
            )
            .order_by(InstitutionPost.created_at.desc())
            .limit(limit)
        )
        for post, inst_name in post_result.all():
            items.append(
                {
                    "type": "post",
                    "id": str(post.id),
                    "institution_id": str(post.institution_id),
                    "institution_name": inst_name,
                    "title": post.title,
                    "body": post.body,
                    "media_urls": resolve_media_urls(post.media_urls),
                    "date": post.created_at.isoformat(),
                }
            )

    # Sort combined feed by date descending
    items.sort(key=lambda x: x.get("date", ""), reverse=True)

    return {
        "items": items[:limit],
        "followed_count": len(followed_inst_ids),
    }


# --- Package A: Major readiness (per-track self-rating blob) -----------
# Superseded by Spec 43's /students/me/major-specific/* (canonical
# `student_major_specific_signals` store with §5 provenance + 15-track registry
# + §4.18 scoring). These two endpoints are kept as back-compat shims that
# delegate to MajorSpecificService over the same store (track-name remap).


@router.get("/me/major-readiness", response_model=list[MajorReadinessResponse])
async def list_major_readiness(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """List all track-level readiness rows for the logged-in student."""
    from unipaith.services.major_specific_service import MajorSpecificService

    rows = await MajorSpecificService(db).list_legacy(user.id)
    return [MajorReadinessResponse.model_validate(r) for r in rows]


@router.put("/me/major-readiness", response_model=MajorReadinessResponse)
async def upsert_major_readiness(
    body: UpsertMajorReadinessRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Upsert a track-level readiness row. Unique on (student_id, track)."""
    from unipaith.services.major_specific_service import MajorSpecificService

    row = await MajorSpecificService(db).upsert_legacy(user.id, body.track, body.readiness_data)
    await db.commit()
    return MajorReadinessResponse.model_validate(row)


# --- Package A: Platform events (analytics log) -------------------------


@router.post(
    "/me/events",
    response_model=PlatformEventResponse,
    status_code=status.HTTP_201_CREATED,
)
async def log_platform_event(
    body: LogPlatformEventRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Log a broad analytics event (session, search, page view, CTA, etc.).

    Program-scoped engagement signals still go to
    ``/me/engagement`` which writes to ``student_engagement_signals``.
    """
    from unipaith.models.student import StudentPlatformEvent

    profile = await _svc(db)._get_student_profile(user.id)
    row = StudentPlatformEvent(
        student_id=profile.id,
        event_type=body.event_type,
        event_metadata=body.event_metadata,
        session_id=body.session_id,
        device_type=body.device_type,
        url_path=body.url_path,
        referral_source=body.referral_source,
        utm_campaign=body.utm_campaign,
        ip_country=body.ip_country,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return PlatformEventResponse.model_validate(row)

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import settings
from unipaith.core.exceptions import NotFoundException
from unipaith.database import get_db
from unipaith.dependencies import require_student
from unipaith.models.engagement import StudentEngagementSignal
from unipaith.models.matching import MatchResult
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
    CreateAcademicRecordRequest,
    CreateActivityRequest,
    CreateCompetitionRequest,
    CreateLanguageRequest,
    CreateOnlinePresenceRequest,
    CreatePortfolioItemRequest,
    CreateResearchRequest,
    CreateTestScoreRequest,
    CreateWorkExperienceRequest,
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
    UpdateLanguageRequest,
    UpdateOnlinePresenceRequest,
    UpdatePortfolioItemRequest,
    UpdateProfileRequest,
    UpdateResearchRequest,
    UpdateTestScoreRequest,
    UpdateWorkExperienceRequest,
    UpsertAccommodationRequest,
    UpsertPreferencesRequest,
    UpsertSchedulingRequest,
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

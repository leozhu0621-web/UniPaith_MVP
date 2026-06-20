from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from unipaith.core.exceptions import (
    ForbiddenException,
    NotFoundException,
    UnprocessableEntityException,
)
from unipaith.models.application import Application
from unipaith.models.engagement import StudentEngagementSignal
from unipaith.models.goals import StudentGoal
from unipaith.models.matching import MatchResult
from unipaith.models.student import (
    AcademicRecord,
    Activity,
    OnboardingProgress,
    StudentAccommodation,
    StudentCompetition,
    StudentCourse,
    StudentDataConsent,
    StudentLanguage,
    StudentOnlinePresence,
    StudentPortfolioItem,
    StudentPreference,
    StudentProfile,
    StudentResearch,
    StudentScheduling,
    StudentVisaInfo,
    StudentWorkExperience,
    TestScore,
)
from unipaith.schemas.student import (
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
    NextStepResponse,
    OnboardingStatusResponse,
    PatchOnboardingStateRequest,
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
)


class StudentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_profile(self, user_id: UUID) -> StudentProfile:
        result = await self.db.execute(
            select(StudentProfile)
            .where(StudentProfile.user_id == user_id)
            .options(
                selectinload(StudentProfile.academic_records).selectinload(AcademicRecord.courses),
                selectinload(StudentProfile.test_scores),
                selectinload(StudentProfile.activities),
                selectinload(StudentProfile.online_presence),
                selectinload(StudentProfile.portfolio_items),
                selectinload(StudentProfile.research_entries),
                selectinload(StudentProfile.languages),
                selectinload(StudentProfile.work_experiences),
                selectinload(StudentProfile.competitions),
                selectinload(StudentProfile.accommodations),
                selectinload(StudentProfile.scheduling),
                selectinload(StudentProfile.visa_info),
                selectinload(StudentProfile.data_consent),
                selectinload(StudentProfile.preferences),
                selectinload(StudentProfile.onboarding_progress),
            )
        )
        profile = result.scalar_one_or_none()
        if not profile:
            raise NotFoundException("Student profile not found")
        return profile

    async def get_full_snapshot(self, user_id: UUID) -> dict:
        """Consolidated counselor snapshot for the Uni managed agent.

        Composes the existing per-domain loaders into one compact,
        JSON-serializable dict the host hands back from the
        ``get_profile_snapshot`` custom tool. The agent uses this to ground
        the conversation in what UniPaith already knows about the student.
        Imports are local to avoid a service-layer import cycle.
        """
        from unipaith.services.discovery_service import DiscoveryService
        from unipaith.services.goals_service import GoalsService
        from unipaith.services.identity_service import IdentityService
        from unipaith.services.needs_service import NeedsService
        from unipaith.services.strategy_service import StrategyService

        profile = await self.get_profile(user_id)
        goals = await GoalsService(self.db).list_goals(user_id)
        needs = await NeedsService(self.db).list_needs(user_id)
        identity = await IdentityService(self.db).get(user_id)
        strategy = await StrategyService(self.db).get_active(user_id)
        completion = await DiscoveryService(self.db).get_completion_map(user_id)

        return {
            "profile": {
                "first_name": profile.first_name,
                "last_name": profile.last_name,
            },
            "goals": [
                {"category": g.category, "specific": g.specific, "status": g.status} for g in goals
            ],
            "needs": [
                {"maslow_level": n.maslow_level, "signal": n.signal, "severity": n.severity}
                for n in needs
            ],
            "identity": {
                "core_values": identity.core_values,
                "worldview": identity.worldview,
                "self_awareness": identity.self_awareness,
                "summary": identity.identity_summary,
            },
            "active_strategy": (
                {
                    "career_target": strategy.career_target,
                    "target_degree": strategy.target_degree,
                    "narrative": strategy.narrative,
                }
                if strategy
                else None
            ),
            "completion": {k: float(v) for k, v in completion.items()},
        }

    # Gender (a basic demographic) may be changed only once every 3 months.
    GENDER_CHANGE_LOCK = timedelta(days=90)

    async def update_profile(self, user_id: UUID, data: UpdateProfileRequest) -> StudentProfile:
        profile = await self._get_student_profile(user_id)
        update_data = data.model_dump(exclude_unset=True)

        # 3-month gender change-lock. "gender_identity" in update_data means the
        # client explicitly sent the field (model_dump(exclude_unset=True)). A
        # change is allowed on first set (timestamp null) or >= 90 days since the
        # last change; otherwise reject with 422. Unchanged gender — or editing
        # any other field — never blocks and never re-stamps. The server owns the
        # timestamp; the client never sends gender_identity_updated_at.
        gender_changed = (
            "gender_identity" in update_data
            and update_data["gender_identity"] != profile.gender_identity
        )
        if gender_changed:
            last = profile.gender_identity_updated_at
            if last is not None and (datetime.now(UTC) - last) < self.GENDER_CHANGE_LOCK:
                unlock = (last + self.GENDER_CHANGE_LOCK).date().isoformat()
                raise UnprocessableEntityException(
                    "Gender can be changed once every 3 months. "
                    f"You can update it again on {unlock}."
                )

        for key, value in update_data.items():
            setattr(profile, key, value)
        if gender_changed:
            profile.gender_identity_updated_at = datetime.now(UTC)

        await self.db.flush()
        await self._update_onboarding(profile.id)
        # Re-fetch with all relationships eagerly loaded for serialization
        return await self.get_profile(user_id)

    # --- Academic Records ---

    async def list_academic_records(self, student_id: UUID) -> list[AcademicRecord]:
        result = await self.db.execute(
            select(AcademicRecord)
            .where(AcademicRecord.student_id == student_id)
            .options(selectinload(AcademicRecord.courses))
        )
        return list(result.scalars().all())

    async def create_academic_record(
        self, student_id: UUID, data: CreateAcademicRecordRequest
    ) -> AcademicRecord:
        record = AcademicRecord(student_id=student_id, **data.model_dump())
        if record.is_current:
            record.end_date = None
        self.db.add(record)
        await self.db.flush()
        await self.db.refresh(record, attribute_names=["courses"])
        await self._update_onboarding(student_id)
        return record

    async def update_academic_record(
        self, student_id: UUID, record_id: UUID, data: UpdateAcademicRecordRequest
    ) -> AcademicRecord:
        record = await self._get_record(AcademicRecord, record_id)
        await self._verify_ownership(student_id, record.student_id)
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(record, key, value)
        if record.is_current:
            record.end_date = None
        await self.db.flush()
        await self.db.refresh(record, attribute_names=["courses"])
        await self._update_onboarding(student_id)
        return record

    async def delete_academic_record(self, student_id: UUID, record_id: UUID) -> None:
        record = await self._get_record(AcademicRecord, record_id)
        await self._verify_ownership(student_id, record.student_id)
        await self.db.delete(record)
        await self.db.flush()
        await self._update_onboarding(student_id)

    # --- Courses (nested under AcademicRecord) ---

    async def list_courses(
        self,
        student_id: UUID,
        record_id: UUID,
    ) -> list[StudentCourse]:
        record = await self._get_record(AcademicRecord, record_id)
        await self._verify_ownership(student_id, record.student_id)
        result = await self.db.execute(
            select(StudentCourse).where(StudentCourse.academic_record_id == record_id)
        )
        return list(result.scalars().all())

    async def create_course(
        self,
        student_id: UUID,
        record_id: UUID,
        data: CreateCourseRequest,
    ) -> StudentCourse:
        record = await self._get_record(AcademicRecord, record_id)
        await self._verify_ownership(student_id, record.student_id)
        course = StudentCourse(academic_record_id=record_id, **data.model_dump())
        self.db.add(course)
        await self.db.flush()
        return course

    async def update_course(
        self,
        student_id: UUID,
        record_id: UUID,
        course_id: UUID,
        data: UpdateCourseRequest,
    ) -> StudentCourse:
        record = await self._get_record(AcademicRecord, record_id)
        await self._verify_ownership(student_id, record.student_id)
        course = await self._get_record(StudentCourse, course_id)
        if course.academic_record_id != record_id:
            raise ForbiddenException("Course does not belong to this record")
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(course, key, value)
        await self.db.flush()
        return course

    async def delete_course(
        self,
        student_id: UUID,
        record_id: UUID,
        course_id: UUID,
    ) -> None:
        record = await self._get_record(AcademicRecord, record_id)
        await self._verify_ownership(student_id, record.student_id)
        course = await self._get_record(StudentCourse, course_id)
        if course.academic_record_id != record_id:
            raise ForbiddenException("Course does not belong to this record")
        await self.db.delete(course)
        await self.db.flush()

    # --- Test Scores ---

    async def list_test_scores(self, student_id: UUID) -> list[TestScore]:
        result = await self.db.execute(select(TestScore).where(TestScore.student_id == student_id))
        return list(result.scalars().all())

    async def create_test_score(self, student_id: UUID, data: CreateTestScoreRequest) -> TestScore:
        score = TestScore(student_id=student_id, **data.model_dump())
        self.db.add(score)
        await self.db.flush()
        await self._update_onboarding(student_id)
        return score

    async def update_test_score(
        self, student_id: UUID, score_id: UUID, data: UpdateTestScoreRequest
    ) -> TestScore:
        score = await self._get_record(TestScore, score_id)
        await self._verify_ownership(student_id, score.student_id)
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(score, key, value)
        await self.db.flush()
        await self._update_onboarding(student_id)
        return score

    async def delete_test_score(self, student_id: UUID, score_id: UUID) -> None:
        score = await self._get_record(TestScore, score_id)
        await self._verify_ownership(student_id, score.student_id)
        await self.db.delete(score)
        await self.db.flush()
        await self._update_onboarding(student_id)

    # --- Activities ---

    async def list_activities(self, student_id: UUID) -> list[Activity]:
        result = await self.db.execute(select(Activity).where(Activity.student_id == student_id))
        return list(result.scalars().all())

    async def create_activity(self, student_id: UUID, data: CreateActivityRequest) -> Activity:
        activity = Activity(student_id=student_id, **data.model_dump())
        if activity.is_current:
            activity.end_date = None
        self.db.add(activity)
        await self.db.flush()
        await self._update_onboarding(student_id)
        return activity

    async def update_activity(
        self, student_id: UUID, activity_id: UUID, data: UpdateActivityRequest
    ) -> Activity:
        activity = await self._get_record(Activity, activity_id)
        await self._verify_ownership(student_id, activity.student_id)
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(activity, key, value)
        if activity.is_current:
            activity.end_date = None
        await self.db.flush()
        await self._update_onboarding(student_id)
        return activity

    async def delete_activity(self, student_id: UUID, activity_id: UUID) -> None:
        activity = await self._get_record(Activity, activity_id)
        await self._verify_ownership(student_id, activity.student_id)
        await self.db.delete(activity)
        await self.db.flush()
        await self._update_onboarding(student_id)

    # --- Online Presence ---

    async def list_online_presence(
        self,
        student_id: UUID,
    ) -> list[StudentOnlinePresence]:
        result = await self.db.execute(
            select(StudentOnlinePresence).where(
                StudentOnlinePresence.student_id == student_id,
            )
        )
        return list(result.scalars().all())

    async def create_online_presence(
        self,
        student_id: UUID,
        data: CreateOnlinePresenceRequest,
    ) -> StudentOnlinePresence:
        record = StudentOnlinePresence(student_id=student_id, **data.model_dump())
        self.db.add(record)
        await self.db.flush()
        await self._update_onboarding(student_id)
        return record

    async def update_online_presence(
        self,
        student_id: UUID,
        record_id: UUID,
        data: UpdateOnlinePresenceRequest,
    ) -> StudentOnlinePresence:
        record = await self._get_record(StudentOnlinePresence, record_id)
        await self._verify_ownership(student_id, record.student_id)
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(record, key, value)
        await self.db.flush()
        await self._update_onboarding(student_id)
        return record

    async def delete_online_presence(
        self,
        student_id: UUID,
        record_id: UUID,
    ) -> None:
        record = await self._get_record(StudentOnlinePresence, record_id)
        await self._verify_ownership(student_id, record.student_id)
        await self.db.delete(record)
        await self.db.flush()
        await self._update_onboarding(student_id)

    # --- Portfolio Items ---

    async def list_portfolio_items(self, student_id: UUID) -> list[StudentPortfolioItem]:
        result = await self.db.execute(
            select(StudentPortfolioItem)
            .where(StudentPortfolioItem.student_id == student_id)
            .order_by(StudentPortfolioItem.display_order)
        )
        return list(result.scalars().all())

    async def create_portfolio_item(
        self,
        student_id: UUID,
        data: CreatePortfolioItemRequest,
    ) -> StudentPortfolioItem:
        record = StudentPortfolioItem(student_id=student_id, **data.model_dump())
        self.db.add(record)
        await self.db.flush()
        await self._update_onboarding(student_id)
        return record

    async def update_portfolio_item(
        self,
        student_id: UUID,
        record_id: UUID,
        data: UpdatePortfolioItemRequest,
    ) -> StudentPortfolioItem:
        record = await self._get_record(StudentPortfolioItem, record_id)
        await self._verify_ownership(student_id, record.student_id)
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(record, key, value)
        await self.db.flush()
        await self._update_onboarding(student_id)
        return record

    async def delete_portfolio_item(
        self,
        student_id: UUID,
        record_id: UUID,
    ) -> None:
        record = await self._get_record(StudentPortfolioItem, record_id)
        await self._verify_ownership(student_id, record.student_id)
        await self.db.delete(record)
        await self.db.flush()
        await self._update_onboarding(student_id)

    # --- Research ---

    async def list_research(self, student_id: UUID) -> list[StudentResearch]:
        result = await self.db.execute(
            select(StudentResearch).where(StudentResearch.student_id == student_id)
        )
        return list(result.scalars().all())

    async def create_research(
        self,
        student_id: UUID,
        data: CreateResearchRequest,
    ) -> StudentResearch:
        record = StudentResearch(student_id=student_id, **data.model_dump())
        if record.is_current:
            record.end_date = None
        self.db.add(record)
        await self.db.flush()
        await self._update_onboarding(student_id)
        return record

    async def update_research(
        self,
        student_id: UUID,
        record_id: UUID,
        data: UpdateResearchRequest,
    ) -> StudentResearch:
        record = await self._get_record(StudentResearch, record_id)
        await self._verify_ownership(student_id, record.student_id)
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(record, key, value)
        if record.is_current:
            record.end_date = None
        await self.db.flush()
        await self._update_onboarding(student_id)
        return record

    async def delete_research(
        self,
        student_id: UUID,
        record_id: UUID,
    ) -> None:
        record = await self._get_record(StudentResearch, record_id)
        await self._verify_ownership(student_id, record.student_id)
        await self.db.delete(record)
        await self.db.flush()
        await self._update_onboarding(student_id)

    # --- Languages ---

    async def list_languages(self, student_id: UUID) -> list[StudentLanguage]:
        result = await self.db.execute(
            select(StudentLanguage).where(StudentLanguage.student_id == student_id)
        )
        return list(result.scalars().all())

    async def create_language(
        self,
        student_id: UUID,
        data: CreateLanguageRequest,
    ) -> StudentLanguage:
        record = StudentLanguage(student_id=student_id, **data.model_dump())
        self.db.add(record)
        await self.db.flush()
        await self._update_onboarding(student_id)
        return record

    async def update_language(
        self,
        student_id: UUID,
        record_id: UUID,
        data: UpdateLanguageRequest,
    ) -> StudentLanguage:
        record = await self._get_record(StudentLanguage, record_id)
        await self._verify_ownership(student_id, record.student_id)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(record, key, value)
        await self.db.flush()
        await self._update_onboarding(student_id)
        return record

    async def delete_language(
        self,
        student_id: UUID,
        record_id: UUID,
    ) -> None:
        record = await self._get_record(StudentLanguage, record_id)
        await self._verify_ownership(student_id, record.student_id)
        await self.db.delete(record)
        await self.db.flush()
        await self._update_onboarding(student_id)

    # --- Work Experiences ---

    async def list_work_experiences(self, student_id: UUID) -> list[StudentWorkExperience]:
        result = await self.db.execute(
            select(StudentWorkExperience).where(StudentWorkExperience.student_id == student_id)
        )
        return list(result.scalars().all())

    async def create_work_experience(
        self,
        student_id: UUID,
        data: CreateWorkExperienceRequest,
    ) -> StudentWorkExperience:
        record = StudentWorkExperience(student_id=student_id, **data.model_dump())
        if record.is_current:
            record.end_date = None
        self.db.add(record)
        await self.db.flush()
        await self._update_onboarding(student_id)
        return record

    async def update_work_experience(
        self,
        student_id: UUID,
        record_id: UUID,
        data: UpdateWorkExperienceRequest,
    ) -> StudentWorkExperience:
        record = await self._get_record(StudentWorkExperience, record_id)
        await self._verify_ownership(student_id, record.student_id)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(record, key, value)
        if record.is_current:
            record.end_date = None
        await self.db.flush()
        await self._update_onboarding(student_id)
        return record

    async def delete_work_experience(
        self,
        student_id: UUID,
        record_id: UUID,
    ) -> None:
        record = await self._get_record(StudentWorkExperience, record_id)
        await self._verify_ownership(student_id, record.student_id)
        await self.db.delete(record)
        await self.db.flush()
        await self._update_onboarding(student_id)

    # --- Competitions ---

    async def list_competitions(self, student_id: UUID) -> list[StudentCompetition]:
        result = await self.db.execute(
            select(StudentCompetition).where(StudentCompetition.student_id == student_id)
        )
        return list(result.scalars().all())

    async def create_competition(
        self,
        student_id: UUID,
        data: CreateCompetitionRequest,
    ) -> StudentCompetition:
        record = StudentCompetition(student_id=student_id, **data.model_dump())
        self.db.add(record)
        await self.db.flush()
        await self._update_onboarding(student_id)
        return record

    async def update_competition(
        self,
        student_id: UUID,
        record_id: UUID,
        data: UpdateCompetitionRequest,
    ) -> StudentCompetition:
        record = await self._get_record(StudentCompetition, record_id)
        await self._verify_ownership(student_id, record.student_id)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(record, key, value)
        await self.db.flush()
        await self._update_onboarding(student_id)
        return record

    async def delete_competition(
        self,
        student_id: UUID,
        record_id: UUID,
    ) -> None:
        record = await self._get_record(StudentCompetition, record_id)
        await self._verify_ownership(student_id, record.student_id)
        await self.db.delete(record)
        await self.db.flush()
        await self._update_onboarding(student_id)

    # --- Accommodations ---

    async def get_accommodations(
        self,
        student_id: UUID,
    ) -> StudentAccommodation | None:
        result = await self.db.execute(
            select(StudentAccommodation).where(
                StudentAccommodation.student_id == student_id,
            )
        )
        return result.scalar_one_or_none()

    async def upsert_accommodations(
        self,
        student_id: UUID,
        data: UpsertAccommodationRequest,
    ) -> StudentAccommodation:
        result = await self.db.execute(
            select(StudentAccommodation).where(
                StudentAccommodation.student_id == student_id,
            )
        )
        record = result.scalar_one_or_none()
        update_data = data.model_dump(exclude_unset=True)
        if record is None:
            record = StudentAccommodation(student_id=student_id, **update_data)
            self.db.add(record)
        else:
            for key, value in update_data.items():
                setattr(record, key, value)
        await self.db.flush()
        return record

    # --- Scheduling ---

    async def get_scheduling(self, student_id: UUID) -> StudentScheduling | None:
        result = await self.db.execute(
            select(StudentScheduling).where(StudentScheduling.student_id == student_id)
        )
        return result.scalar_one_or_none()

    async def upsert_scheduling(
        self,
        student_id: UUID,
        data: UpsertSchedulingRequest,
    ) -> StudentScheduling:
        result = await self.db.execute(
            select(StudentScheduling).where(StudentScheduling.student_id == student_id)
        )
        record = result.scalar_one_or_none()
        update_data = data.model_dump(exclude_unset=True)
        if record is None:
            record = StudentScheduling(student_id=student_id, **update_data)
            self.db.add(record)
        else:
            for key, value in update_data.items():
                setattr(record, key, value)
        await self.db.flush()
        return record

    # --- Visa Info ---

    async def get_visa_info(self, student_id: UUID) -> StudentVisaInfo | None:
        result = await self.db.execute(
            select(StudentVisaInfo).where(StudentVisaInfo.student_id == student_id)
        )
        return result.scalar_one_or_none()

    async def upsert_visa_info(
        self,
        student_id: UUID,
        data: UpsertVisaInfoRequest,
    ) -> StudentVisaInfo:
        result = await self.db.execute(
            select(StudentVisaInfo).where(StudentVisaInfo.student_id == student_id)
        )
        record = result.scalar_one_or_none()
        update_data = data.model_dump(exclude_unset=True)
        if record is None:
            record = StudentVisaInfo(student_id=student_id, **update_data)
            self.db.add(record)
        else:
            for key, value in update_data.items():
                setattr(record, key, value)
        await self.db.flush()
        return record

    # --- Preferences ---

    async def get_preferences(self, student_id: UUID) -> StudentPreference | None:
        result = await self.db.execute(
            select(StudentPreference).where(StudentPreference.student_id == student_id)
        )
        return result.scalar_one_or_none()

    async def upsert_preferences(
        self, student_id: UUID, data: UpsertPreferencesRequest
    ) -> StudentPreference:
        result = await self.db.execute(
            select(StudentPreference).where(StudentPreference.student_id == student_id)
        )
        pref = result.scalar_one_or_none()
        update_data = data.model_dump(exclude_unset=True)

        if pref is None:
            pref = StudentPreference(student_id=student_id, **update_data)
            self.db.add(pref)
        else:
            for key, value in update_data.items():
                setattr(pref, key, value)

        await self.db.flush()
        await self._update_onboarding(student_id)
        return pref

    # --- Onboarding ---

    async def get_onboarding_status(self, student_id: UUID) -> OnboardingStatusResponse:
        profile = await self.db.execute(
            select(StudentProfile)
            .where(StudentProfile.id == student_id)
            .options(
                selectinload(StudentProfile.academic_records).selectinload(AcademicRecord.courses),
                selectinload(StudentProfile.test_scores),
                selectinload(StudentProfile.activities),
                selectinload(StudentProfile.online_presence),
                selectinload(StudentProfile.portfolio_items),
                selectinload(StudentProfile.research_entries),
                selectinload(StudentProfile.languages),
                selectinload(StudentProfile.work_experiences),
                selectinload(StudentProfile.competitions),
                selectinload(StudentProfile.preferences),
            )
        )
        p = profile.scalar_one_or_none()
        if not p:
            raise NotFoundException("Student profile not found")

        steps: list[str] = []
        pct = 0

        # account created: 10%
        steps.append("account")
        pct += 10

        # basic profile (name, nationality): 15%
        if p.first_name and p.last_name and p.nationality:
            steps.append("basic_profile")
            pct += 15

        # at least 1 academic record: 15%
        if p.academic_records:
            steps.append("academics")
            pct += 15

        # at least 1 test score: 10%
        if p.test_scores:
            steps.append("test_scores")
            pct += 10

        # at least 1 activity: 5%
        if p.activities:
            steps.append("activities")
            pct += 5

        # at least 1 online presence link: 5%
        if p.online_presence:
            steps.append("online_presence")
            pct += 5

        # at least 1 portfolio item: 5%
        if p.portfolio_items:
            steps.append("portfolio")
            pct += 5

        # at least 1 research entry: 5%
        if p.research_entries:
            steps.append("research")
            pct += 5

        # at least 1 language: 5%
        if p.languages:
            steps.append("languages")
            pct += 5

        # at least 1 work experience: 5%
        if p.work_experiences:
            steps.append("work_experience")
            pct += 5

        # at least 1 competition: 5%
        if p.competitions:
            steps.append("competitions")
            pct += 5

        # goals_text: 5%
        if p.goals_text:
            steps.append("goals")
            pct += 5

        # preferences set: 10%
        if p.preferences:
            steps.append("preferences")
            pct += 10

        next_step = self._compute_next_step(steps, p)
        return OnboardingStatusResponse(
            completion_percentage=pct,
            steps_completed=steps,
            next_step=next_step,
        )

    # Ship C — Imprint-style wizard state (student_profiles.onboarding_state).

    # Budget bands from the wizard → rough USD/yr ranges matching can read.
    # "need_aid" intentionally has no numeric mapping (it expresses an aid
    # requirement, not a budget) and stays in onboarding_state only.
    _BUDGET_BAND_RANGES: dict[str, tuple[int | None, int | None]] = {
        "lt_20k": (None, 20_000),
        "20k_40k": (20_000, 40_000),
        "40k_60k": (40_000, 60_000),
        "60k_plus": (60_000, None),
    }
    _DEGREE_LABELS: dict[str, str] = {
        "bachelors": "bachelor's",
        "masters": "master's",
        "mba": "MBA",
        "phd": "PhD",
    }

    async def patch_onboarding_state(
        self, user_id: UUID, data: PatchOnboardingStateRequest
    ) -> dict:
        """Key-wise merge into ``student_profiles.onboarding_state``.

        ``completed``/``dismissed`` stamp their timestamps exactly once —
        replays never overwrite an existing stamp. On first completion the
        answers fan into existing structures where the mapping is trivially
        safe (see ``_fan_in_onboarding_answers``); ``onboarding_state``
        itself stays the source of truth.
        """
        profile = await self._get_student_profile(user_id)
        state: dict = dict(profile.onboarding_state or {})
        answers: dict = dict(state.get("answers") or {})
        if data.answers is not None:
            for key, value in data.answers.model_dump(exclude_unset=True).items():
                if value is None:
                    answers.pop(key, None)
                else:
                    answers[key] = value
        state["answers"] = answers
        if data.last_step is not None:
            state["last_step"] = data.last_step
        now_iso = datetime.now(UTC).isoformat()
        if data.completed and not state.get("completed_at"):
            state["completed_at"] = now_iso
            await self._fan_in_onboarding_answers(profile.id, answers)
        if data.dismissed and not state.get("dismissed_at"):
            state["dismissed_at"] = now_iso
        profile.onboarding_state = state
        await self.db.flush()
        return state

    async def _fan_in_onboarding_answers(self, student_id: UUID, answers: dict) -> None:
        """Map completed-wizard answers into existing structures.

        Conservative by design — fill-only-if-empty, single-table writes:

        - degree_level / intake_term / geos / budget_band → StudentPreference
          (``target_degree_level`` / ``target_start_term`` /
          ``preferred_regions`` / ``budget_min``+``budget_max``); never
          overwrites a value the student already set.
        - degree_level and/or intake_term → one ``student_goals`` row
          (source='manual'), only on the first completion stamp.

        ``interests`` and ``stage`` stay in onboarding_state only — there is
        no trivially safe target structure (academic records describe schools
        attended, not aspirations).
        """
        degree = answers.get("degree_level")
        term = answers.get("intake_term")
        geos = answers.get("geos") or []
        band = answers.get("budget_band")
        if not (degree or term or geos or band):
            return

        pref = await self.get_preferences(student_id)
        if pref is None:
            pref = StudentPreference(student_id=student_id)
            self.db.add(pref)
        if degree and not pref.target_degree_level:
            pref.target_degree_level = degree
        if term and not pref.target_start_term:
            pref.target_start_term = term
        if geos and not pref.preferred_regions:
            pref.preferred_regions = list(geos)
        if band in self._BUDGET_BAND_RANGES and pref.budget_min is None and pref.budget_max is None:
            pref.budget_min, pref.budget_max = self._BUDGET_BAND_RANGES[band]

        if degree or term:
            label = self._DEGREE_LABELS.get(degree, degree) if degree else "degree"
            specific = f"Start a {label} program"
            if term:
                specific += f" in {term}"
            self.db.add(
                StudentGoal(
                    student_id=student_id,
                    category="academic",
                    specific=specific,
                    source="manual",
                )
            )

        await self.db.flush()
        await self._update_onboarding(student_id)

    def _compute_next_step(
        self, steps: list[str], profile: StudentProfile
    ) -> NextStepResponse | None:
        if "basic_profile" not in steps:
            return NextStepResponse(
                section="basic_profile",
                fields=["first_name", "last_name", "nationality", "country_of_residence"],
                guidance_text="Let's start with your basic information.",
            )
        if "academics" not in steps:
            return NextStepResponse(
                section="academics",
                fields=["institution_name", "degree_type", "field_of_study", "gpa"],
                guidance_text="Add your educational background.",
            )
        if "test_scores" not in steps:
            return NextStepResponse(
                section="test_scores",
                fields=["test_type", "total_score"],
                guidance_text="Add any standardized test scores you have.",
            )
        if "activities" not in steps:
            has_phd = any(r.degree_type == "phd" for r in profile.academic_records)
            if has_phd:
                return NextStepResponse(
                    section="activities",
                    fields=["activity_type", "title", "description"],
                    guidance_text="Share your research experience and publications.",
                )
            return NextStepResponse(
                section="activities",
                fields=["activity_type", "title", "description"],
                guidance_text="Tell us about your activities and experiences.",
            )
        if "online_presence" not in steps:
            return NextStepResponse(
                section="online_presence",
                fields=["platform_type", "url"],
                guidance_text="Add your LinkedIn or portfolio links.",
            )
        if "portfolio" not in steps:
            return NextStepResponse(
                section="portfolio",
                fields=["title", "item_type", "url"],
                guidance_text="Showcase a project or work sample.",
            )
        if "research" not in steps:
            return NextStepResponse(
                section="research",
                fields=["title", "role", "institution_lab"],
                guidance_text="Add any research experience you have.",
            )
        if "languages" not in steps:
            return NextStepResponse(
                section="languages",
                fields=["language", "proficiency_level"],
                guidance_text="Add the languages you speak.",
            )
        if "work_experience" not in steps:
            return NextStepResponse(
                section="work_experience",
                fields=["experience_type", "organization", "role_title"],
                guidance_text="Add work, internship, or volunteer experience.",
            )
        if "competitions" not in steps:
            return NextStepResponse(
                section="competitions",
                fields=["competition_name", "level", "result_placement"],
                guidance_text="Add any competitions or hackathons you've done.",
            )
        if "goals" not in steps:
            return NextStepResponse(
                section="goals",
                fields=["goals_text"],
                guidance_text="Describe your academic and career goals.",
            )
        if "preferences" not in steps:
            return NextStepResponse(
                section="preferences",
                fields=["preferred_countries", "budget_max", "funding_requirement"],
                guidance_text="Set your program preferences to improve match quality.",
            )
        return None

    # --- Timeline ---

    async def get_timeline(self, student_id: UUID) -> list[dict]:
        """Compute a chronological list of profile milestones."""
        profile = await self.db.execute(
            select(StudentProfile)
            .where(StudentProfile.id == student_id)
            .options(
                selectinload(StudentProfile.academic_records),
                selectinload(StudentProfile.test_scores),
                selectinload(StudentProfile.activities),
                selectinload(StudentProfile.online_presence),
                selectinload(StudentProfile.portfolio_items),
                selectinload(StudentProfile.research_entries),
                selectinload(StudentProfile.languages),
                selectinload(StudentProfile.work_experiences),
                selectinload(StudentProfile.competitions),
            )
        )
        p = profile.scalar_one_or_none()
        if not p:
            raise NotFoundException("Student profile not found")

        milestones: list[dict] = []

        # Profile created
        milestones.append(
            {
                "date": p.created_at.isoformat(),
                "event_type": "profile_created",
                "label": "Profile created",
                "detail": "You started your UniPaith journey.",
            }
        )

        # Section completions (use created_at of first item)
        section_map = [
            (p.academic_records, "academics", "Added first academic record"),
            (p.test_scores, "test_score", "Added first test score"),
            (p.activities, "activity", "Added first activity"),
            (p.online_presence, "online_presence", "Added first link"),
            (p.portfolio_items, "portfolio", "Added first portfolio item"),
            (p.research_entries, "research", "Added first research entry"),
            (p.languages, "language", "Added first language"),
            (p.work_experiences, "work_experience", "Added first work experience"),
            (p.competitions, "competition", "Added first competition"),
        ]
        for items, evt_type, label in section_map:
            if items:
                earliest = min(items, key=lambda x: x.created_at)
                milestones.append(
                    {
                        "date": earliest.created_at.isoformat(),
                        "event_type": evt_type,
                        "label": label,
                        "detail": None,
                    }
                )

        # Application events
        apps_result = await self.db.execute(
            select(Application).where(Application.student_id == student_id)
        )
        for app in apps_result.scalars().all():
            milestones.append(
                {
                    "date": app.created_at.isoformat(),
                    "event_type": "application_created",
                    "label": "Started application",
                    "detail": None,
                }
            )
            if app.submitted_at:
                milestones.append(
                    {
                        "date": app.submitted_at.isoformat(),
                        "event_type": "application_submitted",
                        "label": "Submitted application",
                        "detail": None,
                    }
                )
            if app.decision_at:
                milestones.append(
                    {
                        "date": app.decision_at.isoformat(),
                        "event_type": "decision_received",
                        "label": f"Decision: {app.decision or 'pending'}",
                        "detail": None,
                    }
                )

        milestones.sort(key=lambda m: m["date"])
        return milestones

    # --- Analytics ---

    async def get_analytics(self, student_id: UUID) -> dict:
        """Compute profile-level activity metrics."""
        from sqlalchemy import func as sqla_func

        profile = await self.db.execute(
            select(StudentProfile)
            .where(StudentProfile.id == student_id)
            .options(
                selectinload(StudentProfile.academic_records),
                selectinload(StudentProfile.test_scores),
                selectinload(StudentProfile.activities),
                selectinload(StudentProfile.online_presence),
                selectinload(StudentProfile.portfolio_items),
                selectinload(StudentProfile.research_entries),
                selectinload(StudentProfile.languages),
                selectinload(StudentProfile.work_experiences),
                selectinload(StudentProfile.competitions),
            )
        )
        p = profile.scalar_one_or_none()
        if not p:
            raise NotFoundException("Student profile not found")

        # Profile section counts
        sections = {
            "academics": len(p.academic_records),
            "test_scores": len(p.test_scores),
            "activities": len(p.activities),
            "online_presence": len(p.online_presence),
            "portfolio": len(p.portfolio_items),
            "research": len(p.research_entries),
            "languages": len(p.languages),
            "work_experiences": len(p.work_experiences),
            "competitions": len(p.competitions),
        }
        sections_completed = sum(1 for v in sections.values() if v > 0)
        total_items = sum(sections.values())

        # Match summary
        matches_result = await self.db.execute(
            select(MatchResult).where(MatchResult.student_id == student_id)
        )
        matches = list(matches_result.scalars().all())
        match_count = len(matches)
        avg_score = (
            round(sum(m.match_score for m in matches if m.match_score is not None) / match_count, 1)
            if match_count > 0
            else None
        )
        top_tier = min((m.match_tier for m in matches), default=None)

        # Application stats
        apps_result = await self.db.execute(
            select(Application).where(Application.student_id == student_id)
        )
        apps = list(apps_result.scalars().all())
        app_by_status: dict[str, int] = {}
        decisions: dict[str, int] = {}
        for a in apps:
            app_by_status[a.status] = app_by_status.get(a.status, 0) + 1
            if a.decision:
                decisions[a.decision] = decisions.get(a.decision, 0) + 1

        # Engagement count
        eng_result = await self.db.execute(
            select(sqla_func.count())
            .select_from(StudentEngagementSignal)
            .where(StudentEngagementSignal.student_id == student_id)
        )
        engagement_count = eng_result.scalar_one()

        return {
            "profile": {
                "sections_completed": sections_completed,
                "total_sections": len(sections),
                "total_items": total_items,
                "section_counts": sections,
            },
            "matches": {
                "count": match_count,
                "average_score": avg_score,
                "top_tier": top_tier,
            },
            "applications": {
                "total": len(apps),
                "by_status": app_by_status,
                "decisions": decisions,
            },
            "engagement": {
                "total_signals": engagement_count,
            },
        }

    # --- Data Rights ---

    async def get_data_consent(self, student_id: UUID) -> StudentDataConsent | None:
        result = await self.db.execute(
            select(StudentDataConsent).where(StudentDataConsent.student_id == student_id)
        )
        return result.scalar_one_or_none()

    async def upsert_data_consent(
        self,
        student_id: UUID,
        data: UpsertDataConsentRequest,
        actor_user_id: UUID | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> StudentDataConsent:
        from datetime import datetime as dt

        result = await self.db.execute(
            select(StudentDataConsent).where(StudentDataConsent.student_id == student_id)
        )
        record = result.scalar_one_or_none()
        update_data = data.model_dump(exclude_unset=True)

        # Spec 03 §12 — when consent_matching flips, cached rationales
        # are stale derivative data the student no longer consents to
        # keep. Compare BEFORE applying the patch so we only invalidate
        # on a real change.
        prior_matching = bool(record.consent_matching) if record is not None else True
        prior_peer = bool(record.consent_peer_connect) if record is not None else False

        # Spec 36 §2 — snapshot consent levers before the patch so we can audit
        # exactly which toggles flipped (consent_change / data_deletion).
        audit_levers = (
            "consent_matching",
            "consent_outreach",
            "consent_research",
            "consent_training",
            "consent_peer_connect",
        )
        _audit_priors = {
            k: (getattr(record, k) if record is not None else None) for k in audit_levers
        }
        _audit_priors["deletion_requested"] = (
            bool(record.deletion_requested) if record is not None else False
        )

        if record is None:
            record = StudentDataConsent(student_id=student_id, **update_data)
            self.db.add(record)
        else:
            for key, value in update_data.items():
                setattr(record, key, value)

        # Track when deletion was requested
        if record.deletion_requested and record.deletion_requested_at is None:
            record.deletion_requested_at = dt.now(UTC)
        elif not record.deletion_requested:
            record.deletion_requested_at = None

        await self.db.flush()

        # Spec 36 §2 — audit each consent toggle that flipped + deletion
        # request/cancel from the Data tab. Student-scoped (no institution).
        from unipaith.services.audit_service import AuditService

        _audit = AuditService(self.db)
        for k in audit_levers:
            if k in update_data and bool(getattr(record, k)) != bool(_audit_priors[k]):
                await _audit.log(
                    institution_id=None,
                    actor_user_id=actor_user_id,
                    actor_role="student",
                    action="consent_change",
                    category="consent_change",
                    entity_type="consent",
                    entity_id=k,
                    old_value={k: _audit_priors[k]},
                    new_value={k: bool(getattr(record, k))},
                    ip_address=ip_address,
                    user_agent=user_agent,
                )
        if "deletion_requested" in update_data and bool(record.deletion_requested) != bool(
            _audit_priors["deletion_requested"]
        ):
            _requested = bool(record.deletion_requested)
            await _audit.log(
                institution_id=None,
                actor_user_id=actor_user_id,
                actor_role="student",
                action="account_deletion_requested" if _requested else "account_deletion_cancelled",
                category="data_deletion",
                entity_type="consent",
                entity_id="account",
                new_value={"deletion_requested": _requested},
                ip_address=ip_address,
                user_agent=user_agent,
            )

        # After flush, invalidate downstream caches when consent.matching
        # changed in either direction. Opt-out drops them so the student
        # never sees a rationale they didn't consent to; opt-back-in
        # drops them so the next read regenerates under the new mask
        # (recording the new consent_mask on the audit ledger row).
        if bool(record.consent_matching) != prior_matching:
            from unipaith.ai.cache_invalidation import invalidate_for_consent_change

            await invalidate_for_consent_change(self.db, student_id)

        # Spec 20 §6.1 — opt-in via Data tab seeds the peer visibility profile.
        if bool(record.consent_peer_connect) and not prior_peer:
            from unipaith.services.peer_service import PeerService

            await PeerService(self.db).get_my_profile(student_id)

        # Load server-side defaults (created_at/updated_at) within the async
        # context so response serialization never triggers a sync lazy-load
        # (MissingGreenlet) on a fresh insert.
        await self.db.refresh(record)
        return record

    # --- Access Log (spec 08 §16 / 46 §8) ---

    async def get_access_log(self, student_id: UUID, limit: int = 50) -> list[dict]:
        """Return a human-readable log of who/what accessed the student's data.

        Sourced from the AI audit ledger (`ai_turns`): every agent run on the
        student's data writes one row with provider, model, and the consent
        mask active at request time. We map each agent to a plain-language
        actor + action + the data category it touched, plus any recorded
        consent-change events. Newest first.
        """
        from unipaith.models.ai_artifacts import AiTurn

        # agent -> (actor, action, fields touched)
        agent_map: dict[str, tuple[str, str, str]] = {
            "orchestrator": (
                "Discovery assistant",
                "Guided your discovery conversation",
                "Chat messages",
            ),
            "extractor": (
                "Signal extractor",
                "Extracted profile signals from your messages",
                "Discovery messages",
            ),
            "validator": (
                "Signal validator",
                "Checked extracted signals for accuracy",
                "Extracted signals",
            ),
            "feature_emitter": ("Match engine", "Built your match profile", "Profile"),
            "rationale": (
                "Match engine",
                "Explained why a program matched you",
                "Profile, program",
            ),
            "workshop_coach": ("Workshop coach", "Gave feedback on your draft", "Your draft"),
            "workshop_judge": (
                "Workshop coach",
                "Scored your practice response",
                "Your draft",
            ),
            "embedding": ("Match engine", "Indexed your profile for matching", "Profile"),
            "review_summarizer": (
                "Institution reviewer",
                "Summarized your application packet",
                "Application",
            ),
            "authenticity_risk": ("Integrity check", "Scanned a submitted essay", "Essay"),
            "matcher": ("Match engine", "Scored your program matches", "Profile"),
        }

        result = await self.db.execute(
            select(AiTurn)
            .where(AiTurn.student_id == student_id)
            .order_by(AiTurn.created_at.desc())
            .limit(limit)
        )
        entries: list[dict] = []
        for turn in result.scalars().all():
            actor, action, fields = agent_map.get(
                turn.agent, ("AI service", "Processed your data", "Profile")
            )
            entries.append(
                {
                    "timestamp": turn.created_at.isoformat(),
                    "actor": actor,
                    "action": action,
                    "fields": fields,
                    "provider": turn.provider,
                    "model": turn.model,
                }
            )

        # Prepend consent-change events when present.
        consent = await self.get_data_consent(student_id)
        if consent and consent.consent_revocation_timestamps:
            for evt in consent.consent_revocation_timestamps:
                if isinstance(evt, dict) and evt.get("timestamp"):
                    entries.append(
                        {
                            "timestamp": evt["timestamp"],
                            "actor": "You",
                            "action": f"Changed consent: {evt.get('lever', 'preferences')}",
                            "fields": "Consent settings",
                            "provider": None,
                            "model": None,
                        }
                    )

        # Spec 36 §5 — institution-side access to your data. Surface audit
        # events on your applications so you can see who at an institution
        # touched your record and when ("who saw your data").
        from unipaith.models.audit import AdmissionsAuditLog
        from unipaith.models.institution import Institution

        app_ids = (
            (
                await self.db.execute(
                    select(Application.id).where(Application.student_id == student_id)
                )
            )
            .scalars()
            .all()
        )
        if app_ids:
            audit_map = {
                "decision_release": ("Released an admissions decision", "Application"),
                "reviewer_assigned": ("Assigned a reviewer to your application", "Application"),
                "status_change": ("Updated your application status", "Application"),
                "document_replaced": ("Updated a document on your application", "Documents"),
                "ai_generated": ("Reviewed an AI artifact on your application", "Application"),
            }
            audit_rows = (
                (
                    await self.db.execute(
                        select(AdmissionsAuditLog)
                        .where(
                            AdmissionsAuditLog.application_id.in_(app_ids),
                            AdmissionsAuditLog.category.in_(list(audit_map.keys())),
                        )
                        .order_by(AdmissionsAuditLog.created_at.desc())
                        .limit(limit)
                    )
                )
                .scalars()
                .all()
            )
            inst_ids = {r.institution_id for r in audit_rows if r.institution_id}
            inst_names: dict = {}
            if inst_ids:
                name_rows = (
                    await self.db.execute(
                        select(Institution.id, Institution.name).where(Institution.id.in_(inst_ids))
                    )
                ).all()
                inst_names = {iid: nm for iid, nm in name_rows}
            for r in audit_rows:
                action_label, fields = audit_map.get(
                    r.category, ("Accessed your application", "Application")
                )
                entries.append(
                    {
                        "timestamp": r.created_at.isoformat(),
                        "actor": inst_names.get(r.institution_id, "Admissions office"),
                        "action": action_label,
                        "fields": fields,
                        "provider": None,
                        "model": None,
                    }
                )

        entries.sort(key=lambda e: e["timestamp"], reverse=True)
        return entries[:limit]

    # --- Peer Comparison ---

    async def get_peer_comparison(self, student_id: UUID) -> dict:
        """Compute anonymized percentile bands vs all students."""
        from sqlalchemy import func as sqla_func

        profile = await self.db.execute(
            select(StudentProfile)
            .where(StudentProfile.id == student_id)
            .options(
                selectinload(StudentProfile.academic_records),
                selectinload(StudentProfile.test_scores),
                selectinload(StudentProfile.activities),
                selectinload(StudentProfile.research_entries),
                selectinload(StudentProfile.work_experiences),
                selectinload(StudentProfile.competitions),
            )
        )
        p = profile.scalar_one_or_none()
        if not p:
            raise NotFoundException("Student profile not found")

        def percentile_label(pct: float) -> str:
            if pct >= 90:
                return "Top 10%"
            if pct >= 75:
                return "Top 25%"
            if pct >= 50:
                return "Above average"
            if pct >= 25:
                return "Average"
            return "Below average"

        metrics: list[dict] = []

        # GPA percentile (highest GPA per student, 4.0 scale)
        my_gpa = max(
            (float(r.gpa) for r in p.academic_records if r.gpa is not None),
            default=None,
        )
        if my_gpa is not None:
            total = (
                await self.db.execute(
                    select(sqla_func.count(sqla_func.distinct(AcademicRecord.student_id))).where(
                        AcademicRecord.gpa.is_not(None)
                    )
                )
            ).scalar_one()
            below = (
                await self.db.execute(
                    select(sqla_func.count(sqla_func.distinct(AcademicRecord.student_id)))
                    .where(AcademicRecord.gpa < my_gpa)
                    .where(AcademicRecord.gpa.is_not(None))
                )
            ).scalar_one()
            pct = round(below / total * 100) if total > 0 else 50
            metrics.append(
                {
                    "metric": "GPA",
                    "value": my_gpa,
                    "percentile": pct,
                    "label": percentile_label(pct),
                }
            )

        # Test score percentile (highest total_score)
        my_score = max(
            (s.total_score for s in p.test_scores if s.total_score is not None),
            default=None,
        )
        if my_score is not None:
            total = (
                await self.db.execute(
                    select(sqla_func.count(sqla_func.distinct(TestScore.student_id))).where(
                        TestScore.total_score.is_not(None)
                    )
                )
            ).scalar_one()
            below = (
                await self.db.execute(
                    select(sqla_func.count(sqla_func.distinct(TestScore.student_id)))
                    .where(TestScore.total_score < my_score)
                    .where(TestScore.total_score.is_not(None))
                )
            ).scalar_one()
            pct = round(below / total * 100) if total > 0 else 50
            metrics.append(
                {
                    "metric": "Test Score",
                    "value": my_score,
                    "percentile": pct,
                    "label": percentile_label(pct),
                }
            )

        # Activity count percentile
        my_count = (
            len(p.activities)
            + len(p.research_entries)
            + len(p.work_experiences)
            + len(p.competitions)
        )
        if my_count > 0:
            # Count activities per student across all tables
            total = (
                await self.db.execute(select(sqla_func.count()).select_from(StudentProfile))
            ).scalar_one()
            # Simplified: compare against average
            avg_result = await self.db.execute(
                select(
                    sqla_func.avg(
                        sqla_func.coalesce(
                            select(sqla_func.count())
                            .where(Activity.student_id == StudentProfile.id)
                            .correlate(StudentProfile)
                            .scalar_subquery(),
                            0,
                        )
                    )
                ).select_from(StudentProfile)
            )
            avg_count = float(avg_result.scalar_one() or 1)
            pct = min(99, round(my_count / max(avg_count * 2, 1) * 100))
            metrics.append(
                {
                    "metric": "Activities",
                    "value": my_count,
                    "percentile": pct,
                    "label": percentile_label(pct),
                }
            )

        return {"metrics": metrics}

    # --- Helpers ---

    async def _get_student_profile(self, user_id: UUID) -> StudentProfile:
        result = await self.db.execute(
            select(StudentProfile).where(StudentProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        if not profile:
            raise NotFoundException("Student profile not found")
        return profile

    async def _get_record(self, model: type, record_id: UUID):  # noqa: ANN201
        result = await self.db.execute(select(model).where(model.id == record_id))
        record = result.scalar_one_or_none()
        if not record:
            raise NotFoundException(f"{model.__name__} not found")
        return record

    async def _verify_ownership(self, student_id: UUID, record_owner_id: UUID) -> None:
        if student_id != record_owner_id:
            raise ForbiddenException("You do not own this resource")

    async def _update_onboarding(self, student_id: UUID) -> None:
        status = await self.get_onboarding_status(student_id)
        result = await self.db.execute(
            select(OnboardingProgress).where(OnboardingProgress.student_id == student_id)
        )
        progress = result.scalar_one_or_none()
        if progress is None:
            progress = OnboardingProgress(student_id=student_id)
            self.db.add(progress)

        progress.steps_completed = status.steps_completed
        progress.completion_percentage = status.completion_percentage
        await self.db.flush()
        # AI feature extraction skipped (engine being rebuilt)

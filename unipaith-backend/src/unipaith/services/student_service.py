from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from unipaith.ai.jobs import on_student_profile_updated
from unipaith.core.exceptions import ForbiddenException, NotFoundException
from unipaith.models.student import (
    AcademicRecord,
    Activity,
    OnboardingProgress,
    StudentAccommodation,
    StudentCompetition,
    StudentLanguage,
    StudentOnlinePresence,
    StudentPortfolioItem,
    StudentPreference,
    StudentProfile,
    StudentResearch,
    StudentScheduling,
    StudentWorkExperience,
    TestScore,
)
from unipaith.schemas.student import (
    CreateAcademicRecordRequest,
    CreateActivityRequest,
    CreateCompetitionRequest,
    CreateLanguageRequest,
    CreateOnlinePresenceRequest,
    CreatePortfolioItemRequest,
    CreateResearchRequest,
    CreateTestScoreRequest,
    CreateWorkExperienceRequest,
    NextStepResponse,
    OnboardingStatusResponse,
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
)


class StudentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_profile(self, user_id: UUID) -> StudentProfile:
        result = await self.db.execute(
            select(StudentProfile)
            .where(StudentProfile.user_id == user_id)
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
                selectinload(StudentProfile.accommodations),
                selectinload(StudentProfile.scheduling),
                selectinload(StudentProfile.preferences),
                selectinload(StudentProfile.onboarding_progress),
            )
        )
        profile = result.scalar_one_or_none()
        if not profile:
            raise NotFoundException("Student profile not found")
        return profile

    async def update_profile(self, user_id: UUID, data: UpdateProfileRequest) -> StudentProfile:
        profile = await self._get_student_profile(user_id)
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(profile, key, value)
        await self.db.flush()
        await self._update_onboarding(profile.id)
        return await self.get_profile(user_id)

    # --- Academic Records ---

    async def list_academic_records(self, student_id: UUID) -> list[AcademicRecord]:
        result = await self.db.execute(
            select(AcademicRecord).where(AcademicRecord.student_id == student_id)
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
        await self._update_onboarding(student_id)
        return record

    async def delete_academic_record(self, student_id: UUID, record_id: UUID) -> None:
        record = await self._get_record(AcademicRecord, record_id)
        await self._verify_ownership(student_id, record.student_id)
        await self.db.delete(record)
        await self.db.flush()
        await self._update_onboarding(student_id)

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
        self, student_id: UUID,
    ) -> list[StudentOnlinePresence]:
        result = await self.db.execute(
            select(StudentOnlinePresence).where(
                StudentOnlinePresence.student_id == student_id,
            )
        )
        return list(result.scalars().all())

    async def create_online_presence(
        self, student_id: UUID, data: CreateOnlinePresenceRequest,
    ) -> StudentOnlinePresence:
        record = StudentOnlinePresence(student_id=student_id, **data.model_dump())
        self.db.add(record)
        await self.db.flush()
        await self._update_onboarding(student_id)
        return record

    async def update_online_presence(
        self, student_id: UUID, record_id: UUID, data: UpdateOnlinePresenceRequest,
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
        self, student_id: UUID, record_id: UUID,
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
        self, student_id: UUID, data: CreatePortfolioItemRequest,
    ) -> StudentPortfolioItem:
        record = StudentPortfolioItem(student_id=student_id, **data.model_dump())
        self.db.add(record)
        await self.db.flush()
        await self._update_onboarding(student_id)
        return record

    async def update_portfolio_item(
        self, student_id: UUID, record_id: UUID, data: UpdatePortfolioItemRequest,
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
        self, student_id: UUID, record_id: UUID,
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
        self, student_id: UUID, data: CreateResearchRequest,
    ) -> StudentResearch:
        record = StudentResearch(student_id=student_id, **data.model_dump())
        if record.is_current:
            record.end_date = None
        self.db.add(record)
        await self.db.flush()
        await self._update_onboarding(student_id)
        return record

    async def update_research(
        self, student_id: UUID, record_id: UUID, data: UpdateResearchRequest,
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
        self, student_id: UUID, record_id: UUID,
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
        self, student_id: UUID, data: CreateLanguageRequest,
    ) -> StudentLanguage:
        record = StudentLanguage(student_id=student_id, **data.model_dump())
        self.db.add(record)
        await self.db.flush()
        await self._update_onboarding(student_id)
        return record

    async def update_language(
        self, student_id: UUID, record_id: UUID, data: UpdateLanguageRequest,
    ) -> StudentLanguage:
        record = await self._get_record(StudentLanguage, record_id)
        await self._verify_ownership(student_id, record.student_id)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(record, key, value)
        await self.db.flush()
        await self._update_onboarding(student_id)
        return record

    async def delete_language(
        self, student_id: UUID, record_id: UUID,
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
        self, student_id: UUID, data: CreateWorkExperienceRequest,
    ) -> StudentWorkExperience:
        record = StudentWorkExperience(student_id=student_id, **data.model_dump())
        if record.is_current:
            record.end_date = None
        self.db.add(record)
        await self.db.flush()
        await self._update_onboarding(student_id)
        return record

    async def update_work_experience(
        self, student_id: UUID, record_id: UUID, data: UpdateWorkExperienceRequest,
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
        self, student_id: UUID, record_id: UUID,
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
        self, student_id: UUID, data: CreateCompetitionRequest,
    ) -> StudentCompetition:
        record = StudentCompetition(student_id=student_id, **data.model_dump())
        self.db.add(record)
        await self.db.flush()
        await self._update_onboarding(student_id)
        return record

    async def update_competition(
        self, student_id: UUID, record_id: UUID, data: UpdateCompetitionRequest,
    ) -> StudentCompetition:
        record = await self._get_record(StudentCompetition, record_id)
        await self._verify_ownership(student_id, record.student_id)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(record, key, value)
        await self.db.flush()
        await self._update_onboarding(student_id)
        return record

    async def delete_competition(
        self, student_id: UUID, record_id: UUID,
    ) -> None:
        record = await self._get_record(StudentCompetition, record_id)
        await self._verify_ownership(student_id, record.student_id)
        await self.db.delete(record)
        await self.db.flush()
        await self._update_onboarding(student_id)

    # --- Accommodations ---

    async def get_accommodations(
        self, student_id: UUID,
    ) -> StudentAccommodation | None:
        result = await self.db.execute(
            select(StudentAccommodation).where(
                StudentAccommodation.student_id == student_id,
            )
        )
        return result.scalar_one_or_none()

    async def upsert_accommodations(
        self, student_id: UUID, data: UpsertAccommodationRequest,
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
        self, student_id: UUID, data: UpsertSchedulingRequest,
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
                selectinload(StudentProfile.academic_records),
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
        await on_student_profile_updated(self.db, student_id)

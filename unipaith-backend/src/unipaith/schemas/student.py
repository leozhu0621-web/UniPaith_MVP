from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UpdateProfileRequest(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    date_of_birth: date | None = None
    nationality: str | None = None
    country_of_residence: str | None = None
    bio_text: str | None = None
    goals_text: str | None = None


class CreateAcademicRecordRequest(BaseModel):
    institution_name: str = Field(min_length=1, max_length=255)
    degree_type: Literal["high_school", "bachelors", "masters", "phd", "associate", "diploma"]
    field_of_study: str | None = None
    gpa: Decimal | None = Field(None, ge=0, le=100)
    gpa_scale: str | None = None
    start_date: date
    end_date: date | None = None
    is_current: bool = False
    honors: str | None = None
    thesis_title: str | None = None
    country: str | None = None


class UpdateAcademicRecordRequest(BaseModel):
    institution_name: str | None = Field(None, min_length=1, max_length=255)
    degree_type: (
        Literal["high_school", "bachelors", "masters", "phd", "associate", "diploma"] | None
    ) = None
    field_of_study: str | None = None
    gpa: Decimal | None = Field(None, ge=0, le=100)
    gpa_scale: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool | None = None
    honors: str | None = None
    thesis_title: str | None = None
    country: str | None = None


class AcademicRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    student_id: UUID
    institution_name: str
    degree_type: str
    field_of_study: str | None
    gpa: Decimal | None
    gpa_scale: str | None
    start_date: date | None
    end_date: date | None
    is_current: bool
    honors: str | None
    thesis_title: str | None
    country: str | None
    created_at: datetime
    updated_at: datetime


class CreateTestScoreRequest(BaseModel):
    test_type: Literal[
        "SAT", "GRE", "GMAT", "TOEFL", "IELTS", "AP", "IB", "ACT", "LSAT", "MCAT", "DUOLINGO"
    ]
    total_score: int | None = None
    section_scores: dict | None = None
    test_date: date | None = None
    is_official: bool = False


class UpdateTestScoreRequest(BaseModel):
    test_type: (
        Literal[
            "SAT", "GRE", "GMAT", "TOEFL", "IELTS", "AP", "IB", "ACT", "LSAT", "MCAT", "DUOLINGO"
        ]
        | None
    ) = None
    total_score: int | None = None
    section_scores: dict | None = None
    test_date: date | None = None
    is_official: bool | None = None


class TestScoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    student_id: UUID
    test_type: str
    total_score: int | None
    section_scores: dict | None
    test_date: date | None
    is_official: bool
    created_at: datetime
    updated_at: datetime


class CreateActivityRequest(BaseModel):
    activity_type: Literal[
        "work_experience",
        "research",
        "volunteering",
        "extracurricular",
        "leadership",
        "awards",
        "publications",
    ]
    title: str = Field(min_length=1, max_length=255)
    organization: str | None = None
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool = False
    hours_per_week: int | None = None
    impact_description: str | None = None


class UpdateActivityRequest(BaseModel):
    activity_type: (
        Literal[
            "work_experience",
            "research",
            "volunteering",
            "extracurricular",
            "leadership",
            "awards",
            "publications",
        ]
        | None
    ) = None
    title: str | None = Field(None, min_length=1, max_length=255)
    organization: str | None = None
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool | None = None
    hours_per_week: int | None = None
    impact_description: str | None = None


class ActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    student_id: UUID
    activity_type: str
    title: str
    organization: str | None
    description: str | None
    start_date: date | None
    end_date: date | None
    is_current: bool
    hours_per_week: int | None
    impact_description: str | None
    created_at: datetime
    updated_at: datetime


class UpsertPreferencesRequest(BaseModel):
    preferred_countries: list[str] | None = None
    preferred_regions: list[str] | None = None
    preferred_city_size: (
        Literal["big_city", "college_town", "suburban", "rural", "no_preference"] | None
    ) = None
    preferred_climate: str | None = None
    budget_min: int | None = None
    budget_max: int | None = None
    funding_requirement: (
        Literal["full_scholarship", "partial", "self_funded", "flexible"] | None
    ) = None
    program_size_preference: Literal["small", "large", "no_preference"] | None = None
    career_goals: list[str] | None = None
    values_priorities: dict | None = None
    dealbreakers: list[str] | None = None
    goals_text: str | None = None


class StudentPreferenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    student_id: UUID
    preferred_countries: list[str] | None
    preferred_regions: list[str] | None
    preferred_city_size: str | None
    preferred_climate: str | None
    budget_min: int | None
    budget_max: int | None
    funding_requirement: str | None
    program_size_preference: str | None
    career_goals: list[str] | None
    values_priorities: dict | None
    dealbreakers: list[str] | None
    goals_text: str | None
    created_at: datetime
    updated_at: datetime


class CreateOnlinePresenceRequest(BaseModel):
    platform_type: Literal[
        "linkedin", "github", "personal_site", "portfolio",
        "wechat", "twitter", "other",
    ]
    url: str = Field(min_length=1, max_length=1000)
    display_name: str | None = Field(None, max_length=255)


class UpdateOnlinePresenceRequest(BaseModel):
    platform_type: (
        Literal[
            "linkedin", "github", "personal_site", "portfolio",
            "wechat", "twitter", "other",
        ]
        | None
    ) = None
    url: str | None = Field(None, min_length=1, max_length=1000)
    display_name: str | None = Field(None, max_length=255)


class OnlinePresenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    student_id: UUID
    platform_type: str
    url: str
    display_name: str | None
    created_at: datetime
    updated_at: datetime


class CreatePortfolioItemRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    item_type: Literal[
        "project", "writing_sample", "artwork",
        "presentation", "code", "other",
    ]
    url: str | None = Field(None, max_length=1000)
    document_id: UUID | None = None
    display_order: int = 0


class UpdatePortfolioItemRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    item_type: (
        Literal[
            "project", "writing_sample", "artwork",
            "presentation", "code", "other",
        ]
        | None
    ) = None
    url: str | None = Field(None, max_length=1000)
    document_id: UUID | None = None
    display_order: int | None = None


class PortfolioItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    student_id: UUID
    title: str
    description: str | None
    item_type: str
    url: str | None
    document_id: UUID | None
    display_order: int
    created_at: datetime
    updated_at: datetime


class NextStepResponse(BaseModel):
    section: str
    fields: list[str]
    guidance_text: str


class OnboardingStatusResponse(BaseModel):
    completion_percentage: int
    steps_completed: list[str]
    next_step: NextStepResponse | None


class StudentProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    user_id: UUID
    first_name: str | None
    last_name: str | None
    date_of_birth: date | None
    nationality: str | None
    country_of_residence: str | None
    bio_text: str | None
    goals_text: str | None
    created_at: datetime
    updated_at: datetime
    academic_records: list[AcademicRecordResponse] = []
    test_scores: list[TestScoreResponse] = []
    activities: list[ActivityResponse] = []
    online_presence: list[OnlinePresenceResponse] = []
    portfolio_items: list[PortfolioItemResponse] = []
    preferences: StudentPreferenceResponse | None = None
    onboarding: OnboardingStatusResponse | None = None


class StudentAssistantChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    context_program_id: UUID | None = None


class StudentAssistantChatResponse(BaseModel):
    reply: str
    model: str
    provider: str = "openai"

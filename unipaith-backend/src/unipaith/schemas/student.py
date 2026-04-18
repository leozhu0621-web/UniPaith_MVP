from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UpdateProfileRequest(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    preferred_name: str | None = None
    name_in_native_script: str | None = None
    preferred_pronouns: str | None = None
    date_of_birth: date | None = None
    gender_identity: str | None = None
    legal_sex: str | None = None
    place_of_birth: str | None = None
    nationality: str | None = None
    passport_issuing_country: str | None = None
    country_of_residence: str | None = None
    bio_text: str | None = None
    goals_text: str | None = None
    secondary_email: str | None = None
    secondary_phone: str | None = None
    preferred_contact_channel: str | None = None
    preferred_platform_language: str | None = None
    preferred_writing_language: str | None = None
    marital_status: str | None = None
    residency_status_for_tuition: str | None = None
    domicile_state: str | None = None
    duration_of_residency_months: int | None = None
    # JSONB blobs - shape documented on the model.
    addresses: dict | None = None
    emergency_contact: dict | None = None
    guardian: dict | None = None
    email_verified: bool | None = None
    phone_verified: bool | None = None
    id_verification_status: str | None = None


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
    transcript_language: str | None = None
    credential_evaluation_status: (
        Literal["none", "in_progress", "provided", "verified"] | None
    ) = None
    credential_evaluation_report_url: str | None = Field(
        None, max_length=1000,
    )
    rigor_indicator_count: int | None = None
    attendance_rate: Decimal | None = Field(None, ge=0, le=1)
    class_rank: int | None = Field(None, ge=1)
    class_rank_denominator: int | None = Field(None, ge=1)
    percentile_rank: Decimal | None = Field(None, ge=0, le=100)
    weighted_gpa_flag: bool | None = None
    leave_of_absence_flag: bool | None = None
    withdrawal_incomplete_flag: bool | None = None
    grading_scale_type: str | None = None
    term_system_type: str | None = None
    transcript_upload_url: str | None = None
    translation_provided_flag: bool | None = None
    # {ap_count, ib_count, honors_count, college_count}
    school_reported_rigor: dict | None = None
    disruption_details: str | None = None
    normalized_gpa: Decimal | None = Field(None, ge=0, le=4)
    transcript_parse_status: str = "not_parsed"


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
    transcript_language: str | None = None
    credential_evaluation_status: (
        Literal["none", "in_progress", "provided", "verified"] | None
    ) = None
    credential_evaluation_report_url: str | None = Field(
        None, max_length=1000,
    )
    rigor_indicator_count: int | None = None
    attendance_rate: Decimal | None = Field(None, ge=0, le=1)
    class_rank: int | None = Field(None, ge=1)
    class_rank_denominator: int | None = Field(None, ge=1)
    percentile_rank: Decimal | None = Field(None, ge=0, le=100)
    weighted_gpa_flag: bool | None = None
    leave_of_absence_flag: bool | None = None
    withdrawal_incomplete_flag: bool | None = None
    grading_scale_type: str | None = None
    term_system_type: str | None = None
    transcript_upload_url: str | None = None
    translation_provided_flag: bool | None = None
    # {ap_count, ib_count, honors_count, college_count}
    school_reported_rigor: dict | None = None
    disruption_details: str | None = None
    normalized_gpa: Decimal | None = Field(None, ge=0, le=4)
    transcript_parse_status: str | None = None


class CourseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    academic_record_id: UUID
    course_name: str
    course_code: str | None
    subject_area: str | None
    course_level: str
    grade: str | None
    credits: Decimal | None
    term: str | None
    created_at: datetime
    updated_at: datetime


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
    transcript_language: str | None
    credential_evaluation_status: str | None
    credential_evaluation_report_url: str | None
    rigor_indicator_count: int | None
    attendance_rate: Decimal | None = None
    class_rank: int | None = None
    class_rank_denominator: int | None = None
    percentile_rank: Decimal | None = None
    weighted_gpa_flag: bool | None = None
    leave_of_absence_flag: bool | None = None
    withdrawal_incomplete_flag: bool | None = None
    grading_scale_type: str | None = None
    term_system_type: str | None = None
    transcript_upload_url: str | None = None
    translation_provided_flag: bool | None = None
    school_reported_rigor: dict | None = None
    disruption_details: str | None = None
    normalized_gpa: Decimal | None = None
    transcript_parse_status: str | None = None
    courses: list[CourseResponse] = []
    created_at: datetime
    updated_at: datetime


class CreateCourseRequest(BaseModel):
    course_name: str = Field(min_length=1, max_length=255)
    course_code: str | None = Field(None, max_length=50)
    subject_area: str | None = Field(None, max_length=100)
    course_level: Literal[
        "regular", "honors", "AP", "IB", "college",
    ]
    grade: str | None = Field(None, max_length=20)
    credits: Decimal | None = None
    term: str | None = Field(None, max_length=50)


class UpdateCourseRequest(BaseModel):
    course_name: str | None = Field(None, min_length=1, max_length=255)
    course_code: str | None = Field(None, max_length=50)
    subject_area: str | None = Field(None, max_length=100)
    course_level: (
        Literal["regular", "honors", "AP", "IB", "college"] | None
    ) = None
    grade: str | None = Field(None, max_length=20)
    credits: Decimal | None = None
    term: str | None = Field(None, max_length=50)


class CreateTestScoreRequest(BaseModel):
    test_type: Literal[
        "SAT", "GRE", "GMAT", "TOEFL", "IELTS", "AP", "IB", "ACT", "LSAT", "MCAT", "DUOLINGO"
    ]
    total_score: int | None = None
    section_scores: dict | None = None
    test_date: date | None = None
    is_official: bool = False
    percentile: Decimal | None = Field(None, ge=0, le=100)
    test_attempt_number: int | None = Field(None, ge=1)
    superscore_preference: bool | None = None
    score_expiration_date: date | None = None
    test_waiver_flag: bool | None = None
    test_waiver_basis: str | None = None
    official_score_report_url: str | None = None
    is_verified: bool | None = None
    score_normalization_status: str = "unmapped"


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
    percentile: Decimal | None = Field(None, ge=0, le=100)
    test_attempt_number: int | None = Field(None, ge=1)
    superscore_preference: bool | None = None
    score_expiration_date: date | None = None
    test_waiver_flag: bool | None = None
    test_waiver_basis: str | None = None
    official_score_report_url: str | None = None
    is_verified: bool | None = None
    score_normalization_status: str | None = None


class TestScoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    student_id: UUID
    test_type: str
    total_score: int | None
    section_scores: dict | None
    test_date: date | None
    is_official: bool
    percentile: Decimal | None = None
    test_attempt_number: int | None = None
    superscore_preference: bool | None = None
    score_expiration_date: date | None = None
    test_waiver_flag: bool | None = None
    test_waiver_basis: str | None = None
    official_score_report_url: str | None = None
    is_verified: bool = False
    score_normalization_status: str = "unmapped"
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
    career_goal_short_term: str | None = None
    # Preference weights: 0-10 scale per appendix "Intent, goals,
    # priorities, tradeoffs" section. Matching reads these directly.
    weight_cost: int | None = Field(None, ge=0, le=10)
    weight_location: int | None = Field(None, ge=0, le=10)
    weight_outcomes: int | None = Field(None, ge=0, le=10)
    weight_ranking: int | None = Field(None, ge=0, le=10)
    weight_flexibility: int | None = Field(None, ge=0, le=10)
    weight_support: int | None = Field(None, ge=0, le=10)
    weight_time_to_degree: int | None = Field(None, ge=0, le=10)
    application_intensity: str | None = None
    preferred_learning_style: str | None = None
    preferred_program_style: str | None = None
    research_interest_level: str | None = None
    return_home_intent: str | None = None
    risk_tolerance: str | None = None
    stretch_target_safety_mix: str | None = None
    target_degree_level: str | None = None
    target_start_term: str | None = None
    thesis_interest: str | None = None


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
    career_goal_short_term: str | None = None
    # Appendix "preference weights" on 0-10 scale.
    weight_cost: int | None = None
    weight_location: int | None = None
    weight_outcomes: int | None = None
    weight_ranking: int | None = None
    weight_flexibility: int | None = None
    weight_support: int | None = None
    weight_time_to_degree: int | None = None
    application_intensity: str | None = None
    preferred_learning_style: str | None = None
    preferred_program_style: str | None = None
    research_interest_level: str | None = None
    return_home_intent: str | None = None
    risk_tolerance: str | None = None
    stretch_target_safety_mix: str | None = None
    target_degree_level: str | None = None
    target_start_term: str | None = None
    thesis_interest: str | None = None
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


class CreateResearchRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    institution_lab: str | None = None
    field_discipline: str | None = None
    role: Literal["assistant", "independent", "lead"]
    advisor_name: str | None = None
    methods_tools: str | None = None
    outcomes: str | None = None
    outputs: Literal["paper", "poster", "code", "none"] | None = None
    publication_link: str | None = Field(None, max_length=1000)
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool = False


class UpdateResearchRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    institution_lab: str | None = None
    field_discipline: str | None = None
    role: Literal["assistant", "independent", "lead"] | None = None
    advisor_name: str | None = None
    methods_tools: str | None = None
    outcomes: str | None = None
    outputs: (
        Literal["paper", "poster", "code", "none"] | None
    ) = None
    publication_link: str | None = Field(None, max_length=1000)
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool | None = None


class ResearchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    student_id: UUID
    title: str
    institution_lab: str | None
    field_discipline: str | None
    role: str
    advisor_name: str | None
    methods_tools: str | None
    outcomes: str | None
    outputs: str | None
    publication_link: str | None
    start_date: date | None
    end_date: date | None
    is_current: bool
    created_at: datetime
    updated_at: datetime


class CreateLanguageRequest(BaseModel):
    language: str = Field(min_length=1, max_length=100)
    proficiency_level: Literal[
        "native", "fluent", "advanced", "intermediate", "beginner",
    ]
    certification_type: str | None = Field(None, max_length=100)
    certification_score: str | None = Field(None, max_length=50)
    test_date: date | None = None


class UpdateLanguageRequest(BaseModel):
    language: str | None = Field(None, min_length=1, max_length=100)
    proficiency_level: (
        Literal["native", "fluent", "advanced", "intermediate", "beginner"]
        | None
    ) = None
    certification_type: str | None = Field(None, max_length=100)
    certification_score: str | None = Field(None, max_length=50)
    test_date: date | None = None


class LanguageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    student_id: UUID
    language: str
    proficiency_level: str
    certification_type: str | None
    certification_score: str | None
    test_date: date | None
    created_at: datetime
    updated_at: datetime


class CreateWorkExperienceRequest(BaseModel):
    experience_type: Literal[
        "employment", "internship", "volunteering", "service",
    ]
    organization: str = Field(min_length=1, max_length=255)
    role_title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool = False
    hours_per_week: int | None = None
    compensation_type: Literal[
        "paid", "unpaid", "stipend",
    ] | None = None
    key_achievements: str | None = None
    supervisor_name: str | None = None
    organization_country: str | None = None
    organization_city: str | None = None


class UpdateWorkExperienceRequest(BaseModel):
    experience_type: (
        Literal["employment", "internship", "volunteering", "service"]
        | None
    ) = None
    organization: str | None = Field(None, min_length=1, max_length=255)
    role_title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool | None = None
    hours_per_week: int | None = None
    compensation_type: (
        Literal["paid", "unpaid", "stipend"] | None
    ) = None
    key_achievements: str | None = None
    supervisor_name: str | None = None
    organization_country: str | None = None
    organization_city: str | None = None


class WorkExperienceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    student_id: UUID
    experience_type: str
    organization: str
    role_title: str
    description: str | None
    start_date: date | None
    end_date: date | None
    is_current: bool
    hours_per_week: int | None
    compensation_type: str | None
    key_achievements: str | None
    supervisor_name: str | None
    organization_country: str | None
    organization_city: str | None
    created_at: datetime
    updated_at: datetime


class CreateCompetitionRequest(BaseModel):
    competition_name: str = Field(min_length=1, max_length=255)
    domain: str | None = Field(None, max_length=100)
    level: Literal[
        "school", "state", "national", "international",
    ]
    role: str | None = Field(None, max_length=50)
    result_placement: str | None = Field(None, max_length=100)
    year: int | None = None
    team_size: int | None = None
    description: str | None = None
    link_proof: str | None = Field(None, max_length=1000)


class UpdateCompetitionRequest(BaseModel):
    competition_name: str | None = Field(None, min_length=1, max_length=255)
    domain: str | None = Field(None, max_length=100)
    level: (
        Literal["school", "state", "national", "international"]
        | None
    ) = None
    role: str | None = Field(None, max_length=50)
    result_placement: str | None = Field(None, max_length=100)
    year: int | None = None
    team_size: int | None = None
    description: str | None = None
    link_proof: str | None = Field(None, max_length=1000)


class CompetitionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    student_id: UUID
    competition_name: str
    domain: str | None
    level: str
    role: str | None
    result_placement: str | None
    year: int | None
    team_size: int | None
    description: str | None
    link_proof: str | None
    created_at: datetime
    updated_at: datetime


class UpsertAccommodationRequest(BaseModel):
    accommodations_needed: bool = False
    category: str | None = Field(None, max_length=100)
    details_text: str | None = None
    documentation_status: (
        Literal["none", "in_progress", "available", "verified"]
        | None
    ) = None
    dyslexia_friendly_mode: bool = False
    font_size_pref: (
        Literal["default", "large", "extra_large"] | None
    ) = None


class AccommodationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    student_id: UUID
    accommodations_needed: bool
    category: str | None
    details_text: str | None
    documentation_status: str | None
    dyslexia_friendly_mode: bool
    font_size_pref: str | None
    created_at: datetime
    updated_at: datetime


class UpsertSchedulingRequest(BaseModel):
    timezone: str | None = Field(None, max_length=50)
    general_availability: dict | None = None
    preferred_interview_format: (
        Literal["video", "in_person", "phone", "no_preference"]
        | None
    ) = None
    campus_visit_interest: bool = False
    notes: str | None = None


class SchedulingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    student_id: UUID
    timezone: str | None
    general_availability: dict | None
    preferred_interview_format: str | None
    campus_visit_interest: bool
    notes: str | None
    created_at: datetime
    updated_at: datetime


class UpsertVisaInfoRequest(BaseModel):
    current_immigration_status: str | None = Field(None, max_length=50)
    visa_required: bool = False
    target_study_country: str | None = Field(None, max_length=100)
    passport_expiration_date: date | None = None
    sponsorship_source: (
        Literal["self", "family", "scholarship", "employer"] | None
    ) = None
    financial_proof_available: bool = False
    financial_proof_amount_band: str | None = Field(None, max_length=50)
    post_study_work_interest: bool = False
    prior_visa_refusals: bool = False
    travel_constraints: str | None = None
    work_authorization_needed: bool = False
    current_location_city: str | None = Field(None, max_length=100)
    current_location_country: str | None = Field(None, max_length=100)
    dependents_accompanying: bool | None = None
    intended_start_term: str | None = Field(None, max_length=30)
    visa_type_current: str | None = Field(None, max_length=30)
    country_of_citizenship: str | None = Field(None, max_length=100)


class VisaInfoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    student_id: UUID
    current_immigration_status: str | None
    visa_required: bool
    target_study_country: str | None
    passport_expiration_date: date | None
    sponsorship_source: str | None
    financial_proof_available: bool
    financial_proof_amount_band: str | None
    post_study_work_interest: bool
    prior_visa_refusals: bool
    travel_constraints: str | None
    work_authorization_needed: bool
    current_location_city: str | None = None
    current_location_country: str | None = None
    dependents_accompanying: bool | None = None
    intended_start_term: str | None = None
    visa_type_current: str | None = None
    country_of_citizenship: str | None = None
    created_at: datetime
    updated_at: datetime


class UpsertDataConsentRequest(BaseModel):
    consent_matching: bool | None = None
    consent_outreach: bool | None = None
    consent_research: bool | None = None
    data_retention_preference: (
        Literal["standard", "minimum", "delete_after_cycle"] | None
    ) = None
    deletion_requested: bool | None = None
    first_generation_status: bool | None = None
    first_generation_definition: str | None = None
    ferpa_release: bool | None = None
    honor_code_ack: bool | None = None
    background_check_required: bool | None = None
    code_of_conduct_ack: bool | None = None
    criminal_history_disclosed: bool | None = None
    disciplinary_history_disclosed: bool | None = None
    immunization_compliance: str | None = None
    health_insurance_waiver_intent: bool | None = None
    military_status: str | None = None
    veteran_status: bool | None = None
    prior_academic_dismissal_flag: bool | None = None
    directory_info_release: bool | None = None
    third_party_sharing_consent: bool | None = None
    marketing_channel_consent: dict | None = None
    consent_revocation_timestamps: list | None = None


class DataConsentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    student_id: UUID
    consent_matching: bool
    consent_outreach: bool
    consent_research: bool
    data_retention_preference: str | None
    deletion_requested: bool
    deletion_requested_at: datetime | None
    first_generation_status: bool | None = None
    first_generation_definition: str | None = None
    ferpa_release: bool | None = None
    honor_code_ack: bool | None = None
    background_check_required: bool | None = None
    code_of_conduct_ack: bool | None = None
    criminal_history_disclosed: bool | None = None
    disciplinary_history_disclosed: bool | None = None
    immunization_compliance: str | None = None
    health_insurance_waiver_intent: bool | None = None
    military_status: str | None = None
    veteran_status: bool | None = None
    prior_academic_dismissal_flag: bool | None = None
    directory_info_release: bool | None = None
    third_party_sharing_consent: bool | None = None
    marketing_channel_consent: dict | None = None
    consent_revocation_timestamps: list | None = None
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
    preferred_name: str | None = None
    name_in_native_script: str | None = None
    preferred_pronouns: str | None = None
    date_of_birth: date | None
    gender_identity: str | None = None
    legal_sex: str | None = None
    place_of_birth: str | None = None
    nationality: str | None
    passport_issuing_country: str | None = None
    country_of_residence: str | None
    bio_text: str | None
    goals_text: str | None
    secondary_email: str | None = None
    secondary_phone: str | None = None
    preferred_contact_channel: str | None = None
    preferred_platform_language: str | None = None
    preferred_writing_language: str | None = None
    marital_status: str | None = None
    residency_status_for_tuition: str | None = None
    domicile_state: str | None = None
    duration_of_residency_months: int | None = None
    addresses: dict | None = None
    emergency_contact: dict | None = None
    guardian: dict | None = None
    email_verified: bool = False
    phone_verified: bool = False
    id_verification_status: str = "none"
    created_at: datetime
    updated_at: datetime
    academic_records: list[AcademicRecordResponse] = []
    test_scores: list[TestScoreResponse] = []
    activities: list[ActivityResponse] = []
    online_presence: list[OnlinePresenceResponse] = []
    portfolio_items: list[PortfolioItemResponse] = []
    research_entries: list[ResearchResponse] = []
    languages: list[LanguageResponse] = []
    work_experiences: list[WorkExperienceResponse] = []
    competitions: list[CompetitionResponse] = []
    accommodations: AccommodationResponse | None = None
    scheduling: SchedulingResponse | None = None
    visa_info: VisaInfoResponse | None = None
    data_consent: DataConsentResponse | None = None
    preferences: StudentPreferenceResponse | None = None
    onboarding: OnboardingStatusResponse | None = None


class StudentAssistantChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    context_program_id: UUID | None = None


class StudentAssistantChatResponse(BaseModel):
    reply: str
    model: str
    provider: str = "openai"


# --- Package A: Major Readiness -----------------------------------------

MajorTrackLiteral = Literal["cs", "engineering", "business", "health", "arts", "humanities"]


class UpsertMajorReadinessRequest(BaseModel):
    """Upsert a track-level readiness blob.

    `readiness_data` shape is track-specific (see
    docs/STUDENT_DATA_STANDARD.md). The API does not enforce a per-field
    schema here because the set of valid keys is large, track-specific, and
    evolves; callers are expected to send a dict that conforms to the track's
    section in the standard doc.
    """

    track: MajorTrackLiteral
    readiness_data: dict = Field(description="Track-specific self-rating blob")


class MajorReadinessResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    student_id: UUID
    track: str
    readiness_data: dict
    created_at: datetime
    updated_at: datetime


# --- Package A: Platform events (analytics) -----------------------------


class LogPlatformEventRequest(BaseModel):
    event_type: str = Field(
        min_length=1, max_length=50,
        description="Short tag e.g. 'login', 'search', 'program_view', 'compare'",
    )
    event_metadata: dict | None = None
    session_id: str | None = Field(None, max_length=100)
    device_type: Literal["desktop", "mobile", "tablet"] | None = None
    url_path: str | None = Field(None, max_length=500)
    referral_source: str | None = Field(None, max_length=100)
    utm_campaign: str | None = Field(None, max_length=255)
    ip_country: str | None = Field(None, max_length=100)


class PlatformEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    student_id: UUID
    event_type: str
    event_metadata: dict | None
    session_id: str | None
    device_type: str | None
    url_path: str | None
    referral_source: str | None
    utm_campaign: str | None
    ip_country: str | None
    occurred_at: datetime

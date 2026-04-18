from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    ARRAY,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from unipaith.models.base import Base


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    first_name: Mapped[str | None] = mapped_column(String(100))
    last_name: Mapped[str | None] = mapped_column(String(100))
    preferred_name: Mapped[str | None] = mapped_column(String(100))
    name_in_native_script: Mapped[str | None] = mapped_column(String(255))
    preferred_pronouns: Mapped[str | None] = mapped_column(String(50))
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    gender_identity: Mapped[str | None] = mapped_column(String(50))
    legal_sex: Mapped[str | None] = mapped_column(String(20))
    place_of_birth: Mapped[str | None] = mapped_column(String(255))
    nationality: Mapped[str | None] = mapped_column(String(100))
    passport_issuing_country: Mapped[str | None] = mapped_column(String(100))
    country_of_residence: Mapped[str | None] = mapped_column(String(100))
    bio_text: Mapped[str | None] = mapped_column(Text)
    goals_text: Mapped[str | None] = mapped_column(Text)
    secondary_email: Mapped[str | None] = mapped_column(String(255))
    secondary_phone: Mapped[str | None] = mapped_column(String(50))
    preferred_contact_channel: Mapped[str | None] = mapped_column(String(30))
    preferred_platform_language: Mapped[str | None] = mapped_column(String(30))
    preferred_writing_language: Mapped[str | None] = mapped_column(String(30))
    marital_status: Mapped[str | None] = mapped_column(String(30))
    residency_status_for_tuition: Mapped[str | None] = mapped_column(String(50))
    domicile_state: Mapped[str | None] = mapped_column(String(50))
    duration_of_residency_months: Mapped[int | None] = mapped_column(Integer)
    # Address/contact bundles kept as JSONB - see appendix Identity section.
    # Shape: {current, permanent, mailing, billing} each {line1, line2, city,
    # state, postal_code, country}.
    addresses: Mapped[dict | None] = mapped_column(JSONB)
    # {name, email, phone, relationship}.
    emergency_contact: Mapped[dict | None] = mapped_column(JSONB)
    # {name, email, phone, relationship, custody_status}.
    guardian: Mapped[dict | None] = mapped_column(JSONB)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    phone_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    id_verification_status: Mapped[str] = mapped_column(String(20), default="none")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped[User] = relationship("User", back_populates="student_profile")  # type: ignore[name-defined]  # noqa: F821
    academic_records: Mapped[list[AcademicRecord]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )
    test_scores: Mapped[list[TestScore]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )
    activities: Mapped[list[Activity]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )
    documents: Mapped[list[StudentDocument]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )
    preferences: Mapped[StudentPreference | None] = relationship(
        back_populates="student", uselist=False, cascade="all, delete-orphan"
    )
    online_presence: Mapped[list[StudentOnlinePresence]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )
    portfolio_items: Mapped[list[StudentPortfolioItem]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )
    research_entries: Mapped[list[StudentResearch]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )
    languages: Mapped[list[StudentLanguage]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )
    work_experiences: Mapped[list[StudentWorkExperience]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )
    competitions: Mapped[list[StudentCompetition]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )
    accommodations: Mapped[StudentAccommodation | None] = relationship(
        back_populates="student", uselist=False, cascade="all, delete-orphan"
    )
    scheduling: Mapped[StudentScheduling | None] = relationship(
        back_populates="student", uselist=False, cascade="all, delete-orphan"
    )
    visa_info: Mapped[StudentVisaInfo | None] = relationship(
        back_populates="student", uselist=False, cascade="all, delete-orphan"
    )
    data_consent: Mapped[StudentDataConsent | None] = relationship(
        back_populates="student", uselist=False, cascade="all, delete-orphan"
    )
    recommendation_requests: Mapped[list[RecommendationRequest]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )
    onboarding_progress: Mapped[OnboardingProgress | None] = relationship(
        back_populates="student", uselist=False, cascade="all, delete-orphan"
    )


class AcademicRecord(Base):
    __tablename__ = "academic_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    institution_name: Mapped[str] = mapped_column(String(255), nullable=False)
    degree_type: Mapped[str] = mapped_column(String(50), nullable=False)
    field_of_study: Mapped[str | None] = mapped_column(String(255))
    gpa: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    gpa_scale: Mapped[str | None] = mapped_column(String(20))
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    honors: Mapped[str | None] = mapped_column(String(255))
    thesis_title: Mapped[str | None] = mapped_column(String(500))
    country: Mapped[str | None] = mapped_column(String(100))
    transcript_language: Mapped[str | None] = mapped_column(String(50))
    credential_evaluation_status: Mapped[str | None] = mapped_column(String(30))
    credential_evaluation_report_url: Mapped[str | None] = mapped_column(String(1000))
    rigor_indicator_count: Mapped[int | None] = mapped_column(Integer)
    attendance_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    class_rank: Mapped[int | None] = mapped_column(Integer)
    class_rank_denominator: Mapped[int | None] = mapped_column(Integer)
    percentile_rank: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    weighted_gpa_flag: Mapped[bool | None] = mapped_column(Boolean)
    leave_of_absence_flag: Mapped[bool | None] = mapped_column(Boolean)
    withdrawal_incomplete_flag: Mapped[bool | None] = mapped_column(Boolean)
    grading_scale_type: Mapped[str | None] = mapped_column(String(30))
    term_system_type: Mapped[str | None] = mapped_column(String(30))
    transcript_upload_url: Mapped[str | None] = mapped_column(String(1000))
    translation_provided_flag: Mapped[bool | None] = mapped_column(Boolean)
    # {ap_count, ib_count, honors_count, college_count}
    school_reported_rigor: Mapped[dict | None] = mapped_column(JSONB)
    disruption_details: Mapped[str | None] = mapped_column(Text)
    normalized_gpa: Mapped[Decimal | None] = mapped_column(Numeric(4, 2))
    transcript_parse_status: Mapped[str] = mapped_column(String(20), default="not_parsed")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    student: Mapped[StudentProfile] = relationship(back_populates="academic_records")
    courses: Mapped[list[StudentCourse]] = relationship(
        back_populates="academic_record", cascade="all, delete-orphan"
    )


class StudentCourse(Base):
    __tablename__ = "student_courses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    academic_record_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("academic_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    course_name: Mapped[str] = mapped_column(String(255), nullable=False)
    course_code: Mapped[str | None] = mapped_column(String(50))
    subject_area: Mapped[str | None] = mapped_column(String(100))
    course_level: Mapped[str] = mapped_column(String(30), nullable=False)
    grade: Mapped[str | None] = mapped_column(String(20))
    credits: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    term: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    academic_record: Mapped[AcademicRecord] = relationship(back_populates="courses")


class TestScore(Base):
    __test__ = False  # Prevent pytest from collecting this as a test class
    __tablename__ = "test_scores"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    test_type: Mapped[str] = mapped_column(String(50), nullable=False)
    total_score: Mapped[int | None] = mapped_column(Integer)
    section_scores: Mapped[dict | None] = mapped_column(JSONB)
    test_date: Mapped[date | None] = mapped_column(Date)
    is_official: Mapped[bool] = mapped_column(Boolean, default=False)
    percentile: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    test_attempt_number: Mapped[int | None] = mapped_column(Integer)
    superscore_preference: Mapped[bool | None] = mapped_column(Boolean)
    score_expiration_date: Mapped[date | None] = mapped_column(Date)
    test_waiver_flag: Mapped[bool | None] = mapped_column(Boolean)
    test_waiver_basis: Mapped[str | None] = mapped_column(String(255))
    official_score_report_url: Mapped[str | None] = mapped_column(String(1000))
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    score_normalization_status: Mapped[str] = mapped_column(String(20), default="unmapped")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    student: Mapped[StudentProfile] = relationship(back_populates="test_scores")


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    activity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    organization: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    hours_per_week: Mapped[int | None] = mapped_column(Integer)
    impact_description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    student: Mapped[StudentProfile] = relationship(back_populates="activities")


class StudentDocument(Base):
    __tablename__ = "student_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_url: Mapped[str | None] = mapped_column(String(1000))
    file_size_bytes: Mapped[int | None] = mapped_column(Integer)
    mime_type: Mapped[str | None] = mapped_column(String(100))
    extracted_text: Mapped[str | None] = mapped_column(Text)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    student: Mapped[StudentProfile] = relationship(back_populates="documents")


class StudentPreference(Base):
    __tablename__ = "student_preferences"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    preferred_countries: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    preferred_regions: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    preferred_city_size: Mapped[str | None] = mapped_column(String(30))
    preferred_climate: Mapped[str | None] = mapped_column(String(50))
    budget_min: Mapped[int | None] = mapped_column(Integer)
    budget_max: Mapped[int | None] = mapped_column(Integer)
    funding_requirement: Mapped[str | None] = mapped_column(String(30))
    program_size_preference: Mapped[str | None] = mapped_column(String(20))
    career_goals: Mapped[list | None] = mapped_column(JSONB)
    values_priorities: Mapped[dict | None] = mapped_column(JSONB)
    dealbreakers: Mapped[list | None] = mapped_column(JSONB)
    goals_text: Mapped[str | None] = mapped_column(Text)
    career_goal_short_term: Mapped[str | None] = mapped_column(Text)
    # Appendix "preference weights" - 7 explicit 0-10 scales. Kept as
    # separate columns (not only the values_priorities JSONB) so matching
    # can read each dimension by name.
    weight_cost: Mapped[int | None] = mapped_column(Integer)
    weight_location: Mapped[int | None] = mapped_column(Integer)
    weight_outcomes: Mapped[int | None] = mapped_column(Integer)
    weight_ranking: Mapped[int | None] = mapped_column(Integer)
    weight_flexibility: Mapped[int | None] = mapped_column(Integer)
    weight_support: Mapped[int | None] = mapped_column(Integer)
    weight_time_to_degree: Mapped[int | None] = mapped_column(Integer)
    application_intensity: Mapped[str | None] = mapped_column(String(30))
    preferred_learning_style: Mapped[str | None] = mapped_column(String(30))
    preferred_program_style: Mapped[str | None] = mapped_column(String(30))
    research_interest_level: Mapped[str | None] = mapped_column(String(20))
    return_home_intent: Mapped[str | None] = mapped_column(String(20))
    risk_tolerance: Mapped[str | None] = mapped_column(String(20))
    stretch_target_safety_mix: Mapped[str | None] = mapped_column(String(50))
    target_degree_level: Mapped[str | None] = mapped_column(String(30))
    target_start_term: Mapped[str | None] = mapped_column(String(30))
    thesis_interest: Mapped[str | None] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    student: Mapped[StudentProfile] = relationship(back_populates="preferences")


class RecommendationRequest(Base):
    __tablename__ = "recommendation_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    recommender_name: Mapped[str] = mapped_column(String(255), nullable=False)
    recommender_email: Mapped[str | None] = mapped_column(String(255))
    recommender_title: Mapped[str | None] = mapped_column(String(255))
    recommender_institution: Mapped[str | None] = mapped_column(String(255))
    recommender_relationship: Mapped[str | None] = mapped_column("relationship", String(100))
    status: Mapped[str] = mapped_column(String(30), default="draft", nullable=False)
    requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    due_date: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)
    target_program_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    student: Mapped[StudentProfile] = relationship(back_populates="recommendation_requests")


class OnboardingProgress(Base):
    __tablename__ = "onboarding_progress"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    steps_completed: Mapped[list | None] = mapped_column(JSONB)
    completion_percentage: Mapped[int] = mapped_column(Integer, default=0)
    last_step_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    nudge_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    student: Mapped[StudentProfile] = relationship(back_populates="onboarding_progress")


class StudentOnlinePresence(Base):
    __tablename__ = "student_online_presence"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    platform_type: Mapped[str] = mapped_column(String(50), nullable=False)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    student: Mapped[StudentProfile] = relationship(back_populates="online_presence")


class StudentPortfolioItem(Base):
    __tablename__ = "student_portfolio_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    item_type: Mapped[str] = mapped_column(String(50), nullable=False)
    url: Mapped[str | None] = mapped_column(String(1000))
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_documents.id", ondelete="SET NULL"),
    )
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    student: Mapped[StudentProfile] = relationship(back_populates="portfolio_items")


class StudentResearch(Base):
    __tablename__ = "student_research"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    institution_lab: Mapped[str | None] = mapped_column(String(255))
    field_discipline: Mapped[str | None] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    advisor_name: Mapped[str | None] = mapped_column(String(255))
    methods_tools: Mapped[str | None] = mapped_column(Text)
    outcomes: Mapped[str | None] = mapped_column(Text)
    outputs: Mapped[str | None] = mapped_column(String(50))
    publication_link: Mapped[str | None] = mapped_column(String(1000))
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    student: Mapped[StudentProfile] = relationship(back_populates="research_entries")


class StudentLanguage(Base):
    __tablename__ = "student_languages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    language: Mapped[str] = mapped_column(String(100), nullable=False)
    proficiency_level: Mapped[str] = mapped_column(String(30), nullable=False)
    certification_type: Mapped[str | None] = mapped_column(String(100))
    certification_score: Mapped[str | None] = mapped_column(String(50))
    test_date: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    student: Mapped[StudentProfile] = relationship(back_populates="languages")


class StudentWorkExperience(Base):
    __tablename__ = "student_work_experiences"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    experience_type: Mapped[str] = mapped_column(String(50), nullable=False)
    organization: Mapped[str] = mapped_column(String(255), nullable=False)
    role_title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    hours_per_week: Mapped[int | None] = mapped_column(Integer)
    compensation_type: Mapped[str | None] = mapped_column(String(30))
    key_achievements: Mapped[str | None] = mapped_column(Text)
    supervisor_name: Mapped[str | None] = mapped_column(String(255))
    organization_country: Mapped[str | None] = mapped_column(String(100))
    organization_city: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    student: Mapped[StudentProfile] = relationship(back_populates="work_experiences")


class StudentCompetition(Base):
    __tablename__ = "student_competitions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    competition_name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str | None] = mapped_column(String(100))
    level: Mapped[str] = mapped_column(String(30), nullable=False)
    role: Mapped[str | None] = mapped_column(String(50))
    result_placement: Mapped[str | None] = mapped_column(String(100))
    year: Mapped[int | None] = mapped_column(Integer)
    team_size: Mapped[int | None] = mapped_column(Integer)
    description: Mapped[str | None] = mapped_column(Text)
    link_proof: Mapped[str | None] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    student: Mapped[StudentProfile] = relationship(back_populates="competitions")


class StudentAccommodation(Base):
    __tablename__ = "student_accommodations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    accommodations_needed: Mapped[bool] = mapped_column(Boolean, default=False)
    category: Mapped[str | None] = mapped_column(String(100))
    details_text: Mapped[str | None] = mapped_column(Text)
    documentation_status: Mapped[str | None] = mapped_column(String(30))
    dyslexia_friendly_mode: Mapped[bool] = mapped_column(Boolean, default=False)
    font_size_pref: Mapped[str | None] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    student: Mapped[StudentProfile] = relationship(back_populates="accommodations")


class StudentScheduling(Base):
    __tablename__ = "student_scheduling"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    timezone: Mapped[str | None] = mapped_column(String(50))
    general_availability: Mapped[dict | None] = mapped_column(JSONB)
    preferred_interview_format: Mapped[str | None] = mapped_column(String(30))
    campus_visit_interest: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    student: Mapped[StudentProfile] = relationship(back_populates="scheduling")


class StudentVisaInfo(Base):
    __tablename__ = "student_visa_info"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    current_immigration_status: Mapped[str | None] = mapped_column(String(50))
    visa_required: Mapped[bool] = mapped_column(Boolean, default=False)
    target_study_country: Mapped[str | None] = mapped_column(String(100))
    passport_expiration_date: Mapped[date | None] = mapped_column(Date)
    sponsorship_source: Mapped[str | None] = mapped_column(String(50))
    financial_proof_available: Mapped[bool] = mapped_column(Boolean, default=False)
    financial_proof_amount_band: Mapped[str | None] = mapped_column(String(50))
    post_study_work_interest: Mapped[bool] = mapped_column(Boolean, default=False)
    prior_visa_refusals: Mapped[bool] = mapped_column(Boolean, default=False)
    travel_constraints: Mapped[str | None] = mapped_column(Text)
    work_authorization_needed: Mapped[bool] = mapped_column(Boolean, default=False)
    current_location_city: Mapped[str | None] = mapped_column(String(100))
    current_location_country: Mapped[str | None] = mapped_column(String(100))
    dependents_accompanying: Mapped[bool | None] = mapped_column(Boolean)
    intended_start_term: Mapped[str | None] = mapped_column(String(30))
    visa_type_current: Mapped[str | None] = mapped_column(String(30))
    # Explicit citizenship for visa flow when it differs from the broader
    # `nationality` field on the profile (e.g., dual-citizen applying via a
    # specific passport).
    country_of_citizenship: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    student: Mapped[StudentProfile] = relationship(back_populates="visa_info")


class StudentDataConsent(Base):
    __tablename__ = "student_data_consent"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    consent_matching: Mapped[bool] = mapped_column(Boolean, default=True)
    consent_outreach: Mapped[bool] = mapped_column(Boolean, default=True)
    consent_research: Mapped[bool] = mapped_column(Boolean, default=True)
    data_retention_preference: Mapped[str | None] = mapped_column(String(30))
    deletion_requested: Mapped[bool] = mapped_column(Boolean, default=False)
    deletion_requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Appendix "Eligibility, compliance, consent" fields. All nullable so
    # legacy rows remain unaffected.
    first_generation_status: Mapped[bool | None] = mapped_column(Boolean)
    first_generation_definition: Mapped[str | None] = mapped_column(String(50))
    ferpa_release: Mapped[bool | None] = mapped_column(Boolean)
    honor_code_ack: Mapped[bool | None] = mapped_column(Boolean)
    background_check_required: Mapped[bool | None] = mapped_column(Boolean)
    code_of_conduct_ack: Mapped[bool | None] = mapped_column(Boolean)
    criminal_history_disclosed: Mapped[bool | None] = mapped_column(Boolean)
    disciplinary_history_disclosed: Mapped[bool | None] = mapped_column(Boolean)
    immunization_compliance: Mapped[str | None] = mapped_column(String(30))
    health_insurance_waiver_intent: Mapped[bool | None] = mapped_column(Boolean)
    military_status: Mapped[str | None] = mapped_column(String(30))
    veteran_status: Mapped[bool | None] = mapped_column(Boolean)
    prior_academic_dismissal_flag: Mapped[bool | None] = mapped_column(Boolean)
    directory_info_release: Mapped[bool | None] = mapped_column(Boolean)
    third_party_sharing_consent: Mapped[bool | None] = mapped_column(Boolean)
    # {email: bool, sms: bool, calls: bool}.
    marketing_channel_consent: Mapped[dict | None] = mapped_column(JSONB)
    # [{channel, timestamp, version}].
    consent_revocation_timestamps: Mapped[list | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    student: Mapped[StudentProfile] = relationship(back_populates="data_consent")


class StudentPlatformEvent(Base):
    """Broad analytics events (not program-scoped).

    Complements ``student_engagement_signals`` which is scoped to a specific
    program. This table captures platform-wide events like login, session,
    search queries, page views, CTA taps, drop-off steps, UTM campaign, device,
    IP country. Every row is tied to a student (no anonymous events here).
    Feeds the OUTPUT-side engagement signals (apply propensity, churn risk,
    drop-off diagnosis, next-best-action) in the inference pipeline.
    """

    __tablename__ = "student_platform_events"
    __table_args__ = (
        Index("ix_platform_events_student_type", "student_id", "event_type"),
        Index("ix_platform_events_occurred_at", "occurred_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    event_metadata: Mapped[dict | None] = mapped_column(JSONB)
    session_id: Mapped[str | None] = mapped_column(String(100))
    device_type: Mapped[str | None] = mapped_column(String(30))
    url_path: Mapped[str | None] = mapped_column(String(500))
    referral_source: Mapped[str | None] = mapped_column(String(100))
    utm_campaign: Mapped[str | None] = mapped_column(String(255))
    ip_country: Mapped[str | None] = mapped_column(String(100))
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class StudentMajorReadiness(Base):
    """Track-level self-rating rollup for major-specific appendix fields.

    One row per (student, track) where track is one of:
    ``cs``, ``engineering``, ``business``, ``health``, ``arts``, ``humanities``.

    ``readiness_data`` is a JSONB blob holding the per-track fields from the
    appendix (e.g., CS track has ~73 fields: CS fundamentals self-ratings,
    data/ML readiness, programming languages, tools, etc.). We keep them as
    JSONB because the field set varies by track and evolves; the blob is the
    authoritative store, the individual fields are validated at the Pydantic
    schema layer and scored in the inference pipeline.
    """

    __tablename__ = "student_major_readiness"
    __table_args__ = (
        UniqueConstraint("student_id", "track", name="uq_major_readiness_student_track"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    track: Mapped[str] = mapped_column(String(30), nullable=False)
    readiness_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

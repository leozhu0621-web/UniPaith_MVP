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
    Integer,
    Numeric,
    String,
    Text,
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
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    nationality: Mapped[str | None] = mapped_column(String(100))
    country_of_residence: Mapped[str | None] = mapped_column(String(100))
    bio_text: Mapped[str | None] = mapped_column(Text)
    goals_text: Mapped[str | None] = mapped_column(Text)
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
    gpa: Mapped[Decimal | None] = mapped_column(Numeric(4, 2))
    gpa_scale: Mapped[str | None] = mapped_column(String(20))
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    honors: Mapped[str | None] = mapped_column(String(255))
    thesis_title: Mapped[str | None] = mapped_column(String(500))
    country: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    student: Mapped[StudentProfile] = relationship(back_populates="academic_records")


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
    career_goals: Mapped[dict | None] = mapped_column(JSONB)
    values_priorities: Mapped[dict | None] = mapped_column(JSONB)
    dealbreakers: Mapped[dict | None] = mapped_column(JSONB)
    goals_text: Mapped[str | None] = mapped_column(Text)
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
    steps_completed: Mapped[dict | None] = mapped_column(JSONB)
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

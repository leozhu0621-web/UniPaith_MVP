from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Generic, Literal, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int


# --- Institution ---


class CreateInstitutionRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    type: Literal["university", "college", "technical_institute", "community_college"]
    country: str = Field(min_length=1, max_length=100)
    region: str | None = None
    city: str | None = None
    description_text: str | None = None
    campus_description: str | None = None
    campus_setting: Literal["urban", "suburban", "rural"] | None = None
    student_body_size: int | None = None
    contact_email: str | None = None
    logo_url: str | None = None
    website_url: str | None = None
    media_gallery: list[str] | None = None
    social_links: dict | None = None


class UpdateInstitutionRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    type: Literal["university", "college", "technical_institute", "community_college"] | None = None
    country: str | None = Field(None, min_length=1, max_length=100)
    region: str | None = None
    city: str | None = None
    description_text: str | None = None
    campus_description: str | None = None
    campus_setting: Literal["urban", "suburban", "rural"] | None = None
    student_body_size: int | None = None
    contact_email: str | None = None
    logo_url: str | None = None
    website_url: str | None = None
    media_gallery: list[str] | None = None
    social_links: dict | None = None


class InstitutionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    type: str
    country: str
    region: str | None
    city: str | None
    ranking_data: dict | None = None
    description_text: str | None
    campus_description: str | None = None
    campus_setting: str | None = None
    student_body_size: int | None = None
    contact_email: str | None = None
    logo_url: str | None
    website_url: str | None
    media_gallery: list | dict | None = None
    social_links: dict | None = None
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    program_count: int | None = None


# --- Program ---


class CreateProgramRequest(BaseModel):
    program_name: str = Field(min_length=1, max_length=255)
    degree_type: Literal["bachelors", "masters", "phd", "certificate", "diploma"]
    department: str | None = None
    duration_months: int | None = Field(None, ge=1, le=120)
    tuition: int | None = Field(None, ge=0)
    acceptance_rate: Decimal | None = Field(None, ge=0, le=1)
    delivery_format: Literal["in_person", "online", "hybrid"] | None = None
    campus_setting: Literal["urban", "suburban", "rural"] | None = None
    requirements: dict | None = None
    application_requirements: list[dict] | None = None
    description_text: str | None = None
    who_its_for: str | None = None
    application_deadline: date | None = None
    program_start_date: date | None = None
    tracks: list[str] | None = None
    outcomes_data: dict | None = None
    intake_rounds: list[dict] | None = None
    media_urls: list[str] | None = None
    highlights: list[str] | None = None
    faculty_contacts: list[dict] | None = None


class UpdateProgramRequest(BaseModel):
    program_name: str | None = Field(None, min_length=1, max_length=255)
    degree_type: Literal["bachelors", "masters", "phd", "certificate", "diploma"] | None = None
    department: str | None = None
    duration_months: int | None = Field(None, ge=1, le=120)
    tuition: int | None = Field(None, ge=0)
    acceptance_rate: Decimal | None = Field(None, ge=0, le=1)
    delivery_format: Literal["in_person", "online", "hybrid"] | None = None
    campus_setting: Literal["urban", "suburban", "rural"] | None = None
    requirements: dict | None = None
    application_requirements: list[dict] | None = None
    description_text: str | None = None
    who_its_for: str | None = None
    application_deadline: date | None = None
    program_start_date: date | None = None
    tracks: list[str] | None = None
    outcomes_data: dict | None = None
    intake_rounds: list[dict] | None = None
    media_urls: list[str] | None = None
    highlights: list[str] | None = None
    faculty_contacts: list[dict] | None = None


class ProgramResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    institution_id: UUID
    program_name: str
    degree_type: str
    department: str | None
    duration_months: int | None
    tuition: int | None
    acceptance_rate: Decimal | None
    delivery_format: str | None = None
    campus_setting: str | None = None
    requirements: dict | None
    application_requirements: list | dict | None = None
    description_text: str | None
    who_its_for: str | None = None
    is_published: bool
    application_deadline: date | None
    program_start_date: date | None
    tracks: list | dict | None = None
    outcomes_data: dict | None = None
    intake_rounds: list | dict | None = None
    media_urls: list | dict | None = None
    highlights: list | dict | None
    faculty_contacts: list | dict | None = None
    created_at: datetime
    updated_at: datetime


class ProgramSummaryResponse(BaseModel):
    id: UUID
    program_name: str
    degree_type: str
    department: str | None
    tuition: int | None
    application_deadline: date | None
    institution_name: str
    institution_country: str


# --- Target Segments ---


class CreateSegmentRequest(BaseModel):
    segment_name: str = Field(min_length=1, max_length=255)
    program_id: UUID | None = None
    criteria: dict
    is_active: bool = True


class UpdateSegmentRequest(BaseModel):
    segment_name: str | None = Field(None, min_length=1, max_length=255)
    program_id: UUID | None = None
    criteria: dict | None = None
    is_active: bool | None = None


class SegmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    institution_id: UUID
    program_id: UUID | None
    segment_name: str
    criteria: dict | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


# --- Dashboard Summary ---


class DashboardSummaryResponse(BaseModel):
    program_count: int
    published_program_count: int
    total_applications: int
    pending_review_count: int
    active_events_count: int
    unread_messages_count: int
    acceptance_rate: float | None = None
    yield_rate: float | None = None


# --- Analytics ---


class ProgramApplicationCount(BaseModel):
    program_name: str
    count: int


class MonthlyApplicationCount(BaseModel):
    month: str
    count: int


class AnalyticsResponse(BaseModel):
    total_applications: int
    acceptance_rate: float | None
    avg_match_score: float | None
    yield_rate: float | None
    apps_by_status: dict[str, int]
    apps_by_program: list[ProgramApplicationCount]
    apps_by_month: list[MonthlyApplicationCount]
    decisions_breakdown: dict[str, int]


# --- Campaigns ---


class CreateCampaignRequest(BaseModel):
    campaign_name: str = Field(min_length=1, max_length=255)
    campaign_type: str | None = None
    program_id: UUID | None = None
    segment_id: UUID | None = None
    message_subject: str | None = None
    message_body: str | None = None
    scheduled_send_at: datetime | None = None


class UpdateCampaignRequest(BaseModel):
    campaign_name: str | None = Field(None, min_length=1, max_length=255)
    campaign_type: str | None = None
    program_id: UUID | None = None
    segment_id: UUID | None = None
    message_subject: str | None = None
    message_body: str | None = None
    status: str | None = None
    scheduled_send_at: datetime | None = None


class CampaignResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    institution_id: UUID
    program_id: UUID | None
    segment_id: UUID | None
    campaign_name: str
    campaign_type: str | None
    message_subject: str | None
    message_body: str | None
    status: str | None
    scheduled_send_at: datetime | None
    sent_at: datetime | None
    created_at: datetime
    updated_at: datetime


class CampaignMetricsResponse(BaseModel):
    campaign_id: UUID
    total_recipients: int
    delivered: int
    opened: int
    clicked: int
    responded: int

"""Phase 5 — Pydantic schemas for the Data Crawler API."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ======================================================================
# Source schemas
# ======================================================================


class URLPatternInput(BaseModel):
    url_pattern: str
    page_type: str | None = None
    follow_links: bool = True
    link_selector: str | None = None
    requires_javascript: bool = False
    extraction_prompt_override: str | None = None


class CreateSourceRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    url: str = Field(..., min_length=1, max_length=1000)
    source_type: str = Field(..., max_length=20)
    category: str = Field(..., max_length=50)
    frequency_hours: int = Field(168, ge=1, le=8760)
    url_patterns: list[URLPatternInput] | None = None


class SourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source_name: str
    source_url: str | None
    source_type: str | None
    data_category: str | None
    crawl_frequency: str | None
    last_crawled_at: datetime | None
    reliability_score: Decimal | None
    is_active: bool
    created_at: datetime


class SourceListResponse(BaseModel):
    sources: list[SourceResponse]
    total: int


# ======================================================================
# Crawl job schemas
# ======================================================================


class CrawlJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source_id: UUID
    status: str
    pages_crawled: int
    pages_failed: int
    items_extracted: int
    items_ingested: int
    items_queued_for_review: int
    items_duplicate: int
    error_log: dict | list | None = None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


class CrawlJobListResponse(BaseModel):
    jobs: list[CrawlJobResponse]
    total: int


# ======================================================================
# Extracted program schemas
# ======================================================================


class ExtractedProgramResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    crawl_job_id: UUID
    source_id: UUID
    source_url: str | None
    institution_name: str | None
    program_name: str | None
    degree_type: str | None
    match_type: str | None
    review_status: str
    extraction_confidence: Decimal | None
    created_at: datetime


class ExtractedProgramDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    crawl_job_id: UUID
    source_id: UUID
    raw_data_id: UUID | None
    source_url: str | None

    institution_name: str | None
    institution_country: str | None
    institution_city: str | None
    institution_type: str | None
    institution_website: str | None

    program_name: str | None
    degree_type: str | None
    department: str | None
    duration_months: int | None
    tuition: int | None
    tuition_currency: str | None
    acceptance_rate: Decimal | None
    requirements: dict | None
    description_text: str | None
    application_deadline: date | None
    program_start_date: date | None
    highlights: dict | list | None = None
    faculty_contacts: dict | list | None = None
    rankings: dict | None
    financial_aid_info: dict | None

    extraction_confidence: Decimal | None
    field_confidences: dict | None
    extraction_model: str | None
    raw_extracted_json: dict | None

    matched_institution_id: UUID | None
    matched_program_id: UUID | None
    match_type: str | None

    review_status: str
    reviewed_by: UUID | None
    reviewed_at: datetime | None
    review_notes: str | None
    created_at: datetime


# ======================================================================
# Review schemas
# ======================================================================


class ReviewListResponse(BaseModel):
    items: list[ExtractedProgramResponse]
    total: int
    pending_count: int


class ReviewApproveRequest(BaseModel):
    edits: dict | None = None
    notes: str | None = None


class ReviewRejectRequest(BaseModel):
    reason: str | None = None


class ReviewStatsResponse(BaseModel):
    pending: int = 0
    approved: int = 0
    rejected: int = 0
    auto_ingested: int = 0


# ======================================================================
# Pipeline & misc schemas
# ======================================================================


class CrawlSingleURLRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=2000)
    source_id: UUID | None = None


class PipelineResultResponse(BaseModel):
    source_id: str | None = None
    source_name: str | None = None
    job_id: str | None = None
    status: str
    pages_crawled: int = 0
    pages_failed: int = 0
    items_extracted: int = 0
    deduplication: dict | None = None
    ingestion: dict | None = None
    error: str | None = None
    error_log: dict | list | None = None


class CrawlerDashboardResponse(BaseModel):
    active_sources: int
    total_jobs: int
    recent_jobs: list[CrawlJobResponse]
    pending_reviews: int
    review_stats: ReviewStatsResponse
    sources: list[SourceResponse]

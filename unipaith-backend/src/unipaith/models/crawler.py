"""Phase 5 — Data Crawler models.

Five new tables supporting the crawl-extract-deduplicate-ingest pipeline:
CrawlJob, ExtractedProgram, CrawlSchedule, SourceURLPattern, EnrichmentRecord.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
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
from sqlalchemy.orm import Mapped, mapped_column

from unipaith.models.base import Base


class CrawlJob(Base):
    """Tracks a single crawl execution against a data source."""

    __tablename__ = "crawl_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("data_sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    pages_crawled: Mapped[int] = mapped_column(Integer, default=0)
    pages_failed: Mapped[int] = mapped_column(Integer, default=0)
    items_extracted: Mapped[int] = mapped_column(Integer, default=0)
    items_ingested: Mapped[int] = mapped_column(Integer, default=0)
    items_queued_for_review: Mapped[int] = mapped_column(Integer, default=0)
    items_duplicate: Mapped[int] = mapped_column(Integer, default=0)
    error_log: Mapped[dict | None] = mapped_column(JSONB)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ExtractedProgram(Base):
    """Holds a program record extracted from crawled HTML before ingestion."""

    __tablename__ = "extracted_programs"
    __table_args__ = (
        Index("ix_extracted_programs_review", "review_status", "extraction_confidence"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    crawl_job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("crawl_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("data_sources.id", ondelete="CASCADE"),
        nullable=False,
    )
    raw_data_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("raw_ingested_data.id", ondelete="SET NULL"),
    )
    source_url: Mapped[str | None] = mapped_column(String(1000))

    # Institution fields
    institution_name: Mapped[str | None] = mapped_column(String(255))
    institution_country: Mapped[str | None] = mapped_column(String(100))
    institution_city: Mapped[str | None] = mapped_column(String(100))
    institution_type: Mapped[str | None] = mapped_column(String(50))
    institution_website: Mapped[str | None] = mapped_column(String(1000))

    # Program fields
    program_name: Mapped[str | None] = mapped_column(String(255))
    degree_type: Mapped[str | None] = mapped_column(String(30))
    department: Mapped[str | None] = mapped_column(String(255))
    duration_months: Mapped[int | None] = mapped_column(Integer)
    tuition: Mapped[int | None] = mapped_column(Integer)
    tuition_currency: Mapped[str | None] = mapped_column(String(10))
    acceptance_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    requirements: Mapped[dict | None] = mapped_column(JSONB)
    description_text: Mapped[str | None] = mapped_column(Text)
    application_deadline: Mapped[date | None] = mapped_column(Date)
    program_start_date: Mapped[date | None] = mapped_column(Date)
    highlights: Mapped[dict | None] = mapped_column(JSONB)
    faculty_contacts: Mapped[dict | None] = mapped_column(JSONB)
    rankings: Mapped[dict | None] = mapped_column(JSONB)
    financial_aid_info: Mapped[dict | None] = mapped_column(JSONB)

    # Extraction metadata
    extraction_confidence: Mapped[Decimal | None] = mapped_column(Numeric(3, 2))
    field_confidences: Mapped[dict | None] = mapped_column(JSONB)
    extraction_model: Mapped[str | None] = mapped_column(String(50))
    raw_extracted_json: Mapped[dict | None] = mapped_column(JSONB)

    # Matching / deduplication
    matched_institution_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="SET NULL"),
    )
    matched_program_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("programs.id", ondelete="SET NULL"),
    )
    match_type: Mapped[str | None] = mapped_column(String(20))  # new/update/duplicate/conflict

    # Review workflow
    review_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    review_notes: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class CrawlSchedule(Base):
    """Per-source crawl schedule with failure tracking."""

    __tablename__ = "crawl_schedules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("data_sources.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    frequency_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    next_run_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class SourceURLPattern(Base):
    """Describes URL patterns to crawl within a data source."""

    __tablename__ = "source_url_patterns"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("data_sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    url_pattern: Mapped[str] = mapped_column(String(1000), nullable=False)
    page_type: Mapped[str | None] = mapped_column(String(30))  # program_list/program_detail/department/ranking
    follow_links: Mapped[bool] = mapped_column(Boolean, default=True)
    link_selector: Mapped[str | None] = mapped_column(String(500))
    requires_javascript: Mapped[bool] = mapped_column(Boolean, default=False)
    extraction_prompt_override: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class EnrichmentRecord(Base):
    """Additional data enrichment applied to institutions or programs."""

    __tablename__ = "enrichment_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    program_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("programs.id", ondelete="SET NULL"),
    )
    institution_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="SET NULL"),
    )
    enrichment_type: Mapped[str] = mapped_column(String(30), nullable=False)  # ranking/stats/financial_aid/deadline
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("data_sources.id", ondelete="CASCADE"),
        nullable=False,
    )
    data: Mapped[dict | None] = mapped_column(JSONB)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(3, 2))
    effective_date: Mapped[date | None] = mapped_column(Date)
    expires_at: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

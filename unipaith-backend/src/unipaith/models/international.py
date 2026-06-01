"""Spec 38 — International Admissions (institution processing).

Institution-side records that sit *beside* the application and the student's
own visa signals (Spec 42 §3.3 / §4.3). These tables never feed matching or
ranking — visa / immigration status is operational only and is gated by the
fairness rules in Spec 46 §6 (enforced by the Spec-38 fairness contract test).

- ``InternationalProcessing`` — one row per application: credential evaluation,
  English-proficiency verification, country-requirement checklist, immigration
  document (I-20 / DS-2019), and visa-interview tracking.
- ``CountryRequirementPack`` — per-country requirement packs. A row with
  ``institution_id IS NULL`` is a platform default; an institution may override
  a country with its own pack.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from unipaith.models.base import Base


class InternationalProcessing(Base):
    """Spec 38 §4 — the ``InternationalProcessing`` record (one per application).

    All editable fields are institution-owned. The student-side inputs the
    reviewer also sees (raw GPA, financial-proof band, uploaded credential
    report, English test scores) are read live from the student profile — they
    are not duplicated here.
    """

    __tablename__ = "international_processing"
    __table_args__ = (
        UniqueConstraint("application_id", name="uq_intl_processing_application"),
        CheckConstraint(
            "credential_provider IS NULL OR credential_provider IN "
            "('WES','ECE','SpanTran','other')",
            name="ck_intl_credential_provider",
        ),
        CheckConstraint(
            "credential_status IN ('none','requested','in_progress','received','verified')",
            name="ck_intl_credential_status",
        ),
        CheckConstraint(
            "english_test IS NULL OR english_test IN ('TOEFL','IELTS','DET','PTE')",
            name="ck_intl_english_test",
        ),
        CheckConstraint(
            "immigration_doc_type IS NULL OR immigration_doc_type IN ('I-20','DS-2019')",
            name="ck_intl_immigration_doc_type",
        ),
        CheckConstraint(
            "immigration_doc_status IN ('not_started','drafted','issued','sent','received')",
            name="ck_intl_immigration_doc_status",
        ),
        CheckConstraint(
            "visa_outcome IS NULL OR visa_outcome IN ('pending','approved','denied')",
            name="ck_intl_visa_outcome",
        ),
        Index("ix_intl_processing_institution", "institution_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Denormalized for institution-scoped listing + audit ownership checks.
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
    )

    # ── §2.1 Credential evaluation ──────────────────────────────────────────
    credential_provider: Mapped[str | None] = mapped_column(String(20))
    credential_status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="none", default="none"
    )
    credential_report_ref: Mapped[str | None] = mapped_column(String(1000))
    # The institution's normalization decision (distinct from the student's
    # self-reported AcademicRecord.normalized_gpa). Reviewers see raw + this.
    credential_normalized_gpa: Mapped[Decimal | None] = mapped_column(Numeric(4, 2))
    # Human-readable source scale the normalization came from, e.g. "85/100",
    # "UK First", "IB 38". Surfaced as "Normalized GPA: 3.6 (from 85/100)".
    credential_source_scale: Mapped[str | None] = mapped_column(String(60))
    credential_notes: Mapped[str | None] = mapped_column(Text)

    # ── §2.2 English-proficiency verification ───────────────────────────────
    english_test: Mapped[str | None] = mapped_column(String(10))
    english_score: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    english_meets_minimum: Mapped[bool | None] = mapped_column(Boolean)
    english_waiver_eligible: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false", default=False
    )
    english_waiver_basis: Mapped[str | None] = mapped_column(String(255))

    # ── §2.3 Country-specific requirements ──────────────────────────────────
    # List of {item, status} where status ∈ pending/received/verified/waived.
    country_requirements: Mapped[list | None] = mapped_column(JSONB)

    # ── §2.4 Immigration document (I-20 / DS-2019) ──────────────────────────
    immigration_doc_type: Mapped[str | None] = mapped_column(String(10))
    immigration_doc_status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="not_started", default="not_started"
    )
    sevis_id: Mapped[str | None] = mapped_column(String(40))
    immigration_issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # SEVIS-batch-compatible field map snapshot produced at generation time. The
    # institution uploads this to SEVIS themselves (no direct SEVIS API).
    sevis_export: Mapped[dict | None] = mapped_column(JSONB)

    # ── §2.5 Visa-interview coordination ────────────────────────────────────
    visa_appointment_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    visa_consulate: Mapped[str | None] = mapped_column(String(120))
    visa_outcome: Mapped[str | None] = mapped_column(String(10))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class CountryRequirementPack(Base):
    """Spec 38 §2.3 — per-country requirement packs.

    ``institution_id IS NULL`` rows are platform defaults (seeded by the Spec-38
    migration); an institution can override a country with its own row. The
    service merges institution rows over defaults by ``country_code``.
    """

    __tablename__ = "country_requirement_packs"
    __table_args__ = (
        # Per-institution override is unique by country; platform defaults
        # (institution_id NULL) are unique by country via a partial index in
        # the migration (Postgres treats NULLs as distinct so a plain unique
        # constraint can't enforce that).
        UniqueConstraint("institution_id", "country_code", name="uq_country_pack_inst_country"),
        Index("ix_country_pack_country", "country_code"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    institution_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    # ISO 3166-1 alpha-2 country code (e.g. "CN", "IN"); matched case-insensitively
    # against the applicant's nationality / country_of_birth.
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    country_name: Mapped[str] = mapped_column(String(120), nullable=False)
    # List of {item, description?} requirement entries.
    requirements: Mapped[list | None] = mapped_column(JSONB)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true", default=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

"""Spec 43 — Major-Specific Field Catalog storage (Spec 42 §3.18 / §8).

One row per ``(student, track_key)``. The per-discipline readiness signals live
in the ``signals`` JSONB subdocument (Spec 43 §17: "one JSONB column per active
track… new tracks add a track_key + a field set; no schema migration"). Carries
the universal record metadata (Spec 42 §5, ``SignalRecordMixin``) like every
other signal store.

A track activates when the student's major maps to its ``track_key`` (Spec 43
§1, via ``services.major_track_catalog.infer_tracks_from_major``) or when the
student opts in explicitly. The §4.18 outputs (fit score, readiness band,
suggested artifacts, …) are derived from ``signals`` by the deterministic
``major_track_coach``; they are not stored here.

Supersedes the pre-spec ``student_major_readiness`` scaffold (raw 6-track store,
no provenance/scoring/registry) — its rows are migrated into this table by
``m43a1b2c3d4e``.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from unipaith.models.base import (
    SIGNAL_SOURCE_CHECK_SQL,
    Base,
    SignalRecordMixin,
)

# The 15 track_keys (Spec 43 §1). MUST stay in sync with
# ``services.major_track_catalog.TRACK_KEYS`` and the migration CHECK — the
# vocabulary is intentionally duplicated here (model layer) like the prompt
# library's controlled vocabularies, so the table self-documents its domain.
TRACK_KEYS: tuple[str, ...] = (
    "cs_data_ai",
    "engineering",
    "business",
    "health",
    "arts_design",
    "performing_arts",
    "humanities_social_sciences",
    "law_policy",
    "education_counseling",
    "journalism_communications",
    "math_physics_chemistry_sciences",
    "comp_engineering_robotics",
    "environmental_sustainability",
    "language_linguistics",
    "entrepreneurship_product",
)
TRACK_KEY_CHECK_SQL = "track_key IN (" + ",".join(f"'{k}'" for k in TRACK_KEYS) + ")"


class StudentMajorSpecificSignals(Base, SignalRecordMixin):
    """Per-(student, track) major-specific signal subdocument (Spec 43 §3.18)."""

    __tablename__ = "student_major_specific_signals"
    __table_args__ = (
        UniqueConstraint("student_id", "track_key", name="uq_student_major_specific_student_track"),
        CheckConstraint(TRACK_KEY_CHECK_SQL, name="ck_student_major_specific_track"),
        CheckConstraint(SIGNAL_SOURCE_CHECK_SQL, name="ck_student_major_specific_source"),
        Index("ix_student_major_specific_student", "student_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    track_key: Mapped[str] = mapped_column(String(40), nullable=False)
    # The track's field subdocument: {field_key: value}. Validated against the
    # catalog schema (services.major_track_catalog) at the service layer.
    signals: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

"""Phase A1 — LLM-only model storage.

The typed *durable artifacts* the Discovery LLM produces — goals, needs,
identity — live in `models/goals.py`, `models/needs.py`, and
`models/identity.py` (created in the parallel Phase-A discovery PRs #111
and #113). The LLM service layer writes to those tables with
`source='discovery'`; this module ships only the LLM-side companions:

  - StudentFeatureVector  — voyage-3-large embedding + sparse feature dict;
                            the ML matcher's input
  - AiTurn                — per-call cost / latency metering ledger; the
                            single source of truth for AI spend

Design notes
------------
- `StudentFeatureVector` is keyed by `student_id`, with `profile_version`
  for cache-bust. The embedding column is `VECTOR(1024)` in production
  (pgvector) and JSONB in dev DBs without the extension; the AI service
  layer round-trips list[float] in either case.
- `AiTurn` is written by `unipaith.ai.client.AIClient` and only by it.
  Direct Anthropic SDK use anywhere else in the codebase is a bug —
  bypasses the cost ledger and per-student cap.
- This module is imported by `unipaith.models.__init__` so the tables are
  registered on `Base.metadata` for Alembic autogenerate / app boot.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from unipaith.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

# ── Feature vectors (LLM emitter → ML matcher handoff) ──────────────────────


class StudentFeatureVector(Base, TimestampMixin):
    """Per-student dense embedding + sparse feature dict.

    Written by the A4 Feature Emitter at end-of-Discovery (and re-emitted on
    profile change). Read by the ML matcher (`unipaith.services.matching`).

    `embedding` uses voyage-3-large (1024 dims). The migration installs the
    pgvector type via `Vector(1024)`.
    `sparse_features` schema is defined in `unipaith.ai.tools.feature_schema`.
    `applicant_summary` is the 200-word LLM-written narrative used by the
    rationale agent (A5).

    Versioned by `profile_version`: any change to source profile fields bumps
    the version, which invalidates downstream caches (match_rationales).
    """

    __tablename__ = "student_feature_vectors"

    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        primary_key=True,
    )
    profile_version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default="1"
    )
    # NOTE: Vector column is added in the migration directly via raw DDL
    # because pgvector's Python type lives in a separate package that isn't
    # a hard dependency yet. The model exposes the column as JSONB at the
    # SQLAlchemy layer (read/write goes through the AI service layer, not
    # the ORM, so this is safe for now).
    embedding: Mapped[dict | None] = mapped_column(JSONB)
    sparse_features: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict, server_default="{}"
    )
    applicant_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    emitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


# ── Cost / latency metering ─────────────────────────────────────────────────


class AiTurn(Base, UUIDPrimaryKeyMixin):
    """One row per LLM/embedding call. The cost ledger.

    Every Anthropic and Voyage request writes one row. The `unipaith.ai.client`
    wrapper is the only writer. Used for:
      - per-student cost cap enforcement (§10 of the plan)
      - cache-hit-rate dashboards
      - p50/p95 latency monitoring
      - cost-by-agent breakdown for budget reviews

    Loosely linked to discovery_messages by `discovery_message_id`. Workshop
    coach calls and rationale calls have NULL there but populate `surface`.
    """

    __tablename__ = "ai_turns"
    __table_args__ = (
        CheckConstraint(
            "role IN ('user','assistant','tool','system')",
            name="ck_ai_turns_role",
        ),
        CheckConstraint(
            "agent IN ('orchestrator','extractor','validator','feature_emitter',"
            "'rationale','workshop_coach','workshop_judge','embedding')",
            name="ck_ai_turns_agent",
        ),
        Index("ix_ai_turns_student_created", "student_id", "created_at"),
        Index("ix_ai_turns_agent_created", "agent", "created_at"),
    )

    student_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="SET NULL"),
        nullable=True,
    )
    discovery_message_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("discovery_messages.id", ondelete="SET NULL"),
        nullable=True,
    )
    agent: Mapped[str] = mapped_column(String(30), nullable=False)
    surface: Mapped[str | None] = mapped_column(String(40))
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    model: Mapped[str] = mapped_column(String(60), nullable=False)
    input_tokens: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    output_tokens: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    cache_read_tokens: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    cache_creation_tokens: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    cost_usd: Mapped[Decimal] = mapped_column(
        Numeric(10, 6), nullable=False, default=Decimal("0"), server_default="0"
    )
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

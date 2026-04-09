"""Knowledge engine models.

Tables for the perpetual knowledge engine:
- KnowledgeDocument: any processed knowledge from any source/format
- KnowledgeLink: connects knowledge to entities
- CrawlFrontier: URLs/endpoints to visit with priority and domain rate limiting
- EngineDirective: admin steering instructions
- InteractionSignal: every user behavior with context
- PersonInsight: AI's evolving understanding of each person
- AdvisorPersona: tunable advisor personality configuration
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from unipaith.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class KnowledgeDocument(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "knowledge_documents"

    source_url: Mapped[str | None] = mapped_column(Text)
    source_domain: Mapped[str | None] = mapped_column(String(500))
    content_format: Mapped[str] = mapped_column(
        String(50),
        default="webpage",
    )
    content_type: Mapped[str | None] = mapped_column(String(100))

    title: Mapped[str | None] = mapped_column(Text)
    raw_text: Mapped[str | None] = mapped_column(Text)
    extracted_text: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)
    extracted_entities: Mapped[dict | None] = mapped_column(JSONB)
    extracted_facts: Mapped[dict | None] = mapped_column(JSONB)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB)

    embedding = mapped_column(Vector(1536), nullable=True)

    quality_score: Mapped[float | None] = mapped_column(Float)
    credibility_score: Mapped[float | None] = mapped_column(Float)
    relevance_score: Mapped[float | None] = mapped_column(Float)

    language: Mapped[str | None] = mapped_column(String(10))
    word_count: Mapped[int | None] = mapped_column(Integer)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    processing_status: Mapped[str] = mapped_column(String(30), default="pending")
    processing_error: Mapped[str | None] = mapped_column(Text)

    # use_alter breaks crawl_frontier <-> knowledge_documents cycle
    # so create_all/drop_all work in tests
    crawl_frontier_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("crawl_frontier.id", ondelete="SET NULL", use_alter=True),
    )

    __table_args__ = (
        Index("ix_knowledge_documents_source_domain", "source_domain"),
        Index("ix_knowledge_documents_content_format", "content_format"),
        Index("ix_knowledge_documents_content_type", "content_type"),
        Index("ix_knowledge_documents_processing_status", "processing_status"),
        Index("ix_knowledge_documents_quality", "quality_score"),
        Index("ix_knowledge_documents_ingested_at", "ingested_at"),
    )


class KnowledgeLink(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "knowledge_links"

    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("knowledge_documents.id", ondelete="CASCADE"),
    )
    entity_type: Mapped[str] = mapped_column(String(50))
    entity_id: Mapped[UUID | None] = mapped_column()
    entity_name: Mapped[str | None] = mapped_column(String(500))
    relationship_type: Mapped[str] = mapped_column(String(50), default="mentions")
    confidence: Mapped[float] = mapped_column(Float, default=0.5)

    __table_args__ = (
        Index("ix_knowledge_links_document_id", "document_id"),
        Index("ix_knowledge_links_entity", "entity_type", "entity_id"),
        Index("ix_knowledge_links_entity_name", "entity_name"),
    )


class CrawlFrontier(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "crawl_frontier"

    url: Mapped[str] = mapped_column(Text, unique=True)
    domain: Mapped[str] = mapped_column(String(500))
    priority: Mapped[int] = mapped_column(Integer, default=50)
    content_format_hint: Mapped[str | None] = mapped_column(String(50))

    discovered_from_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("knowledge_documents.id", ondelete="SET NULL"),
    )
    discovery_method: Mapped[str | None] = mapped_column(String(50))

    status: Mapped[str] = mapped_column(String(30), default="pending")
    last_crawled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_crawl_after: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    crawl_count: Mapped[int] = mapped_column(Integer, default=0)
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text)

    domain_crawl_delay_seconds: Mapped[int] = mapped_column(Integer, default=2)
    max_depth: Mapped[int] = mapped_column(Integer, default=3)
    respect_robots: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = (
        Index("ix_crawl_frontier_status_priority", "status", "priority"),
        Index("ix_crawl_frontier_domain", "domain"),
        Index("ix_crawl_frontier_next_crawl", "next_crawl_after"),
    )


class EngineLoopSnapshot(Base, TimestampMixin):
    """Singleton row (id=1) persisted each knowledge-engine tick for cross-worker admin truth."""

    __tablename__ = "engine_loop_snapshot"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    last_tick_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_processed: Mapped[int] = mapped_column(Integer, default=0)
    last_errors: Mapped[int] = mapped_column(Integer, default=0)
    last_discovered: Mapped[int] = mapped_column(Integer, default=0)
    last_skipped: Mapped[int] = mapped_column(Integer, default=0)
    last_bootstrap_added: Mapped[int] = mapped_column(Integer, default=0)
    frontier_pending_before: Mapped[int] = mapped_column(Integer, default=0)
    frontier_pending_after: Mapped[int] = mapped_column(Integer, default=0)
    batch_was_empty: Mapped[bool] = mapped_column(Boolean, default=True)
    tick_status: Mapped[str] = mapped_column(String(30), default="pending")
    last_error_message: Mapped[str | None] = mapped_column(Text)
    cumulative_processed: Mapped[int] = mapped_column(Integer, default=0)
    cumulative_errors: Mapped[int] = mapped_column(Integer, default=0)
    ai_mock_mode: Mapped[bool] = mapped_column(Boolean, default=False)
    gpu_mode: Mapped[str] = mapped_column(String(20), default="openai")


class EngineDirective(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "engine_directives"

    directive_type: Mapped[str] = mapped_column(String(50))
    directive_key: Mapped[str] = mapped_column(String(200))
    directive_value: Mapped[dict] = mapped_column(JSONB, default=dict)
    description: Mapped[str | None] = mapped_column(Text)

    priority: Mapped[int] = mapped_column(Integer, default=50)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
    )

    __table_args__ = (
        UniqueConstraint("directive_type", "directive_key", name="uq_directive_type_key"),
        Index("ix_engine_directives_active", "is_active", "directive_type"),
    )


class InteractionSignal(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "interaction_signals"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    signal_type: Mapped[str] = mapped_column(String(50))
    entity_type: Mapped[str | None] = mapped_column(String(50))
    entity_id: Mapped[UUID | None] = mapped_column()

    context: Mapped[dict | None] = mapped_column(JSONB)
    value: Mapped[float | None] = mapped_column(Float)
    session_id: Mapped[str | None] = mapped_column(String(100))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )

    __table_args__ = (
        Index("ix_interaction_signals_user", "user_id", "signal_type"),
        Index("ix_interaction_signals_entity", "entity_type", "entity_id"),
        Index("ix_interaction_signals_created", "created_at"),
    )


class PersonInsight(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "person_insights"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    insight_type: Mapped[str] = mapped_column(String(50))
    insight_text: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    evidence_turns: Mapped[list | None] = mapped_column(JSONB)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    source: Mapped[str] = mapped_column(String(50), default="conversation")
    superseded_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("person_insights.id", ondelete="SET NULL"),
    )

    __table_args__ = (
        Index("ix_person_insights_user_active", "user_id", "is_active"),
        Index("ix_person_insights_user_type", "user_id", "insight_type"),
    )


class AdvisorPersona(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "advisor_personas"

    name: Mapped[str] = mapped_column(String(200), default="default")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    warmth: Mapped[int] = mapped_column(Integer, default=80)
    directness: Mapped[int] = mapped_column(Integer, default=50)
    formality: Mapped[int] = mapped_column(Integer, default=30)
    challenge_level: Mapped[int] = mapped_column(Integer, default=40)
    data_reference_frequency: Mapped[int] = mapped_column(Integer, default=25)
    humor: Mapped[int] = mapped_column(Integer, default=20)
    proactivity: Mapped[int] = mapped_column(Integer, default=60)
    empathy_depth: Mapped[int] = mapped_column(Integer, default=85)

    custom_instructions: Mapped[str | None] = mapped_column(Text)
    base_persona_prompt: Mapped[str | None] = mapped_column(Text)

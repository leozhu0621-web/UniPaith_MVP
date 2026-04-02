"""add knowledge engine tables

Revision ID: c3a7f9e1d502
Revises: b8d4e2a1c9f0
Create Date: 2026-04-02
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "c3a7f9e1d502"
down_revision: Union[str, None] = "b8d4e2a1c9f0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "crawl_frontier",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("domain", sa.String(500), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("content_format_hint", sa.String(50), nullable=True),
        sa.Column("discovered_from_id", sa.Uuid(), nullable=True),
        sa.Column("discovery_method", sa.String(50), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("last_crawled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_crawl_after", sa.DateTime(timezone=True), nullable=True),
        sa.Column("crawl_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("consecutive_failures", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("domain_crawl_delay_seconds", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("max_depth", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("respect_robots", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("url"),
    )
    op.create_index("ix_crawl_frontier_status_priority", "crawl_frontier", ["status", "priority"])
    op.create_index("ix_crawl_frontier_domain", "crawl_frontier", ["domain"])
    op.create_index("ix_crawl_frontier_next_crawl", "crawl_frontier", ["next_crawl_after"])

    op.create_table(
        "knowledge_documents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("source_domain", sa.String(500), nullable=True),
        sa.Column("content_format", sa.String(50), nullable=False, server_default="webpage"),
        sa.Column("content_type", sa.String(100), nullable=True),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("extracted_entities", postgresql.JSONB(), nullable=True),
        sa.Column("extracted_facts", postgresql.JSONB(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=True),
        sa.Column("quality_score", sa.Float(), nullable=True),
        sa.Column("credibility_score", sa.Float(), nullable=True),
        sa.Column("relevance_score", sa.Float(), nullable=True),
        sa.Column("language", sa.String(10), nullable=True),
        sa.Column("word_count", sa.Integer(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ingested_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("processing_status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("processing_error", sa.Text(), nullable=True),
        sa.Column("crawl_frontier_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["crawl_frontier_id"], ["crawl_frontier.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute(
        "ALTER TABLE knowledge_documents ADD COLUMN IF NOT EXISTS embedding vector(1536)"
    )
    op.create_index("ix_knowledge_documents_source_domain", "knowledge_documents", ["source_domain"])
    op.create_index("ix_knowledge_documents_content_format", "knowledge_documents", ["content_format"])
    op.create_index("ix_knowledge_documents_content_type", "knowledge_documents", ["content_type"])
    op.create_index("ix_knowledge_documents_processing_status", "knowledge_documents", ["processing_status"])
    op.create_index("ix_knowledge_documents_quality", "knowledge_documents", ["quality_score"])
    op.create_index("ix_knowledge_documents_ingested_at", "knowledge_documents", ["ingested_at"])

    op.create_table(
        "knowledge_links",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=True),
        sa.Column("entity_name", sa.String(500), nullable=True),
        sa.Column("relationship_type", sa.String(50), nullable=False, server_default="mentions"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["knowledge_documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_knowledge_links_document_id", "knowledge_links", ["document_id"])
    op.create_index("ix_knowledge_links_entity", "knowledge_links", ["entity_type", "entity_id"])
    op.create_index("ix_knowledge_links_entity_name", "knowledge_links", ["entity_name"])

    op.create_table(
        "engine_directives",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("directive_type", sa.String(50), nullable=False),
        sa.Column("directive_key", sa.String(200), nullable=False),
        sa.Column("directive_value", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("directive_type", "directive_key", name="uq_directive_type_key"),
    )
    op.create_index("ix_engine_directives_active", "engine_directives", ["is_active", "directive_type"])

    op.create_table(
        "interaction_signals",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("signal_type", sa.String(50), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=True),
        sa.Column("entity_id", sa.Uuid(), nullable=True),
        sa.Column("context", postgresql.JSONB(), nullable=True),
        sa.Column("value", sa.Float(), nullable=True),
        sa.Column("session_id", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_interaction_signals_user", "interaction_signals", ["user_id", "signal_type"])
    op.create_index("ix_interaction_signals_entity", "interaction_signals", ["entity_type", "entity_id"])
    op.create_index("ix_interaction_signals_created", "interaction_signals", ["created_at"])

    op.create_table(
        "person_insights",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("insight_type", sa.String(50), nullable=False),
        sa.Column("insight_text", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("evidence_turns", postgresql.JSONB(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("source", sa.String(50), nullable=False, server_default="conversation"),
        sa.Column("superseded_by_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["superseded_by_id"], ["person_insights.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_person_insights_user_active", "person_insights", ["user_id", "is_active"])
    op.create_index("ix_person_insights_user_type", "person_insights", ["user_id", "insight_type"])

    op.create_table(
        "advisor_personas",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False, server_default="default"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("warmth", sa.Integer(), nullable=False, server_default="80"),
        sa.Column("directness", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("formality", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("challenge_level", sa.Integer(), nullable=False, server_default="40"),
        sa.Column("data_reference_frequency", sa.Integer(), nullable=False, server_default="25"),
        sa.Column("humor", sa.Integer(), nullable=False, server_default="20"),
        sa.Column("proactivity", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("empathy_depth", sa.Integer(), nullable=False, server_default="85"),
        sa.Column("custom_instructions", sa.Text(), nullable=True),
        sa.Column("base_persona_prompt", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.execute("""
        INSERT INTO advisor_personas (id, name, is_active, base_persona_prompt)
        VALUES (
            gen_random_uuid(),
            'default',
            true,
            'You are a warm, empathetic college advisor. You lead with understanding, not data. You help students build self-awareness about what they truly want before recommending programs. You remember everything about the student and reference previous conversations naturally. You never sound like a search engine or a database. When you need to deliver hard truths, you do it with care. You are persuasive when it matters — if a student is making a mistake, you say so warmly but firmly.'
        )
    """)


def downgrade() -> None:
    op.drop_table("advisor_personas")
    op.drop_table("person_insights")
    op.drop_table("interaction_signals")
    op.drop_table("engine_directives")
    op.drop_table("knowledge_links")
    op.drop_table("knowledge_documents")
    op.drop_table("crawl_frontier")

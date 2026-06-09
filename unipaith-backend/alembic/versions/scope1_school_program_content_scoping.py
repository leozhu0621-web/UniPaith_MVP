"""school/program content scoping: school_id, program_id, content_sources

Adds ``school_id`` to events + institution_posts, ``program_id`` to
institution_posts, and ``content_sources`` JSONB to schools + programs, then
widens the source-dedupe unique index to include scope. ``NULLS NOT DISTINCT``
(PG15+; RDS is PG16) keeps institution-scope rows (NULL scope) deduping
correctly while letting the same external_id exist once per scope (e.g. a
Sloan article on both MIT's institution feed and Sloan's school feed).

Revision ID: scope1
Revises: campusinfo1
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision = "scope1"
down_revision = "campusinfo1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Scope columns
    op.add_column("events", sa.Column("school_id", UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_events_school_id", "events", "schools", ["school_id"], ["id"], ondelete="SET NULL"
    )
    op.create_index("ix_events_school_id", "events", ["school_id"])

    op.add_column("institution_posts", sa.Column("school_id", UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_institution_posts_school_id",
        "institution_posts",
        "schools",
        ["school_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_institution_posts_school_id", "institution_posts", ["school_id"])

    op.add_column("institution_posts", sa.Column("program_id", UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_institution_posts_program_id",
        "institution_posts",
        "programs",
        ["program_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_institution_posts_program_id", "institution_posts", ["program_id"])

    # content_sources on schools + programs (mirrors institutions.content_sources)
    op.add_column("schools", sa.Column("content_sources", JSONB, nullable=True))
    op.add_column("programs", sa.Column("content_sources", JSONB, nullable=True))

    # Widen the source-dedupe unique index to include scope.
    op.drop_index("ix_events_source_dedup", table_name="events")
    op.create_index(
        "ix_events_source_dedup",
        "events",
        ["institution_id", "source", "external_id", "school_id", "program_id"],
        unique=True,
        postgresql_where=sa.text("external_id IS NOT NULL"),
        postgresql_nulls_not_distinct=True,
    )
    op.drop_index("ix_institution_posts_source_dedup", table_name="institution_posts")
    op.create_index(
        "ix_institution_posts_source_dedup",
        "institution_posts",
        ["institution_id", "source", "external_id", "school_id", "program_id"],
        unique=True,
        postgresql_where=sa.text("external_id IS NOT NULL"),
        postgresql_nulls_not_distinct=True,
    )


def downgrade() -> None:
    op.drop_index("ix_institution_posts_source_dedup", table_name="institution_posts")
    op.create_index(
        "ix_institution_posts_source_dedup",
        "institution_posts",
        ["institution_id", "source", "external_id"],
        unique=True,
        postgresql_where=sa.text("external_id IS NOT NULL"),
    )
    op.drop_index("ix_events_source_dedup", table_name="events")
    op.create_index(
        "ix_events_source_dedup",
        "events",
        ["institution_id", "source", "external_id"],
        unique=True,
        postgresql_where=sa.text("external_id IS NOT NULL"),
    )

    op.drop_column("programs", "content_sources")
    op.drop_column("schools", "content_sources")

    op.drop_index("ix_institution_posts_program_id", table_name="institution_posts")
    op.drop_constraint("fk_institution_posts_program_id", "institution_posts", type_="foreignkey")
    op.drop_column("institution_posts", "program_id")
    op.drop_index("ix_institution_posts_school_id", table_name="institution_posts")
    op.drop_constraint("fk_institution_posts_school_id", "institution_posts", type_="foreignkey")
    op.drop_column("institution_posts", "school_id")
    op.drop_index("ix_events_school_id", table_name="events")
    op.drop_constraint("fk_events_school_id", "events", type_="foreignkey")
    op.drop_column("events", "school_id")

"""channel-sourced events/updates: content_sources + source provenance

Adds `institutions.content_sources` (feed config) and source/external_id/
source_url to `events` + `institution_posts` (with a partial-unique dedupe
index), then re-applies the MIT profile to seed MIT's public feeds.

Revision ID: contentsrc1
Revises: campusphoto1
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import mit_profile

revision = "contentsrc1"
down_revision = "campusphoto1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("institutions", sa.Column("content_sources", JSONB, nullable=True))
    for table in ("events", "institution_posts"):
        op.add_column(
            table,
            sa.Column("source", sa.String(length=24), nullable=False, server_default="manual"),
        )
        op.add_column(table, sa.Column("external_id", sa.String(length=500), nullable=True))
        op.add_column(table, sa.Column("source_url", sa.String(length=1000), nullable=True))
        op.create_index(
            f"ix_{table}_source_dedup",
            table,
            ["institution_id", "source", "external_id"],
            unique=True,
            postgresql_where=sa.text("external_id IS NOT NULL"),
        )
    # Seed MIT's content_sources (idempotent re-apply), then best-effort populate
    # MIT's Events/Updates from those feeds (fail-soft — a slow/down feed won't
    # break the migration).
    from sqlalchemy import select

    from unipaith.models.institution import Institution
    from unipaith.services.content_ingest.service import seed_populate_sync

    session = Session(bind=op.get_bind())
    mit_profile.apply(session)
    mit = session.scalar(
        select(Institution).where(Institution.name == mit_profile.INSTITUTION_NAME)
    )
    if mit is not None:
        seed_populate_sync(session, mit)


def downgrade() -> None:
    for table in ("events", "institution_posts"):
        op.drop_index(f"ix_{table}_source_dedup", table_name=table)
        op.drop_column(table, "source_url")
        op.drop_column(table, "external_id")
        op.drop_column(table, "source")
    op.drop_column("institutions", "content_sources")

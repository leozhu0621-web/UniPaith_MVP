"""student_program_reviews: nullable student_id + external_source JSONB

Reviews seeded from authoritative external sources (NYU Stories, Niche,
bulletin publications) do not have an owning UniPaith user - the existing
NOT NULL student_id FK blocks ingesting them. This migration:

- Makes student_program_reviews.student_id nullable.
- Adds student_program_reviews.external_source JSONB for attribution
  ({source, source_url, author_handle, retrieved_at}).

Revision ID: 2a5f8c1d9e3b
Revises: 1499ba1b4c8a
Create Date: 2026-04-17 00:00:00.000000

"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "2a5f8c1d9e3b"
down_revision = "1499ba1b4c8a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "student_program_reviews",
        "student_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=True,
    )
    op.add_column(
        "student_program_reviews",
        sa.Column("external_source", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("student_program_reviews", "external_source")
    op.alter_column(
        "student_program_reviews",
        "student_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )

"""add institution_datasets table

Revision ID: a1b2c3d4e5f6
Revises: cce471db5933
Create Date: 2026-04-08
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "a1b2c3d4e5f6"
down_revision = "cce471db5933"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "institution_datasets",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("institution_id", UUID(as_uuid=True),
                  sa.ForeignKey("institutions.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("dataset_name", sa.String(255), nullable=False),
        sa.Column("dataset_type", sa.String(50), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("s3_key", sa.String(1000), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("file_size_bytes", sa.Integer()),
        sa.Column("row_count", sa.Integer()),
        sa.Column("column_mapping", JSONB()),
        sa.Column("validation_errors", JSONB()),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("usage_scope", sa.String(50)),
        sa.Column("version", sa.Integer(), server_default="1"),
        sa.Column("uploaded_by", UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("institution_datasets")

"""Spec 24 — dataset versions, mapping templates, coverage dates

Revision ID: d4e5f6a7b8c0
Revises: a8263041209b
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision = "d4e5f6a7b8c0"  # pragma: allowlist secret
down_revision = "a8263041209b"  # pragma: allowlist secret
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "institution_datasets",
        sa.Column("coverage_start", sa.Date(), nullable=True),
    )
    op.add_column(
        "institution_datasets",
        sa.Column("coverage_end", sa.Date(), nullable=True),
    )

    op.create_table(
        "institution_dataset_versions",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column(
            "dataset_id",
            UUID(as_uuid=True),
            sa.ForeignKey("institution_datasets.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("s3_key", sa.String(1000), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("row_count", sa.Integer()),
        sa.Column("column_mapping", JSONB()),
        sa.Column(
            "changes_summary", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")
        ),
        sa.Column("validation_report", JSONB()),
        sa.Column(
            "uploaded_by",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_dataset_versions_dataset_id",
        "institution_dataset_versions",
        ["dataset_id"],
    )

    op.create_table(
        "institution_dataset_mapping_templates",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column(
            "institution_id",
            UUID(as_uuid=True),
            sa.ForeignKey("institutions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("template_name", sa.String(255), nullable=False),
        sa.Column("dataset_type", sa.String(50), nullable=False),
        sa.Column("column_mapping", JSONB(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_dataset_mapping_templates_institution",
        "institution_dataset_mapping_templates",
        ["institution_id", "dataset_type"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_dataset_mapping_templates_institution",
        table_name="institution_dataset_mapping_templates",
    )
    op.drop_table("institution_dataset_mapping_templates")
    op.drop_index("ix_dataset_versions_dataset_id", table_name="institution_dataset_versions")
    op.drop_table("institution_dataset_versions")
    op.drop_column("institution_datasets", "coverage_end")
    op.drop_column("institution_datasets", "coverage_start")

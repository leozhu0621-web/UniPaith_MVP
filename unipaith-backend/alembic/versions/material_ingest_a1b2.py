"""Material ingest — material_ingests table.

Records uploaded materials, the AI's structured reading, and what the student
confirmed into My Space. Guarded so it is a safe no-op against the conftest
``create_all`` test DB and idempotent on re-run.

Revision ID: material_ingest_a1b2
Revises: chicagoprof6
Create Date: 2026-06-16
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision = "material_ingest_a1b2"  # pragma: allowlist secret
down_revision = "chicagoprof6"  # pragma: allowlist secret
branch_labels = None
depends_on = None


def _has_table(name: str) -> bool:
    return name in sa.inspect(op.get_bind()).get_table_names()


def upgrade() -> None:
    if _has_table("material_ingests"):
        return
    op.create_table(
        "material_ingests",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "student_id",
            UUID(as_uuid=True),
            sa.ForeignKey("student_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("filename", sa.String(length=512)),
        sa.Column("mime_type", sa.String(length=128)),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="parsed"),
        sa.Column("proposed", JSONB),
        sa.Column("applied_summary", JSONB),
        sa.Column("error", sa.Text()),
        sa.Column("applied_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint(
            "status IN ('parsed','applied','failed')",
            name="ck_material_ingests_status",
        ),
    )
    op.create_index("ix_material_ingests_student", "material_ingests", ["student_id"])


def downgrade() -> None:
    if _has_table("material_ingests"):
        op.drop_index("ix_material_ingests_student", table_name="material_ingests")
        op.drop_table("material_ingests")

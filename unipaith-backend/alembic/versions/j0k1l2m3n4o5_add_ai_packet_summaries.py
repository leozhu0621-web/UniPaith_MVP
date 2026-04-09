"""add ai packet summaries

Revision ID: j0k1l2m3n4o5
Revises: i9j0k1l2m3n4
Create Date: 2026-04-09 08:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "j0k1l2m3n4o5"
down_revision = "i9j0k1l2m3n4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_packet_summaries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "application_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("applications.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "institution_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("institutions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "rubric_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("rubrics.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("overall_summary", sa.Text, nullable=False),
        sa.Column("strengths", postgresql.JSONB, nullable=True),
        sa.Column("concerns", postgresql.JSONB, nullable=True),
        sa.Column("criterion_assessments", postgresql.JSONB, nullable=True),
        sa.Column("recommended_score", sa.Numeric(6, 3), nullable=True),
        sa.Column("confidence_level", sa.String(20), nullable=True),
        sa.Column("model_used", sa.String(100), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("ai_packet_summaries")

"""add intake rounds table

Revision ID: h8i9j0k1l2m3
Revises: g7h8i9j0k1l2
Create Date: 2026-04-09 06:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "h8i9j0k1l2m3"
down_revision = "g7h8i9j0k1l2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "intake_rounds",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "program_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("programs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("round_name", sa.String(100), nullable=False),
        sa.Column("intake_term", sa.String(50), nullable=True),
        sa.Column("application_open", sa.Date, nullable=True),
        sa.Column("application_deadline", sa.Date, nullable=True),
        sa.Column("decision_date", sa.Date, nullable=True),
        sa.Column("program_start", sa.Date, nullable=True),
        sa.Column("capacity", sa.Integer, nullable=True),
        sa.Column(
            "enrolled_count", sa.Integer, server_default="0", nullable=False,
        ),
        sa.Column("requirements", postgresql.JSONB, nullable=True),
        sa.Column(
            "status",
            sa.String(20),
            server_default="upcoming",
            nullable=False,
        ),
        sa.Column(
            "is_active", sa.Boolean, server_default="true", nullable=False,
        ),
        sa.Column(
            "sort_order", sa.Integer, server_default="0", nullable=False,
        ),
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
    op.create_index(
        "ix_intake_rounds_program", "intake_rounds", ["program_id"],
    )


def downgrade() -> None:
    op.drop_table("intake_rounds")

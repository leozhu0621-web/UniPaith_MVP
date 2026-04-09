"""add inquiries table and inquiry_routing column

Revision ID: d4e5f6g7h8i9
Revises: c3d4e5f6g7h8
Create Date: 2026-04-09 02:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "d4e5f6g7h8i9"
down_revision = "c3d4e5f6g7h8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "institutions",
        sa.Column("inquiry_routing", postgresql.JSONB, nullable=True),
    )

    op.create_table(
        "inquiries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "institution_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("institutions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "program_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("programs.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("student_profiles.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("student_name", sa.String(255), nullable=False),
        sa.Column("student_email", sa.String(255), nullable=False),
        sa.Column("subject", sa.String(500), nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column(
            "inquiry_type", sa.String(30), server_default="general", nullable=False,
        ),
        sa.Column(
            "status", sa.String(20), server_default="new", nullable=False,
        ),
        sa.Column(
            "assigned_to",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("response_text", sa.Text, nullable=True),
        sa.Column(
            "responded_at", sa.DateTime(timezone=True), nullable=True,
        ),
        sa.Column(
            "campaign_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("campaigns.id", ondelete="SET NULL"),
            nullable=True,
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
        "ix_inquiries_institution_status",
        "inquiries",
        ["institution_id", "status"],
    )


def downgrade() -> None:
    op.drop_table("inquiries")
    op.drop_column("institutions", "inquiry_routing")

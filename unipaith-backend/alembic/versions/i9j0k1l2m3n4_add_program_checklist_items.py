"""add program checklist items

Revision ID: i9j0k1l2m3n4
Revises: h8i9j0k1l2m3
Create Date: 2026-04-09 07:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "i9j0k1l2m3n4"
down_revision = "h8i9j0k1l2m3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "program_checklist_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "program_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("programs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("item_name", sa.String(255), nullable=False),
        sa.Column(
            "category",
            sa.String(50),
            server_default="document",
            nullable=False,
        ),
        sa.Column(
            "requirement_level",
            sa.String(20),
            server_default="required",
            nullable=False,
        ),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("instructions", sa.Text, nullable=True),
        sa.Column(
            "sort_order", sa.Integer, server_default="0", nullable=False,
        ),
        sa.Column(
            "is_active", sa.Boolean, server_default="true", nullable=False,
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
        "ix_prog_checklist_program",
        "program_checklist_items",
        ["program_id"],
    )


def downgrade() -> None:
    op.drop_table("program_checklist_items")

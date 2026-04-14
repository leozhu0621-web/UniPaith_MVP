"""add institution claim fields

Revision ID: l2m3n4o5p6q7
Revises: k1l2m3n4o5p6
Create Date: 2026-04-10 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "l2m3n4o5p6q7"
down_revision = "k1l2m3n4o5p6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "institutions",
        sa.Column("claimed_from_source", sa.String(50), nullable=True),
    )
    op.add_column(
        "institutions",
        sa.Column("claimed_extracted_ids", postgresql.JSONB, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("institutions", "claimed_extracted_ids")
    op.drop_column("institutions", "claimed_from_source")

"""Widen academic_records.gpa from Numeric(4,2) to Numeric(5,2)

GPA values up to 100 are valid on some international scales. The schema
already allows le=100 but Numeric(4,2) caps at 99.99.

Revision ID: 4c9e5f3a8b2d
Revises: 3b8d4e2f7a1c
Create Date: 2026-04-18 03:00:00.000000

"""
import sqlalchemy as sa

from alembic import op

revision = "4c9e5f3a8b2d"
down_revision = "3b8d4e2f7a1c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "academic_records",
        "gpa",
        type_=sa.Numeric(5, 2),
        existing_type=sa.Numeric(4, 2),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "academic_records",
        "gpa",
        type_=sa.Numeric(4, 2),
        existing_type=sa.Numeric(5, 2),
        existing_nullable=True,
    )

"""Widen academic_records.gpa from Numeric(4,2) to Numeric(5,2)

The Pydantic schema allows gpa up to 100 (valid on many international
grading scales), but the column was Numeric(4,2) which maxes out at 99.99.
Values of 100.0 would cause a numeric overflow at the DB level.

Revision ID: 4c9e5f3a8b2d
Revises: 3b8d4e2f7a1c
Create Date: 2026-04-21 00:00:00.000000

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
        existing_type=sa.Numeric(precision=4, scale=2),
        type_=sa.Numeric(precision=5, scale=2),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "academic_records",
        "gpa",
        existing_type=sa.Numeric(precision=5, scale=2),
        type_=sa.Numeric(precision=4, scale=2),
        existing_nullable=True,
    )

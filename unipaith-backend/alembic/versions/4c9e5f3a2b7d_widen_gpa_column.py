"""Widen gpa column from Numeric(4,2) to Numeric(5,2)

The model was updated in ebbfebc to support GPA scales that exceed 99.99
(e.g. percentage-based 100.00), but no migration was generated, so the
production DB column is still Numeric(4,2).

Revision ID: 4c9e5f3a2b7d
Revises: 3b8d4e2f7a1c
Create Date: 2026-04-18 22:30:00.000000

"""
import sqlalchemy as sa

from alembic import op

revision = "4c9e5f3a2b7d"
down_revision = "3b8d4e2f7a1c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "academic_records",
        "gpa",
        type_=sa.Numeric(precision=5, scale=2),
        existing_type=sa.Numeric(precision=4, scale=2),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "academic_records",
        "gpa",
        type_=sa.Numeric(precision=4, scale=2),
        existing_type=sa.Numeric(precision=5, scale=2),
        existing_nullable=True,
    )

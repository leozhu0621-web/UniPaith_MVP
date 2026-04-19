"""Add 2 review + 2 employer rating dimensions per business-plan spec

Plan spec ("Insights" section of Program Detail Page) calls for 6 review
dimensions (teaching/workload/career_support/internship_access/community_culture/roi)
and 5 employer dimensions (technical/practical/communication/teamwork/reliability).
Schema currently has 5 review (missing internship_access + community_culture)
and 4 employer (missing teamwork + reliability) dimensions.

This migration adds the 4 missing nullable Integer columns. Existing rows
remain compatible (null = not rated on that dimension).

Revision ID: 4c9d6e1a8b3f
Revises: 3b8d4e2f7a1c
Create Date: 2026-04-19 02:00:00.000000

"""
import sqlalchemy as sa

from alembic import op

revision = "4c9d6e1a8b3f"
down_revision = "3b8d4e2f7a1c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Reviews
    op.add_column(
        "student_program_reviews",
        sa.Column("rating_internship_access", sa.Integer(), nullable=True),
    )
    op.add_column(
        "student_program_reviews",
        sa.Column("rating_community_culture", sa.Integer(), nullable=True),
    )
    # Employer feedback
    op.add_column(
        "employer_feedback",
        sa.Column("rating_teamwork", sa.Integer(), nullable=True),
    )
    op.add_column(
        "employer_feedback",
        sa.Column("rating_reliability", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("employer_feedback", "rating_reliability")
    op.drop_column("employer_feedback", "rating_teamwork")
    op.drop_column("student_program_reviews", "rating_community_culture")
    op.drop_column("student_program_reviews", "rating_internship_access")

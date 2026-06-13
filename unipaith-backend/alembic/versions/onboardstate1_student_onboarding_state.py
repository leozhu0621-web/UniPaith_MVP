"""Ship C — student_profiles.onboarding_state JSONB

Adds the server-persisted Imprint-style onboarding wizard state to
``student_profiles``. Shape: ``{answers: {stage, interests, degree_level,
intake_term, budget_band, geos}, last_step, completed_at, dismissed_at}``.
Replaces the frontend's 60-second account-age heuristic — "needs onboarding"
is ``completed_at IS NULL AND dismissed_at IS NULL``. Nullable; existing rows
are untouched (NULL = legacy account, treated as not needing the wizard only
by the frontend rule once stamped).

Revision ID: onboardstate1
Revises: campusgallery1
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "onboardstate1"
down_revision = "campusgallery1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "student_profiles",
        sa.Column("onboarding_state", postgresql.JSONB(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("student_profiles", "onboarding_state")

"""Cornell description depth pass — field-specific descriptions for all 274 programs

Replaces classification-only program descriptions with field-specific clauses
from ``cornell_field_descriptions.py`` and re-applies ``cornell_profile.apply()``.

Revision ID: cornellprof6
Revises: pennprof8
Create Date: 2026-06-16
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import cornell_profile

revision = "cornellprof6"
down_revision = "pennprof8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    cornell_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass

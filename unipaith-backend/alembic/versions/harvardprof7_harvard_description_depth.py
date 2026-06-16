"""Harvard description depth pass — field-specific descriptions for all 343 programs

Replaces classification-only program descriptions with field-specific clauses
from ``harvard_field_descriptions.py`` and re-applies ``harvard_profile.apply()``.

Revision ID: harvardprof7
Revises: cornellprof6
Create Date: 2026-06-16
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import harvard_profile

revision = "harvardprof7"
down_revision = "cornellprof6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    harvard_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass

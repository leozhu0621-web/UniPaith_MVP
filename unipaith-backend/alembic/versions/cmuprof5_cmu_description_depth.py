"""CMU description depth pass — field-specific descriptions for all 180 programs

Replaces classification-only program descriptions with field-specific clauses
from ``cmu_field_descriptions.py`` and re-applies ``carnegie_mellon_profile.apply()``.

Revision ID: cmuprof5
Revises: jhuprof5
Create Date: 2026-06-16
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import carnegie_mellon_profile

revision = "cmuprof5"
down_revision = "jhuprof5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    carnegie_mellon_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass

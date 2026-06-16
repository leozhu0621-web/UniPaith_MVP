"""Yale description depth pass — field-specific descriptions for all 189 programs

Replaces classification-only program descriptions with field-specific clauses
from ``yale_field_descriptions.py`` and re-applies ``yale_profile.apply()``.

Revision ID: yaleprof6
Revises: northwesternprof4
Create Date: 2026-06-16
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import yale_profile

revision = "yaleprof6"
down_revision = "northwesternprof4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    yale_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass

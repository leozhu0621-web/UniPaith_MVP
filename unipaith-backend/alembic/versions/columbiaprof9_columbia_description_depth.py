"""Columbia description depth pass — field-specific descriptions for all 263 programs

Replaces classification-only program descriptions with field-specific clauses
from ``columbia_field_descriptions.py`` and re-applies ``columbia_profile.apply()``.

Revision ID: columbiaprof9
Revises: dukeprof5
Create Date: 2026-06-16
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import columbia_profile

revision = "columbiaprof9"
down_revision = "dukeprof5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    columbia_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass

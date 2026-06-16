"""Northwestern description depth pass — field-specific descriptions for all 308 programs

Replaces classification-only program descriptions with field-specific clauses
from ``northwestern_field_descriptions.py`` and re-applies ``northwestern_profile.apply()``.

Revision ID: northwesternprof4
Revises: harvardprof7
Create Date: 2026-06-16
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import northwestern_profile

revision = "northwesternprof4"
down_revision = "harvardprof7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    northwestern_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass

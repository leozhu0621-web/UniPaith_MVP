"""Stanford description depth pass — field-specific descriptions for all 188 programs

Replaces classification-only program descriptions with field-specific clauses
from ``stanford_field_descriptions.py`` and re-applies ``stanford_profile.apply()``.

Revision ID: stanfordprof7
Revises: columbiaprof9
Create Date: 2026-06-16
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import stanford_profile

revision = "stanfordprof7"
down_revision = "columbiaprof9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    stanford_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass

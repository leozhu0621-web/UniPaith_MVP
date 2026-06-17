"""JHU description repair — drop program_name prefix from all descriptions

Re-applies ``jhu_profile.apply()`` so every program description opens on a
field-specific clause (gold MIT/Chicago pattern) instead of ``{program_name}: …``.

Revision ID: jhuprof6
Revises: cornellprof7
Create Date: 2026-06-17
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import jhu_profile

revision = "jhuprof6"
down_revision = "cornellprof7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    jhu_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass

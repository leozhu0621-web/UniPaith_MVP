"""Penn description repair — drop program_name prefix from all descriptions

Re-applies ``penn_profile.apply()`` so every program description opens on a
field-specific clause (gold MIT/JHU pattern) instead of ``{program_name}: …``.

Revision ID: pennprof9
Revises: jhuprof6
Create Date: 2026-06-17
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import penn_profile

revision = "pennprof9"
down_revision = "jhuprof6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    penn_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass

"""Rice description repair — drop program_name prefix from all descriptions

Re-applies ``rice_profile.apply()`` so every program description opens on a
field-specific clause (gold MIT/JHU pattern) instead of ``{program_name} is …``.

Revision ID: riceprof5
Revises: purdueprof5
Create Date: 2026-06-17
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import rice_profile

revision = "riceprof5"
down_revision = "purdueprof5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    rice_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass

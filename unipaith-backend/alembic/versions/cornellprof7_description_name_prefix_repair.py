"""Cornell description repair — drop program_name prefix from all descriptions

Re-applies ``cornell_profile.apply()`` so every program description opens on a
field-specific clause (gold MIT/Chicago pattern) instead of ``{program_name}: …``.

Revision ID: cornellprof7
Revises: berkeleyprof8
Create Date: 2026-06-17
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import cornell_profile

revision = "cornellprof7"
down_revision = "berkeleyprof8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    cornell_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass

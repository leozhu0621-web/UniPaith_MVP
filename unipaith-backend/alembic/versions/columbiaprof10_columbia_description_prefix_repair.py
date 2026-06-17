"""Columbia description prefix repair — drop program_name prefixes

Re-applies ``columbia_profile.apply()`` so every program description opens on a
field-specific clause (gold MIT/BU pattern) instead of
``{program_name}: {clause}`` name-prefixed stubs.

Revision ID: columbiaprof10
Revises: buprof9
Create Date: 2026-06-17
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import columbia_profile

revision = "columbiaprof10"
down_revision = "buprof9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    columbia_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass

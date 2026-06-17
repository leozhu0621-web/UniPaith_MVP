"""Harvard description prefix repair — drop program_name prefixes

Re-applies ``harvard_profile.apply()`` so every program description opens on a
field-specific clause (gold MIT/Columbia pattern) instead of
``{program_name}: {clause}`` name-prefixed stubs, with credential-level
differentiation so sibling rows do not share identical text.

Revision ID: harvardprof8
Revises: columbiaprof10
Create Date: 2026-06-17
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import harvard_profile

revision = "harvardprof8"
down_revision = "columbiaprof10"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    harvard_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass

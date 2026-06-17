"""Stanford description prefix repair — drop program_name prefixes

Re-applies ``stanford_profile.apply()`` so every program description opens on a
field-specific clause (gold MIT/Harvard pattern) instead of
``{program_name}: {clause}`` name-prefixed stubs, with credential-level
differentiation and peer-contamination fixes in field clauses.

Revision ID: stanfordprof9
Revises: harvardprof8
Create Date: 2026-06-17
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import stanford_profile

revision = "stanfordprof9"
down_revision = "harvardprof8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    stanford_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass

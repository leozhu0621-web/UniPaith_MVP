"""Penn description depth pass — field-specific descriptions for all 250 programs

Replaces classification-only program descriptions with field-specific clauses
from ``penn_field_descriptions.py`` and re-applies ``penn_profile.apply()``.

Revision ID: pennprof8
Revises: berkeleyprof7
Create Date: 2026-06-16
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import penn_profile

revision = "pennprof8"
down_revision = "berkeleyprof7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    penn_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass

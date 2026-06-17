"""Berkeley description depth pass — field-specific descriptions for all 269 programs

Replaces classification-only program descriptions with field-specific clauses
from ``berkeley_field_descriptions.py`` and re-applies ``berkeley_profile.apply()``.

Revision ID: berkeleyprof7
Revises: cmuprof5
Create Date: 2026-06-16
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import berkeley_profile

revision = "berkeleyprof7"
down_revision = "cmuprof5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    berkeley_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass

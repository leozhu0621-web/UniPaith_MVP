"""Purdue catalog structural repair — de-fabricate IPEDS template stubs

Replaces 96% ``program_description`` template rows with field-specific descriptions,
maps CIP rollup titles to real Purdue degree names and owning departments, and
re-applies ``purdue_profile.apply()``.

Revision ID: purdueprof4
Revises: buprof8
Create Date: 2026-06-16
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import purdue_profile

revision = "purdueprof4"
down_revision = "buprof8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    purdue_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass

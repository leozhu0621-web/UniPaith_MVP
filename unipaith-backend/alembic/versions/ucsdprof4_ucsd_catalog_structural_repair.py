"""UCSD catalog structural repair — de-fabricate IPEDS template stubs

Replaces 96% ``program_description`` template rows with field-specific descriptions,
maps CIP rollup titles to real UCSD degree names and owning departments, and
re-applies ``ucsd_profile.apply()``.

Revision ID: ucsdprof4
Revises: purdueprof4
Create Date: 2026-06-16
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import ucsd_profile

revision = "ucsdprof4"
down_revision = "purdueprof4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    ucsd_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass

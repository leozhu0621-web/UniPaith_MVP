"""persist Berkeley program departments on apply()

Re-applies ``berkeley_profile.apply()`` so every program's ``department`` column
is written to the database (was missing from ``_apply_programs``).

Revision ID: berkeleyprof5
Revises: berkeleyprof4
Create Date: 2026-06-14
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import berkeley_profile

revision = "berkeleyprof5"
down_revision = "berkeleyprof4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    berkeley_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass

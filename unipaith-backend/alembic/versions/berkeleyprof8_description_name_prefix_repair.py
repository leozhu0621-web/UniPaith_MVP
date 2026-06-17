"""Berkeley description repair — drop program_name prefix from all descriptions

Re-applies ``berkeley_profile.apply()`` so every program description opens on a
field-specific clause (gold MIT/Chicago pattern) instead of ``{program_name}: …``.

Revision ID: berkeleyprof8
Revises: chicagoprof7
Create Date: 2026-06-17
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import berkeley_profile

revision = "berkeleyprof8"
down_revision = "chicagoprof7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    berkeley_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass

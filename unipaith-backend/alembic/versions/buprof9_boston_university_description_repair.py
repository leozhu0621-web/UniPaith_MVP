"""Boston University description repair — drop classification stubs

Re-applies ``bu_profile.apply()`` so every program description opens on a
field-specific clause (gold MIT/JHU pattern) instead of ``{program_name} is
{role} at Boston University's {school}`` classification stubs.

Revision ID: buprof9
Revises: northwesternprof5
Create Date: 2026-06-17
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import bu_profile

revision = "buprof9"
down_revision = "northwesternprof5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    bu_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass

"""UW-Madison description repair — drop program_name prefix from all descriptions

Re-applies ``uw_madison_profile.apply()`` so every program description opens on a
field-specific clause (gold MIT/JHU pattern) instead of ``{program_name} is …``.

Revision ID: uwmadisonprof5
Revises: ucsdprof5
Create Date: 2026-06-17
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import uw_madison_profile

revision = "uwmadisonprof5"
down_revision = "ucsdprof5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    uw_madison_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass

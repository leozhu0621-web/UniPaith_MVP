"""Northwestern description repair — drop program_name prefix from all descriptions

Re-applies ``northwestern_profile.apply()`` so every program description opens on a
field-specific clause (gold MIT/JHU pattern) instead of ``{program_name}: …``; fixes
peer-institution contamination in field clauses.

Revision ID: northwesternprof5
Revises: uwmadisonprof5
Create Date: 2026-06-17
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import northwestern_profile

revision = "northwesternprof5"
down_revision = "uwmadisonprof5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    northwestern_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass

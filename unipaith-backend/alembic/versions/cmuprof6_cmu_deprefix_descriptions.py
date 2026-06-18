"""CMU de-prefix descriptions — remove the "{program_name}: " prefix-double

The 180 CMU program descriptions were field-specific and researched per-program
but each opened by restating the ``program_name`` verbatim ("Computer Science:
Spans algorithms…"), doubling the page heading (REPAIR_BACKLOG miss #9). This
re-applies ``carnegie_mellon_profile.apply()`` so every description opens on a
field fact instead of its own title; the underlying researched clauses are
unchanged (6 clauses that themselves opened on the field name were reworded to
open on a fact, same verified content).

Revision ID: cmuprof6
Revises: princetonprof9
Create Date: 2026-06-18
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import carnegie_mellon_profile

revision = "cmuprof6"
down_revision = "princetonprof9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    carnegie_mellon_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass

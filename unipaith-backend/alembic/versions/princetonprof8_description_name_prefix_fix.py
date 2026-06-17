"""Princeton — drop name-prefixed program descriptions

Re-applies ``princeton_profile.apply()`` after removing the ``{program_name}: …``
description prefix on 13 catalog rows (gold contrast: open on the field fact).

Revision ID: princetonprof8
Revises: princetonprof7
Create Date: 2026-06-17
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import princeton_profile

revision = "princetonprof8"
down_revision = "princetonprof7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    princeton_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass

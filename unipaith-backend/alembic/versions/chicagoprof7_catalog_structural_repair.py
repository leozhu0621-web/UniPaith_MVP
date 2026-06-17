"""UChicago structural repair — real degree names + field-specific descriptions

Replaces CIP-prefix program names and name-prefixed descriptions with verified
UChicago degree designations and field-specific clauses; re-applies
``chicago_profile.apply()``.

Revision ID: chicagoprof7
Revises: caltechprof7
Create Date: 2026-06-17
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import chicago_profile

revision = "chicagoprof7"
down_revision = "caltechprof7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    chicago_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass

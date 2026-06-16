"""Princeton catalog structural repair — field-specific descriptions

De-fabricates the Princeton catalog: drops federal certificate and incidental
master's padding rows, replaces CIP-prefix program names with real Princeton
degree titles, and stamps field-specific descriptions on every program node.
Re-applies ``princeton_profile.apply()``.

Revision ID: princetonprof7
Revises: stanfordprof8
Create Date: 2026-06-16
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import princeton_profile

revision = "princetonprof7"
down_revision = "stanfordprof8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    princeton_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass

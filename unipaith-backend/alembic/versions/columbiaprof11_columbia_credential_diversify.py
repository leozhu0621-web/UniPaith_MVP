"""Columbia credential-level description diversification

Re-applies ``columbia_profile.apply()`` so credential-sibling programs (certificate,
bachelor's, master's, Ph.D. in the same field) carry distinct description text via
Columbia-specific level suffixes; clears remaining peer-institution contamination
(Kelly Writers House, Perry World House, Morris Arboretum, Haas/CDSS).

Revision ID: columbiaprof11
Revises: stanfordprof9
Create Date: 2026-06-17
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import columbia_profile

revision = "columbiaprof11"
down_revision = "stanfordprof9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    columbia_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass

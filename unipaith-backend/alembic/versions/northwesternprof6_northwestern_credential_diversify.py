"""Northwestern credential-level description diversification

Re-applies ``northwestern_profile.apply()`` so credential-sibling programs
(certificate, bachelor's, master's, Ph.D. in the same field) carry distinct
description text via Northwestern-specific level suffixes.

Revision ID: northwesternprof6
Revises: columbiaprof11
Create Date: 2026-06-17
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import northwestern_profile

revision = "northwesternprof6"
down_revision = "columbiaprof11"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    northwestern_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass

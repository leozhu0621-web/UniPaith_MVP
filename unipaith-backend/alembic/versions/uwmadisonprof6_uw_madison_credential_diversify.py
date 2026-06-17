"""UW-Madison credential-level description diversification

Re-applies ``uw_madison_profile.apply()`` so credential-sibling programs
(certificate, bachelor's, master's, Ph.D. in the same field) carry distinct
description text via UW-Madison-specific level suffixes, and peer-institution
contamination in field clauses is cleared.

Revision ID: uwmadisonprof6
Revises: northwesternprof6
Create Date: 2026-06-17
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import uw_madison_profile

revision = "uwmadisonprof6"
down_revision = "northwesternprof6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    uw_madison_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass

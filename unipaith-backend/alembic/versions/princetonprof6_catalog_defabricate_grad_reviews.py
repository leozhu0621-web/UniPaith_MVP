"""Princeton catalog de-fabrication + graduate coverable reviews

Removes fabricated IPEDS rollup programs (Engineering General, duplicate Computer
Engineering, standalone Economics M.S.), renames graduate engineering and M.Arch.
programs to Princeton's published degree titles, and adds aggregated external_reviews
on five coverable graduate programs. Re-applies ``princeton_profile.apply()``.

Revision ID: princetonprof6
Revises: chicagoprof5
Create Date: 2026-06-16
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import princeton_profile

revision = "princetonprof6"
down_revision = "chicagoprof5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    princeton_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass

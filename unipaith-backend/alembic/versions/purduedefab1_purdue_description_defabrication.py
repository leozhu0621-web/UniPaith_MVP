"""Purdue description de-fabrication — remove peer-institution copy + per-credential rewrite

Re-applies ``purdue_profile.apply()`` after the data module was de-fabricated
(REPAIR_BACKLOG critical #3): every program description is regenerated from a verified,
field-specific discipline definition + Purdue's real owning college on the West Lafayette,
Indiana campus, per credential level (gold MIT / Michigan model). This removes the
cross-institution-copy fabrications that had been find-replaced from peer catalogs (Penn's
SAS/Wharton/Perelman, JHU's Chesapeake/Writing Seminars, Northwestern's McCormick, Cornell's
Weill) and fixes the 82% verbatim-across-levels descriptions. It also de-rolls-up the CIP
rollup program names/departments (resolving them to real Purdue degrees, or dropping the
unverifiable/duplicate rows), so ``apply()`` deletes the dropped slugs.

Revision ID: purduedefab1
Revises: progprefbf1
Create Date: 2026-06-19
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import purdue_profile

revision = "purduedefab1"
down_revision = "progprefbf1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    purdue_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass

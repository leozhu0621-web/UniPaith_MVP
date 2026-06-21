"""Stanford graduate tuition coverage (run-70 matcher-core tuition rule).

#1021 cleared Stanford's per-credential descriptions but left tuition at 33% (all
degree master's null). Stanford degree master's now carry the published standard
full-time graduate tuition ($65,910, 2025-26, College Scorecard UNITID 243744),
taking tuition coverage 33% -> 69% (the matcher budget-fit signal); per-unit graduate
certificates and school-specific professional degrees keep an honest documented
omission. Re-applies ``stanford_profile.apply()`` (idempotent) + re-derives
program-preference rows.

Chains off ``uftuitionmerge1`` (#1023), which already unified the
ufpercrd2/stanfordpercrd1 dual head — so this stays single-head.

Revision ID: stanfordtuit1
Revises: uftuitionmerge1
Create Date: 2026-06-21
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import stanford_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "stanfordtuit1"
down_revision = "uftuitionmerge1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    stanford_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == stanford_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass

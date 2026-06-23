"""Emory published graduate-tier tuition backfill (REPAIR_BACKLOG #4)

Clears the master's / professional-tier tuition STARVATION the catalog aggregate hid:
Emory's bachelor's tier shipped 100% but the master's tier was 0/5 and professional 0/2
(the CPEF matcher scored Emory's graduate budget-fit BLIND). Emory publishes graduate/
professional tuition BY SCHOOL on the Student Financial Services rate sheet (2025-26),
so the nulls were a skipped knowable field, not an honest omission. Every figure is
verified and stamped in ``emory_profile._COST_BY_SLUG``:

  * Laney Graduate School (MS) -> $73,200/yr;
  * Goizueta Traditional MBA -> $76,900/yr (fall + spring);
  * Rollins MPH -> $43,264/yr; MSPH -> $50,186/yr;
  * Candler MDiv -> $27,500/yr;
  * Law J.D. -> $69,510/yr;
  * School of Medicine M.D. -> $59,000/yr.

Values are school-distinct and NONE equals the $64,280 undergraduate sticker.
PhD rows remain funded-omit-with-reason.

Idempotent: re-applies ``emory_profile.apply()`` and re-derives program-preference rows.

Revision ID: emorygradtuition1
Revises: chigradtuition1
Create Date: 2026-06-23
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import emory_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "emorygradtuition1"
down_revision = "chigradtuition1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    emory_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == emory_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass

"""Dartmouth published graduate-tier tuition backfill (REPAIR_BACKLOG #4)

Clears the master's / professional-tier tuition STARVATION the catalog aggregate hid:
Dartmouth's bachelor's tier shipped 100% but the master's tier was 0/6 and the
professional tier 0/1 (the CPEF matcher scored Dartmouth's graduate budget-fit BLIND).
Dartmouth publishes graduate/professional tuition BY SCHOOL on each school's official
2026-27 tuition page, so the nulls were a skipped knowable field, not an honest
omission. Every figure is verified and stamped in ``dartmouth_profile._COST_BY_SLUG``:

  * Thayer MEng -> $71,697 (3 quarters); MEM -> $95,596 (4 quarters);
  * Tuck MBA -> $87,536;
  * Geisel M.D. -> $75,110;
  * Dartmouth Institute on-campus MPH -> $82,232;
  * Guarini MS in Computer Science -> $95,596 (4 quarters);
  * MALS full-time -> $66,917.

Values are school-distinct and NONE equals the $66,123 undergraduate sticker.
PhD rows remain funded-omit-with-reason.

Idempotent: re-applies ``dartmouth_profile.apply()`` and re-derives program-preference
rows.

Revision ID: dartgradtuition1
Revises: emorygradtuition1
Create Date: 2026-06-23
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import dartmouth_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "dartgradtuition1"
down_revision = "emorygradtuition1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    dartmouth_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == dartmouth_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass

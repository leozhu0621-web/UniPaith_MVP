"""Chicago published graduate-tier tuition backfill (REPAIR_BACKLOG #4)

Clears the master's / professional-tier tuition STARVATION the catalog aggregate hid:
UChicago's bachelor's tier shipped 100% but the master's tier was 3/41 (the CPEF matcher
scored Chicago's graduate budget-fit BLIND). UChicago publishes graduate/professional
tuition BY DIVISION or PROGRAM on the Bursar and school cost pages (2025-26 unless
noted), so the nulls were a skipped knowable field, not an honest omission. Every
figure is verified and stamped in ``chicago_profile._published_grad_cost``:

  * Social Sciences Division M.A. (3 courses/quarter) -> $69,888/yr;
  * Humanities Division full-time M.A./M.F.A. -> $67,200/yr;
  * Harris MS/MPP/MA (3 courses/quarter) -> $66,573/yr;
  * Divinity MDiv full-time -> $30,000/yr;
  * Physical Sciences Division standard M.S. (3 courses/quarter) -> $61,725/yr;
  * Pritzker Molecular Engineering M.S. -> $69,780/yr;
  * Per-program overrides retained for Booth MBA, Law J.D., Pritzker M.D., Crown A.M.,
    and MPCS.

Values are division/program-distinct and NONE equals the $71,325 undergraduate sticker.

Idempotent: re-applies ``chicago_profile.apply()`` and re-derives program-preference rows.

Revision ID: chigradtuition1
Revises: ricegradtuition1
Create Date: 2026-06-23
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import chicago_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "chigradtuition1"
down_revision = "ricegradtuition1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    chicago_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == chicago_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass

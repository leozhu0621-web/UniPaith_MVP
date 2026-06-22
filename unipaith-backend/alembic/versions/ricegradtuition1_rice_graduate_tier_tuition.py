"""Rice published graduate-tier tuition backfill (REPAIR_BACKLOG #4)

Clears the master's / professional-tier tuition STARVATION the catalog aggregate hid:
Rice's bachelor's tier shipped 100% but the master's tier was 1/29 and the professional
tier 11/38 (the CPEF matcher scored Rice's graduate budget-fit BLIND). Rice publishes
graduate/professional tuition BY SCHOOL or PROGRAM on the Bursar rate sheets (2026-27),
so the nulls were a skipped knowable field, not an honest omission. Every figure is
verified and stamped in ``rice_profile._published_grad_cost``:

  * GS full-time research master's (Engineering / Natural Sciences / Humanities /
    Social Sciences) -> $66,784;
  * Professional Master's in Engineering (on-campus PM degrees) -> $61,440;
  * Professional Master's in Natural Sciences (MST) -> $40,600;
  * Architecture M.S. Option 3 -> $41,333; Music M.M. / Artist Diploma -> $35,020;
  * Rice Business Full-Time MBA -> $79,116; PMBA Evening/Weekend/Hybrid, EMBA, MAcc,
    MBA@Rice Online at distinct published rates;
  * Social-sciences professional master's (MEEcon, MGA, MSPE, MHCIHF, MCEcon, MIOP)
    at school-published annual figures;
  * Glasscock per-credit programs -> per-credit x typical 18-credit annual load.

Funded research doctorates (Ph.D., D.M.A.) stay omitted-with-reason. Values are
school-distinct and NONE equals the $66,540 undergraduate sticker.

Idempotent: re-applies ``rice_profile.apply()`` and re-derives program-preference rows.

Revision ID: ricegradtuition1
Revises: colgradtuition1
Create Date: 2026-06-22
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import rice_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "ricegradtuition1"
down_revision = "colgradtuition1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    rice_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == rice_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass

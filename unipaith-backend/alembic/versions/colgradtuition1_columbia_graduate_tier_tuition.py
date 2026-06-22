"""Columbia published graduate-tier tuition backfill (REPAIR_BACKLOG #4)

Clears the master's / professional-tier tuition STARVATION the catalog aggregate hid:
Columbia's bachelor's tier shipped 100% but the master's tier was 3/45 and the
professional tier 2/8 (the CPEF matcher scored Columbia's graduate budget-fit BLIND).
Columbia publishes graduate/professional tuition BY SCHOOL or PROGRAM on first-party
bulletin / cost-of-attendance pages, so the nulls were a skipped knowable field, not
an honest omission. Every figure is verified and stamped in
``columbia_profile._COST_BY_SLUG``:

  * GSAS terminal M.A. -> $73,454 (2 × $36,727 Residence Unit)
  * SEAS M.S. -> $81,000 (30 × $2,700/credit)
  * GSAPP M.S. / M.Arch -> $70,380/year or $105,570 for 12-month programs
  * SIPA MIA/MPA -> $74,220; MSSW -> $60,364; Journalism / Arts / CBS MS / CUIMC
    programs at each school's published rate
  * Law J.D./LL.M. -> $85,368; M.D. -> $76,336; D.D.S. -> $105,048; DPT -> $46,928
  * Mailman MPH/MHA flat -> $49,888; Biostatistics M.S. Year 1 -> $53,352

Funded research doctorates (Ph.D., J.S.D.) and the per-credit-only DrPH stay at verified
omit-with-reason. Values are school/program-distinct and NONE equals the $70,170
undergraduate sticker.

Idempotent: re-applies ``columbia_profile.apply()`` and re-derives program-preference rows.

Revision ID: colgradtuition1
Revises: penncip2
Create Date: 2026-06-22
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import columbia_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "colgradtuition1"
down_revision = "penncip2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    columbia_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(
            Institution.name == columbia_profile.INSTITUTION_NAME
        )
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass

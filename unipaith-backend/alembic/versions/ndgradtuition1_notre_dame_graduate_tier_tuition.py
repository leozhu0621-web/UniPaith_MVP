"""Notre Dame published graduate-tier tuition backfill (REPAIR_BACKLOG #4)

Clears the master's / professional-tier tuition STARVATION the catalog aggregate hid:
Notre Dame's bachelor's tier shipped 100% but the master's tier was 0/24 and the
professional tier 0/1 (the CPEF matcher scored Notre Dame's graduate budget-fit BLIND).
Notre Dame publishes graduate/professional tuition BY PROGRAM or SCHOOL on the Office
of Student Accounts rate sheets (2026-27), so the nulls were a skipped knowable field,
not an honest omission. Every figure is verified and stamped in
``notre_dame_profile._COST_BY_SLUG``:

  * Graduate School full-time terminal master's -> $69,110 (Arts & Letters MA/MFA,
    Engineering MS, Mathematics MS, Data Science MS, Global Affairs MGA, Architecture);
  * ACMS MS -> $55,248 (12-credit traditional load); ESTEEM -> $69,610;
  * Mendoza MBA -> $75,460; MS Accountancy -> $55,660; MS Business Analytics -> $69,630;
    MS Finance -> $74,618;
  * Law J.D. -> $75,816; LL.M. -> $37,892;
  * Sacred Music MSM -> $0 (100% tuition via graduate assistantship).

Funded research doctorates (Ph.D., J.S.D., D.M.A.) stay at verified $0 with
``funded=True``. Values are program/school-distinct and NONE equals the $67,444
undergraduate sticker.

Idempotent: re-applies ``notre_dame_profile.apply()`` and re-derives program-preference
rows.

Revision ID: ndgradtuition1
Revises: yalegradtuition1
Create Date: 2026-06-22
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import notre_dame_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "ndgradtuition1"
down_revision = "yalegradtuition1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    notre_dame_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == notre_dame_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass

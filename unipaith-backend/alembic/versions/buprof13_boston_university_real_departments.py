"""Boston University — real owning-college departments + real dual-degree names.

Re-applies ``bu_profile.apply()`` after the buprof13 structural repair (SKILL miss #2
department bullet + miss #9 verify-output). The live BU catalog still echoed the field
from each program name into ``department`` on 216 rows (e.g. "Bachelor of Arts in
Anthropology" -> department "Anthropology") while the real owning College of Arts &
Sciences was known — the dept-echo defect (REPAIR_BACKLOG CRITICAL #1). It also shipped
nine mechanical credential-combo tokens as names/departments ("Jdma English",
"Jdllm In Finance", "PhD, MD/PhD"). buprof13:
  * ``_department_for`` now groups every program under its real owning school/college
    (the verified Harvard-Business-School-model grouping, gold-acceptable), so the bare
    field is never echoed into ``department``; per-slug ``_DEPARTMENT_OVERRIDES`` keep the
    more-specific real units (Department of Anatomy & Neurobiology, etc.)
  * real names for the four Law J.D./M.A. duals ("Juris Doctor / Master of Arts in
    English / History / International Relations / Philosophy") and the GMS
    Virology, Immunology & Microbiology PhD (was the bare "PhD, MD/PhD" credential combo);
    the Law J.D./LL.M. and virology departments now resolve to School of Law / Graduate
    Medical Sciences
Derives ``program_preferences`` for every BU program (skips claimed rows).

Revision ID: buprof13
Revises: cornelldefab1
Create Date: 2026-06-19
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import bu_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "buprof13"
down_revision = "cornelldefab1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    bu_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == bu_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass

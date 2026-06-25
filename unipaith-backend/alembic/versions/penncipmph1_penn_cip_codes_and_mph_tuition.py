"""Penn cip_code per program + MPH master's tuition (REPAIR_BACKLOG #1 + #2)

Two matcher-side repairs for the University of Pennsylvania, shipped as one
re-apply of ``penn_profile.apply()`` (idempotent):

1. **cip_code (REPAIR_BACKLOG #1 — matcher field-signal starvation).** ``cip_code``
   is serialized on ``GET /programs/{id}`` and is the CIP join key the CPEF matcher
   uses to resolve a program's field to ``ref_majors`` + the field-66 vocabulary (the
   interest/field signal alongside the dense ``description_text`` embedding), yet Penn
   shipped it NULL on all 180 programs, scoring every one field-blind on the CIP key.
   ``penn_profile`` already carried the verified IPEDS CIP per row (it gates catalog
   breadth) and ``apply()`` now stamps ``p.cip_code = spec.get("cip")`` — coverage is
   100% (180/180), every code one Penn reports to IPEDS for UNITID 215062, never
   guessed.

2. **MPH master's tuition (REPAIR_BACKLOG #2 — graduate budget-fit residual).** The
   Perelman M.P.H. shipped with tuition NULL, leaving the matcher blind on its
   budget-fit. Penn SRFS publishes the MPH at $5,490 per course unit (2026-27); the
   MPH financing page states half-time is 2 c.u./semester, so a full-time academic
   year is the 4-c.u./semester cap (8 c.u.) = $43,920 — the same per-c.u. ×
   full-time-load derivation already used for SEAS/GSE/Nursing. The remaining null
   graduate rows (Carey Law LL.M./ML, Annenberg communication, Perelman research
   master's, SP&P public-administration CIP-rollup, per-credit certificates, funded
   research doctorates) stay honestly omitted-with-reason — no single citable
   per-program annual rate was verifiable, so none is guessed (verify-or-omit).

Idempotent: re-applies ``penn_profile.apply()`` and re-derives program-preference
rows for any program lacking one (claimed/first-party rows are never touched).

Revision ID: penncipmph1
Revises: uclacip2
Create Date: 2026-06-25
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import penn_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "penncipmph1"
down_revision = "uclacip2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    penn_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == penn_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        # Cover any program still lacking a derived ProgramPreference row; never
        # force-refresh existing derived/claimed rows (the matcher reads the corrected
        # field signal from Program.cip_code directly).
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass

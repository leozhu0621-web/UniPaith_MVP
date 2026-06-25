"""UW-Seattle matcher-core repair: cip_code on every program + public non-resident tuition scalar.

Clears UW-Seattle's two acute matcher-core defects:

* **REPAIR_BACKLOG #1 (cip_code STARVATION).** Every one of the catalog's 360 programs shipped
  ``cip_code = null`` — the CIP join key the CPEF matcher uses to resolve a program's field to
  ``ref_majors`` + the field-66 vocabulary — so the catalog was scored field-blind on the CIP
  signal. Each program now carries its NCES CIP-2020 4-digit code (``uw_profile._CIP_BY_FIELD``,
  keyed by field), never a guess; an interdisciplinary field with no single-discipline CIP is
  mapped to its closest CIP family (incl. 30.xx).

* **REPAIR_BACKLOG #2 (PUBLIC resident-tuition scalar mis-signal).** UW is public and the CPEF
  budget feature reads the flat ``program.tuition`` scalar for its over-budget breaker +
  affordability fit. The catalog shipped the IN-STATE resident rate as that scalar, so the
  out-of-state + ALL-international applicant pool (the flagship majority) was scored 2.5–3.5×
  too cheap and the budget veto never fired. The scalar now carries UW's published NON-RESIDENT
  annual sticker per tier — bachelor's $44,460, graduate Tier I $33,171 (UW OPB 2025-26 Seattle
  quarterly tuition & fees), the professional schools their own published non-resident rates
  (Law $58,956, Medicine $102,319, Dentistry $84,926, Pharmacy $51,582, DNP $50,037, DPT $43,461)
  — while ``cost_data.breakdown`` keeps BOTH the resident and non-resident rates (honest +
  sourced). The Doctor of Audiology + 15 fee-based online programs keep tuition omitted-with-reason.

Structure + descriptions are unchanged (uw is already CERTIFIED_CLEAN). Re-applies
``uw_profile.apply()`` (idempotent) and re-derives program-preference rows.

Revision ID: uwcipscalar1
Revises: ucsdcipdefab1
Create Date: 2026-06-25
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import uw_profile
from unipaith.models import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "uwcipscalar1"
down_revision = "ucsdcipdefab1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    uw_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == uw_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass

"""Northwestern published graduate / professional tuition — clear tier starvation

REPAIR_BACKLOG #3 (graduate-tier tuition starvation behind a 100% bachelor's tier).
Northwestern's IPEDS-derived graduate rows shipped with ``tuition = None``, so the
matcher scored graduate budget-fit blind: live coverage was master's 0/26 and
professional 0/4 (bachelor's 71/71).

``northwestern_profile`` now fills each master's / professional row from its owning
school's published 2025-26 Northwestern Student Financial Services rate — every
figure DISTINCT from the $68,322 undergraduate sticker:

- TGS / McCormick standard MS: $22,973/quarter × 3 = $68,919 (MEM $67,968)
- Kellogg MBA: $86,370; MiM / MSMS: $69,129
- Pritzker Law JD: $79,772; LLM: $83,462; MSL: $65,686
- Feinberg MD: $74,104; MPH / GC / DPT trimester rates; MPO $43,351; PA $57,231
- Medill IMC / journalism program totals; Communication AuD / SLP / RTVF MFA
- SPS online per-unit program totals (MSDS $62,796, etc.)

Funded research doctorates retain ``tuition_usd = 0`` with TGS funding note.
Result: master's 26/26, professional 4/4 — no undergrad sticker copied down.

Re-applies ``northwestern_profile.apply()`` (idempotent) and re-derives
``program_preferences``. Chains after ``gatepennmerge1``.

Revision ID: nwtuition1
Revises: gatepennmerge1
Create Date: 2026-06-22
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import northwestern_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "nwtuition1"
down_revision = "gatepennmerge1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    northwestern_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(
            Institution.name == northwestern_profile.INSTITUTION_NAME
        )
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass

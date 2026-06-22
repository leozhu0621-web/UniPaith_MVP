"""UC San Diego published graduate / professional tuition backfill (clears grad-tier 0%).

Clears UCSD's acute matcher-core defect (REPAIR_BACKLOG run 76 HIGH #3 — graduate-tier
0% tuition behind a 100% bachelor's tier): all 60 master's and both professional
programs (M.D., Pharm.D.) shipped ``tuition = null`` so the CPEF matcher scored
budget-fit blind on the entire graduate tier. Each now carries UCSD's published 2024-25
California-resident tuition-and-fees (excluding the waivable graduate health-insurance
premium, the same basis as the undergraduate sticker), cited to the Office of the
Registrar registration-fee tables — academic graduate $15,197 res / $30,299 nonres,
M.D. $44,715 / $56,960, Pharm.D. $50,345 / $62,590, Rady state-supported M.B.A. $53,727
/ $65,972, Rady MS Business Analytics $71,300 (self-supporting, one rate). Every tier is
distinct (the academic-graduate rate itself differs from the undergrad sticker) — never
a copy-down. The three funded research PhDs keep their $0 tuition-remission record, and
the two remaining Rady self-supporting per-unit master's (MS Finance, MS Information
Technology Management) record tuition omitted-with-reason — never a guessed figure.
Re-applies ``ucsd_profile.apply()`` (idempotent) and re-derives program-preference rows.

Revision ID: ucsdgradtuition1
Revises: purduetuition1
Create Date: 2026-06-22
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import ucsd_profile
from unipaith.models import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "ucsdgradtuition1"
down_revision = "purduetuition1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    ucsd_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == ucsd_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass

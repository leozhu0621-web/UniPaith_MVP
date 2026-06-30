"""Georgetown master's / professional tuition fills (matcher budget signal).

Continues the REPAIR_BACKLOG #1 (run 94) Georgetown tuition repair started in
``gtowntuition1`` (#1218). Four more null graduate rows now carry a verified,
first-party-published rate × the program's published required credit count — never
the undergraduate sticker, never a guess:

  * Master of Arts in English (GSAS)            — $2,652/credit × 24 credits = $63,648
  * Master of Science in Spanish Linguistics    — $2,652/credit × 33 credits = $87,516
  * Executive Doctor of Nursing Practice        — Nursing@Georgetown $2,758/credit × 30 = $82,740
  * Executive Master of Policy Leadership (EMPL) — 6 cr @ $2,652 + 24 cr @ $2,758 = $82,104

Master's coverage rises 74/79 → 76/79 and professional 13/17 → 14/17 for Georgetown.
The remaining null graduate rows stay honest omit-with-reason (recorded in each node's
``_standard.omitted`` with a precise reason): the residency-billed S.J.D. research
doctorate; the on-campus DNAP (no first-party total credit count); the
specialization-varying BSN-to-DNP; the track-varying MSN; and the Executive MS in
Clinical Quality, Safety & Leadership whose tuition Georgetown lists as not-yet-determined.

Re-applies ``georgetown_profile.apply()`` (idempotent) and re-derives program-preference
rows so the program → student match reads the now-populated budget signal.

Revision ID: gtowntuition2
Revises: washuolinms1
Create Date: 2026-06-30
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import georgetown_profile
from unipaith.models import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "gtowntuition2"
down_revision = "washuolinms1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    georgetown_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == georgetown_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass

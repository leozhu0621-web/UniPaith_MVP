"""UC Davis M.B.A. + M.P.H. master's tuition fill (matcher-core budget signal).

Fills the two largest null professional-master's tuition rows on the UC Davis
catalog from each program's own published cost page (verified 2026-06-30, the same
first-party basis as the J.D./M.D./D.V.M. professional rates already shipped):

1. **Full-time M.B.A.** (Graduate School of Management) — annual tuition & fees
   $51,297 (California resident) / $63,542 (non-resident = resident total plus the
   $12,245 nonresident supplemental tuition). The prior build *omitted* the all-in
   figure on the ground that only the UCOP Professional Degree Supplemental Tuition
   was confirmable, but the GSM full-time M.B.A. tuition page publishes the resident
   total directly, so it is read first-party rather than omitted.
2. **M.P.H.** (School of Medicine, Dept. of Public Health Sciences) — annual tuition
   & fees $29,960 (resident) / $42,205 (non-resident), read off the UC Davis Health
   M.P.H. Cost of Attendance page.

UC Davis is public, so ``program.tuition`` carries the NON-RESIDENT scalar (the
matcher's budget input for the out-of-state + international pool, REPAIR_BACKLOG #2)
while ``cost_data.breakdown`` preserves BOTH the resident and non-resident rates.

The remaining null master's stay honest omit-with-reason (recorded in each node's
``_standard.omitted``): the M.P.V.M., whose clean tuition+fees subtotal could not be
isolated from a published page this session (its UCOP supplemental is noted instead),
and the Master's Entry Program in Nursing (a self-supporting program whose published
figure could not be cleanly separated from total cost of attendance). PhD rows ship
``tuition`` null (funded convention).

Re-applies ``ucdavis_profile.apply()`` (idempotent) and re-derives
``program_preferences`` so the program -> student match reads the updated budget
signal. No programs added/removed (151 unchanged), so the once-backfilled
preference rows stay intact. Safe on a fresh/CI database (no-op if UC Davis absent).

Revision ID: ucdavistuition1
Revises: gtowntuition3
Create Date: 2026-06-30
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import ucdavis_profile
from unipaith.models import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "ucdavistuition1"
down_revision = "gtowntuition3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    ucdavis_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == ucdavis_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass

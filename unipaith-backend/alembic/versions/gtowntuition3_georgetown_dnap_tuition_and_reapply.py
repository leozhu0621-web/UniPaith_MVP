"""Georgetown DNAP tuition fill + re-apply the stranded grad-tuition repair.

Lands two things in production:

1. **A new master's/professional tuition fill** — the Doctor of Nurse Anesthesia
   Practice (DNAP), an on-campus graduate professional doctorate billed at the
   standard $2,652/credit graduate rate (finaid 2025-26 Graduate Program Cost of
   Attendance) across its published 70-credit curriculum = $185,640. The prior
   repair (``gtowntuition2`` / #1227) had *omitted* DNAP on the incorrect ground
   that no first-party total credit count is published, but the DNAP curriculum
   page publishes the 70-credit total (39 + 18 + 13 across three years), so the
   program total is computed first-party rather than omitted.

2. **The stranded ``gtowntuition2`` fills** — that migration's Deploy Backend run
   was *cancelled* (superseded by a following deploy), so its four fills
   (MA in English, MS in Spanish Linguistics, Executive DNP, Executive Master of
   Policy Leadership) never reached production and the live API still served them
   null. Re-applying ``georgetown_profile.apply()`` here (idempotent) lands those
   four plus the DNAP fill in one pass, so the matcher reads the now-populated
   budget signal for all five.

After this migration Georgetown master's coverage is 77/79 and professional 15/17;
the remaining null graduate rows stay honest omit-with-reason (recorded in each
node's ``_standard.omitted``): the residency-billed S.J.D. research doctorate; the
specialization-varying BSN-to-DNP; the track-varying MSN umbrella; and the
Executive MS in Clinical Quality, Safety & Leadership whose tuition Georgetown
lists as not-yet-determined. PhD rows ship ``tuition`` null (funded convention).

Re-derives ``program_preferences`` so the program -> student match reads the
updated data; idempotent and safe on a fresh/CI database (no-op if Georgetown
is absent).

Revision ID: gtowntuition3
Revises: gtowntuition2
Create Date: 2026-06-30
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import georgetown_profile
from unipaith.models import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "gtowntuition3"
down_revision = "gtowntuition2"
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

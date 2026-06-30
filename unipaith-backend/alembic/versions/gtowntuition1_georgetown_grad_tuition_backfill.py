"""Georgetown graduate / professional tuition backfill.

Clears the top REPAIR_BACKLOG HIGH (#1, run 92): Georgetown is structurally + description
clean, but its bachelor's tier fills 100% while the MASTER'S (73/79) and some PROFESSIONAL
(7/17) tiers shipped null tuition, so the CPEF matcher scored those graduate programs'
budget-fit BLIND. ``georgetown_profile`` now stamps each null master's / professional row
with its school's verified published 2025-26 rate:

  * Walsh School of Foreign Service master's — $2,758/credit × published degree credits
    (EIA at the $2,652 Graduate School rate);
  * Graduate School of Arts & Sciences master's — $2,652/credit × published credits;
  * McDonough (Business) master's — finaid 2025-26 per-credit rates × published credits;
  * Biomedical Graduate Education (School of Medicine) master's — $2,529/credit
    ($2,539 Biotechnology) × published credits;
  * School of Health master's — $2,652/credit × published credits;
  * School of Continuing Studies — each program's published total program tuition;
  * Georgetown Law non-JD master's (MLT, MSL Taxation) — $3,596/credit × required credits;
  * McCourt Master of Policy Management — $2,550/credit × 36 credits;
  * School of Nursing Entry-to-Nursing — $1,586/credit × 67 credits.

Master's coverage rises 6/79 → 74/79 and professional 13/17. The residual nulls are honest
omit-with-reason (recorded in each node's ``_standard.omitted``): funded research PhDs; the
residency-billed S.J.D.; the track-varying MSN and nursing practice doctorates; the not-yet-
published Executive MS in Clinical Quality; and the GSAS master's with no single published
credit total (English, Spanish Linguistics) and the executive-rate-unpublished EMPL. The
undergraduate sticker is NEVER copied onto a graduate/professional row.

Re-applies ``georgetown_profile.apply()`` (idempotent) and re-derives program-preference
rows so the program → student match reads the now-populated budget signal.

Revision ID: gtowntuition1
Revises: nyuamfeed1
Create Date: 2026-06-30
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import georgetown_profile
from unipaith.models import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "gtowntuition1"
down_revision = "nyuamfeed1"
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

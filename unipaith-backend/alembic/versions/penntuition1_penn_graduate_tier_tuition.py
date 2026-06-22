"""Penn graduate-tier published tuition — clear master's / professional starvation

REPAIR_BACKLOG #3 (graduate-tier tuition starvation behind a 100% bachelor's tier). Penn's
IPEDS-derived graduate rows shipped with ``tuition = None``, so the matcher scored graduate
budget-fit blind: live coverage was master's 8/64 (56 null) and professional 0/2.

``penn_profile`` now fills each such row from its owning school's published, first-party
tuition rate (Penn SRFS / the school, 2025-26 or 2026-27), every figure DISTINCT from the
$71,236 undergraduate sticker (never the undergrad number copied down):

- School of Arts and Sciences master's → $46,540 (standard full-time academic-graduate rate)
- School of Engineering and Applied Science master's → $70,600 (full-time year, 8 c.u. × $8,825)
- The Wharton School master's → $87,970 (the single full-time MBA)
- Graduate School of Education master's → $66,240 (full-time year, 8 c.u. × $8,280)
- Stuart Weitzman School of Design master's → $63,308 (school-wide graduate budget)
- School of Nursing master's → $57,280 (full-time year, 8 c.u. × $7,160/c.u.)
- School of Veterinary Medicine professional → $68,712 (VMD, out-of-state)
- Penn Carey Law professional → $81,796 (JD)

Tiers Penn does not publish a single citable per-program rate for — academic research
master's billed within funded Ph.D. study, per-credit graduate certificates, the Carey Law
LL.M./ML, and funded research doctorates — remain omitted-with-reason (each row's
``cost_data`` carries the reason), never guessed. After this run: master's 57/64,
professional 2/2; the 7 remaining master's nulls are honestly recorded in
``_standard.omitted`` (verify-or-omit).

Re-applies ``unipaith.data.penn_profile.apply()`` (idempotent, upserts by slug) and
re-derives ``program_preferences`` for any newly-covered row. No schema (DDL) changes;
no-op when Penn is absent, so it is safe on every environment.

Revision ID: penntuition1
Revises: harvardcip2
Create Date: 2026-06-22
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import penn_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "penntuition1"
down_revision = "harvardcip2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # apply() flushes; Alembic commits the surrounding migration transaction.
    bind = op.get_bind()
    session = Session(bind=bind)
    penn_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == penn_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    # Data-only enrichment — nothing structural to roll back.
    pass

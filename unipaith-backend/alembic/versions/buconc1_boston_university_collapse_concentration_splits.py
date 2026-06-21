"""Boston University — collapse concentration-split rows + clean disambiguator names.

Clears BU's residual structure defect (REPAIR_BACKLOG run 74 HIGH #1, miss #2): the catalog
still shipped nine ``{degree} — {concentration}`` rows. Two were true concentration splits of
an existing general sibling (GRS M.S. in CS — Artificial Intelligence; JD/MBA — Health Sector
Management) — collapsed into the keeper's ``tracks`` and dropped. The rest are genuinely
distinct programs (the M.S. in Computer Science through CAS/GRS/MET, the MET M.S. in Computer
Information Systems, the Earth & Environment B.A./M.A. keepers, the BFA in Theatre Arts) that
the dedup cascade had left with an em-dash concentration tail — renamed to clean,
school/delivery-distinguished names verified against the bu.edu/academics catalog URLs. The
two Earth & Environment graduate keepers are corrected from "M.S." to the published "M.A."
designation (URLs ".../bama-…", ".../ma-…" + descriptions).

Re-applies ``bu_profile.apply()`` (idempotent — ``_apply_programs`` deletes the now-stale
concentration rows) and re-derives program-preference rows.

Revision ID: buconc1
Revises: bupercred2
Create Date: 2026-06-21
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import bu_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "buconc1"
down_revision = "bupercred2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    bu_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == bu_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass

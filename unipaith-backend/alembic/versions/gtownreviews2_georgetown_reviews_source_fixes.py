"""Georgetown external_reviews fixes — current-year specialty ranks + independent sourcing.

Follow-up to ``gtownreviews1`` addressing automated-review feedback on the reviews depth pass:

1. **Current-year U.S. News law specialty ranks.** The International Legal Studies and National
   & Global Health Law LL.M. reviews used the 2025-26 specialty ranks; TaxProf Blog has since
   published the 2026-27 tables. Updated to the current cycle (verified first-hand): international
   law Georgetown **#2-tie** (2026-27, with Harvard behind only NYU) and health-care law **#6**
   (2026-27), each re-sourced to the 2026-27 TaxProf page.

2. **Two independent authoritative sources per review** (the manifest ``authoritative_2x`` rule).
   Added an independent second source (ABA Journal specialty omnibus) to the Environmental & Energy
   and National & Global Health Law reviews, and the independent APSIA report of the Foreign Policy
   #1 ranking to the Security Studies, Latin American Studies, and BSFS International Politics
   reviews (which previously cited only Georgetown-hosted pages).

3. **Omitted two reviews lacking an independent source.** The M.S. Finance and M.S. Management
   reviews rested solely on Georgetown's own rankings page for the QS ranks (no resolvable
   independent QS URL), so they are reverted to honest omit-with-reason rather than shipped on a
   single first-party source. Reviewed-program count goes 20 -> 18.

Re-applies ``georgetown_profile.apply()`` (idempotent) so production serves the corrected review
data, and re-derives ``program_preferences``. Idempotent and safe on a fresh/CI database.

Revision ID: gtownreviews2
Revises: gtownreviews1
Create Date: 2026-07-01
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import georgetown_profile
from unipaith.models import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "gtownreviews2"
down_revision = "gtownreviews1"
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

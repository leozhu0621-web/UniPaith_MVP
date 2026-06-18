"""De-pad Caltech + UCSD catalogs (drop fabricated certificate/non-terminal-MS rows)

Unifies the two concurrent heads on ``main`` (``seed12univ1`` from the 12-university
seed and ``ucsdprof7`` from the UCSD credential-description repair) into a single head,
and re-applies the de-fabricated Caltech and UCSD catalogs so the fabricated graduate
rows are pruned live.

What changed in the data modules this migration re-applies:
 - Caltech: drop all graduate-certificate rows (Caltech awards none) and every terminal
   Master of Science row except the three verified terminal-MS options (Aeronautics,
   Electrical Engineering, Space Engineering); drop the reviews that had been attached to
   the now-removed (nonexistent) MS programs. Source: Caltech Graduate Studies Office.
 - UCSD: drop all per-field graduate-certificate rows (UC San Diego academic departments
   award no graduate certificates — its certificates are Division of Extended Studies
   professional credentials); give the MPH its own description so it no longer shares the
   BS in Public Health body. Source: UC San Diego Graduate Degrees Offered 2026-27.

``apply()`` upserts the canonical catalog and prunes any program whose slug is no longer
canonical (delete when FK-unreferenced, else unpublish), so the fabricated rows disappear
from the live catalog. Idempotent; both applies are no-ops when the institution is absent.

Concurrent sessions shipped ``ucsdseedmerge1`` (merging the seed12univ1 + ucsdprof7
pair) and then ``ucsdprof8`` (the UCSD genuine-per-credential-descriptions + reviews
de-synthesis repair) to main while this PR was in flight, so this migration chains
after ``ucsdprof8`` — the single current head — rather than re-merging an older head
(which would recreate a dual head and fail the deploy).

Revision ID: depadcu1
Revises: ucsdprof8
Create Date: 2026-06-18
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import caltech_profile, ucsd_profile

revision = "depadcu1"
down_revision = "ucsdprof8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    caltech_profile.apply(session)
    ucsd_profile.apply(session)
    session.flush()


def downgrade() -> None:
    pass

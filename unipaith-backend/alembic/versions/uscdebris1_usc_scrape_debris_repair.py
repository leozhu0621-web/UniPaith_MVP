"""USC scrape-debris + garbled-name + concentration-split repair (REPAIR_BACKLOG CRITICAL #1)

Re-applies ``usc_profile.apply()`` after the data module was repaired:

- Replaces ~85 ``description_text`` values that were raw scraped catalogue debris
  (degree-requirements / course-code fragments, unit-count openings, contact / address
  blocks, admin notes, and a few rows whose scrape was mismatched to the wrong program)
  with researched per-program prose grounded in each program's verified owning USC school.
- Corrects five garbled program names produced by wrong/colliding ``_CODE_PREFIX`` codes
  that glued a DIFFERENT program's credential onto the field
  (Academic Medicine, the two Advanced Architectural degrees, Aging Biology, the
  MSN-FNP) plus the doubled Heritage Conservation name.
- Collapses 13 concentration-split rows into 4 base degrees carrying the variants as
  ``tracks`` (the DMA in Performance by instrument, the BA in Social Sciences by emphasis,
  the MA and PhD in Music by musicology emphasis), removing the now-absent split slugs.

The catalog is anti-stub clean and now also scrape-debris clean and frame-stripped
shared-body clean (gold MIT = 0). Idempotent: ``apply`` upserts by slug and deletes
non-canonical rows.

Revision ID: uscdebris1
Revises: uwmadpercred1
Create Date: 2026-06-20
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import usc_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "uscdebris1"
down_revision = "uwmadpercred1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    usc_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == usc_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass

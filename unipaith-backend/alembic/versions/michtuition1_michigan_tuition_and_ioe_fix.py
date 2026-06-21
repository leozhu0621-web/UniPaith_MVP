"""Michigan tuition backfill + IOE template-slot description fix (REPAIR BACKLOG run 73 #2).

Two acute live defects on the University of Michigan-Ann Arbor catalog (340+ programs):

  1. ``tuition`` was null catalog-wide (0% coverage) so the CPEF matcher scored budget-fit
     BLIND on every program. Tuition is institution-PUBLISHED, so a whole-catalog null is
     matcher STARVATION, not an honest omission. ``apply()`` now stamps the real cited
     published rate per credential level — College Scorecard's in-state UG sticker
     ($17,736) and U-M's per-term Fee Bulletin graduate/professional rate for the owning
     school (× 2 terms = academic year), with the out-of-state rate in cost_data.breakdown.
  2. The Industrial & Operations Engineering master's + PhD rows shipped machine-broken
     "research in ," / "expertise in ," grammar from a mis-parsed verb-list focus
     (template_slot_artifacts). Both rows now carry researched, credential-distinct bodies.

Re-applies ``michigan_profile.apply()`` (idempotent) and re-derives program-preference rows.

Revision ID: michtuition1
Revises: ndllmmerge1
Create Date: 2026-06-21
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import michigan_profile
from unipaith.models import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "michtuition1"
down_revision = "ndllmmerge1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    michigan_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == michigan_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass

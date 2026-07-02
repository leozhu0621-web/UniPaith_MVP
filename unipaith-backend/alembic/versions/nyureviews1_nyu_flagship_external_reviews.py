"""NYU external_reviews depth pass — 11 coverable flagship programs.

Structure is clean fleet-wide, so the miss-#8 STRUCTURE-BEFORE-DEPTH order unblocks the
reviews depth pass (REPAIR_BACKLOG #5). NYU shipped external_reviews on only 3 of 502
programs (Stern Full-Time MBA, Law J.D., Tisch Film & TV BFA); this pass adds 11 more
hand-gathered, program-specific reviews across the coverable flagship set:

- Stern undergraduate BS in Business (Poets&Quants No. 5, 2025)
- Stern MS in Business Analytics and AI (executive analytics credential)
- Grossman School of Medicine MD (tuition-free since 2018)
- Courant MS in Mathematics in Finance (QuantNet financial-engineering ranking)
- Wagner MPA in Public and Nonprofit Management and Policy (U.S. News No. 1 urban policy)
- Silver MSW (U.S. News No. 12, 2024)
- School of Global Public Health MPH (CEPH-accredited, U.S. News No. 27)
- College of Dentistry DDS (largest U.S. dental school)
- Courant MS in Computer Science (U.S. News CS No. 30)
- Center for Data Science MS in Data Science
- Rory Meyers traditional four-year BS in Nursing (U.S. News No. 9, 2022)

Each review is read off real third-party coverage (Poets&Quants, U.S. News, QuantNet,
official employment/outcome reports, CEPH, and reputable review communities), summarized in
the MBAn shape with program-specific themes that include the common cautions, and cited with
resolvable sources. No synthesized-from-metadata reviews; every other NYU program keeps
``external_reviews`` in its ``_standard.omitted`` until genuine coverage exists.

Idempotent: re-applies ``nyu_profile.apply()`` (which sets external_reviews from
``_REVIEWS_BY_SLUG`` and drops ``external_reviews.summary`` from the covered rows' omitted
list) and re-derives program-preference rows.

Revision ID: nyureviews1
Revises: rochprof1
Create Date: 2026-07-02
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import nyu_profile
from unipaith.models import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "nyureviews1"
down_revision = "rochprof1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    nyu_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == nyu_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass

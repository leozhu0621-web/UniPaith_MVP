"""enrich University of Southern California (USC) profile (data-only, no DDL)

Populates USC's canonical profile — rankings (QS #146, THE #73, U.S. News #28
National), ownership/Carnegie/accreditor classification, school_outcomes depth
(report-card stats, admissions funnel, demographics, scale with endowment,
research with lab links, campus life with resource links, location, a verified
5-photo campus gallery, flagship facts, sources), a character-leading intro, its
21 real degree-granting schools/academic units (the Dornsife College plus the
Viterbi, Marshall, Keck Medicine, Gould Law, Price, Rossier, Annenberg, Cinematic
Arts, Thornton, Ostrow Dentistry, Mann Pharmacy, Architecture, Roski, Dramatic
Arts, Leonard Davis Gerontology, Dworak-Peck Social Work, Leventhal Accounting,
Kaufman Dance, Iovine and Young, and Bovard schools — each with sourced About-tab
detail and its own content_sources), and the FULL published degree catalog (613
degree programs built from the official USC Catalogue "Programs by School", each
mapped to its owning school, with delivery_format set on the online/Bovard
programs). Flagship coverable programs (the Marshall Full-Time MBA, the Gould
J.D., plus Computer Science, the M.D., the M.S. in Computer Science, Cinematic
Arts, Journalism, the undergraduate business program, and the M.P.A.) carry
external_reviews and, for the MBA and J.D., verified employment outcomes — via
``unipaith.data.usc_profile.apply()``.

No schema (DDL) changes. The enrichment is idempotent and a no-op when USC is
absent, so this migration is safe on every environment (and on CI databases built
with ``create_all``, which never run migrations anyway). It ships to production
automatically: the container entrypoint runs ``alembic upgrade heads`` before
serving.

Revision ID: uscprof1
Revises: onboardstate1
Create Date: 2026-06-13
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import usc_profile

revision = "uscprof1"
# Chain off the current single head so the migration chain stays single-headed.
down_revision = "onboardstate1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # apply() flushes; Alembic commits the surrounding migration transaction.
    session = Session(bind=op.get_bind())
    usc_profile.apply(session)
    session.flush()


def downgrade() -> None:
    # Data-only enrichment — nothing structural to roll back.
    pass

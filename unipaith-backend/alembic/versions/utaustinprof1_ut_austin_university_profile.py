"""enrich The University of Texas at Austin profile (data-only, no DDL)

Populates UT Austin's canonical gold-standard profile — rankings (QS #68, THE #50,
U.S. News #30 National, Carnegie R1, SACSCOC), school_outcomes depth (admissions
funnel 72,885 → 19,417 → 9,210, test scores, financial aid, demographics, campus
location, scale, research labs with links, campus-life resources, a verified
5-photo Wikimedia Commons gallery, flagship facts, sources), a rich intro, the 18
real colleges/schools (each with sourced About-tab detail + content_sources), and
the full 338-program degree catalog across them — including UT's 100%-online
master's degrees (MSCS, MSDS, MSAI) and verified external_reviews + employment
outcomes on the flagship coverable programs — via
``unipaith.data.ut_austin_profile.apply()``.

No schema (DDL) changes. The enrichment is idempotent and a no-op when UT Austin is
absent, so this migration is safe on every environment (and on CI databases built
with ``create_all``, which never run migrations anyway). It ships to production
automatically: the container entrypoint runs ``alembic upgrade heads`` before
serving.

Revision ID: utaustinprof1
Revises: onboardstate1
Create Date: 2026-06-13
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import ut_austin_profile

revision = "utaustinprof1"
down_revision = "uscprof1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # apply() flushes; Alembic commits the surrounding migration transaction.
    session = Session(bind=op.get_bind())
    ut_austin_profile.apply(session)
    session.flush()


def downgrade() -> None:
    # Data-only enrichment — nothing structural to roll back.
    pass

"""enrich University of Washington (Seattle) profile (data-only, no DDL)

Populates UW's canonical profile — rankings (U.S. News #42 National / #16 public,
QS #81, THE #25, Carnegie R1, NWCCU), school_outcomes depth (Fall 2024 admissions
funnel 69,166/27,076/7,196, financial aid, demographics, campus location, scale
incl. the ~$5.34B endowment and 20:1 ratio, research labs with links, campus-life
resources with links, a verified 5-photo Wikimedia Commons gallery, flagship facts,
and sources; test_scores omitted because UW is test-blind), a public-research-
university intro, its 16 real degree-granting colleges/schools plus the
interdisciplinary Graduate School (each with sourced About-tab leadership + units
and content_sources), and the FULL 365-program degree catalog parsed from the
official UW General Catalog indexes (plus the professional M.D./D.D.S./J.D./
PharmD/DNP/DPT/AuD and UW's online degrees via UW Professional & Continuing
Education) with delivery_format and content_sources on every program, and
external_reviews on the flagship coverable programs — via
``unipaith.data.uw_profile.apply()``.

No schema (DDL) changes. The enrichment is idempotent and a no-op when UW is
absent, so this migration is safe on every environment (and on CI databases built
with ``create_all``, which never run migrations anyway). It ships to production
automatically: the container entrypoint runs ``alembic upgrade heads`` before
serving.

Revision ID: uwprof1
Revises: onboardstate1
Create Date: 2026-06-13
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import uw_profile

revision = "uwprof1"
down_revision = "uiucprof1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # apply() flushes; Alembic commits the surrounding migration transaction.
    session = Session(bind=op.get_bind())
    uw_profile.apply(session)
    session.flush()


def downgrade() -> None:
    # Data-only enrichment — nothing structural to roll back.
    pass

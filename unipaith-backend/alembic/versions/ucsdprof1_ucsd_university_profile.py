"""enrich University of California-San Diego profile (data-only, no DDL)

Populates UCSD's canonical profile — rankings (U.S. News #29 National, QS #66,
THE #47, Carnegie R1, WSCUC), school_outcomes depth (College Scorecard +
Campus Profile, financial aid, demographics, campus location, scale incl.
the ~$3.29B endowment and 26:1 ratio, research labs with links, campus-life
resources with links, a verified 5-photo Wikimedia Commons gallery, flagship facts,
and sources), a public research-university intro, its 12 real schools (each with
sourced About-tab leadership + units and content_sources), and the FULL
194-program degree catalog from the College Scorecard Field-of-Study list mapped to
UCSD schools (plus explicit MD/PharmD flagships) with delivery_format and
content_sources on every program, and external_reviews on flagship coverable
programs — via ``unipaith.data.ucsd_profile.apply()``.

No schema (DDL) changes. Idempotent; no-op when UCSD is absent.

Revision ID: ucsdprof1
Revises: purdueprof1
Create Date: 2026-06-13
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import ucsd_profile

revision = "ucsdprof1"
down_revision = "purdueprof1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    ucsd_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass

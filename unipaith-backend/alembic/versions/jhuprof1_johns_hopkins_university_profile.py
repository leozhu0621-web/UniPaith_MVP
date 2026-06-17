"""enrich Johns Hopkins University profile (data-only, no DDL)

Populates JHU's canonical profile — rankings (U.S. News #7 National, QS #24,
THE #16, Carnegie R1, MSCHE), school_outcomes depth (College Scorecard +
institutional research, financial aid, demographics, campus location, scale incl.
the ~$13.06B endowment and 6:1 ratio, research labs with links, campus-life
resources with links, a verified 5-photo Wikimedia Commons gallery, flagship facts,
and sources), a private-research-university intro, its 10 real schools
(each with sourced About-tab leadership + units and content_sources), and the FULL
249-program degree catalog from the College Scorecard Field-of-Study list mapped to
JHU schools (plus explicit flagships) with delivery_format and content_sources on
every program, and external_reviews on flagship coverable programs — via
``unipaith.data.jhu_profile.apply()``.

No schema (DDL) changes. Idempotent; no-op when JHU is absent.

Revision ID: jhuprof1
Revises: buprof1
Create Date: 2026-06-13
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import jhu_profile

revision = "jhuprof1"
down_revision = "buprof1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    jhu_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass

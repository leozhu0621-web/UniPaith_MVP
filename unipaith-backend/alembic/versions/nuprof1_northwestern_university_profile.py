"""enrich Northwestern University profile (data-only, no DDL)

Populates Northwestern's canonical profile — rankings (U.S. News #7 National, QS #42,
THE #30, Carnegie R1, HLC), school_outcomes depth (College Scorecard +
institutional research, financial aid, demographics, campus location, scale incl.
the ~$15.3B endowment and 6:1 ratio, research labs with links, campus-life
resources with links, a verified 5-photo Wikimedia Commons gallery, flagship facts,
and sources), a private-research-university intro, its 11 real schools
(each with sourced About-tab leadership + units and content_sources), and the FULL
308-program degree catalog from the College Scorecard Field-of-Study list mapped to
Northwestern schools (plus explicit flagships) with delivery_format and content_sources on
every program, and external_reviews on flagship coverable programs — via
``unipaith.data.northwestern_profile.apply()``.

No schema (DDL) changes. Idempotent; no-op when Northwestern is absent.

Revision ID: nuprof1
Revises: jhuprof1
Create Date: 2026-06-13
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import northwestern_profile

revision = "nuprof1"
down_revision = "jhuprof1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    northwestern_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass

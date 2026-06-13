"""enrich Purdue University-Main Campus profile (data-only, no DDL)

Populates Purdue's canonical profile — rankings (U.S. News #46 National, QS #88,
THE #85, Carnegie R1, HLC), school_outcomes depth (College Scorecard +
institutional research, financial aid, demographics, campus location, scale incl.
the ~$4.4B endowment and 15:1 ratio, research labs with links, campus-life
resources with links, a verified 5-photo Wikimedia Commons gallery, flagship facts,
and sources), a public land-grant research-university intro, its 10 real schools
(each with sourced About-tab leadership + units and content_sources), and the FULL
310-program degree catalog from the College Scorecard Field-of-Study list mapped to
Purdue schools (plus explicit flagships) with delivery_format and content_sources on
every program, and external_reviews on flagship coverable programs — via
``unipaith.data.purdue_profile.apply()``.

No schema (DDL) changes. Idempotent; no-op when Purdue is absent.

Revision ID: purdueprof1
Revises: nuprof1
Create Date: 2026-06-13
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import purdue_profile

revision = "purdueprof1"
down_revision = "nuprof1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    purdue_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass

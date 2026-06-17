"""enrich University of Wisconsin-Madison profile (data-only, no DDL)

Populates UW-Madison's canonical profile — rankings (U.S. News #36 National, QS #110,
THE #53, Carnegie R1, HLC), school_outcomes depth (College Scorecard + UW Facts,
financial aid, demographics, campus location, scale incl. the ~$4.9B endowment and
17:1 ratio, research labs with links, campus-life resources with links, a verified
5-photo Wikimedia Commons gallery, flagship facts, and sources), a public research-
university intro, its 15 real schools (each with sourced About-tab leadership +
units and content_sources), and the FULL ~350-program degree catalog from the College
Scorecard Field-of-Study list mapped to UW-Madison schools (plus explicit MD/PharmD/
DVM/JD/MBA flagships) with delivery_format and content_sources on every program, and
external_reviews on flagship coverable programs — via ``unipaith.data.uw_madison_profile.apply()``.

No schema (DDL) changes. Idempotent; no-op when UW-Madison is absent.

Revision ID: uwmadprof1
Revises: ucsdprof1
Create Date: 2026-06-14
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import uw_madison_profile

revision = "uwmadprof1"
down_revision = "ucsdprof1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    uw_madison_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass

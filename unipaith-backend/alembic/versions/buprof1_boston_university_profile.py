"""enrich Boston University profile (data-only, no DDL)

Populates BU's canonical profile — rankings (U.S. News #42 National, QS #88,
THE #76, Carnegie R1, NECHE), school_outcomes depth (Fall 2024 admissions funnel
78,769/8,749/3,268, financial aid, demographics, campus location, scale incl.
the ~$3.53B endowment and 11:1 ratio, research labs with links, campus-life
resources with links, a verified 5-photo Wikimedia Commons gallery, flagship facts,
and sources), a private-research-university intro, its 22 real schools/colleges
(each with sourced About-tab leadership + units and content_sources), and the FULL
483-program degree catalog parsed from the official BU Academics degree-programs
index (plus CGS and ROTC) with delivery_format and content_sources on every program,
and external_reviews on flagship coverable programs — via
``unipaith.data.bu_profile.apply()``.

No schema (DDL) changes. Idempotent; no-op when BU is absent.

Revision ID: buprof1
Revises: onboardstate1
Create Date: 2026-06-13
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import bu_profile

revision = "buprof1"
down_revision = "onboardstate1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    bu_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass

"""enrich University of Illinois Urbana-Champaign profile (data-only, no DDL)

Populates UIUC's canonical profile — rankings (U.S. News #36 National / #12 public,
QS #70, THE #41, Carnegie R1, HLC), school_outcomes depth (Fall 2024 admissions
funnel 73,742/31,247/9,008, financial aid, demographics, SAT/ACT test scores,
campus location, scale incl. the ~$2.6B endowment and 18:1 ratio, research labs
with links, campus-life resources with links, a verified 5-photo Wikimedia Commons
gallery, flagship facts, and sources), a land-grant-research-university intro, its
14 real degree-granting colleges/schools (each with sourced About-tab leadership +
units and content_sources), and the FULL 419-program degree catalog parsed from the
official UIUC Academic Catalog indexes (plus the professional J.D./M.D./D.V.M. and
the flagship Coursera online degrees — iMBA, iMSA, iMSM, and the online MCS) with
delivery_format and content_sources on every program, and external_reviews on 19
flagship coverable programs — via ``unipaith.data.uiuc_profile.apply()``.

No schema (DDL) changes. The enrichment is idempotent and a no-op when UIUC is
absent, so this migration is safe on every environment (and on CI databases built
with ``create_all``, which never run migrations anyway). It ships to production
automatically: the container entrypoint runs ``alembic upgrade heads`` before
serving.

Revision ID: uiucprof1
Revises: onboardstate1
Create Date: 2026-06-13
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import uiuc_profile

revision = "uiucprof1"
down_revision = "utaustinprof1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # apply() flushes; Alembic commits the surrounding migration transaction.
    session = Session(bind=op.get_bind())
    uiuc_profile.apply(session)
    session.flush()


def downgrade() -> None:
    # Data-only enrichment — nothing structural to roll back.
    pass

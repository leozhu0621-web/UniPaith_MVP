"""enrich University of Michigan-Ann Arbor profile (data-only, no DDL)

Populates Michigan's canonical profile — rankings (QS #45, THE #23, U.S. News #20
National; Carnegie R1; HLC accreditation), school_outcomes depth (admissions
funnel 98,310/15,373 for Fall 2024, test scores, financial aid, demographics,
campus location, scale, research with links, campus-life resources, a verified
5-photo campus gallery, flagship facts, sources), a rich intro, the 19 real
schools and colleges (with sourced About-tab detail + content_sources), and the
full published 379-program degree catalog mapped to its owning school (with the
Ross Full-Time MBA and Michigan Law J.D. as the most-enriched flagships) — via
``unipaith.data.michigan_profile.apply()``.

No schema (DDL) changes. The enrichment is idempotent and a no-op when Michigan
is absent, so this migration is safe on every environment (and on CI databases
built with ``create_all``, which never run migrations anyway). It ships to
production automatically: the container entrypoint runs ``alembic upgrade heads``
before serving.

Revision ID: michprof1
Revises: onboardstate1
Create Date: 2026-06-13
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import michigan_profile

revision = "michprof1"
down_revision = "nyuprof1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # apply() flushes; Alembic commits the surrounding migration transaction.
    session = Session(bind=op.get_bind())
    michigan_profile.apply(session)
    session.flush()


def downgrade() -> None:
    # Data-only enrichment — nothing structural to roll back.
    pass

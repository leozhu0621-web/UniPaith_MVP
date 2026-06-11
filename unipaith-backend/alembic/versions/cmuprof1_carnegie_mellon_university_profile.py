"""enrich Carnegie Mellon University profile (data-only, no DDL)

Populates Carnegie Mellon's canonical profile — rankings (QS #52, THE #24, U.S.
News #20), ownership/Carnegie/accreditor, school_outcomes depth (report-card key
stats, admissions funnel, financial aid, demographics, test scores, campus
location, scale, research labs WITH links, campus-life resources WITH links,
flagship facts, sources), a rich character-leading intro, the seven real
degree-granting colleges/schools (with sourced About-tab detail), and Carnegie
Mellon's undergraduate program catalog across them (with the Computer Science
major as the most-enriched flagship) — via
``unipaith.data.cmu_profile.apply()``.

No schema (DDL) changes. The enrichment is idempotent and a no-op when Carnegie
Mellon is absent, so this migration is safe on every environment (and on CI
databases built with ``create_all``, which never run migrations anyway). It ships
to production automatically: the container entrypoint runs ``alembic upgrade
heads`` before serving.

Revision ID: cmuprof1
Revises: feedsforce1
Create Date: 2026-06-10
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import cmu_profile

revision = "cmuprof1"
down_revision = "feedsforce1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # apply() flushes; Alembic commits the surrounding migration transaction.
    session = Session(bind=op.get_bind())
    cmu_profile.apply(session)
    session.flush()


def downgrade() -> None:
    # Data-only enrichment — nothing structural to roll back.
    pass

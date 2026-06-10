"""enrich University of Chicago profile (data-only, no DDL)

Populates UChicago's canonical profile — rankings (QS #13, THE #15, U.S. News #6),
school_outcomes depth (admissions funnel, financial aid, demographics, test scores,
campus location, scale incl. the $10.4B FY24 endowment, research, first-destination
outcomes, flagship facts, sources), a rich intro, its real degree-granting schools (the
College, Booth, Harris, the Law School, Pritzker Medicine, Crown Family, the Divinity
School, Pritzker Molecular Engineering and the Physical Sciences, Social Sciences and
Humanities Divisions — each with sourced About-tab detail), and a program catalog across
them built from the College Scorecard Field-of-Study list for UNITID 144050 (with the
Booth Full-Time MBA as the most-enriched flagship) — via
``unipaith.data.chicago_profile.apply()``.

No schema (DDL) changes. The enrichment is idempotent and a no-op when UChicago is
absent, so this migration is safe on every environment (and on CI databases built with
``create_all``, which never run migrations anyway). It ships to production automatically:
the container entrypoint runs ``alembic upgrade heads`` before serving.

Revision ID: chicagoprof1
Revises: yaleprof1
Create Date: 2026-06-10
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import chicago_profile

revision = "chicagoprof1"
down_revision = "yaleprof1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # apply() flushes; Alembic commits the surrounding migration transaction.
    session = Session(bind=op.get_bind())
    chicago_profile.apply(session)
    session.flush()


def downgrade() -> None:
    # Data-only enrichment — nothing structural to roll back.
    pass

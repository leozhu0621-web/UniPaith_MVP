"""enrich Princeton University profile (data-only, no DDL)

Populates Princeton's canonical profile — rankings (QS #25, THE joint #3, U.S. News #1),
school_outcomes depth (admissions funnel, financial aid, demographics, test scores,
campus location, scale incl. the $36.4B endowment, research, flagship facts, sources),
a rich intro, its real degree-granting academic units (School of Engineering and Applied
Science, the School of Public and International Affairs, and the Humanities / Social
Sciences / Natural Sciences faculty divisions, each with sourced About-tab detail), and a
program catalog across them built from the complete College Scorecard Field-of-Study list
for UNITID 186131 (with Computer Science as the most-enriched flagship) — via
``unipaith.data.princeton_profile.apply()``.

No schema (DDL) changes. The enrichment is idempotent and a no-op when Princeton is
absent, so this migration is safe on every environment (and on CI databases built with
``create_all``, which never run migrations anyway). It ships to production automatically:
the container entrypoint runs ``alembic upgrade heads`` before serving.

Revision ID: princetonprof1
Revises: harvardprof3
Create Date: 2026-06-10
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import princeton_profile

revision = "princetonprof1"
down_revision = "harvardprof3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # apply() flushes; Alembic commits the surrounding migration transaction.
    session = Session(bind=op.get_bind())
    princeton_profile.apply(session)
    session.flush()


def downgrade() -> None:
    # Data-only enrichment — nothing structural to roll back.
    pass

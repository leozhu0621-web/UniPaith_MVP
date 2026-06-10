"""enrich California Institute of Technology profile (data-only, no DDL)

Populates Caltech's canonical profile — rankings (QS #10, THE #7, US News #11),
school_outcomes depth (admissions funnel, test scores, financial aid, demographics,
campus location, scale, research, flagship facts, sources), a rich intro, the six
real academic divisions (with sourced About-tab detail), and a program catalog
across them (with the Computer Science option as the most-enriched flagship) — via
``unipaith.data.caltech_profile.apply()``.

No schema (DDL) changes. The enrichment is idempotent and a no-op when Caltech is
absent, so this migration is safe on every environment (and on CI databases built
with ``create_all``, which never run migrations anyway). It ships to production
automatically: the container entrypoint runs ``alembic upgrade heads`` before
serving.

Revision ID: caltechprof1
Revises: stanfordprof1
Create Date: 2026-06-10
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import caltech_profile

revision = "caltechprof1"
down_revision = "stanfordprof1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # apply() flushes; Alembic commits the surrounding migration transaction.
    session = Session(bind=op.get_bind())
    caltech_profile.apply(session)
    session.flush()


def downgrade() -> None:
    # Data-only enrichment — nothing structural to roll back.
    pass

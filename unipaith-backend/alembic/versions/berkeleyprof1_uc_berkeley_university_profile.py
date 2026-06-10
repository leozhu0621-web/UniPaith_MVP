"""enrich University of California, Berkeley profile (data-only, no DDL)

Populates UC Berkeley's canonical profile — rankings (QS #17, THE #9, US News #15 /
#1 public), school_outcomes depth (admissions funnel, financial aid, demographics,
campus location, scale, research, flagship facts, sources), a rich intro, the seven
real undergraduate-degree-granting colleges (with sourced About-tab detail), and an
undergraduate program catalog across them (with the EECS major as the most-enriched
flagship) — via ``unipaith.data.berkeley_profile.apply()``.

No schema (DDL) changes. The enrichment is idempotent and a no-op when Berkeley is
absent, so this migration is safe on every environment (and on CI databases built
with ``create_all``, which never run migrations anyway). It ships to production
automatically: the container entrypoint runs ``alembic upgrade heads`` before
serving.

Revision ID: berkeleyprof1
Revises: caltechprof1
Create Date: 2026-06-10
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import berkeley_profile

revision = "berkeleyprof1"
down_revision = "caltechprof1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # apply() flushes; Alembic commits the surrounding migration transaction.
    session = Session(bind=op.get_bind())
    berkeley_profile.apply(session)
    session.flush()


def downgrade() -> None:
    # Data-only enrichment — nothing structural to roll back.
    pass

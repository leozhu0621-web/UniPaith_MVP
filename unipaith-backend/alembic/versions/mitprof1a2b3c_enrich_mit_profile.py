"""enrich MIT institution profile (data-only, no DDL)

Populates MIT's canonical profile — rankings (QS #1, THE #2, US News #2),
school_outcomes depth (test scores, financial aid, demographics, campus
location, flagship facts, sources), a rich intro, the six real academic units,
and the program catalog — via ``unipaith.data.mit_profile.apply()``.

No schema (DDL) changes. The enrichment is idempotent and a no-op when MIT is
absent, so this migration is safe on every environment (and on CI databases
built with ``create_all``, which never run migrations anyway). It ships to
production automatically: the container entrypoint runs ``alembic upgrade
heads`` before serving.

Revision ID: mitprof1a2b3c
Revises: p65embed1a2b3
Create Date: 2026-06-06
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import mit_profile

revision = "mitprof1a2b3c"
down_revision = "p65embed1a2b3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # apply() flushes; Alembic commits the surrounding migration transaction.
    session = Session(bind=op.get_bind())
    mit_profile.apply(session)
    session.flush()


def downgrade() -> None:
    # Data-only enrichment — nothing structural to roll back.
    pass

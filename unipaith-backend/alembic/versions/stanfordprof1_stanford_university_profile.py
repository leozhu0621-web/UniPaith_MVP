"""enrich Stanford University profile (data-only, no DDL)

Populates Stanford's canonical profile — rankings (QS #3, THE #6, US News #4),
school_outcomes depth (test scores, financial aid, demographics, campus location,
flagship facts, sources), a rich intro, the seven real schools (with sourced
About-tab detail), and a program catalog (with the Stanford GSB MBA as the fully
enriched flagship) — via ``unipaith.data.stanford_profile.apply()``.

No schema (DDL) changes. The enrichment is idempotent and a no-op when Stanford is
absent, so this migration is safe on every environment (and on CI databases built
with ``create_all``, which never run migrations anyway). It ships to production
automatically: the container entrypoint runs ``alembic upgrade heads`` before
serving.

Revision ID: stanfordprof1
Revises: mbanoutcomes1
Create Date: 2026-06-10
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import stanford_profile

revision = "stanfordprof1"
down_revision = "mbanoutcomes1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # apply() flushes; Alembic commits the surrounding migration transaction.
    session = Session(bind=op.get_bind())
    stanford_profile.apply(session)
    session.flush()


def downgrade() -> None:
    # Data-only enrichment — nothing structural to roll back.
    pass

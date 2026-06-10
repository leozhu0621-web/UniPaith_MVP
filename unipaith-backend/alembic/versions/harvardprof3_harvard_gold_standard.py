"""bring Harvard University profile to the gold standard (data-only, no DDL)

Re-applies ``unipaith.data.harvard_profile.apply()`` now that the module carries the
profile-standard scaffolding: every node stamped with its ``_standard`` provenance,
the institution faculty headcount + Harvard Gazette feed, verified ``about_detail``
(founded / dean / research centers) for all twelve schools, and the flagship Harvard
Business School MBA brought to full conformance — its own employment report
(Class of 2025), entering class profile (Class of 2027), faculty leads, aggregated
reviews, application deadlines, and HBS feeds.

No schema (DDL) changes. The enrichment is idempotent and a no-op when Harvard is
absent, so this migration is safe on every environment (and on CI databases built
with ``create_all``, which never run migrations anyway). It ships to production
automatically: the container entrypoint runs ``alembic upgrade heads`` before serving.

Revision ID: harvardprof3
Revises: berkeleyprof1
Create Date: 2026-06-10
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import harvard_profile

revision = "harvardprof3"
down_revision = "berkeleyprof1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # apply() flushes; Alembic commits the surrounding migration transaction.
    session = Session(bind=op.get_bind())
    harvard_profile.apply(session)
    session.flush()


def downgrade() -> None:
    # Data-only enrichment — nothing structural to roll back.
    pass

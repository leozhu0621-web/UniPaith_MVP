"""re-apply Columbia profile — clean curated program catalog (data-only, no DDL)

Re-runs ``unipaith.data.columbia_profile.apply()`` after the reconciliation fix so the
live Columbia catalog shows ONLY the curated, gold programs. The initial ``columbiaprof1``
enrichment left the pre-seeded Columbia programs published alongside the 13 curated ones
(35 total — duplicate subjects on the student-facing page). ``apply()`` now reconciles
every non-canonical program (unpublish when referenced by an application/match, otherwise
delete), matching the clean-catalog behaviour of the full-university profiles; deferred
subjects return as curated programs in the resume run.

No schema (DDL) changes. Idempotent and a no-op when Columbia is absent, so it is safe on
every environment (and on CI databases built with ``create_all``). It ships to production
automatically via the container entrypoint's ``alembic upgrade heads``.

Revision ID: columbiaprof2
Revises: columbiaprof1
Create Date: 2026-06-10
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import columbia_profile

revision = "columbiaprof2"
down_revision = "columbiaprof1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # apply() flushes; Alembic commits the surrounding migration transaction.
    session = Session(bind=op.get_bind())
    columbia_profile.apply(session)
    session.flush()


def downgrade() -> None:
    # Data-only enrichment — nothing structural to roll back.
    pass

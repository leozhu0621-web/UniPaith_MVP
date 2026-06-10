"""finish Columbia University profile — resume run to the gold standard (data-only)

Resumes and completes Columbia University in the City of New York (UNITID 190150). Prior
runs shipped a verified partial (``columbiaprof1``, institution + 5 schools + 13 programs,
MBA flagship) and a clean-catalog fix (``columbiaprof2``). This run brings the WHOLE tree
to the gold standard: the institution node (now with the verified university-wide
full-time faculty count, 4,787, from Columbia OPIR "Columbia Facts 2024", and the
corrected U.S. News 2026 rank #15), **12** real degree-granting schools, and **25**
programs across them, with BOTH the Columbia Business School MBA and undergraduate
Computer Science as deeply-enriched flagships — via the updated
``unipaith.data.columbia_profile.apply()``.

Because the earlier revisions already ran on production, this separate revision re-invokes
``apply()`` so the now-richer, fully-verified data is persisted. ``apply()`` is idempotent
and reconciles the catalog (upserts the canonical schools/programs, removes legacy rows
FK-safely), so re-running converges cleanly to the complete tree.

No schema (DDL) changes. A no-op when Columbia is absent, so it is safe on every
environment (and on CI databases built with ``create_all``, which never run migrations).

Revision ID: columbiaprof3
Revises: columbiaprof2
Create Date: 2026-06-10
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import columbia_profile

revision = "columbiaprof3"
down_revision = "columbiaprof2"
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

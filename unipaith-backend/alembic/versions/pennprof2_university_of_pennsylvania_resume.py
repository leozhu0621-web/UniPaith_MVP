"""resume University of Pennsylvania profile — add MD + JD programs (data-only, no DDL)

Resume run for Penn's whole-tree enrichment. The first run (``pennprof1``) enriched the
institution and all twelve schools but left the graduate/professional schools without a
program catalog. This run adds the first two professional flagship programs — the
Perelman School of Medicine **Doctor of Medicine (MD)** and the University of
Pennsylvania Carey Law School **Juris Doctor (JD)** — each carrying a first-party-verified
cost of attendance (PSOM MD student budget 2026-27; Penn SRFS JD cost of attendance
2026-27) and a verified admissions set (AMCAS / LSAC). Both reach the established Penn
program bar (all verifiable required fields filled; the uniform insight fields recorded
in ``_standard.omitted``).

Re-applies ``unipaith.data.penn_profile.apply()``, which is fully idempotent (upserts by
slug), so re-running only adds/updates the new programs and leaves the rest untouched.

No schema (DDL) changes. No-op when Penn is absent, so it is safe on every environment.

Revision ID: pennprof2
Revises: pennprof1
Create Date: 2026-06-10
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import penn_profile

revision = "pennprof2"
down_revision = "pennprof1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # apply() flushes; Alembic commits the surrounding migration transaction.
    session = Session(bind=op.get_bind())
    penn_profile.apply(session)
    session.flush()


def downgrade() -> None:
    # Data-only enrichment — nothing structural to roll back.
    pass

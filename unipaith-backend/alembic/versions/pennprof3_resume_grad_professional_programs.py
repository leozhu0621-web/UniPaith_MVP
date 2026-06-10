"""resume Penn profile — add the six graduate/professional flagship programs (data-only)

Final resume run for Penn's whole-tree enrichment. ``pennprof1`` enriched the institution
and all twelve schools; ``pennprof2`` added the Perelman MD and Penn Carey Law JD. This run
completes the tree by adding a verified flagship degree for each of the remaining six
graduate/professional schools, so every one of Penn's twelve schools now carries at least
one fully enriched program:

- School of Dental Medicine — **Doctor of Dental Medicine (DMD)**
- School of Veterinary Medicine — **Doctor of Veterinary Medicine (VMD)**
- Stuart Weitzman School of Design — **Master of Architecture (M.Arch)**
- School of Social Policy & Practice — **Master of Social Work (MSW)**
- Graduate School of Education — **Higher Education (M.S.Ed.)**
- Annenberg School for Communication — **Communication (PhD)**

Each program carries a first-party-verified cost of attendance (official Penn SRFS / school
budgets, 2025-26 or 2026-27) and a verified admissions set, and reaches the established Penn
program bar (all verifiable required fields filled; the uniform insight fields and any
unverifiable field — e.g. the Penn GSE deadline served only via a dynamic dropdown —
recorded in each program's ``_standard.omitted`` rather than guessed).

Re-applies ``unipaith.data.penn_profile.apply()``, which is fully idempotent (upserts by
slug), so re-running only adds/updates the new programs and leaves the rest untouched.

No schema (DDL) changes. No-op when Penn is absent, so it is safe on every environment.

Revision ID: pennprof3
Revises: pennprof2
Create Date: 2026-06-10
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import penn_profile

revision = "pennprof3"
down_revision = "pennprof2"
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

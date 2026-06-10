"""finish University of Pennsylvania profile — every school now has programs (data-only)

Final resume run for Penn's whole-tree enrichment. ``pennprof1`` enriched the institution
and all twelve schools; ``pennprof2`` added the first two professional flagships (Perelman
MD, Penn Carey Law JD). This run completes the tree by giving every remaining school its
flagship program, so all twelve schools now carry a program catalog:

- School of Dental Medicine — **Doctor of Dental Medicine (DMD)**
- School of Veterinary Medicine — **Doctor of Veterinary Medicine (VMD)**
- Stuart Weitzman School of Design — **Master of Architecture (M.Arch)**
- School of Social Policy and Practice — **Master of Social Work (MSW)**
- Graduate School of Education — **Higher Education (M.S.Ed.)**
- Annenberg School for Communication — **Communication (Ph.D.)** (fully funded)
- School of Engineering and Applied Science — **MAS-CS Online** (fully ONLINE)

Each carries a first-party-verified cost of attendance (SRFS / school budgets, 2026-27;
Weitzman M.Arch estimated cost) and a verified admissions set (AADSAS / VMCAS / Weitzman /
SP2 / GSE / Annenberg / Penn Engineering Online). Every node reaches the established Penn
program bar (all verifiable required fields filled; the uniform insight fields recorded in
``_standard.omitted``). ``delivery_format`` is set on every program, including the online
MAS-CS degree.

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

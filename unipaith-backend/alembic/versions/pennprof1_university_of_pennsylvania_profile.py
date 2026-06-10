"""enrich University of Pennsylvania profile (data-only, no DDL)

Populates Penn's canonical profile — rankings (QS #15, THE #14, U.S. News #7),
school_outcomes depth (admissions funnel, financial aid, demographics, test scores,
campus location, scale incl. the $24.81B endowment, research, flagship facts, sources),
a rich intro, its twelve real dean-led schools (Arts & Sciences, Wharton, Engineering,
Nursing, Perelman Medicine, Carey Law, GSE, Dental, Weitzman Design, SP2, Vet,
Annenberg — each with sourced About-tab detail), and an undergraduate + Wharton-MBA
program catalog across them (with the Wharton MBA as the most-enriched flagship,
carrying its official Class-of-2024 employment report) — via
``unipaith.data.penn_profile.apply()``.

No schema (DDL) changes. The enrichment is idempotent and a no-op when Penn is absent,
so this migration is safe on every environment (and on CI databases built with
``create_all``, which never run migrations anyway). It ships to production automatically:
the container entrypoint runs ``alembic upgrade heads`` before serving.

Revision ID: pennprof1
Revises: columbiaprof3
Create Date: 2026-06-10
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import penn_profile

revision = "pennprof1"
down_revision = "columbiaprof3"
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

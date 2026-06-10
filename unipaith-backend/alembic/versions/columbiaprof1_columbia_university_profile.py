"""enrich Columbia University profile — verified partial (data-only, no DDL)

Populates Columbia's canonical profile — rankings (QS #38, THE #20, U.S. News #13),
school_outcomes depth (admissions funnel, financial aid, demographics, test scores,
campus location, scale incl. the $14.8B endowment, research, first-destination outcomes,
flagship facts, sources; instructional-faculty headline honestly omitted), a rich intro,
five of its real degree-granting schools (Columbia College, the Fu Foundation School of
Engineering and Applied Science, Columbia Business School, SIPA and the Journalism School,
each with sourced About-tab detail), and a program catalog across them built from the
College Scorecard Field-of-Study list for UNITID 190150 plus the Columbia Business School
MBA as the most-enriched flagship — via ``unipaith.data.columbia_profile.apply()``.

Columbia is a giant; this is a VERIFIED PARTIAL (institution + 5 schools + 13 programs).
The remaining schools/programs (Public Health, Social Work, Law, Nursing, Architecture,
Climate, the Graduate School of Arts and Sciences and further Engineering master's) are
deferred to a resume run on the SAME university, per the routine's resumption design. The
enrichment is idempotent, partial-safe (it never deletes Columbia schools/programs it does
not own), and a no-op when Columbia is absent, so this migration is safe on every
environment (and on CI databases built with ``create_all``, which never run migrations).
It ships to production automatically: the container entrypoint runs ``alembic upgrade
heads`` before serving.

Revision ID: columbiaprof1
Revises: chicagoprof1
Create Date: 2026-06-10
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import columbia_profile

revision = "columbiaprof1"
down_revision = "chicagoprof1"
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

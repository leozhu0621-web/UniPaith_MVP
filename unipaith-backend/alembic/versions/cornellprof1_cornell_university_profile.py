"""enrich Cornell University profile (data-only, no DDL)

Populates Cornell's canonical profile — rankings (QS #16, THE =18, U.S. News #12),
school_outcomes depth (admissions funnel, financial aid, demographics, test scores,
campus location, scale incl. the $11.8B FY2025 endowment, research with lab links,
campus life with resource links, first-destination outcomes, flagship facts, sources),
a rich intro, its real degree-granting colleges (Arts and Sciences, the Duffield College
of Engineering, the Ann S. Bowers College of Computing and Information Science, CALS, the
Dyson/Johnson/Nolan schools of the SC Johnson College of Business, ILR, Human Ecology,
AAP, the Brooks School of Public Policy, Cornell Law School, the College of Veterinary
Medicine and Weill Cornell Medicine — each with sourced About-tab detail), and a program
catalog across them built from the College Scorecard Field-of-Study list for UNITID 190415
plus Cornell's real online/hybrid professional master's and flagship professional degrees
(with Computer Science as the most-enriched flagship) — via
``unipaith.data.cornell_profile.apply()``.

No schema (DDL) changes. The enrichment is idempotent and a no-op when Cornell is absent,
so this migration is safe on every environment (and on CI databases built with
``create_all``, which never run migrations anyway). It ships to production automatically:
the container entrypoint runs ``alembic upgrade heads`` before serving.

Revision ID: cornellprof1
Revises: instenrich2
Create Date: 2026-06-10
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import cornell_profile

revision = "cornellprof1"
# Chain off the current single head so the migration chain stays single-headed.
down_revision = "instenrich2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # apply() flushes; Alembic commits the surrounding migration transaction.
    session = Session(bind=op.get_bind())
    cornell_profile.apply(session)
    session.flush()


def downgrade() -> None:
    # Data-only enrichment — nothing structural to roll back.
    pass

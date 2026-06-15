"""enrich Georgia Institute of Technology profile (data-only, no DDL)

Populates Georgia Tech's canonical profile — rankings (QS =123, THE =41, U.S. News #32,
ownership public, Carnegie R1, SACSCOC), school_outcomes depth (report card, admissions
funnel, demographics, test scores, Atlanta campus location, scale incl. ~$1.48B research
expenditures, research institutes with links, campus life with links, a verified 5-photo
Wikimedia campus gallery, top employers, sources), a rich intro, its six real colleges
(Engineering, Computing, Sciences, Scheller Business, Design, Ivan Allen Liberal Arts —
each with sourced About-tab detail and its own filtered content feed), and a 130-program
catalog across them built from the complete College Scorecard Field-of-Study list for
UNITID 139755 plus Georgia Tech's flagship online degrees (OMSCS, OMS Analytics, OMS
Cybersecurity), with content feeds, costs, FOS earnings, and aggregated cited reviews on
the fifteen coverable flagship programs — via ``unipaith.data.georgia_tech_profile.apply()``.

No schema (DDL) changes. The enrichment is idempotent and a no-op when Georgia Tech is
absent, so this migration is safe on every environment (and on CI databases built with
``create_all``, which never run migrations anyway). It ships to production automatically:
the container entrypoint runs ``alembic upgrade heads`` before serving.

Revision ID: gatechprof1
Revises: onboardstate1
Create Date: 2026-06-13
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import georgia_tech_profile

revision = "gatechprof1"
down_revision = "onboardstate1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # apply() flushes; Alembic commits the surrounding migration transaction.
    session = Session(bind=op.get_bind())
    georgia_tech_profile.apply(session)
    session.flush()


def downgrade() -> None:
    # Data-only enrichment — nothing structural to roll back.
    pass

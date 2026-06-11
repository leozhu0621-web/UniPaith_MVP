"""enrich Carnegie Mellon University profile (data-only, no DDL)

Populates CMU's canonical university-granularity profile via
``unipaith.data.carnegie_mellon_profile.apply()``: institution-level rankings +
ownership/Carnegie/accreditor, report-card + admissions funnel + test scores +
demographics + financial aid (CMU Common Data Set 2024-25 and College Scorecard
UNITID 211440, cross-checked), research/campus-life WITH links, official
news+events feeds, a character-leading description and campus photo; the seven
real degree-granting colleges with sourced About-tab detail; and a breadth-first
catalog of 180 verified degree programs across every college (residential, online,
hybrid, bicoastal, and CMU-Africa), each with a delivery_format and official page.

No schema (DDL) changes. The enrichment is idempotent and a no-op when CMU is
absent, so it is safe on every environment (and on CI databases built with
``create_all``, which never run migrations). The container entrypoint runs
``alembic upgrade heads`` before serving, so it ships to production automatically.

Revision ID: cmuprof1
Revises: cornellprof1
Create Date: 2026-06-10
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import carnegie_mellon_profile

revision = "cmuprof1"
down_revision = "cornellprof1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # apply() flushes; Alembic commits the surrounding migration transaction.
    session = Session(bind=op.get_bind())
    carnegie_mellon_profile.apply(session)
    session.flush()


def downgrade() -> None:
    # Data-only enrichment; nothing to roll back structurally.
    pass

"""enrich Yale University profile (data-only, no DDL)

Populates Yale's canonical profile — rankings (QS #21, THE #10, U.S. News #4),
school_outcomes depth (admissions funnel, financial aid, demographics, test scores,
campus location, scale incl. the $44.1B endowment, research, first-destination outcomes,
flagship facts, sources), a rich intro, its real degree-granting schools (Yale College,
the Schools of Management, the Environment, Public Health, Medicine, Nursing, Divinity,
Architecture, Art and Music — each with sourced About-tab detail), and a program catalog
across them built from the College Scorecard Field-of-Study list for UNITID 130794 (with
Computer Science as the most-enriched flagship) — via ``unipaith.data.yale_profile.apply()``.

No schema (DDL) changes. The enrichment is idempotent and a no-op when Yale is absent,
so this migration is safe on every environment (and on CI databases built with
``create_all``, which never run migrations anyway). It ships to production automatically:
the container entrypoint runs ``alembic upgrade heads`` before serving.

Revision ID: yaleprof1
Revises: princetonprof1
Create Date: 2026-06-10
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import yale_profile

revision = "yaleprof1"
down_revision = "princetonprof1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # apply() flushes; Alembic commits the surrounding migration transaction.
    session = Session(bind=op.get_bind())
    yale_profile.apply(session)
    session.flush()


def downgrade() -> None:
    # Data-only enrichment — nothing structural to roll back.
    pass

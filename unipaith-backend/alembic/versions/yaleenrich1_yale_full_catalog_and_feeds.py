"""re-enrich Yale to the gold standard — full catalog, feeds on every node (data-only)

Re-applies ``unipaith.data.yale_profile.apply()`` after the profile was rebuilt to the
gold standard:
  • feeds fixed everywhere — the institution now carries a real ``news_rss`` (the prior
    ``news_url`` key was never read by the ingest, so Yale showed no updates) plus the Yale
    events iCalendar, and EVERY school and EVERY program now carries a working
    ``content_sources`` (verified Yale News topic RSS + events .ics filtered by keywords),
    so their Events & Updates tabs populate instead of sitting empty;
  • the catalog is now the full published degree set — 15 schools (adds the Graduate School
    of Arts & Sciences, Law, Engineering & Applied Science, the Jackson School and the David
    Geffen School of Drama) and ~189 programs (all 82 Yale College majors, every school's
    graduate/professional degrees and the GSAS programs of study), cross-checked against the
    College Scorecard Field-of-Study list for UNITID 130794;
  • ``delivery_format`` is set on every program and ``_standard`` is stamped on every node.

No schema (DDL) changes. The enrichment is idempotent (upsert by slug) and a no-op when
Yale is absent, so this migration is safe on every environment (and on CI databases built
with ``create_all``, which never run migrations).

Revision ID: yaleenrich1
Revises: cmufeedsmerge1
Create Date: 2026-06-11
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import yale_profile

revision = "yaleenrich1"
down_revision = "cmufeedsmerge1"
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

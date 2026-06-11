"""enrich Johns Hopkins University to the gold standard — full catalog + feeds (data-only)

Applies ``unipaith.data.jhu_profile.apply()``, which brings the Johns Hopkins tree to the
gold standard (STANDARD_VERSION = 2), top-down and fully verified/cited:

  • Institution — ownership/Carnegie/accreditor, cited QS/THE/U.S.News ranks, the full
    admissions funnel + diversity + scale + outcomes + cost/aid (College Scorecard +
    NCES College Navigator, UNITID 162928), research labs WITH links, campus-life resources
    WITH links, a real campus photo, a character-leading description, and a working
    ``content_sources`` (the verified Johns Hopkins Hub news RSS, curated). The only required
    field omitted-with-reason is the university-wide top employer industries (Hopkins reports
    first-destination outcomes per school via interactive dashboards, not university-wide).
  • Nine degree-granting schools — Krieger, Whiting, Medicine, Nursing, Bloomberg Public
    Health, SAIS, Peabody, Carey, and Education — each with a sourced About tab (founded ·
    current 2025-26 dean · research centers) and a working ``content_sources`` (the Hub RSS
    filtered by school keywords). Faculty rosters (and the conservatory's / two professional
    schools' research centers) are honestly omitted per node.
  • 266 published degree programs — the full catalog across all nine schools, residential AND
    online / hybrid / professional / continuing-education (Engineering for Professionals,
    Krieger Advanced Academic Programs, online MPH/MAS, the flexible/executive MBA, online
    EdD). Every program carries verified basics (name, degree type, ``delivery_format``,
    owning school, factual description, school website, generic admissions, cost record,
    institution-wide outcome) and a working ``content_sources`` (Hub RSS + program keywords);
    deeper fields (tracks / per-program outcomes / faculty / reviews / exact tuition) are
    recorded omitted-pending in each node's ``_standard.omitted`` and deepened on resume runs.

``_standard`` is stamped on every node. Legacy/seed program rows (the generic College
Scorecard stubs) are reconciled — deleted when unreferenced, else unpublished — so the
catalog stays clean.

No schema (DDL) changes. The enrichment is idempotent (upsert by slug / school name) and a
no-op when Johns Hopkins is absent, so this migration is safe on every environment (and on
CI databases built with ``create_all``, which never run migrations).

Revision ID: jhuprof1
Revises: dukeprof1
Create Date: 2026-06-11
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import jhu_profile

revision = "jhuprof1"
down_revision = "dukeprof1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # apply() flushes; Alembic commits the surrounding migration transaction.
    session = Session(bind=op.get_bind())
    jhu_profile.apply(session)
    session.flush()


def downgrade() -> None:
    # Data-only enrichment — nothing structural to roll back.
    pass

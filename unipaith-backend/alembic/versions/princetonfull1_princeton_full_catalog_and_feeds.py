"""re-enrich Princeton to the gold standard — full catalog, feeds on every node (data-only)

Re-applies ``unipaith.data.princeton_profile.apply()`` after the profile was rebuilt to the
gold standard:
  • feeds fixed everywhere — the institution now carries a real ``news_rss`` (the prior
    ``news_url`` key was never read by the ingest, so Princeton showed no updates) and EVERY
    school and EVERY program now carries a working ``content_sources`` (the Princeton news
    RSS ``/news/feed/all`` — whose items include ``<enclosure>`` cover images — filtered to
    node-relevant items by keywords), so their Events & Updates tabs populate instead of
    sitting empty. Princeton publishes no public university-wide events iCalendar (its event
    feeds sit behind NetID), so ``events_feed`` is honestly omitted; Updates still populate;
  • the catalog is now the full published degree set — all 37 undergraduate concentrations
    (A.B. / B.S.E.) plus every degree-granting Graduate School field of study (Ph.D. fields
    and the professional master's — MPA, MPP, M.Arch, M.Fin, M.S.E./M.Eng), ~92 programs in
    all, from Princeton's official "Areas of Study" and Graduate School "Fields of Study";
  • ``delivery_format`` is set on every program and ``_standard`` is stamped on every node.

No schema (DDL) changes. The enrichment is idempotent (upsert by slug) and a no-op when
Princeton is absent, so this migration is safe on every environment (and on CI databases
built with ``create_all``, which never run migrations).

Revision ID: princetonfull1
Revises: yaleenrich1
Create Date: 2026-06-11
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import princeton_profile

revision = "princetonfull1"
down_revision = "yaleenrich1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # apply() flushes; Alembic commits the surrounding migration transaction.
    session = Session(bind=op.get_bind())
    princeton_profile.apply(session)
    session.flush()


def downgrade() -> None:
    # Data-only enrichment — nothing structural to roll back.
    pass

"""Repair USC profile: collapse concentration splits, real per-program prose, drop the
catalogue-ref opener.

Builds on uscprof4 (the field-echo-department + slug fix), and additionally:
- Collapses 93 concentration / emphasis / track split rows into their base degree,
  carrying the concentrations as ``tracks`` (613 -> 520 real programs; REPAIR_BACKLOG
  miss #2 / high #4).
- Replaces the per-program "USC Catalogue — programme <slug>." opener (a catalogue-ref
  tell prepended to every description) with real, per-program prose for the ~30 programs
  whose catalogue scrape shared another program's text — so no description carries a
  catalogue ref or slug (REPAIR_BACKLOG critical #2 / miss #8).

Idempotent via ``unipaith.data.usc_profile.apply()`` (replace/dedup; dropped variant
slugs are removed by the canonical cleanup).

Revision ID: uscdefab1
Revises: uscprof4
Create Date: 2026-06-19
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import usc_profile
from unipaith.models import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "uscdefab1"
down_revision = "uscprof4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    applied = usc_profile.apply(session)
    session.flush()
    if applied:
        inst = session.scalar(
            select(Institution).where(Institution.name == usc_profile.INSTITUTION_NAME)
        )
        if inst is not None:
            backfill_program_preferences(session, institution_id=inst.id)
            session.flush()


def downgrade() -> None:
    pass

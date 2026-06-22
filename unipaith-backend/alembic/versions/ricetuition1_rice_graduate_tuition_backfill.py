"""Rice published graduate-tier tuition backfill (matcher-core budget signal).

Clears Rice's acute matcher-core defect (REPAIR_BACKLOG run 74 HIGH #2): the catalog filled
the undergraduate sticker (bachelor's 100%) but shipped the academic graduate tier null —
master's 1/29, PhD 0/29 — because the profile omitted tuition for funded research programs.
Every academic master's and PhD now carries Rice's published 2025-26 standard full-time
graduate tuition ($62,474/yr; Rice General Announcements), with the funded tuition-waiver +
stipend reality recorded separately in ``cost_data`` (funding is a separate matcher signal,
not the budget input). Six professional programs (Executive MBA, MAcc, MGA, MSPE, MHCIHF,
MIOP) gain their published annual rate; the remaining per-credit professional / continuing-
studies programs honestly omit tuition with a sourced per-credit record.

Re-applies ``rice_profile.apply()`` (idempotent) and re-derives program-preference rows.

Revision ID: ricetuition1
Revises: mrguiucbu1
Create Date: 2026-06-22
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import rice_profile
from unipaith.models import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "ricetuition1"
down_revision = "mrguiucbu1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    rice_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == rice_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass

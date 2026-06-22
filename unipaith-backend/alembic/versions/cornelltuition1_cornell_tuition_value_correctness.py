"""Cornell University — tuition VALUE-correctness (REPAIR_BACKLOG run 75 HIGH #2).

The prior pass stamped Cornell's $71,266 endowed undergraduate sticker on 152 of 153
graduate/professional rows (the grader's "undergrad-sticker copy-down"). This migration
ships Cornell's REAL published 2025-26 per-credential rates from the Academic Catalog /
Bursar — research PhD $20,800 (funded, tuition=0) · endowed research M.S./M.A. $29,500 ·
contract-college graduate $20,800 · professional Tier 1 $71,266 · Tier 2 $46,658 · Johnson
Two-Year MBA $86,596 · Law J.D. $84,722 · D.V.M. $66,604 · Weill M.D. $76,486.

Also UNIFIES the live dual Alembic head: ``butuitionval1`` (#1066) and ``jhutuimrg1``
(merge-of-merges from the #1062/#1063 race) both independently sit on ``main``; this
migration's two-parent ``down_revision`` collapses both into a single head.

Revision ID: cornelltuition1
Revises: butuitionval1, jhutuimrg1
Create Date: 2026-06-22
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import cornell_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "cornelltuition1"
down_revision = ("butuitionval1", "jhutuimrg1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    applied = cornell_profile.apply(session)
    if applied:
        inst = session.scalar(
            select(Institution).where(Institution.name == cornell_profile.INSTITUTION_NAME)
        )
        if inst is not None:
            backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass

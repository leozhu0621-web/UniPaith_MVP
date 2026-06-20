"""UIUC — de-roll-up BSLAS/BSAG concentration-split names + clear residual abs-150 frame body.

Follows uiucprof5 (#907), which cleared the scrape-debris and the >=50%-floor frame share but
left two structure defects live (REPAIR_BACKLOG CRITICAL #1, run 67 / miss #2 + #8):

1. 28 ``Bachelor of Science in Liberal Arts and Sciences — {major}`` / ``… Agricultural
   Sciences — {major}`` names that read as concentration splits (one base "field" repeated
   across rows differing only by a trailing "— {major}"). These are renamed to their field of
   study ("Bachelor of Science in Astronomy"); Chemistry and Geology — which each offer a
   distinct Specialized (``-bs``) and Sciences & Letters (``-bslas``) curriculum — keep both as
   distinct degrees, and the VMS clinical-medicine major is named by its field.
2. Two fields (Speech & Hearing Science; Integrative Biology, the latter exposed once the BSLAS
   undergrad name normalized to its field) shared a >=150-char body across credential siblings —
   the run-67 dilution evasion the absolute floor catches. Each credential level now carries its
   own researched body (gold MIT = 0).

Data-only; the data module now enforces the abs-150 floor at build time. This migration
re-applies ``uiuc_profile.apply()`` (idempotent upsert) to force the renamed catalog live and
re-derives ``program_preferences`` for every UIUC program (skips claimed rows).

Revision ID: uiucbslas1
Revises: headfix1
Create Date: 2026-06-20
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import uiuc_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "uiucbslas1"
down_revision = "headfix1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    uiuc_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == uiuc_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass

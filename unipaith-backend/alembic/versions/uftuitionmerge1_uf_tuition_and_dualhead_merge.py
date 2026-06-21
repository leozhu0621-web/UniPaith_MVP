"""UF graduate/professional tuition backfill + merge the stanfordpercrd1/ufpercrd2 dual head.

Two jobs, one migration (so the fix carries exactly ONE head):

1. **Unify the dual head.** ``stanfordpercrd1`` (#1021) and ``ufpercrd2`` (#1018) both branched
   off ``ufpercrd1`` and both auto-merged, leaving ``main`` with TWO alembic heads — which fails
   ``test_alembic_has_single_head`` and BLOCKS every backend deploy (the auto-merge dual-head race,
   SKILL.md §8 step 5). That is why UF's #1016 per-credential descriptions were DEPLOY-STRANDED
   (REPAIR_BACKLOG run 71 entry #1 / FLAG #4): the repo was fixed but prod kept serving the old
   generic-definition rows. ``down_revision`` names both heads so this migration is the single
   new head.

2. **Backfill UF's matcher-core tuition (REPAIR_BACKLOG #7).** Re-applying ``uf_profile.apply()``
   ships UF's now-complete tuition: graduate annual (FL resident $12,740 / non-resident $31,872,
   UF SFA) for master's, the published graduate per-credit estimate for graduate certificates,
   the per-term×2 professional-school rates for MD/PharmD/DVM/JD (UF CFO 2025-26), the existing
   undergraduate sticker, and the funded (tuition 0) PhD treatment — taking tuition coverage from
   28% to every credential level. The re-apply ALSO drives the stranded #1016 per-credential
   descriptions live. Idempotent (``replace``/dedup); re-derives program-preference rows.

Revision ID: uftuitionmerge1
Revises: stanfordpercrd1, ufpercrd2
Create Date: 2026-06-21
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import uf_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "uftuitionmerge1"
down_revision = ("stanfordpercrd1", "ufpercrd2")
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    uf_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == uf_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass

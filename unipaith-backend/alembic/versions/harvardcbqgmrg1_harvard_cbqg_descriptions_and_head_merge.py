"""Harvard CBQG master's + de-fabricated descriptions; unify dual alembic head.

Two jobs in one migration:

1. **Unify the dual head.** ``harvardcipnames1`` (#1088) and ``ucsdgradtuition1`` (#1083)
   both branched off ``cornellcipnames1`` and auto-merged, leaving ``main`` with TWO
   alembic heads (deploys blocked). This migration's tuple ``down_revision`` merges them.

2. **Harvard depth follow-up to #1088** (non-duplicate):
   * Preserve the real **Master of Science in Computational Biology and Quantitative
     Genetics** — #1088 dropped the 26.11 master's, but Harvard T.H. Chan SPH publishes
     this on-campus two-year S.M.; ``harvard_profile`` now reassigns the row to HSPH
     (``_SLUG_SCHOOL_OVERRIDE``) and keeps it instead of dropping it.
   * De-fabricate three field descriptions still live after #1088 (cross-institution /
     unverifiable named units): Penn's "Morris Arboretum" (×2 rows) -> Arnold Arboretum /
     Harvard Forest / Museum of Comparative Zoology; Johns Hopkins' "Institute for
     NanoBioTechnology" -> Harvard's Center for Nanoscale Systems; a fabricated "Language
     Data Institute" removed from the Linguistics description.

Re-applies ``harvard_profile.apply()`` (idempotent), clears Harvard's non-claimed
(derived) ``ProgramPreference`` rows so renamed/remapped programs re-derive their matcher
target from the corrected names (claimed rows untouched), then re-runs
``backfill_program_preferences``.

Revision ID: harvardcbqgmrg1
Revises: harvardcipnames1, ucsdgradtuition1
Create Date: 2026-06-22
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import harvard_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "harvardcbqgmrg1"
down_revision = ("harvardcipnames1", "ucsdgradtuition1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    harvard_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(
            Institution.name == harvard_profile.INSTITUTION_NAME
        )
    )
    if inst is not None:
        # The renamed/remapped rows already carry a DERIVED ProgramPreference whose
        # target fields were inferred from the OLD federal-CIP name; backfill only fills
        # NULL keys, so clear Harvard's non-claimed rows first and let backfill re-derive
        # every preference from the corrected names. Claimed rows are never touched.
        session.execute(
            delete(ProgramPreference).where(
                ProgramPreference.program_id.in_(
                    select(Program.id).where(Program.institution_id == inst.id)
                ),
                ProgramPreference.source != "claimed",
            )
        )
        session.flush()
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass

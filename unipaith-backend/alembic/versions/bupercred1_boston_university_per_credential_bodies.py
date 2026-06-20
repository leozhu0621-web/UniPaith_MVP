"""Boston University per-credential bodies — Whiting fix + frame-share repair

Re-applies ``bu_profile.apply()`` after the data module was repaired:

- Clears the JHU ``Whiting`` cross-institution contamination on the CDS data-science row
  (REPAIR_BACKLOG CRITICAL #2 / miss #8 named-unit-truth).
- Replaces credential-frame + one shared field body (46/79 multi-credential fields) with
  distinct per-credential ``_level_body`` text after each verified field clause, including
  separate M.Eng. vs M.S. graduate bodies where BU offers both (gold MIT =
  0% ``frame_stripped_shared_body``).
- Collapses remaining concentration-split rows into base degrees with ``tracks`` (miss #2).
- Adds slug-specific descriptions for engineering and CS variants that shared a department
  blurb across credential siblings.

Idempotent; re-derives target-applicant rows.

Revision ID: bupercred1
Revises: uscdebris1
Create Date: 2026-06-20
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import bu_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "bupercred1"
down_revision = "uscdebris1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    bu_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == bu_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass

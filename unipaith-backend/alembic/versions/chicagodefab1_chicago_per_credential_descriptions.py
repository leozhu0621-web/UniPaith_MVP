"""Chicago per-credential descriptions + drop certificate padding (de-fabrication)

Re-applies ``chicago_profile.apply()`` after the data module was de-fabricated
(REPAIR_BACKLOG HIGH tier — University of Chicago, 50% verbatim-across-levels):

- Every master's row of a field that also awards a bachelor's now carries its OWN
  graduate description (``GRAD_FIELD_DESCRIPTIONS``), so a field's bachelor's and
  master's never share text (the anti-stub gold-MIT-0% verbatim / shared-leading-body
  gate, which UChicago previously failed on 52 / 22 rows).
- The 12 federal-certificate padding rows (one minted per CIP×award-level, not a
  published UChicago graduate certificate) are dropped, so ``apply()`` deletes those
  slugs and the real published degree catalog stands on its own (enrich-profile
  miss #2: a de-fabrication legitimately SHRINKS the count toward the real catalog).

This migration ALSO merges the two concurrent heads that were live on ``main``
(``purduedefab1`` from the Purdue de-fabrication and ``schol1a2b3c4d`` from the
scholarships table) into a single head, unblocking deploys.

``backfill_program_preferences`` re-derives a grounded target-applicant row for every
remaining UChicago program (skipping any claimed/first-party row), so the program ->
student match keeps firing after the catalog change.

Revision ID: chicagodefab1
Revises: purduedefab1, schol1a2b3c4d
Create Date: 2026-06-19
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import chicago_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "chicagodefab1"
down_revision = ("purduedefab1", "schol1a2b3c4d")
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    chicago_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == chicago_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass

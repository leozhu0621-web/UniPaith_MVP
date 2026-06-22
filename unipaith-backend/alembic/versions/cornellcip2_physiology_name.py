"""Cornell un-enumerated CIP-title residual → real Cornell degree (REPAIR_BACKLOG #1, run 78)

The run-77 CIP-title repair (``cornellcipnames1``) resolved exactly the five
backlog-enumerated federal CIP taxonomy titles but left a sixth same-class title live —
the "…and Related Sciences" suffix form (no comma before "and"), which the build's
``_ROLLUP_NAME_RE`` did not yet catch:

  * "Physiology, Pathology and Related Sciences" (CIP 26.09, PhD) ->
    "Biomedical and Biological Sciences" — Cornell's real named PhD covering human
    physiology, disease mechanisms, and pathobiology (the BBS graduate field,
    administered by the College of Veterinary Medicine; the owning college is moved
    off the College of Arts and Sciences to the Vet College on the IPEDS row).

The (already field-specific, true) description and the published per-tier tuition are
preserved — only the NAME and owning department change. ``_ROLLUP_NAME_RE`` is also
tightened so any future un-resolved "…and Related Sciences/Services" suffix title raises
the build gate (the new miss-#2 whole-class rule). A whole-catalog re-scan with the
miss-#2 CIP-title tells (federal "…and Related Sciences/Services" suffix, ", General"/
", Other", bare CIP rollup, embedded slash, ``(CIP NN.NN)``) now returns ZERO across all
233 Cornell program names and departments.

Re-applies ``cornell_profile.apply()`` and re-derives the matcher's target-applicant rows.

Revision ID: cornellcip2
Revises: harvardgradtuition1
Create Date: 2026-06-22
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import cornell_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "cornellcip2"
down_revision = "harvardgradtuition1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    cornell_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(
            Institution.name == cornell_profile.INSTITUTION_NAME
        )
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass

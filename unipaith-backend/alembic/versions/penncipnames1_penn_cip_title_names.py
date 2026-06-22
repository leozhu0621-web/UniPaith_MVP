"""Penn residual federal CIP-title program names → real Penn degrees (REPAIR_BACKLOG #1)

Resolves the four verbatim federal CIP taxonomy titles still shipped as Penn
``program_name`` (run 77 name-realness scan, 10 rows across BA / MA / PhD levels) to
the institution's real published degree names, verified against Penn's own department /
graduate-group pages:

  * "Linguistic, Comparative, and Related Language Studies and Services" -> Linguistics
    (BA + PhD; masters dropped — the AM is submatriculation-only, no standalone admit)
  * "Electrical, Electronics, and Communications Engineering" -> Electrical Engineering
    (BSE / MSE / PhD; Department of Electrical and Systems Engineering)
  * "Biomathematics, Bioinformatics, and Computational Biology" ->
    Genomics and Computational Biology (PhD; masters dropped — the GCB graduate group
    is PhD-only, no terminal MA)
  * "Ecology, Evolution, Systematics, and Population Biology" -> dropped (MA + PhD;
    Penn confers no distinct EEB degree — already covered by the real Biology BA/MA/PhD)

Dropped credential levels are reconciled out of prod by ``penn_profile._apply_programs``
(slug no longer in the canonical set -> delete-if-unreferenced / unpublish). Also clears
a pre-existing "Penn catalog listing {token}:" machine-token prefix on six SEAS/Wharton
credential siblings (miss #8 build-artifact): description grouping now uses Penn's own
field extractor so a field's BS/MS siblings group together and carry distinct per-credential
bodies instead of an identical body masked by the token. Field-specific descriptions and
published per-tier tuition are preserved on surviving rows. Re-applies ``penn_profile.apply()``
and re-derives the matcher's target-applicant rows.

Chains after ``harvardcbqgmrg1`` (PR #1087's head-unify, which already merged the dual
Alembic head left by the #1083 / #1088 auto-merge race), keeping ``main`` at a single head.

Revision ID: penncipnames1
Revises: harvardcbqgmrg1
Create Date: 2026-06-22
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import penn_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "penncipnames1"
down_revision = "harvardcbqgmrg1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    penn_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == penn_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass

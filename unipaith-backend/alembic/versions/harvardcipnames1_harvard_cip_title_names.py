"""Harvard residual federal CIP-title program names → real Harvard degrees (REPAIR_BACKLOG #1)

Resolves the five verbatim federal CIP taxonomy titles still shipped as Harvard
``program_name`` (run 77 name-realness scan, 11 rows across BA / cert / MA levels)
to the institution's real published degree names, verified against Harvard's own
department / GSAS pages:

  * "Linguistic, Comparative, and Related Language Studies and Services" -> Linguistics
    (BA; masters + certificate dropped — Linguistics is PhD-only at graduate level)
  * "Electrical, Electronics, and Communications Engineering" -> Electrical Engineering
    (bachelor's dropped — flagship ``harvard-electrical-eng-sb`` already ships EE)
  * "Ecology, Evolution, Systematics, and Population Biology" -> Integrative Biology
    (BA; masters + certificate dropped — OEB graduate study is PhD-only)
  * "Biomathematics, Bioinformatics, and Computational Biology" -> dropped at FAS
    (masters + certificate; the real SM is HSPH Computational Biology and Quantitative
    Genetics, a different school)
  * "Architectural History, Criticism, and Conservation" -> dropped (masters +
    certificate; no standalone GSD architectural-history degree at those levels)

Dropped credential levels are reconciled out of prod by ``harvard_profile._apply_programs``
(slug no longer in the canonical set -> delete-if-unreferenced / unpublish). Field-
specific descriptions and published per-tier tuition are preserved on surviving rows.
Re-applies ``harvard_profile.apply()`` and re-derives the matcher's target-applicant rows.

Revision ID: harvardcipnames1
Revises: cornellcipnames1
Create Date: 2026-06-22
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import harvard_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "harvardcipnames1"
down_revision = "cornellcipnames1"
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
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass

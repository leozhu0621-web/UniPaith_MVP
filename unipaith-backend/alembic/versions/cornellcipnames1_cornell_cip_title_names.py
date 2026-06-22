"""Cornell residual federal CIP-title program names → real Cornell degrees (REPAIR_BACKLOG #1)

Resolves the five verbatim federal CIP taxonomy titles still shipped as Cornell
``program_name`` (run 77 name-realness scan, 12 rows across BA / MA / PhD levels) to
the institution's real published degree names, verified against Cornell's own
department / graduate-field pages:

  * "Linguistic, Comparative, and Related Language Studies and Services" -> Linguistics
    (BA + PhD; the masters row is dropped — Linguistics is a PhD-only field at Cornell)
  * "Electrical, Electronics, and Communications Engineering" -> Electrical and Computer
    Engineering (PhD)
  * "Ecology, Evolution, Systematics, and Population Biology" -> Ecology and Evolutionary
    Biology (MA + PhD)
  * "Biomathematics, Bioinformatics, and Computational Biology" -> Computational Biology
    (MA + PhD; the bachelor's row is dropped — it is a concentration within the B.S. in
    Biology, not a standalone degree)
  * "Architectural History, Criticism, and Conservation" -> History of Architecture and
    Urban Development (PhD; BA/MA dropped — no undergraduate major, ambiguous master's)

The four dropped credential levels (Cornell does not confer them) are reconciled out of
prod by ``cornell_profile._apply_programs`` (slug no longer in the canonical set ->
delete-if-unreferenced / unpublish). Field-specific descriptions and published per-tier
tuition are preserved. Re-applies ``cornell_profile.apply()`` and re-derives the
matcher's target-applicant rows.

Revision ID: cornellcipnames1
Revises: purduetuition1
Create Date: 2026-06-22
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import cornell_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "cornellcipnames1"
down_revision = "purduetuition1"
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

"""UW-Madison Zoology CIP-title-slash name fix (REPAIR_BACKLOG #4c).

Clears Wisconsin's lone remaining name-realness defect: three programs shipped the
federal CIP 26.07 rollup TITLE "Zoology/Animal Biology" verbatim as the program name
(byte-identical to CIP 26.0701 — an embedded-slash CIP-title fabrication, miss #2). Each
row is resolved to UW-Madison's REAL published credential (verified guide.wisc.edu), NOT
blanket-aliased to "Zoology" (which would fabricate graduate credential names the school
does not confer):
  * bachelor's -> "Bachelor of Science in Zoology" (the published undergraduate major
    "Zoology, BS", College of Letters & Science, Department of Integrative Biology) via a
    "Zoology/Animal Biology" -> "Zoology" ``FIELD_ALIASES`` entry mirroring the existing
    "Botany/Plant Biology" -> "Plant Biology" alias;
  * master's -> "Master of Science in Integrative Biology" (the Department of Integrative
    Biology's real graduate degree; there is NO "Zoology, MS") — mapped per-slug with its
    own real department, description, and who_its_for;
  * certificate -> DROPPED — UW-Madison confers no graduate certificate in this field
    (only MS/PhD/minor), so the row was an IPEDS x award-level artifact whose only name
    would be fabricated. ``apply()`` deletes the now-non-canonical slug.
The Zoology field description's college was also corrected from "CALS" to the real
"College of Letters & Science". The verified-real "Radio/Television/Film" slash (RTVF,
School of Journalism & Mass Communication) is a run-77 carve-out and is untouched.

Re-applies ``uw_madison_profile.apply()`` (idempotent, replace=True) and re-derives
program-preference rows.

Revision ID: uwmadzoo1
Revises: columbiawho1
Create Date: 2026-07-01
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import uw_madison_profile
from unipaith.models import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "uwmadzoo1"
down_revision = "columbiawho1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    uw_madison_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == uw_madison_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass

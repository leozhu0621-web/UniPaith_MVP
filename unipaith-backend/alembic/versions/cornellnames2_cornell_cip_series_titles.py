"""Cornell whole-class federal CIP-series titles → real degrees (REPAIR_BACKLOG #3)

Run-79 whole-class pass. The run-78 repair cleared only the "…and Related Sciences"
suffix form; a full re-scan surfaced the remaining federal CIP series TITLES no real
Cornell degree carries (the punctuation-keyed gate missed them). Each is resolved to
the verified Cornell graduate Field of Study (gradschool.cornell.edu) or DROPPED when it
collides with a real Cornell degree / is a federal aggregation bucket Cornell does not
confer:

  RESOLVED to a real Cornell field
  * "Biochemistry, Biophysics and Molecular Biology" (CIP 26.02) -> Biochemistry,
    Molecular and Cell Biology (MA + PhD)
  * "Microbiological Sciences and Immunology" (CIP 26.05) -> Microbiology (MA + PhD)
  * "Neurobiology and Neurosciences" (CIP 26.15) -> Neurobiology and Behavior (MA + PhD)
  * "Business Administration, Management and Operations" (CIP 52.02) -> Management
    (Johnson PhD field)
  * "Natural Resources Conservation and Research" (CIP 03.01) -> Natural Resources and
    the Environment (MS + PhD; the bachelor's row is dropped — the undergraduate major is
    "Environment & Sustainability", a distinct name not minted here)

  DROPPED (collide with a real Cornell degree, or federal aggregation Cornell does not award)
  * "Research and Experimental Psychology" (42.27) — Cornell ships real Psychology BA/MA/PhD
  * "Behavioral Sciences" (30.17) — federal interdisciplinary, covered by Psychology
  * "Pharmacology and Toxicology" (26.10) — not a Cornell graduate Field of Study
  * "Biological and Physical Sciences" (30.01) — federal interdisciplinary, covered by
    Biological Sciences
  * "Management Sciences and Quantitative Methods" (52.13) — Johnson master's is the
    Two-Year MBA
  * "Allied Health Diagnostic, Intervention, and Treatment Professions" (51.09) — no such
    Weill master's
  * "Legal Research and Advanced Professional Studies" (22.02) — Cornell Law ships PhD in Law

The 11 dropped credential rows are reconciled out of prod by ``cornell_profile.apply``
(slug no longer canonical -> delete-if-unreferenced / unpublish). The catalog shrinks
233 -> 222 verified real programs; field-specific descriptions and published per-tier
tuition are preserved.

Also unifies the live dual alembic head (``penngatechmrg1`` from #1098 and ``nwtuition1``
from #1100, the auto-merge cascade) into a single head so Deploy Backend's
``alembic upgrade head`` succeeds.

Revision ID: cornellnames2
Revises: penngatechmrg1, nwtuition1
Create Date: 2026-06-22
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import cornell_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "cornellnames2"
down_revision = ("penngatechmrg1", "nwtuition1")
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

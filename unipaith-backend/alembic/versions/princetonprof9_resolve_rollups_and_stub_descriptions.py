"""de-fabricate Princeton catalog — resolve CIP rollups + textbook-definition stubs

Repairs the last two fabrication tells on Princeton's program catalog:

* **9 CIP-rollup names/departments resolved to real Princeton majors.** Seven map
  1:1 to the institution's published departments (Classics; Religion; German;
  Slavic Languages and Literatures; African American Studies; Linguistics;
  Independent Concentration), and two federal aggregates are split into the real
  majors they cover — "Area Studies" → Near Eastern Studies + East Asian Studies,
  and "Romance Languages, Literatures, and Linguistics" → French and Italian +
  Spanish and Portuguese (each a verified Princeton A.B. department).
* **Nineteen flagship majors' bare textbook-definition descriptions** (e.g.
  "Economics — micro, macro and econometrics.") are replaced with the researched,
  Princeton-specific clauses already in ``princeton_field_descriptions`` — each
  states a concrete Princeton fact (Frick Chemistry Laboratory, the Shelby Cullom
  Davis Center, the Princeton Plasma Physics Laboratory, etc.).

All sourced from Princeton's official department / admission pages; no fabrication.
Catalog is now anti-stub clean (gold-MIT-0% on every metric) and certified in
``tests/test_anti_stub_gate.py``. Data-only; idempotent; ``apply()`` reconciles the
renamed legacy slugs (deletes when unreferenced, else unpublishes).

Revision ID: princetonprof9
Revises: nyumrg1
Create Date: 2026-06-18
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import princeton_profile

revision = "princetonprof9"
down_revision = "nyumrg1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # apply() flushes; Alembic commits the surrounding migration transaction.
    session = Session(bind=op.get_bind())
    princeton_profile.apply(session)
    session.flush()


def downgrade() -> None:
    # Data-only enrichment — nothing structural to roll back.
    pass

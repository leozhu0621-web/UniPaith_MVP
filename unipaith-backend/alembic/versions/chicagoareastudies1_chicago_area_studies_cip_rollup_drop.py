"""UChicago — drop the federal CIP-rollup "Area Studies" aggregation rows.

Re-applies ``chicago_profile.apply()`` after the REPAIR_BACKLOG #1 fix:
  * Federal CIP 05.01 "Area Studies" is a series-level aggregation, not a degree
    UChicago confers under that literal name (enrich-profile miss #2). UChicago's
    actual area-studies majors already ship in this catalog under their real
    published names + own CIP codes — East Asian Languages and Civilizations and
    Near Eastern Languages and Civilizations (CIP 16.x), Slavic / Romance / Germanic
    Languages and Literatures, International Relations (45.09) — so the generic 05.01
    bucket maps to no single named degree and the two rows (B.A. + M.A. "Area
    Studies", department echoed as "Area Studies") are dropped, never fabricated.
``apply()`` is idempotent and reconciles the now-non-canonical "Area Studies" slugs
(delete-if-unreferenced, else unpublish). Derives ``program_preferences`` for every
UChicago program (skips claimed/first-party rows). No DDL; data-only and a no-op on a
fresh/CI database where the externally-seeded UChicago institution is absent.

Revision ID: chicagoareastudies1
Revises: berkvandmerge1
Create Date: 2026-06-25
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import chicago_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "chicagoareastudies1"
down_revision = "berkvandmerge1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    chicago_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(
            Institution.name == chicago_profile.INSTITUTION_NAME
        )
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass

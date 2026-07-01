"""Michigan program-distinct who_its_for + flagship external_reviews.

Re-applies ``michigan_profile.apply()`` to write the depth-pass data added in this
change to the live rows (REPAIR_BACKLOG #3b + #5):
  * ``who_its_for`` filled program-distinct on all 379 programs (was type-gamed to
    one template per degree_type via the ``_WHO_BY_TYPE`` fallback, distinct/total
    ~0.15 live);
  * ``external_reviews`` added on 11 flagship programs with genuine third-party
    coverage (MSI, Ford MPP, Data Science MS, Robotics MS, Mechanical Eng MS, IOE MS,
    SEAS MS, BSN, UMSI BSI, Taubman M.Arch, Sport Management).

``apply`` is idempotent (``replace``/merge on existing rows) and re-derives the
target-applicant ``program_preferences`` rows. Direct apply (no lock-bounded skip)
so the data actually reaches prod (FLAG #1). No programs are added, so the
once-backfilled preference rows stay intact.

Revision ID: michwhorev1
Revises: uscnamefix1
Create Date: 2026-07-01
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import michigan_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "michwhorev1"
down_revision = "uscnamefix1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    michigan_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == michigan_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass

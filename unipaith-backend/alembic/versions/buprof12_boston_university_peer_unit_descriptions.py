"""Boston University — remove Penn/Harvard/Cornell unit contamination missed by the denylist.

Re-applies ``bu_profile.apply()`` after the buprof12 description repair. The peer-signature
*denylist* in ``bu_profile`` passed foreign academic units it did not enumerate, so the live
BU catalog still shipped University of Pennsylvania / Harvard / Cornell units in CAS and
Engineering descriptions (SKILL miss #8 — a denylist is incomplete by construction; the
durable fix is a positive allowlist against the institution's own org chart). buprof12:
  * replaces the Penn-copied clauses ("SEAS", "GRASP", Penn's "CIS" department, "Warren
    Center", "Singh Center for Nanotechnology", "Perry World House") on Computer Science /
    Linguistics / Electrical, Computer, Mechanical & Materials Engineering / Political
    Science rows with verified Boston University units (Department of Computer Science,
    Hariri Institute for Computing, Faculty of Computing & Data Sciences, Department of
    Electrical & Computer Engineering, Department of Mechanical Engineering, Division of
    Materials Science & Engineering, Photonics Center, RASTIC robotics center, Center for
    Information & Systems Engineering, Department of Linguistics, Frederick S. Pardee School
    of Global Studies)
  * fixes the Preservation Studies row (Harvard's "Graduate School of Design" + Cornell's
    "upstate New York" geography → BU's American & New England Studies Program, Boston & New
    England) and the "Faculty of Computing & Information Sciences" mis-name
  * adds per-credential ``SLUG_DESCRIPTIONS`` for the five single-clause fields so credential
    siblings no longer share a leading body (anti-stub shared_leading_body=0)
Derives ``program_preferences`` for every BU program (skips claimed rows).

Revision ID: buprof12
Revises: budefab1
Create Date: 2026-06-19
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import bu_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "buprof12"
down_revision = "budefab1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    bu_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == bu_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass

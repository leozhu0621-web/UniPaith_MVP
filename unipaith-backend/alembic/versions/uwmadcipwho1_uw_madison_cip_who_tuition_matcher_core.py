"""UW-Madison matcher-core enrichment (REPAIR_BACKLOG #1 / #2 / #4).

Re-applies ``uw_madison_profile.apply()`` after wiring three matcher-core dimensions the
live catalog (347 programs) was missing or mis-signaling:
  * #1 ``cip_code`` — stamped on every program from the IPEDS CIP already used for the
    breadth cross-check (``spec["cip"]``). The base catalog assigned no CIP at all
    (catalog-wide null), so the matcher scored every UW-Madison program field-blind; the
    matcher resolves the field on the 2-digit CIP family, for which the verified IPEDS
    code is exact (no guess).
  * #2 public NON-RESIDENT tuition scalar — the CPEF budget feature reads the flat
    ``program.tuition`` scalar, not a residency-aware estimator, so for a public flagship
    it must be the out-of-state rate (the conservative input for the national/international
    applicant pool, every international applicant pays non-resident). The scalar now carries
    the published out-of-state rate; BOTH rates stay in ``cost_data.breakdown``.
  * #4 ``who_its_for`` filled on every program with a PROGRAM-DISTINCT (distinct/total = 1.0)
    statement naming the field + its verified subareas + the applicant it fits + the typical
    next step — never a degree-type template.

Because ``progprefbf1`` derived program-preference rows while UW-Madison ``cip_code`` was
still null, and ``backfill_program_preferences`` only fills EMPTY fields on existing rows,
the corrected CIP would not reach the program -> student field signal. So this DELETES
unclaimed ``source="derived"`` preference rows for UW-Madison, then re-derives — the same
recompute the UF / Michigan / Brown / Emory / Purdue / UIUC / Rice CIP repairs use. Direct
apply (no lock-bounded skip) so the data actually lands; verify-live on content.

Revision ID: uwmadcipwho1
Revises: ricecipwho1
Create Date: 2026-06-26
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import uw_madison_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "uwmadcipwho1"
down_revision = "ricecipwho1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    uw_madison_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == uw_madison_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        # Only clear DERIVED rows for UNCLAIMED programs — backfill skips claimed
        # programs, so deleting a claimed row would strand first-party data.
        prog_ids = session.scalars(
            select(Program.id).where(
                Program.institution_id == inst.id,
                Program.is_claimed.is_(False),
            )
        ).all()
        if prog_ids:
            session.execute(
                delete(ProgramPreference).where(
                    ProgramPreference.program_id.in_(prog_ids),
                    ProgramPreference.source == "derived",
                )
            )
            session.flush()
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass

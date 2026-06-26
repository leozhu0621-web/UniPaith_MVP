"""Rice matcher-core enrichment (REPAIR_BACKLOG #1 / #4).

Re-applies ``rice_profile.apply()`` after wiring two matcher-core dimensions the live
catalog (159 programs) was missing:
  * #1 ``cip_code`` — a verified 6-digit CIP-2020 code present in ``ref_majors`` on every
    one of the 159 programs (``rice_cip6.CIP6_BY_SLUG``). The base catalog assigned no CIP
    at all (catalog-wide null), so the matcher scored every Rice program field-blind; each
    program is now resolved to the specific 6-digit NCES code for its field of study (no
    guess — matched by CIP title against ``ref_majors.jsonl``, cross-checked with the
    College Scorecard Fields of Study for UNITID 227757).
  * #4 ``who_its_for`` filled on every program with a PROGRAM-DISTINCT (distinct/total = 1.0)
    statement derived from each program's own verified description and degree level —
    replacing the literal ``p.who_its_for = None`` hard-null (which also regressed the field
    on every replace=True re-apply).

Rice is private, so the public non-resident-tuition scalar (#2) does not apply, and its
master's/professional tuition was already verified per-tier (#3). Because ``progprefbf1``
derived program-preference rows while Rice ``cip_code`` was still null, and
``backfill_program_preferences`` only fills EMPTY fields on existing rows, the corrected CIP
would not reach the program -> student field signal. So this DELETES unclaimed
``source="derived"`` preference rows for Rice, then re-derives — the same recompute the
UF / Michigan / Brown / Emory / Purdue / UIUC CIP repairs use. Direct apply (no lock-bounded
skip) so the data actually lands; verify-live on content.

Revision ID: ricecipwho1
Revises: uiuccipwho2
Create Date: 2026-06-26
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import rice_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "ricecipwho1"
down_revision = "uiuccipwho2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    rice_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == rice_profile.INSTITUTION_NAME)
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

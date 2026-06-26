"""Duke matcher-core enrichment (REPAIR_BACKLOG #1 / #4).

Re-applies ``duke_profile.apply()`` after wiring two matcher-core dimensions the live
catalog (154 programs) was missing:
  * #1 ``cip_code`` — a verified NCES CIP-2020 6-digit code is now stamped on every
    ``Program.cip_code`` (``duke_cip6.CIP6_BY_SLUG``). The base ``apply()`` never assigned it,
    so the matcher scored every Duke program field-blind; the CPEF field signal resolves on
    the CIP code + program-name aliases (``services/match/field_canon``). The less-common
    professional/health codes were verified against the NCES CIP user site — no guesses.
  * #4 ``who_its_for`` filled on every program with a PROGRAM-DISTINCT (distinct/total = 1.0)
    field-specific statement derived from each program's own field + credential level
    (``duke_who.WHO_BY_SLUG``) — never a degree-type template. The base ``apply()`` previously
    HARD-NULLED the field (``p.who_its_for = None``), which both starved the depth field
    catalog-wide AND regressed any sibling fill on every ``replace=True`` re-apply; that
    hard-null is removed.

Duke is private, so the public non-resident-tuition scalar (#2) does not apply, and its
master's / professional tuition is already verified per-tier (PhD rows are funded research
doctorates → tuition honestly omitted with reason). Because ``progprefbf1`` derived
program-preference rows while ``cip_code`` was still null, and ``backfill_program_preferences``
only fills EMPTY fields on existing rows, the corrected CIP would not reach the
program -> student field signal. So this DELETES unclaimed ``source="derived"`` preference
rows for Duke, then re-derives — the same recompute the Northwestern / UF / Michigan / Rice
/ UW-Madison CIP repairs use. Direct apply (no lock-bounded skip) so the data actually lands;
verify-live on content.

Revision ID: dukecipwho1
Revises: nwcipwho1
Create Date: 2026-06-26
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import duke_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "dukecipwho1"
down_revision = "nwcipwho1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    duke_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == duke_profile.INSTITUTION_NAME)
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

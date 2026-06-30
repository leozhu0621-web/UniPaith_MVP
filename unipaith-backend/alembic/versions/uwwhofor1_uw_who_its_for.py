"""UW (Seattle) — who_its_for depth pass (0% → 100% program-distinct)

Takes the University of Washington (Seattle) catalog (360 programs across 16 schools) the
rest of the way to gold by clearing its sole open REPAIR_BACKLOG defect:

  * #3 who_its_for — was a hard-null ``p.who_its_for = None`` (0% catalog-wide). Now every
    one of the 360 programs carries a field-specific, PROGRAM-DISTINCT "who it's for"
    statement (subject + who it fits + typical next step), shaped by the credential level so
    a bachelor's, master's, and PhD in one field read differently. distinct/total == 1.0
    (never a degree-type template).

Everything else on the UW tree is already gold: program names are title-cased (0 sentence-
cased), ``cip_code`` is 100% in-sample, the public budget scalar carries the NON-RESIDENT
sticker, and every null master's/professional tuition is an honest omit-with-reason (14
fee-based / self-sustaining online programs billed per-credit + the Doctor of Audiology on
UW's variable graduate-tier schedule) recorded in ``_standard.omitted`` — left untouched here.

Because the who_its_for the student reads (and the program rows the matcher scores) are
rewritten, this follows the who-repair pattern (cf. ``utawhotuit1``): an idempotent re-apply
of ``uw_profile.apply()``, then for UW's programs delete the stale derived
``program_preferences`` and re-derive them, bump ``Program.feature_version`` so the recompute
path re-embeds, and delete the cached ``MatchResult`` rows so ``GET /me/matches`` rescores
against the refreshed data. Claimed / first-party rows are never touched.

Revision ID: uwwhofor1
Revises: utawhotuit1
Create Date: 2026-06-30
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import uw_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.models.matching import MatchResult
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "uwwhofor1"
down_revision = "utawhotuit1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    uw_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == uw_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        all_prog_ids = session.scalars(
            select(Program.id).where(Program.institution_id == inst.id)
        ).all()
        unclaimed_ids = session.scalars(
            select(Program.id).where(
                Program.institution_id == inst.id,
                Program.is_claimed.is_(False),
            )
        ).all()
        if unclaimed_ids:
            session.execute(
                delete(ProgramPreference).where(
                    ProgramPreference.program_id.in_(unclaimed_ids),
                    ProgramPreference.source == "derived",
                )
            )
            session.flush()
        backfill_program_preferences(session, institution_id=inst.id)
        if all_prog_ids:
            session.execute(
                Program.__table__.update()
                .where(Program.id.in_(all_prog_ids))
                .values(feature_version=Program.feature_version + 1)
            )
            session.execute(delete(MatchResult).where(MatchResult.program_id.in_(all_prog_ids)))
    session.flush()


def downgrade() -> None:
    pass

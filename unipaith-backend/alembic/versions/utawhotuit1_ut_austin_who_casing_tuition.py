"""UT Austin — who_its_for, name casing, and master's/professional tuition repair

Takes the University of Texas at Austin catalog (338 programs across 18 schools) the rest of
the way to gold, clearing its three open REPAIR_BACKLOG entries in ONE pass:

  * #3a/#3b who_its_for — was a hard-null ``p.who_its_for = None`` (0% catalog-wide). Now every
    one of the 338 programs carries a field-specific, PROGRAM-DISTINCT "who it's for" statement
    (subject + who it fits + typical next step), tailored to the credential level so a BA, MA,
    and PhD in one field read differently. distinct/total == 1.0 (never a degree-type template).

  * #4b name casing — ~71 bachelor's (+ a handful of graduate) program names shipped the field
    SENTENCE-cased ("Bachelor of Science in Aerospace engineering", "... in Art history",
    "... in Radio-television-film"). They are now re-cased to UT Austin's PUBLISHED title case
    (incl. each hyphen segment: "Radio-Television-Film"), preserving legitimate lowercase
    connectives, parentheticals, slash forms, and acronyms — only capitalization is corrected.

  * #1 matcher-core tuition — the PROFESSIONAL tier shipped 3 of 5 null (60%). The Doctor of
    Audiology (a Moody College graduate program billed at UT's standard graduate rate) is now
    FILLED, and the academic M.S. in Accounting (also the standard graduate rate) is filled too
    (master's 7→6 null), so the professional tier moves 2/5 → 3/5. The Doctor of Nursing
    Practice keeps its verified $30,000 program total in ``cost_data.total_program_tuition``
    only — the total spans five semesters and ``program.tuition`` renders as an ANNUAL figure,
    so writing it into the scalar would mis-render as "$30,000 / yr"; the annual scalar is
    honestly omitted. The lone remaining professional scalar omission, the Pharm.D., is
    omitted-with-reason: its designated professional-college rate is published only in a
    non-machine-readable Box PDF / login-gated calculator and could not be verified to the
    routine's two-source / first-party gate, so no unverified number is shipped.

Also fixes a latent broken description the casing pass unmasked: the M.A. in Human Dimensions
of Organizations shared its field's opening sentence with its bachelor's sibling, and the focus
heuristic spliced a broken fragment into the master's body — now a hand-authored, distinct,
field-specific description.

Because the program names, descriptions, who_its_for, and tuition that feed the matcher are
rewritten, this follows the cip/who repair pattern (cf. ``usccipwho1``): an idempotent re-apply
of ``ut_austin_profile.apply()``, then for UT Austin's programs delete the stale derived
``program_preferences`` and re-derive them, bump ``Program.feature_version`` so the recompute
path re-embeds, and delete the cached ``MatchResult`` rows so ``GET /me/matches`` rescores
against the corrected data. Claimed / first-party rows are never touched. The public scalar
carries the NON-RESIDENT rate (run-83 rule); each cost_note preserves the Texas-resident rate.

Revision ID: utawhotuit1
Revises: uvatuition1
Create Date: 2026-06-30
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import ut_austin_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.models.matching import MatchResult
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "utawhotuit1"
down_revision = "uvatuition1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    ut_austin_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == ut_austin_profile.INSTITUTION_NAME)
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
            session.execute(
                delete(MatchResult).where(MatchResult.program_id.in_(all_prog_ids))
            )
    session.flush()


def downgrade() -> None:
    pass

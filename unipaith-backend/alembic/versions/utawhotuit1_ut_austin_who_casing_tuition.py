"""UT Austin — who_its_for, name casing, and master's/professional tuition repair

Takes the University of Texas at Austin catalog (338 programs across 18 schools) the rest of
the way to gold, clearing its three open REPAIR_BACKLOG entries in ONE pass:

  * #3a/#3b who_its_for — was a hard-null ``p.who_its_for = None`` (0% catalog-wide). Now every
    one of the 338 programs carries a field-specific, PROGRAM-DISTINCT "who it's for" statement
    (subject + who it fits + typical next step), tailored to the credential level so a BA, MA,
    and PhD in one field read differently. distinct/total == 1.0 (never a degree-type template).

  * #4b name casing — ~71 bachelor's (+ a handful of graduate) program names shipped the field
    SENTENCE-cased ("Bachelor of Science in Aerospace engineering", "... in Art history"). They
    are now re-cased to UT Austin's PUBLISHED title case ("Aerospace Engineering", "Art
    History"), preserving legitimate lowercase connectives, parentheticals, and acronyms — only
    capitalization is corrected, never a word.

  * #1 matcher-core tuition — the PROFESSIONAL tier shipped 3 of 5 null (60%). The Doctor of
    Audiology (a Moody College graduate program billed at UT's standard graduate rate) and the
    Doctor of Nursing Practice (its published $30,000 flat program total) are now FILLED, so the
    professional tier moves 2/5 → 4/5; the academic M.S. in Accounting (billed at the standard
    graduate rate) is filled too (master's 7→6 null). The lone remaining professional null, the
    Pharm.D., is honestly omitted-with-reason: its designated professional-college rate is
    published only in a non-machine-readable Box PDF / login-gated calculator and could not be
    verified to the routine's two-source / first-party gate, so no unverified number is shipped.

Also fixes a latent broken description the casing pass unmasked: the M.A. in Human Dimensions
of Organizations shared its field's opening sentence with its bachelor's sibling, and the focus
heuristic spliced a broken fragment into the master's body — now a hand-authored, distinct,
field-specific description.

This is an idempotent data re-apply of ``ut_austin_profile.apply()`` plus
``backfill_program_preferences`` so derived target-applicant rows stay covered; claimed /
first-party rows are never touched. The public scalar carries the NON-RESIDENT rate (run-83
rule); each cost_note preserves the Texas-resident rate.

Deploy-safety (adopts the fleet pattern): the data apply runs inside a SAVEPOINT bounded by
``lock_timeout`` and is SKIPPED rather than hanging container boot if it cannot get its locks
quickly. The migration still records as applied so the chain advances; ``apply()`` is
idempotent and the routine re-applies + verifies live.

Revision ID: utawhotuit1
Revises: uvatuition1
Create Date: 2026-06-30
"""

from __future__ import annotations

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import ut_austin_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "utawhotuit1"
down_revision = "uvatuition1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    try:
        session.execute(text("SET LOCAL lock_timeout = '30s'"))
        with session.begin_nested():
            ut_austin_profile.apply(session)
            inst = session.scalar(
                select(Institution).where(
                    Institution.name == ut_austin_profile.INSTITUTION_NAME
                )
            )
            if inst is not None:
                backfill_program_preferences(session, institution_id=inst.id)
        session.flush()
    except Exception as exc:  # noqa: BLE001 — never let a data re-apply freeze the deploy
        print(
            f"  utawhotuit1: data re-apply skipped "
            f"({type(exc).__name__}: {str(exc)[:140]})"
        )


def downgrade() -> None:
    pass

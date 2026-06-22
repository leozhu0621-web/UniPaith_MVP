"""Yale published graduate-tier tuition backfill (REPAIR_BACKLOG #3) + unify dual head

Clears the master's / professional-tier tuition STARVATION the catalog aggregate hid:
Yale's bachelor's tier shipped 100% but the master's tier was 10/38, the professional
tier 0/2, and the certificate tier 0/3 (the CPEF matcher scored Yale's graduate
budget-fit BLIND). Yale charges graduate/professional tuition BY SCHOOL — each school
publishes a single full-time figure — so the nulls were a skipped knowable field, not an
honest omission. Every figure is verified against the Yale University Catalog or the
owning school's official 2025-26 tuition page and stamped as the matcher's annual budget
signal in ``yale_profile._COST_BY_SLUG``:

  * GSAS terminal master's -> $50,900 (the 7 self-funded A.M./M.A./M.S. degrees);
  * School of the Environment master's -> $53,550 (M.F., M.F.S. — same rate as the
    M.E.M./M.E.Sc. already filled);
  * Divinity (M.A.R., S.T.M.) -> $30,576; Architecture (M.Arch II, M.E.D.) -> $64,400;
  * Law (J.D., LL.M., M.S.L.) -> $76,636 (the bulletin states all three pay the J.D.
    rate); Medicine (M.D.) -> $74,460; Jackson (M.P.P.) -> $62,900 (Jackson funds 100%
    of tuition — the sticker is the budget signal, funding is a separate signal);
  * School of Management single-degree master's (MAM + the MMS specialized master's) ->
    $87,800; the EMBA -> $224,500 first-year total program fee;
  * David Geffen School of Drama (M.F.A., Certificate, D.F.A.) and the School of Music
    (M.M.A., Artist Diploma, Certificate in Performance, D.M.A.) -> $0 (both schools are
    verifiably tuition-free for all full-time degree/certificate students).

The values are SCHOOL-distinct (14 distinct figures, $0-$224,500) and NONE equals the
$67,250 undergraduate sticker, so no undergrad rate is copied down a heterogeneous tier
(tuition VALUE-realness). Legitimately OMITTED-with-reason (no single published figure /
funded research degree, never guessed): the funded GSAS research PhDs (and the funded
Law/Medicine/Nursing/etc. doctorates), the M.H.S. and the M.S. in Public Health (funded
research master's), the SOM M.M.S. in Public Education Management (no separately-published
rate), and the Jackson M.A.S. (no single published figure) — each recorded in that
program's ``_standard.omitted``.

Idempotent: re-applies ``yale_profile.apply()`` (no rows added/dropped here — only
tuition / cost_data set) and re-derives the matcher's target-applicant rows.

Head-sync: a burst of concurrent tuition/name repairs repeatedly forked the migration
tree off the ``gatechgradtuition1`` + ``penntuition1`` pair. PR #1102's ``cornellnames2``
already re-converged that pair (its ``down_revision`` is the same pair), and is now
``main``'s single non-Yale head, so this revision simply chains LINEARLY after it —
leaving ``main`` at a single head while carrying the Yale tuition backfill.

Revision ID: yalegradtuition1
Revises: cornellnames2
Create Date: 2026-06-22
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import yale_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "yalegradtuition1"
down_revision = "cornellnames2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    yale_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == yale_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass

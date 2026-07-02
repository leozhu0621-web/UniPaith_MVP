"""University of Rochester — land the stranded #1272 tuition/delivery/funding fix (head-synced)

``rochprof1`` (#1271) shipped Rochester's 179-program catalog, and PR #1272 (branch
``claude/loving-hawking-lm1dva``, two review rounds) authored the follow-up data-accuracy
corrections in ``rochester_profile.py`` — but that PR has been STRANDED: its migration
``rochfix1`` sets ``down_revision = "rochprof1"`` (an ANCESTOR of the current head, not the
head), so merging it would fork the tree into a DUAL HEAD and fail the deploy, and its title
does not match the enrichment auto-merge pattern, so it has sat open (8h+ stale) while the live
API keeps serving the OLD, WRONG Rochester data.

This lands that stranded, reviewed fix as repair work (SKILL §2: "land unmerged enrichment PRs
… head-sync each migration onto the current head"). The corrected ``rochester_profile.py`` from
#1272 is adopted onto this branch; this migration re-applies it via a fresh revision chained off
the CURRENT single head (``lmucasewestmerge1``), so it carries exactly one head and cannot create
the dual-head #1272 would have. Corrections re-landed (each verified independently this run —
undergrad $71,750 confirmed against rochester.edu/financial-aid; ``on_campus`` confirmed
non-canonical vs the ``Literal["in_person","online","hybrid"]`` program schema, so the filter
skips those rows):

- Undergraduate tuition scalar $67,080 → published $71,750 (2026-27) — every bachelor's
  budget-fit was understated.
- M.D. tuition $75,690 → URMC $74,050 (2026-27); Simon EMBA annualized from its published
  $107,955 total; MS Marketing Analytics + MS AI in Business filled at $68,000 (previously
  wrongly omitted); part-time Professional MBA de-priced from the full-time rate (per-credit →
  honest omission).
- ``delivery_format = "on_campus"`` (a value the program schema's ``Literal`` does not accept,
  so delivery filters never matched it) → ``in_person`` on the nine graduate rows.
- Eastman / Warner PhD rows de-flagged from ``tuition = 0`` / ``funded = True`` (their funding is
  partial-to-full and not guaranteed) → honest omission; the A&S / Hajim / SMD / Simon / SON
  research doctorates keep the verified full-funding $0.
- Master's Direct Entry to Nursing Practice duration 24 → 16 months; undergraduate deadlines
  corrected to ED I / ED II / RD (Rochester has no Early Action round).

Deploy-safety: the idempotent ``rochester_profile.apply()`` runs inside a ``lock_timeout``-bounded
SAVEPOINT and is skipped (not hung) if it cannot grab locks quickly, still recording as applied so
the chain advances; ``rochprof1`` proved this full apply lands on a clean (non-race) deploy, and
this ships as a single clean head. It does NOT re-derive ``program_preferences`` (none of the
changed fields — tuition / cost / delivery / duration / deadlines — feed a derived preference;
Rochester's rows are intact from ``rochprof1``), keeping the footprint light. The routine
re-verifies the corrected values LIVE after deploy.

Revision ID: rochreapply1
Revises: lmucasewestmerge1
Create Date: 2026-07-02
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import rochester_profile

revision = "rochreapply1"
down_revision = "lmucasewestmerge1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    try:
        session.execute(text("SET LOCAL lock_timeout = '30s'"))
        with session.begin_nested():
            applied = rochester_profile.apply(session)
            print(f"  rochreapply1: rochester_profile.apply -> {applied}")
        session.flush()
    except Exception as exc:  # noqa: BLE001 — never let a data re-apply freeze the deploy
        print(f"  rochreapply1: data re-apply skipped ({type(exc).__name__}: {str(exc)[:140]})")


def downgrade() -> None:
    pass

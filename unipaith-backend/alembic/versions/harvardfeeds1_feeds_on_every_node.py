"""Harvard — feeds on every school + program + per-node _standard fixes (data-only, no DDL).

Harvard predated the per-node feeds convention: only Harvard Business School (1 of 12 schools)
and the MBA (1 of 63 programs) carried content_sources, so every OTHER Harvard school and
program showed an EMPTY Events & Updates tab. Two certificates (CS50, Data Science) were also
left un-stamped (no _standard) because their outcomes_data was null, and a handful of programs
were missing required fields that are actually published (the J.D. / LL.M. / M.D. deadlines and
the Master of Liberal Arts cost omission).

This re-runs harvard_profile.apply(), which now:
  • sets content_sources on ALL 12 schools + ALL 63 programs — the fresh, image-rich Harvard
    Gazette news feed (news.harvard.edu/gazette/feed) filtered to school/program-relevant items
    by keywords (the MIT/MBAn pattern), plus a verified university events calendar (Harvard
    College's Localist iCal); HBS keeps its own verified events calendar + social handles, and
    its stale Working Knowledge RSS is retired in favour of the Gazette filtered to HBS items;
  • fills the J.D. (Feb 15), LL.M. (Dec 1), and M.D. (AMCAS Oct 15 / HMS Supplemental Oct 22)
    application deadlines from each school's official admissions page; and
  • stamps _standard {version, enriched_at, omitted} onto every program — including the
    non-degree certificates, which were previously left un-stamped — so the whole Harvard tree
    is conformant-or-honestly-omitted at STANDARD_VERSION.

Idempotent; no-ops when Harvard is absent (fresh / CI databases).

Revision ID: harvardfeeds1
Revises: mediacredit1
"""

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import harvard_profile

revision = "harvardfeeds1"
down_revision = "mediacredit1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    harvard_profile.apply(Session(bind=op.get_bind()))


def downgrade() -> None:
    # Data-only enrichment; no schema change to reverse. Profile values are idempotently
    # rewritten by upgrade(), so downgrade is intentionally a no-op.
    pass

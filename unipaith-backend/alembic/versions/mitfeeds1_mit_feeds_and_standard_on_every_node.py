"""MIT — feeds + _standard stamp on every node, About tab on every school (data-only, no DDL).

MIT is the gold reference instance, but it predated the per-node feeds + _standard convention:
only Sloan (1 of 6 schools) and MBAn (1 of 65 programs) carried content_sources, and no node
carried a _standard stamp — so every other MIT school and program showed an EMPTY Events &
Updates tab, and the fleet's reference was silently stale versus the current STANDARD_VERSION.

This re-runs mit_profile.apply(), which now:
  • sets content_sources on the institution + ALL 6 schools + ALL 65 programs (the shared,
    verified MIT feeds — news.mit.edu/rss/feed + calendar.mit.edu/calendar.ics — filtered to
    school/program-relevant items by keywords, the MIT/MBAn pattern; Sloan + MBAn keep their
    own topic feeds);
  • fills a rich, sourced About tab (founded · dean · named faculty · research centers WITH
    official links) on the five schools that lacked one (Engineering, Science, SHASS,
    Architecture & Planning, Schwarzman College of Computing); and
  • stamps _standard {version, enriched_at, omitted} onto the institution, every school, and
    every program so the whole MIT tree is conformant-or-honestly-omitted at STANDARD_VERSION.

Idempotent; no-ops when MIT is absent (fresh / CI databases).

Revision ID: mitfeeds1
Revises: cmufeeds1
"""

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import mit_profile

revision = "mitfeeds1"
down_revision = "cmufeeds1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    mit_profile.apply(Session(bind=op.get_bind()))


def downgrade() -> None:
    # Data-only enrichment; no schema change to reverse. Profile values are idempotently
    # rewritten by upgrade(), so downgrade is intentionally a no-op.
    pass

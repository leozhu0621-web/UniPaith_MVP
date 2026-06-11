"""Carnegie Mellon — set content_sources (feeds) on every school and program (data-only, no DDL).

CMU shipped gold at the institution level and across its 7 schools + 180-program catalog, but
content_sources was left null on every school and every program — so each of those ~187
student-facing pages showed an empty Events & Updates tab. CMU runs a single university-wide news
system (https://www.cmu.edu/news/feeds/news.rss, verified 40 items with media:content cover images)
plus a university events iCalendar (https://events.cmu.edu/live/ical/events), so every school and
program now carries that shared, verified feed filtered to college/department-relevant items by
keywords (the MIT/MBAn pattern), and content_sources is removed from the program omitted lists.
Idempotent; no-ops when Carnegie Mellon is absent.

Revision ID: cmufeeds1
Revises: riceprof1
"""

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import carnegie_mellon_profile

revision = "cmufeeds1"
down_revision = "riceprof1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    carnegie_mellon_profile.apply(Session(bind=op.get_bind()))


def downgrade() -> None:
    # Data-only enrichment; no schema change to reverse. Profile values are idempotently
    # rewritten by upgrade(), so downgrade is intentionally a no-op.
    pass

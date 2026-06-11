"""Columbia — content_sources on every school + program (data-only, no DDL).

Columbia predated the per-node feeds convention: only the institution (social-only,
no server-fetchable news_rss) and two flagships (CS + MBA via news_url) carried partial
content_sources, while all 12 schools and 23 other programs had null content_sources —
so their Events & Updates tabs were empty.

Columbia News (news.columbia.edu) and the university events calendar are Cloudflare-
gated to server fetches (HTTP 403). This re-runs columbia_profile.apply(), which now
routes every node through verified, server-fetchable school RSS feeds (CC/SEAS,
Mailman, Nursing, CUIMC, GSAPP, Data Science Institute) filtered by school/program
keywords (the MIT/Harvard pattern), plus media_credit on the campus photo.

Idempotent; no-ops when Columbia is absent (fresh / CI databases).

Revision ID: columbiafeeds1
Revises: harvardfeeds1
"""

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import columbia_profile

revision = "columbiafeeds1"
down_revision = "harvardfeeds1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    columbia_profile.apply(Session(bind=op.get_bind()))


def downgrade() -> None:
    pass

"""Enrich Georgia Institute of Technology to the gold standard — full college + program
catalog, feeds on every node (data-only, no DDL).

Builds out the previously shallow Georgia Tech institution (College Scorecard stats only, no
colleges, generic program stubs) into a complete gold-standard tree: the verified institution
gaps (rankings, admissions funnel, diversity, test scores, scale, research with links, campus
life, cost & aid, location, a 5-photo verified campus gallery, working news feed, citations),
all 7 colleges (with about_detail + content_sources), and the full ~143-program degree catalog
(bachelor's / master's / doctoral / professional plus the at-scale online OMSCS, Online MS
Analytics, and Online MS Cybersecurity), with content_sources on every node and external
reviews on the flagship coverable programs. Every value is researched from an authoritative
source and cited, or honestly omitted in that node's _standard. Idempotent; no-ops when
Georgia Tech is absent.

Revision ID: gatechprof1
Revises: onboardstate1
"""

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import georgia_tech_profile

revision = "gatechprof1"
down_revision = "princetonprof8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    georgia_tech_profile.apply(Session(bind=op.get_bind()))


def downgrade() -> None:
    # Data-only enrichment; no schema change to reverse. Profile values are idempotently
    # rewritten by upgrade(), so downgrade is intentionally a no-op.
    pass

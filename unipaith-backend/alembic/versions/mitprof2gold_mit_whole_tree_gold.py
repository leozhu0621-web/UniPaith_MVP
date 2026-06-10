"""MIT whole-tree gold: re-apply the enriched MIT profile.

The enrich-profile routine's MIT run: stamps ``_standard`` on the institution,
all six schools, and every program (the tree previously carried no stamps);
adds sourced About tabs (founded / leadership / notable faculty / research
centers) + keyword-relevant feeds for the five non-Sloan schools; fills
program-level depth verified this run (registrar cohort sizes, department
heads, catalog tracks, outcomes survey conditions, MIT News department feeds,
2x-sourced reviews) and extends the catalog with newly verified degree
programs. Everything else is honestly recorded in each node's
``_standard.omitted``.

Idempotent: ``mit_profile.apply`` upserts schools by (institution_id, name)
and programs by slug; no-op when MIT is absent.

Revision ID: mitprof2gold
Revises: instenrich2
"""

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import mit_profile

revision = "mitprof2gold"
down_revision = "instenrich2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # apply() flushes; Alembic commits the surrounding migration transaction.
    session = Session(bind=op.get_bind())
    mit_profile.apply(session)
    session.flush()


def downgrade() -> None:
    # Data-only enrichment; previous values are not retained, so downgrade is a
    # no-op (matches every other profile data migration in this repo).
    pass

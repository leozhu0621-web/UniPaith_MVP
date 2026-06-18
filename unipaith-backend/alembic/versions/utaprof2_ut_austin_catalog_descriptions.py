"""De-fabricate the UT Austin program catalog: replace the school-blurb
"connects to … Students build depth in {field}…" descriptions and synthesized
per-program reviews with verified first-party prose scraped from catalog.utexas.edu
(plus graduate area-of-study / hand-verified, cited supplements), set every program's
department to its real owning college, and keep only the hand-gathered flagship
external_reviews. Idempotent re-apply of ut_austin_profile.apply().

Revision ID: utaprof2
Revises: uiucprof4
Create Date: 2026-06-18
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import ut_austin_profile

revision = "utaprof2"
down_revision = "uiucprof4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    ut_austin_profile.apply(session)
    session.flush()


def downgrade() -> None:
    pass

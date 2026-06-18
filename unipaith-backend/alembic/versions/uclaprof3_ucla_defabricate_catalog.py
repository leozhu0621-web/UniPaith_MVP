"""De-fabricate the UCLA program catalog (REPAIR_BACKLOG run 58 #1).

Replaces the one-school-blurb-per-field stub descriptions with
credential-disambiguated program names and field-specific descriptions, sets each
program's department to its real owning UCLA school/college (not the field echoed
from the name), and removes the 84 auto-synthesized external_reviews (which carried
a cross-institution fabrication and mismatched-level rankings), keeping the 7
hand-curated program-specific reviews. Idempotent — re-applies ucla_profile.apply.

Revision ID: uclaprof3
Revises: michgate1
Create Date: 2026-06-18
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import ucla_profile

revision = "uclaprof3"
down_revision = "michgate1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    ucla_profile.apply(session)
    session.flush()


def downgrade() -> None:
    pass

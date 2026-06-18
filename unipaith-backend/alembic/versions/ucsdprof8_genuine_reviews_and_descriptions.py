"""UCSD — genuine per-credential descriptions + gathered reviews (de-synthesize)

Re-applies ``ucsd_profile.apply()`` after (1) replacing #745's frame-spliced /
grammatically-broken per-credential descriptions with genuinely researched
per-level bodies, (2) removing the 30 synthesized "U.S. News — UC San Diego"
boilerplate reviews and replacing them with 6 gathered, program-specific
graduate-flagship reviews (coverable programs without gathered coverage record
external_reviews as omitted), and (3) giving the MPH its own body distinct from
the BS Public Health. Idempotent; no-op when the institution is absent.

Revision ID: ucsdprof8
Revises: ucsdseedmerge1
Create Date: 2026-06-18
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import ucsd_profile

revision = "ucsdprof8"
down_revision = "ucsdseedmerge1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    ucsd_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass

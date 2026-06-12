"""Columbia profile repair — description lead + coverable external_reviews.

Re-applies ``unipaith.data.columbia_profile.apply()`` so the institution description
leads with the private-research-university eyebrow and ten coverable programs — MBA,
undergraduate CS, JD, MD, MPH, economics, journalism, SIPA MPA, M.Arch, and MSW — carry
aggregated, cited external_reviews in the MBAn shape.

Revision ID: columbiaprof5
Revises: pennprof5
Create Date: 2026-06-12
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import columbia_profile

revision = "columbiaprof5"
down_revision = "pennprof5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    columbia_profile.apply(session)
    session.flush()


def downgrade() -> None:
    pass

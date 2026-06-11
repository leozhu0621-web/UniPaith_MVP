"""Cornell — content_sources on every school + program + full IPEDS catalog

Re-runs ``cornell_profile.apply()`` so every Cornell school and program carries
verified Events & Updates feeds (the prior run left ``content_sources`` null except
on the CS flagship) and the program catalog expands to the College Scorecard
Field-of-Study list for UNITID 190415 (274 programs).

No schema (DDL) changes. Idempotent; no-op when Cornell is absent.

Revision ID: cornellfeeds1
Revises: columbiafeeds1
Create Date: 2026-06-11
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import cornell_profile

revision = "cornellfeeds1"
down_revision = "columbiafeeds1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    cornell_profile.apply(session)
    session.flush()


def downgrade() -> None:
    pass

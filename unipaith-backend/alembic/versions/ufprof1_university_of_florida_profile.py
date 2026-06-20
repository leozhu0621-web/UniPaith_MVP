"""enrich University of Florida profile (data-only, no DDL)

Populates UF's canonical profile — rankings, school_outcomes, 16 colleges, verified
feeds, ~314-program catalog, and external_reviews on flagship coverable programs —
via ``unipaith.data.uf_profile.apply()``.

No schema (DDL) changes. Idempotent; no-op when University of Florida is absent.

Revision ID: ufprof1
Revises: bupromptmerge1
Create Date: 2026-06-20
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import uf_profile

revision = "ufprof1"
down_revision = "bupromptmerge1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    uf_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass

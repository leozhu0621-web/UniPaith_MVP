"""Enrich Northwestern University to the gold standard (whole-tree profile).

Data-only, idempotent migration: applies ``northwestern_profile.apply()`` which upserts the
Northwestern institution enrichment, its eleven degree-granting schools, and its full
program catalog (246 programs across the schools), each with verified basics,
``delivery_format``, school-scoped ``content_sources`` and a per-node ``_standard`` stamp.
No DDL. No-op when Northwestern is absent (safe on fresh / CI databases).

Revision ID: northwesternprof1
Revises: dukeprof1
"""

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import northwestern_profile

revision = "northwesternprof1"
down_revision = "dukeprof1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    northwestern_profile.apply(Session(bind=op.get_bind()))


def downgrade() -> None:
    # Data-only enrichment; no schema change to reverse.
    pass

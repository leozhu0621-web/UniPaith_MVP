"""Harvard to profile-standard v2 — institution faculty count + school about_detail

Data-only migration (no DDL). Re-applies the canonical Harvard profile so the
institution carries its CDS instructional-faculty count (closing the last
institution-level gap) and all twelve schools carry verified, cited
``about_detail`` (founded · leadership · notable faculty · research centers ·
named-for · source) — bringing Harvard's institution + every school node to the
gold standard (``STANDARD_VERSION = 2``). Programs are enriched in a later run.

Idempotent and FK-safe; no-ops when Harvard is absent (fresh/CI databases).

Revision ID: harvardprof3
Revises: mbanoutcomes1
"""

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import harvard_profile

revision = "harvardprof3"
down_revision = "mbanoutcomes1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    harvard_profile.apply(Session(bind=op.get_bind()))


def downgrade() -> None:
    # Data-only, idempotent enrichment; no structural rollback.
    pass

"""re-apply Harvard profile — admit-rate / funnel consistency

Data-only migration (no DDL). Re-applies the canonical Harvard profile so the
headline acceptance rate matches the Class-of-2028 admissions funnel exactly
(1,937 / 54,008 = 3.59%), instead of the slightly different pooled Scorecard
figure that rendered an inconsistent headline. Idempotent; no-ops when Harvard
is absent.

Revision ID: harvardprof2
Revises: harvardprof1
"""

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import harvard_profile

revision = "harvardprof2"
down_revision = "harvardprof1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    harvard_profile.apply(Session(bind=op.get_bind()))


def downgrade() -> None:
    # Data-only, idempotent enrichment; no structural rollback.
    pass

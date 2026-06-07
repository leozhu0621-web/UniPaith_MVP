"""per-program official cost rules (Sloan MBA rate, online/cert null) + cost_data

Data-only migration (no DDL). Re-applies the canonical MIT profile so the
refined per-program tuition rules land: standard degree programs at MIT's
published $64,730, PhDs funded (0), the Sloan MBA at its professional rate,
online / MicroMasters / certificate left null (per-course pricing varies);
each priced program also gets sourced ``cost_data`` (MIT SFS). Idempotent;
no-ops when MIT is absent.

Revision ID: mitcrawl5v6w
Revises: mitcrawl4t5u
"""

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import mit_profile

revision = "mitcrawl5v6w"
down_revision = "mitcrawl4t5u"
branch_labels = None
depends_on = None


def upgrade() -> None:
    mit_profile.apply(Session(bind=op.get_bind()))


def downgrade() -> None:
    # Data-only, idempotent enrichment; no structural rollback.
    pass

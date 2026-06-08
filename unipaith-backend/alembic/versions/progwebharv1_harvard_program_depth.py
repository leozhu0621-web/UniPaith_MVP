"""Harvard programs — full degree names, official URLs, detailed admissions

Data-only migration (no DDL — the website_url column is added by progwebmit1).
Re-applies the canonical Harvard profile so every Harvard program gets its full
official degree name as the title, a verified official program-page URL, and
richer undergraduate/graduate application requirements (deadline rounds,
application fee, test ranges, evaluation notes). Idempotent; no-ops when Harvard
is absent.

Revision ID: progwebharv1
Revises: progwebmit1
"""

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import harvard_profile

revision = "progwebharv1"
down_revision = "progwebmit1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    harvard_profile.apply(Session(bind=op.get_bind()))


def downgrade() -> None:
    # Data-only, idempotent enrichment; no structural rollback.
    pass

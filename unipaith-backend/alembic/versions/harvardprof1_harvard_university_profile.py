"""canonical Harvard University profile (institution + 12 schools + catalog)

Data-only migration (no DDL). Applies the canonical Harvard profile: enriches
the Harvard institution row (rankings, real College Scorecard outcomes, financial
aid, scale, research, recognition, sources), upserts the twelve real
degree-granting schools, and builds Harvard's program catalog across all of them
with real per-program cost (per-school published tuition), official admission
requirements, College Scorecard Field-of-Study outcomes, highlights, audience,
concentrations, and application deadlines.

Idempotent and FK-safe; no-ops when Harvard is absent (fresh/CI databases).

Revision ID: harvardprof1
Revises: mitcrawla0b1
"""

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import harvard_profile

revision = "harvardprof1"
down_revision = "mitcrawla0b1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    harvard_profile.apply(Session(bind=op.get_bind()))


def downgrade() -> None:
    # Data-only, idempotent enrichment; no structural rollback.
    pass

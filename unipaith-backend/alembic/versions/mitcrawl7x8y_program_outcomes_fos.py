"""per-program outcomes from College Scorecard Field-of-Study (+ MIT-wide fallback)

Data-only migration (no DDL). Re-applies the canonical MIT profile so each
program gets outcomes_data: real median earnings (+ debt where reported) from
the College Scorecard Field-of-Study file for the ~19 MIT majors with
non-suppressed figures, and a clearly-labelled MIT-wide institution fallback
for the remaining degree programs. Non-degree credentials get none. Idempotent;
no-ops when MIT is absent.

Revision ID: mitcrawl7x8y
Revises: mitcrawl6w7x
"""

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import mit_profile

revision = "mitcrawl7x8y"
down_revision = "mitcrawl6w7x"
branch_labels = None
depends_on = None


def upgrade() -> None:
    mit_profile.apply(Session(bind=op.get_bind()))


def downgrade() -> None:
    # Data-only, idempotent enrichment; no structural rollback.
    pass

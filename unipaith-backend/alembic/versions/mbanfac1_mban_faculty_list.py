"""MBAn full faculty list (from the program website)

Data-only migration (no DDL). Re-applies the MIT profile so the MBAn faculty card
shows the real faculty the program's own site highlights (Bertsimas, Perakis,
Golrezaei, Jacquillat, Ramakrishnan, Freund, Podimata) instead of a single lead.
Idempotent; no-ops when MIT is absent.

Revision ID: mbanfac1
Revises: progreviews1
"""

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import mit_profile

revision = "mbanfac1"
down_revision = "progreviews1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    mit_profile.apply(Session(bind=op.get_bind()))


def downgrade() -> None:
    # Data-only, idempotent enrichment; no structural rollback.
    pass

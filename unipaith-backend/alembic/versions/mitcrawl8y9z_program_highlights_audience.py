"""per-program highlights + who-it's-for

Data-only migration (no DDL). Re-applies the canonical MIT profile so each
program gets a "who it's for" audience line and a set of highlights — real
content, per-program for flagship programs and by degree type otherwise —
filling the program page's previously-empty audience + highlights sections.
Idempotent; no-ops when MIT is absent.

Revision ID: mitcrawl8y9z
Revises: mitcrawl7x8y
"""

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import mit_profile

revision = "mitcrawl8y9z"
down_revision = "mitcrawl7x8y"
branch_labels = None
depends_on = None


def upgrade() -> None:
    mit_profile.apply(Session(bind=op.get_bind()))


def downgrade() -> None:
    # Data-only, idempotent enrichment; no structural rollback.
    pass

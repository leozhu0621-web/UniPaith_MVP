"""international-student requirements (English + visa) on programs

Data-only migration (no DDL). Re-applies the MIT profile so each program's
application_requirements carries an `international` block (English proficiency
policy + F-1/I-20 visa process via the MIT International Students Office, plus
STEM/OPT note for the MBAn). Idempotent; no-ops when MIT is absent.

Revision ID: intlreq1
Revises: mbanfac1
"""

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import mit_profile

revision = "intlreq1"
down_revision = "mbanfac1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    mit_profile.apply(Session(bind=op.get_bind()))


def downgrade() -> None:
    # Data-only, idempotent enrichment; no structural rollback.
    pass

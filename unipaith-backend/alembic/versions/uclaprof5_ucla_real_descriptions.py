"""Re-apply UCLA descriptions with first-party catalog prose, and unify the dual
head left by the concurrent auto-merges of #817 (gendlock3mo) and #822 (uclaprof4).

#822 de-fabricated UCLA from Wikipedia field defs (clearing the "Catalog entry"
junk) but leaked the URL slug into every description and carried no first-party
UCLA catalog prose. This re-applies the higher-quality rebuild: 172 rows from the
UCLA General Catalog 2025, 127 de-namesaked Wikipedia discipline summaries, 65
hand-verified UCLA-specific, 9 flagship overrides — anti-stub + machine-artifact
clean. Idempotent (replace=True).

Revision ID: uclaprof5
Revises: gendlock3mo, uclaprof4
Create Date: 2026-06-18
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import ucla_profile

revision = "uclaprof5"
down_revision = ("gendlock3mo", "uclaprof4")
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    ucla_profile.apply(session)
    session.flush()


def downgrade() -> None:
    pass

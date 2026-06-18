"""Duke anti-stub repair — drop description heading-double + per-credential doctoral clauses

Re-applies ``duke_profile.apply()`` after (a) removing the ``"{program_name}: "``
prefix that doubled the page heading (anti-stub ``name_prefixed``) and (b) giving each
field's Ph.D. row its own research-level clause so no body is shared verbatim across a
field's credential levels. Idempotent; no-op when Duke is absent.

Revision ID: dukeprof6
Revises: princetonprof10
Create Date: 2026-06-18
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import duke_profile

revision = "dukeprof6"
down_revision = "princetonprof10"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    duke_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass

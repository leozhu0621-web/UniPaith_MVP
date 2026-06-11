"""Enrich Rice University to the gold standard — full school + program catalog, feeds on
every node (data-only, no DDL).

Builds out the previously shallow Rice University institution (institution-level stats only,
no schools, generic program stubs) into a complete gold-standard tree: the verified
institution gaps (admissions funnel, diversity, outcomes, cost & aid, retention/grad rate,
working feeds, citations), all 8 degree-granting schools (with about_detail + content_sources),
and the full 159-program catalog (61 undergraduate majors + 98 graduate/professional programs,
including online/hybrid). Every value is researched from an authoritative source and cited, or
honestly omitted in that node's _standard. Idempotent; no-ops when Rice is absent.

Revision ID: riceprof1
Revises: dukeprof1
"""

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import rice_profile

revision = "riceprof1"
down_revision = "dukeprof1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    rice_profile.apply(Session(bind=op.get_bind()))


def downgrade() -> None:
    # Data-only enrichment; no schema change to reverse. Profile values are idempotently
    # rewritten by upgrade(), so downgrade is intentionally a no-op.
    pass

"""University of Florida sibling-topic grammar fix (Codex review on PR #1016).

The per-credential sibling bodies (ufpercrd1) interpolate a field "topic" extracted from the
discipline definition. The first extractor was fragile: definitions that lead with an
article/alias ("The biological sciences study …", "Astronomy is …" for field "Astronomy and
Astrophysics"), a "branch of {X} concerned with …" form (a naive "… of" cut stopped at
"branch of engineering"), or a "{Subject} prepares/applies …" form rendered malformed copy
("courses on Astronomy is …", "expertise in The biological sciences study …", "extend how
schools are led …"). The extractor is rewritten to anchor on the definition's subject + main
verb (robust to articles/aliases/"branch of X concerned with"), and the PhD template no longer
prepends "extend" to a how-clause. This migration re-applies ``uf_profile.apply()`` with the
corrected descriptions and re-derives program-preference rows (idempotent).

Revision ID: ufpercrd2
Revises: ufpercrd1
Create Date: 2026-06-21
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import uf_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "ufpercrd2"
down_revision = "ufpercrd1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    uf_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == uf_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass

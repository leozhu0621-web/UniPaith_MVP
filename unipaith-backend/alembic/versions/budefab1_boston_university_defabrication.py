"""Boston University — de-fabricate names/departments + remove Medill peer-copy (CRITICAL #1).

The BU catalog shipped a critical cross-institution fabrication — two Public Relations
rows whose description cited **Medill**, Northwestern's journalism school (BU's PR program
is in the College of Communication) — plus a tail of structural defects the name-derivation
builder produced: dual/joint/accelerated degrees rendered as bare credential combos
("JD/MBA", "MD/PhD", "BS-to-MS-SLP") with the credential echoed into ``department``; MPH
concentrations minted as 14 separate "M.S. in Mph — …" rows (now collapsed into one
Master of Public Health with the concentrations as tracks); CFA programs whose URL nested
the real discipline under a "school-of-*" segment, so the school name leaked in as the field
("Bachelor of Fine Arts in School Of Music"); and ``.title()``-dropped "&" in compound field
names ("Mathematics Statistics", "World Languages Literatures").

The data module now (a) replaces the Medill clause with BU's real College of Communication
PR program, (b) carries real per-program names + real owning departments for every dual /
joint / accelerated / CFA / Law-LL.M. / SPH / dental / math / world-languages row, (c) gives
each credential level of a multi-credential field its own researched body (gold MIT shares
0% across rows), and (d) splits the wrongly-merged math combined majors and language majors
back into distinct programs. ``bu`` joins the enforced ``CERTIFIED_CLEAN`` anti-stub gate.

This migration re-applies ``bu_profile.apply()`` to force the de-fabricated catalog live
(idempotent upsert) and derives ``program_preferences`` for every BU program (skips claimed
rows) so the program -> student match direction fires.

Revision ID: budefab1
Revises: buprof11
Create Date: 2026-06-19

Supersedes buprof11 (#851), a narrower description-only BU repair that landed
concurrently: this revision chains after it (uiucslugfix1 -> buprof11 -> budefab1)
and re-applies the same ``bu_profile.apply()`` with the full structural de-fabrication,
keeping a single migration head.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import bu_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "budefab1"
down_revision = "buprof11"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    bu_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == bu_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass

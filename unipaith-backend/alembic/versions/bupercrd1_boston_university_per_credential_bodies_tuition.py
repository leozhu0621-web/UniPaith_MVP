"""Boston University — per-credential researched bodies + published tuition (REPAIR_BACKLOG #5/#6).

The live BU catalog shipped two acute defects the enforced anti-stub gate's abs-150 floor and
the matcher-core tuition rule both flag (gold MIT scores 0):

1. **frame_abs150 = 23** — 23 multi-credential fields whose generated ``clause + level-body``
   stamped ONE researched field clause verbatim across the field's BA / MS / MA / PhD rows
   (e.g. Astronomy's "Observational and theoretical astrophysics … Perkins Telescope
   Observatory …" on all four credential levels). A padded per-credential tail diluted the
   shared run below the fraction-only default, so it shipped live as "certified clean"
   (REPAIR_BACKLOG miss #8 fraction-floor / FLAG #1b). The data module now carries a fully
   researched, per-PROGRAM description for each of the 75 rows in those fields
   (``_FULL_DESC_BY_SLUG``) — every credential level its own body, no sibling sharing a
   150+-char run; the verified field facts are reused, never re-fabricated.

2. **0% tuition catalog-wide** — ``apply()`` set ``cost_data`` (JSONB) but never the matcher-core
   ``tuition`` scalar, so the CPEF matcher scored budget-fit BLIND on all 396 programs
   (REPAIR_BACKLOG #6 — a whole-catalog null is STARVATION, not an honest omission). Tuition is
   institution-PUBLISHED, so it is now stamped per credential level from BU's real 2026–27
   figures: $73,024 full-time (undergraduate and most graduate/professional), with the distinct
   professional rates $74,078 (MD), $101,676 (DMD), $41,184 (School of Social Work).

This migration re-applies ``bu_profile.apply()`` (idempotent upsert) to force the per-credential
descriptions + tuition live, and re-derives ``program_preferences`` for every BU program (skips
claimed rows) so the program -> student match direction fires. ``bu`` joins the abs-150-floor,
frame-stripped, and scrape-debris anti-stub parametrize lists (it was already in CERTIFIED_CLEAN).

Revision ID: bupercrd1
Revises: cornelltrm1
Create Date: 2026-06-21
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import bu_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "bupercrd1"
down_revision = "cornelltrm1"
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

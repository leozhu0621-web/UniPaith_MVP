"""Cornell University — Ph.D. tuition VALUE-correctness (REPAIR_BACKLOG run 75 HIGH #2 follow-up).

The Cornell tuition value-correctness repair (``cornelltuition1``, #1068) stopped the
$71,266 undergrad-sticker copy-down on the master's / professional tiers, but it stamped
the research-doctoral rows with a MATCHER ``tuition`` of ``0`` (funded). ``0`` is a WRONG
matcher value — the CPEF budget-fit signal reads it as "this program is free" — so all 74
Cornell Ph.D. rows scored a $0 budget live.

Per the standard, a funded research doctorate carries EITHER the published sticker (the
matcher's budget input; funding is a SEPARATE ``funded`` signal) OR an honest
``_standard.omitted`` null — NEVER ``0``. This ships Cornell's REAL published 2025-26
research-doctoral tuition sticker ($20,800/yr, Cornell Graduate School Tuition Rates) as
the matcher ``tuition``, keeping ``funded=True`` + the funding note in ``cost_data``.

Idempotent: re-applies the Cornell profile (``replace``-style upsert) and re-derives
``program_preferences`` for any program lacking one. Also unifies the live dual head left
by the §8 auto-merge race (``cornelltuition1`` + ``bujhumrg1``, collapsed by ``bucornmrg1``)
by chaining onto that single merged head.

Revision ID: cornellphdtui1
Revises: bucornmrg1
Create Date: 2026-06-22
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import cornell_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "cornellphdtui1"
down_revision = "bucornmrg1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    applied = cornell_profile.apply(session)
    if applied:
        inst = session.scalar(
            select(Institution).where(Institution.name == cornell_profile.INSTITUTION_NAME)
        )
        if inst is not None:
            backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass

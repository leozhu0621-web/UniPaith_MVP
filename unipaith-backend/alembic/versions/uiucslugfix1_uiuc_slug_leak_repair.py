"""UIUC — replace URL-slug-leak descriptions with real per-program prose (CRITICAL #2).

``uiuc_profile._disambiguate_catalog_descriptions`` block 3 prepended the kebab URL slug
(``"uiuc-community-health-phd — …"``) to cross-field / shared-bulletin rows to dodge the
anti-stub cross-field normalization — leaking a build artifact onto 33 live program pages
(REPAIR_BACKLOG CRITICAL #2; the per-row-unique slug also hid the underlying shared-body
stamping from ``anti_stub.analyze``, which read 0). The slug is invisible to the built
``machine_artifacts`` gate (hex-keyed only), so it shipped under CERTIFIED_CLEAN.

The data module now (a) leads any residual cross-field sibling with its real field-of-study
instead of the slug, and (b) carries ``_SLUG_LEAK_OVERRIDES`` — 33 real, field-specific,
per-credential descriptions grounded in each program's discipline and its already-verified
UIUC college/department (gold MIT shares 0% across rows; mirrors the NYU #845 repair). This
migration re-applies ``uiuc_profile.apply()`` to force the de-fabricated descriptions live
(idempotent upsert) and derives ``program_preferences`` for every UIUC program (skips
claimed rows) so the program -> student match direction fires.

Revision ID: uiucslugfix1
Revises: nyumergeheads2
Create Date: 2026-06-19
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import uiuc_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "uiucslugfix1"
down_revision = "nyumergeheads2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    uiuc_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == uiuc_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass

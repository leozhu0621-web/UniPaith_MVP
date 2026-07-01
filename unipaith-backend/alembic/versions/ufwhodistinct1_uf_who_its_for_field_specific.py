"""UF who_its_for — degree-type template -> program-distinct, field-specific (REPAIR_BACKLOG #3b)

Depth repair on the University of Florida (REPAIR_BACKLOG #3b, who_its_for type-gaming). Before
this migration the catalog shipped ``who_its_for`` on every program but collapsed to five
degree-type templates (``_WHO_BY_TYPE``): a Computer Science PhD and a Public-Policy PhD read
identically, so the universal "Who it's for" depth field passed the non-null coverage gate while
telling a prospective student nothing that distinguished one program from the next (distinct
strings / sampled ~= 0.25 live).

Now every one of the 314 programs carries its OWN field-specific ``who_its_for`` — a 1-2 sentence
statement of the applicant the program fits (subject/methods, goals, readiness, typical next step),
authored from the field itself, never a fabricated program fact (no named labs/centers/rankings)
and never the degree-type template. Distinctness distinct/total = 314/314 (1.000); the
``_WHO_BY_TYPE`` fallback no longer fires for any program (module self-check asserts >= 0.95).

No programs are added or dropped and no other field changes, so the fleet-wide ``progprefbf1``
target-applicant rows stay valid; the backfill below is insert-missing-only and never touches a
claimed/first-party row.

Idempotent: re-applies ``uf_profile.apply()`` (updates ``who_its_for`` on existing rows) and
re-runs the target-applicant backfill. Chains after ``utaustuition2``, keeping ``main`` single-head.

Revision ID: ufwhodistinct1
Revises: utaustuition2
Create Date: 2026-07-01
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import uf_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "ufwhodistinct1"
down_revision = "utaustuition2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    uf_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == uf_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        # who_its_for-only depth repair — cip_code / pref_fields unchanged, so the fleet-wide
        # progprefbf1 rows stay valid; just ensure every program still has a derived
        # target-applicant row (insert-missing only; claimed rows untouched).
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass

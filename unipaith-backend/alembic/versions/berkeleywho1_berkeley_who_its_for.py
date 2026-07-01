"""Berkeley who_its_for depth — type-gaming repair (REPAIR_BACKLOG #3b)

UC Berkeley shipped a single shared ``_WHO_BASELINE`` string on every program that fell
through the one curated flagship entry, so ``who_its_for`` was distinct/total ≈ 0.05 — the
worst in the fleet — AND factually wrong on the graduate rows it also covered (an
undergraduate-framed "Undergraduates seeking a rigorous, research-rich education…" stamped
on master's, PhD, and professional programs alike). ``who_its_for`` is a UNIVERSAL depth
field — every real program can state the applicant it fits — so this is un-done depth, not
an honest omission.

``berkeley_who_its_for.WHO_ITS_FOR`` now supplies a field-specific, credential-level-aware
statement for all 230 remaining programs (subject · who it fits · typical next step),
grounded in what each field studies and its owning college — the distinctness bar the
field-specific catalogs (UCLA, UC-Davis, UC-Irvine, …) already meet. Nothing invents an
admissions cutoff, rank, or fact. A build-time gate in ``berkeley_profile`` asserts full
coverage AND program-distinctness (distinct/total == 1.0, all 231 rows), so a future
re-apply cannot silently regress to the shared template.

Idempotent: re-applies ``berkeley_profile.apply()`` (rewrites who_its_for on existing rows;
adds/drops no programs) and re-derives the matcher's target-applicant rows. cip_code /
tuition / names are unchanged, so pref_fields need no delete-and-re-derive;
``backfill_program_preferences`` only inserts any missing row. Chains after ``pennwhotui1``,
keeping ``main`` single-head.

Revision ID: berkeleywho1
Revises: pennwhotui1
Create Date: 2026-07-01
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import berkeley_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "berkeleywho1"
down_revision = "pennwhotui1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    berkeley_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == berkeley_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass

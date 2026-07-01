"""UT Austin master's tuition fills — academic IROM + Management (standard graduate rate)

Matcher-core tuition repair on The University of Texas at Austin (REPAIR_BACKLOG #1), every
value a choice between PUBLISHED/canonical numbers, never a guess. Before this migration the
catalog shipped seven null ``program.tuition`` scalars, so the CPEF budget feature scored those
programs blind; two are now filled from a verified published rate and the remaining five stay
honestly omitted-with-reason.

Filled (2):
  * MS Information, Risk & Operations Management + MS Management — each an academic research
    master's offered only within its McCombs doctoral program (the IROM MS is "offered only to
    students who are enrolled in the doctoral program in information, risk, and operations
    management" per the UT catalog; the MS in Management concentrates in the research fields of
    organization science / strategic management alongside the Management PhD). Like the academic
    MS in Accounting, both bill at UT Austin's STANDARD graduate rate, so each now carries the
    published non-resident graduate scalar ($22,954), with both residency rates in
    ``cost_data.breakdown``.

Still honestly omitted-with-reason (5):
  * MS Computer Science / Data Science / Artificial Intelligence (Online) — UT publishes a
    single FLAT $10,000 total ($333/credit x 30, residency-independent; verified first-party at
    cdso.utexas.edu), but it is a MULTI-YEAR FLEXIBLE total (18–36 months) with no annual basis.
    ``program.tuition`` is consumed as ``tuition_usd_per_year`` (budget veto) and rendered "/yr",
    so the total is kept in ``cost_data.total_program_tuition`` and the annual scalar is omitted
    rather than mis-signal the matcher (over-firing the veto for sub-$10k/yr budgets) or mislabel
    the flexible total as yearly.
  * Pharm.D. — UT publishes its rate only through a login-gated tuition calculator/PDF and the
    lone concordant third-party figure is an IPEDS-republisher echo, so it fails the
    two-independent-source verify gate (no-fabrication).
  * MS Energy Management — an active 10-month professional cohort (STEM-certified, summer
    intensive) whose premium program tuition McCombs does not publish in a verifiable /
    machine-readable form.

master's tuition coverage 122/128 -> 124/128 (the residual — the 3 online master's + MS Energy
Management — is legitimate omit-with-reason); professional stays 4/5 (Pharm.D. omit-with-reason).

Idempotent: re-applies ``ut_austin_profile.apply()`` (updates the tuition scalar + cost_data on
existing rows; adds/drops no programs) and re-runs the target-applicant backfill (insert-missing
only; claimed/first-party rows are never touched). Chains after ``utareviews1``, keeping ``main``
single-head.

Revision ID: utaustuition2
Revises: utareviews1
Create Date: 2026-07-01
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import ut_austin_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "utaustuition2"
down_revision = "utareviews1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    ut_austin_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == ut_austin_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        # Tuition-only repair — cip_code / pref_fields are unchanged, so the fleet-wide
        # progprefbf1 rows stay valid; just ensure every program still has a derived
        # target-applicant row (insert-missing only; claimed rows untouched).
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass

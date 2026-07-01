"""UT Austin master's/professional tuition fills — online master's + academic IROM/Management

Matcher-core tuition repair on The University of Texas at Austin (REPAIR_BACKLOG #1), every
value a choice between PUBLISHED/canonical numbers, never a guess. Before this migration the
catalog shipped seven null ``program.tuition`` scalars, so the CPEF budget feature scored those
programs blind; five are now filled from verified published rates and the remaining two stay
honestly omitted-with-reason.

Filled (5):
  * MS Computer Science (Online) / MS Data Science (Online) / MS Artificial Intelligence
    (Online) — UT's Computer & Data Science Online master's publish a single FLAT total program
    tuition of $10,000 ($333/credit x the 30-credit degree, the SAME for Texas residents,
    non-residents, and international students — no residency split; verified first-party at
    cdso.utexas.edu). The program is completed flexibly part-time, so the flat program total is
    the de-facto cost basis and carries the matcher budget scalar (the lowest-cost graduate
    option in the catalog — a blind scalar had lost the single most-affordable signal there is).
  * MS Information, Risk & Operations Management + MS Management — each an academic research
    master's offered only within its McCombs doctoral program (the IROM MS is "offered only to
    students who are enrolled in the doctoral program in information, risk, and operations
    management" per the UT catalog; the MS in Management concentrates in the research fields of
    organization science / strategic management alongside the Management PhD). Like the academic
    MS in Accounting, both bill at UT Austin's STANDARD graduate rate, so each now carries the
    published non-resident graduate scalar ($22,954), with both residency rates in
    ``cost_data.breakdown``.

Still honestly omitted-with-reason (2):
  * Pharm.D. — UT publishes its rate only through a login-gated tuition calculator/PDF and the
    lone concordant third-party figure is an IPEDS-republisher echo, so it fails the
    two-independent-source verify gate (no-fabrication).
  * MS Energy Management — an active 10-month professional cohort (STEM-certified, summer
    intensive) whose premium program tuition McCombs does not publish in a verifiable /
    machine-readable form.

master's tuition coverage 122/128 -> 127/128 (the lone residual, MS Energy Management, is a
legitimate omit-with-reason); professional stays 4/5 (Pharm.D. omit-with-reason).

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

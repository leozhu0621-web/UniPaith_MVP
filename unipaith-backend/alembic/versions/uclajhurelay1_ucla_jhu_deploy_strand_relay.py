"""Re-apply UCLA + JHU to clear non-self-healing deploy-strands (enrich-profile §9 / FLAG #4).

Two correct, CI-green repairs never reached production:

* **UCLA** (``uclatpl1``, #1027 — REPAIR_BACKLOG CRITICAL C2): rewrote 13 template-slot
  rows of machine-broken grammar ("builds advanced expertise in of artistic production…")
  to researched per-credential prose and backfilled matcher-core tuition. Its Deploy Backend
  was superseded by the dual-head fixup (``uclaberkmerge1``), so prod still serves the broken
  grammar and 0% tuition.
* **JHU** (``jhudefab1``/``jhupercred1``, #984 — REPAIR_BACKLOG #8): per-credential bodies
  cleared the last 3 frame-stripped shared-body fields (Anthropology, Chemical Engineering,
  Communication Studies). Its deploy was cancelled mid-migration, leaving the alembic revision
  marked-applied while the data write never completed — so every later ``alembic upgrade head``
  SKIPS it and the old rows persist.

The in-repo ``PROGRAMS`` for both are already gold (anti-stub clean, frame_stripped/template_slot
= 0); the only missing half is the DEPLOY (a merge is not a deploy). This is a fresh revision, so
the next deploy runs it regardless of the stale marked-applied state, re-writing both catalogs
idempotently (``replace``/dedup) and re-deriving their derived ProgramPreference rows.

No schema (DDL) changes. Idempotent; no-op when an institution is absent.

Revision ID: uclajhurelay1
Revises: uclaberkmerge1
Create Date: 2026-06-21
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import jhu_profile, ucla_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "uclajhurelay1"
down_revision = "uclaberkmerge1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    for profile in (ucla_profile, jhu_profile):
        profile.apply(session)
        inst = session.scalar(
            select(Institution).where(Institution.name == profile.INSTITUTION_NAME)
        )
        if inst is not None:
            backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass

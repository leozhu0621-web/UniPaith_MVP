"""Lehigh University - institution seed to gold + real 164-program catalog

Clears REPAIR_BACKLOG entry #6 (bulk institution-level seeds) for Lehigh University: Lehigh
entered as a bare U.S. News seed with 0 programs, a dead feed, and no report-card / cost /
description content (it carried only ranking basics and a 5-photo campus gallery). This migration
takes the institution to gold (rankings, College Scorecard report-card + admissions funnel +
diversity, enrollment/campus facts, the verified Wikimedia Commons campus gallery, and the working
Lehigh News RSS feed) and adds a real, catalog-verified 164-program catalog across Lehigh's five
colleges: the College of Arts and Sciences, the P.C. Rossin College of Engineering and Applied
Science, the College of Business, the College of Education, and the College of Health.

Every program carries a researched, field-specific ``description_text`` (anti-stub clean), a
program-distinct ``who_its_for``, a real owning ``department``, a ``cip_code``, and a verified
``delivery_format``. Lehigh is private with a single published undergraduate sticker ($66,810,
2025-26); its graduate programs bill per credit at published per-college rates (CAS/Engineering/
Health $1,660, Business $1,400, Education $660), so every master's carries its DISTINCT computed
graduate tuition (rate x standard load), never the undergraduate sticker copied down. Research
doctorates are funded (tuition waived) and part-time/professional doctorates bill per credit with
no single published annual figure, so doctoral tuition is honestly omitted-with-reason. External
reviews are a coverage-gated depth field left honestly omitted on this fresh build
(structure-before-depth). All values are verified-or-omitted in ``lehigh_profile``.

Re-derives ``program_preferences`` after apply so the program -> student match fires on the new
catalog (claimed/first-party rows are never touched).

Deploy-safety: the idempotent data apply runs inside a SAVEPOINT bounded by ``lock_timeout`` and is
SKIPPED (logged) rather than hanging container boot if it cannot get its locks quickly; the
migration still records as applied so the chain advances; ``lehigh_profile.apply()`` is idempotent.

Revision ID: lehighprof1
Revises: rochtuition2
Create Date: 2026-07-02
"""

from __future__ import annotations

import logging

from sqlalchemy import delete, select, text
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import lehigh_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "lehighprof1"
down_revision = "rochtuition2"
branch_labels = None
depends_on = None

log = logging.getLogger("alembic.runtime.migration")


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    try:
        session.execute(text("SET LOCAL lock_timeout = '30s'"))
        with session.begin_nested():
            applied = lehigh_profile.apply(session)
            if applied:
                inst = session.scalar(
                    select(Institution).where(Institution.name == lehigh_profile.INSTITUTION_NAME)
                )
                if inst is not None:
                    prog_ids = session.scalars(
                        select(Program.id).where(Program.institution_id == inst.id)
                    ).all()
                    if prog_ids:
                        session.execute(
                            delete(ProgramPreference).where(
                                ProgramPreference.program_id.in_(prog_ids),
                                ProgramPreference.source == "derived",
                            )
                        )
                        session.flush()
                    backfill_program_preferences(session, institution_id=inst.id)
        session.commit()
    except Exception:  # pragma: no cover - deploy-safety guard
        session.rollback()
        log.exception("lehighprof1: data apply skipped (lock contention or error); chain advances")


def downgrade() -> None:
    pass

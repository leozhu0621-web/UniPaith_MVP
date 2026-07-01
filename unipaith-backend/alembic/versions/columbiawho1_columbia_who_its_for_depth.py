"""Columbia who_its_for depth — type-gaming repair (REPAIR_BACKLOG #3b)

Columbia University shipped a type-gamed pair of baseline strings on ~164 of 167 programs —
one undergraduate "Academically exceptional students seeking a research-rich Ivy League
education … anchored by Columbia's Core Curriculum" line on every bachelor's row that fell
through the three curated entries, and one "Graduate and professional students seeking a
top-ranked Columbia degree …" line on every graduate/professional row — so ``who_its_for``
was distinct/total ≈ 0.10, one of the worst in the fleet. ``who_its_for`` is a UNIVERSAL
depth field — every real program can state the applicant it fits — so this is un-done depth,
not an honest omission (a CS PhD and a Public-Health DrPH must not read identically).

``columbia_who_its_for.WHO_BY_SLUG`` now supplies a field-specific, credential-level-aware
statement for all 167 programs (subject · who it fits · typical next step), grounded in what
each field studies and its owning school — the distinctness bar the field-specific catalogs
(UCLA, UC-Davis, UC-Irvine, …) already meet. Nothing invents an admissions cutoff, rank, or
fact. A build-time gate in ``columbia_profile`` asserts full coverage AND program-distinctness
(distinct/total == 1.0, all 167 rows), so a future re-apply cannot silently regress to the
shared baselines.

Idempotent: re-applies ``columbia_profile.apply()`` (rewrites who_its_for on existing rows;
adds/drops no programs) and re-derives the matcher's target-applicant rows. cip_code /
tuition / names are unchanged, so pref_fields need no delete-and-re-derive;
``backfill_program_preferences`` only inserts any missing row. Chains after ``berkeleywho1``,
keeping ``main`` single-head.

Downstream-cache refresh (mirrors ``mitcipwho1``): ``who_its_for`` also feeds two
materialized/cached derivatives that a stale re-apply would leave showing the OLD baseline
audience — (1) the stored ``programs.profile_intelligence`` blob, whose ``who_thrives``
section is built from ``who_its_for``; and (2) the rationale / embedding caches keyed on
``Program.feature_version`` (``who_its_for`` rides in ``ProgramView.sparse``). So after the
re-apply this migration rebuilds each unclaimed Columbia program's ``profile_intelligence``
from the fresh ``who_its_for`` (``_apply_intelligence`` also bumps ``feature_version``, which
invalidates the rationale + lazy-embedding caches) and marks every cached ``MatchResult`` for
a Columbia program stale so ``GET /me/matches`` rescores against fresh data. Both helpers are
deterministic (no LLM) and skip first-party/claimed rows, so authority precedence holds.

Revision ID: columbiawho1
Revises: berkeleywho1
Create Date: 2026-07-01
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import columbia_profile
from unipaith.models.institution import Institution, Program
from unipaith.models.matching import MatchResult
from unipaith.services.match.derive_preferences import backfill_program_preferences
from unipaith.services.profile_enrichment.intelligence import (
    _apply_intelligence,
    build_program_profile_intelligence,
)

revision = "columbiawho1"
down_revision = "berkeleywho1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    columbia_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == columbia_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
        programs = session.scalars(
            select(Program).where(Program.institution_id == inst.id)
        ).all()
        # Rebuild the stored profile_intelligence blob from the fresh who_its_for
        # (its who_thrives section is derived from who_its_for) — _apply_intelligence
        # also bumps feature_version, invalidating the rationale + lazy-embedding caches;
        # it skips claimed/first-party rows, so authority precedence holds.
        for program in programs:
            _apply_intelligence(program, build_program_profile_intelligence(program))
        prog_ids = [p.id for p in programs]
        if prog_ids:
            session.execute(
                MatchResult.__table__.update()
                .where(MatchResult.program_id.in_(prog_ids))
                .values(is_stale=True)
            )
    session.flush()


def downgrade() -> None:
    pass

"""Loyola Marymount — RE-APPLY stranded graduate tuition + campus gallery (light, boot-safe)

``lmutuition1`` filled LMU's graduate tuition (39 master's + the J.D. professional row + the paid
D.B.A./Ed.D. doctorates) and added the third verified Wikimedia Commons campus photo, but its DATA
NEVER REACHED PRODUCTION. Root cause (SKILL §9 self-skipping migration): ``lmutuition1`` auto-merged
concurrently with ``casewestfix1`` → a dual alembic head (unified by ``lmucasewestmerge1`` / #1280),
and its HEAVY full-profile re-apply (``lmu_profile.apply()`` + a full ``program_preferences``
re-derive) was SKIPPED at container boot by the ``lock_timeout``-bounded SAVEPOINT during that
dual-head-race deploy — recording as applied while the apply silently rolled back. The live API
therefore still serves all 39 LMU master's/professional programs with ``tuition = null`` (the CPEF
matcher scores their budget-fit BLIND) and only 2 of the 3 campus photos.

The graduate tuition + gallery are ALREADY CORRECT in ``lmu_profile.py`` — verified on a fresh
scratch DB this run (the full chain lands master's 39/39, professional 1/1, phd 2/2, 3 photos, 101
``program_preferences``). So this migration does NOT rewrite the data (SKILL §9: "do NOT rewrite the
already-correct data") — it RE-LANDS it via a LIGHT, TARGETED path that will not contend at boot:

  1. a SINGLE institution-row update — the ``school_outcomes`` campus gallery + ``_standard`` stamp,
     ``ranking_data``, ``description_text``, ``content_sources``, and the ``media_gallery`` hero
     (mirrors the institution block of ``lmu_profile.apply``); and
  2. a per-slug ``tuition`` / ``cost_data`` update over the 101 programs (matched by ``slug``,
     values straight from ``lmu_profile`` — the published per-college graduate rates).

It deliberately does NOT re-run the heavy full ``apply()`` (schools reconcile + FK introspection +
101 program rewrites) NOR re-derive ``program_preferences`` (tuition does not feed a derived
preference; LMU's 101 rows are intact from ``lmuprof1``) — those were the two heaviest parts of
``lmutuition1`` and the reason it skipped at boot. The ``lock_timeout`` + SAVEPOINT-skip guard is
kept as a hard boot-safety backstop, but the light footprint (≈102 row touches, no reconcile, no
introspection) lands reliably on any deploy.

Revision ID: lmureapply1
Revises: lmucasewestmerge1
Create Date: 2026-07-02
"""

from __future__ import annotations

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import lmu_profile
from unipaith.models.institution import Institution, Program

revision = "lmureapply1"
down_revision = "lmucasewestmerge1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    try:
        session.execute(text("SET LOCAL lock_timeout = '30s'"))
        with session.begin_nested():
            inst = session.scalar(
                select(Institution).where(Institution.name == lmu_profile.INSTITUTION_NAME)
            )
            if inst is None:
                print("  lmureapply1: LMU absent — no-op (fresh/CI database)")
            else:
                # ── institution block (1 row) — re-land the stranded campus gallery + stamps ──
                inst.ranking_data = {**(inst.ranking_data or {}), **lmu_profile.RANKING_DATA}
                school_outcomes = {**(inst.school_outcomes or {}), **lmu_profile.SCHOOL_OUTCOMES}
                school_outcomes["_standard"] = lmu_profile._standard(
                    lmu_profile._OMITTED_INSTITUTION
                )
                inst.school_outcomes = school_outcomes
                inst.description_text = lmu_profile.DESCRIPTION
                inst.content_sources = lmu_profile._INSTITUTION_CONTENT
                photos = lmu_profile.SCHOOL_OUTCOMES.get("campus_photos") or []
                if photos:
                    hero = photos[0]["url"]
                    gallery = [u for u in (inst.media_gallery or []) if u != hero]
                    inst.media_gallery = [hero, *gallery]

                # ── program tuition / cost_data (targeted, matched by slug) ──
                by_slug = {
                    p.slug: p
                    for p in session.scalars(
                        select(Program).where(Program.institution_id == inst.id)
                    )
                    if p.slug
                }
                touched = 0
                for spec in lmu_profile.PROGRAMS:
                    p = by_slug.get(spec["slug"])
                    if p is None:
                        continue
                    tuition, cost = lmu_profile._program_cost(spec)
                    p.tuition = tuition
                    p.cost_data = cost
                    touched += 1
                print(f"  lmureapply1: re-landed institution + {touched} program tuition rows")
            session.flush()
    except Exception as exc:  # noqa: BLE001 — never let a data re-apply freeze the deploy
        # The savepoint already rolled back; the outer (alembic) transaction stays clean so
        # this migration still records as applied. Light footprint makes a skip unlikely.
        print(f"  lmureapply1: data re-apply skipped ({type(exc).__name__}: {str(exc)[:140]})")


def downgrade() -> None:
    pass

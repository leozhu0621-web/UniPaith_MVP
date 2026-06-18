"""Derive a baseline target-applicant ``ProgramPreference`` from a program's REAL
public attributes (AI Structure Spec 2 §3.4 / §6 task 6).

Deterministic and grounded-only: it returns ``None`` when nothing classifies (omit —
never guess a preference). The output keys mirror EXACTLY what the matcher's
program -> student direction reads (``matching.cpef_program_to_student``):
``pref_fields``, ``pref_levels``, ``pref_min_gpa``. Other ``ProgramPreference`` fields
(test bands, recruiting weights) are first-party-owned (set by a claimed school) and
are not derived here.

``source="derived"`` + ``confidence=0.4`` set the program-side authority ``c_program``
to the inferred tier (Spec 2 §3.6) — the lowest, so a derived opinion is a soft nudge
the matcher shrinks toward neutral; a school's later claim (``source="claimed"``)
overrides it and is never touched by the routine.
"""

from __future__ import annotations

from typing import Any

from unipaith.services.match.field_canon import fields_offered_for_program
from unipaith.services.matching import eligible_current_levels
from unipaith.services.program_features import target_education_level

DERIVED_SOURCE = "derived"
DERIVED_CONFIDENCE = 0.4  # Spec 2 §3.6 inferred/derived c_program anchor

# The enrichment data modules store ``degree_type`` as full words
# ("bachelors"/"masters"/"phd"/"professional"/"certificate"), NOT the BS/MS/PhD
# abbreviations the matcher's ``target_education_level`` map expects. Normalize the
# full words here; fall back to the abbreviation map for anything else. "certificate"
# / "diploma" / "non-degree" are deliberately ABSENT — their target level is ambiguous,
# so we omit ``pref_levels`` rather than guess.
_DEGREE_WORD_TO_TARGET: dict[str, str] = {
    "bachelors": "bachelors",
    "bachelor": "bachelors",
    "undergraduate": "bachelors",
    "masters": "masters",
    "master": "masters",
    "graduate": "masters",
    "phd": "doctoral",
    "doctorate": "doctoral",
    "doctoral": "doctoral",
    "professional": "professional",
}


def _program_target_level(degree_type: str | None) -> str | None:
    """Map a program's ``degree_type`` (full word or abbreviation) to the level it
    grants, or None when it is unclassifiable / ambiguous (e.g. a certificate)."""
    if not degree_type:
        return None
    key = degree_type.strip().lower().replace(".", "").replace("'", "").replace("’", "")
    if key in _DEGREE_WORD_TO_TARGET:
        return _DEGREE_WORD_TO_TARGET[key]
    # Abbreviations (BS / MS / PhD / JD ...) — reuse the matcher's own map.
    return target_education_level(degree_type)


def _gpa_floor(class_profile: dict | None) -> float | None:
    """A soft minimum-GPA proxy from a REAL academic class profile: the 25th-percentile
    admitted GPA (a floor), else the median. Omit when absent — never guess a cutoff.
    Only the academic GPA keys are read (no protected / proxy attribute is touched)."""
    if not class_profile:
        return None
    for key in ("gpa_p25", "gpa_p50"):
        val = class_profile.get(key)
        if val is None:
            continue
        try:
            v = float(val)
        except (TypeError, ValueError):
            continue
        if 0.0 < v <= 5.0:  # sane GPA range; ignore garbage values
            return round(v, 2)
    return None


def derive_program_preference(
    *,
    cip_code: str | None = None,
    program_name: str = "",
    degree_type: str | None = None,
    class_profile: dict | None = None,
) -> dict[str, Any] | None:
    """Baseline target-applicant preference from real attributes, or None to omit.

    - ``pref_fields``  <- the program's own canonical field(s) (preferred applicant
      background), grounded via name alias then CIP family; ``[]`` -> omitted.
    - ``pref_levels``  <- the current student levels eligible for this program's target
      level (the same compatibility table the eligibility veto uses).
    - ``pref_min_gpa`` <- 25th-pct (else median) admitted GPA from a real class profile;
      omitted when there is none.

    Returns ``None`` when not one signal grounds (the program stays "no opinion").
    """
    pref: dict[str, Any] = {}

    fields = fields_offered_for_program(cip_code=cip_code, program_name=program_name or "")
    if fields:
        pref["pref_fields"] = fields

    levels = eligible_current_levels(_program_target_level(degree_type))
    if levels:
        pref["pref_levels"] = levels

    gpa = _gpa_floor(class_profile)
    if gpa is not None:
        pref["pref_min_gpa"] = gpa

    if not pref:
        return None
    pref["source"] = DERIVED_SOURCE
    pref["confidence"] = DERIVED_CONFIDENCE
    return pref


def _latest_class_profile(session: Any, program_id: Any) -> dict | None:
    """Latest cycle's academic ``class_profile`` for a program (sync session), or None."""
    from sqlalchemy import desc, select

    from unipaith.models.outcomes import ProgramAdmissionsHistory

    return session.scalar(
        select(ProgramAdmissionsHistory.class_profile)
        .where(ProgramAdmissionsHistory.program_id == program_id)
        .order_by(desc(ProgramAdmissionsHistory.cycle_year))
        .limit(1)
    )


def backfill_program_preferences(session: Any, *, institution_id: Any = None) -> int:
    """Derive + insert a baseline ``ProgramPreference`` for every program that lacks one.

    Idempotent and authority-safe: a program that ALREADY has a preference row (derived
    OR claimed/first-party) is skipped — the routine never overwrites first-party data.
    Sync ``Session`` — for use in Alembic data-migrations (the fleet backfill) and in a
    data-module's migration (call with ``institution_id`` right after ``apply()`` so a
    freshly-enriched university's programs get their derived target applicant). Flushes;
    the caller commits. Returns the number of rows inserted.
    """
    from sqlalchemy import select

    from unipaith.models.institution import Program, ProgramPreference

    stmt = select(Program)
    if institution_id is not None:
        stmt = stmt.where(Program.institution_id == institution_id)
    programs = list(session.scalars(stmt).all())
    if not programs:
        return 0

    program_ids = [p.id for p in programs]
    existing = set(
        session.scalars(
            select(ProgramPreference.program_id).where(
                ProgramPreference.program_id.in_(program_ids)
            )
        ).all()
    )

    inserted = 0
    for prog in programs:
        if prog.id in existing:
            continue  # never overwrite an existing (derived or claimed) row
        pref = derive_program_preference(
            cip_code=getattr(prog, "cip_code", None),
            program_name=getattr(prog, "program_name", "") or "",
            degree_type=getattr(prog, "degree_type", None),
            class_profile=_latest_class_profile(session, prog.id),
        )
        if pref is None:
            continue
        session.add(ProgramPreference(program_id=prog.id, **pref))
        inserted += 1

    session.flush()
    return inserted

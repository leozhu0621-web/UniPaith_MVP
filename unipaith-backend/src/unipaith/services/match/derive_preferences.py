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

from datetime import UTC, datetime
from typing import Any

from unipaith.schemas.profile_intelligence import (
    assert_no_protected_traits,
    validate_target_profile,
)
from unipaith.services.match.field_canon import fields_offered_for_program
from unipaith.services.matching import eligible_current_levels
from unipaith.services.program_features import target_education_level
from unipaith.services.program_featurizer import featurize_program

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


def _evidence(label: str, url: str | None, *, field_path: str) -> list[dict[str, Any]]:
    if not url:
        return []
    return [
        {
            "label": label,
            "url": url,
            "source_type": "official",
            "field_path": field_path,
            "freshness": {"status": "current", "checked_at": datetime.now(UTC).isoformat()},
        }
    ]


def _safe_preferred_values(values: list[str]) -> list[str]:
    """Drop public labels that cannot legally become matching preference values.

    Program names and CIP labels may legitimately discuss protected-trait fields
    of study on public catalog pages. They must not become target-applicant
    attributes, preference values, or private decision reasoning.
    """
    safe: list[str] = []
    for value in values:
        try:
            assert_no_protected_traits(value)
        except ValueError:
            continue
        safe.append(value)
    return safe


def _add_signal(
    layers: dict[str, list[dict[str, Any]]],
    layer: str,
    *,
    attribute: str,
    preferred_values: list[str],
    statement: str,
    weight: float,
    confidence: float,
    evidence: list[dict[str, Any]],
) -> None:
    preferred_values = _safe_preferred_values(preferred_values)
    if not preferred_values or not evidence:
        return
    layers[layer].append(
        {
            "attribute": attribute,
            "preferred_values": preferred_values,
            "statement": statement,
            "weight": weight,
            "confidence": confidence,
            "evidence": evidence,
        }
    )


def _target_profile(
    *,
    program_name: str,
    degree_type: str | None,
    cip_code: str | None,
    class_profile: dict | None,
    description: str | None,
    outcomes_data: dict | None,
    application_requirements: dict | None,
    source_url: str | None,
    pref_fields: list[str],
    pref_levels: list[str],
    pref_min_gpa: float | None,
    allow_omission_only: bool = False,
) -> dict[str, Any] | None:
    layers: dict[str, list[dict[str, Any]]] = {
        "background_academic": [],
        "goals_behaviors_learning_working_style": [],
        "values_motivations_community": [],
    }
    program_ev = _evidence("Program page", source_url, field_path="program")
    class_ev = _evidence("Class profile", source_url, field_path="class_profile")

    _add_signal(
        layers,
        "background_academic",
        attribute="field_preparation",
        preferred_values=pref_fields,
        statement="The program is best grounded for students prepared in related fields.",
        weight=0.28,
        confidence=0.74,
        evidence=program_ev,
    )
    _add_signal(
        layers,
        "background_academic",
        attribute="current_academic_level",
        preferred_values=pref_levels,
        statement=(
            f"{degree_type or 'This'} program's degree level implies these compatible "
            "current academic stages."
        ),
        weight=0.18,
        confidence=0.68,
        evidence=program_ev,
    )
    if pref_min_gpa is not None:
        _add_signal(
            layers,
            "background_academic",
            attribute="academic_strength",
            preferred_values=[f"gpa_at_or_above_{pref_min_gpa:.2f}"],
            statement=(
                "Published admitted-student academic evidence implies a soft academic "
                "preparation floor."
            ),
            weight=0.16,
            confidence=0.72,
            evidence=class_ev or program_ev,
        )

    derived = featurize_program(
        cip_code=cip_code,
        degree_type=degree_type,
        name=program_name,
        description=description or "",
    )
    career_arcs = list(derived.get("career_arcs") or [])
    interest_themes = list(derived.get("interest_themes") or [])
    values = list(derived.get("values") or [])
    outcomes_url = (
        (outcomes_data or {}).get("source_url") if isinstance(outcomes_data, dict) else None
    )
    outcomes_ev = _evidence(
        "Career outcomes", outcomes_url or source_url, field_path="outcomes_data"
    )
    req_url = (
        (application_requirements or {}).get("source_url")
        if isinstance(application_requirements, dict)
        else None
    )
    req_ev = _evidence(
        "Admissions requirements", req_url or source_url, field_path="application_requirements"
    )

    _add_signal(
        layers,
        "goals_behaviors_learning_working_style",
        attribute="career_direction",
        preferred_values=career_arcs,
        statement="Public program and outcomes evidence points to these likely career directions.",
        weight=0.2,
        confidence=0.7,
        evidence=outcomes_ev or program_ev,
    )
    _add_signal(
        layers,
        "goals_behaviors_learning_working_style",
        attribute="interest_themes",
        preferred_values=interest_themes,
        statement="The curriculum and description emphasize these academic interests.",
        weight=0.18,
        confidence=0.66,
        evidence=program_ev,
    )

    text = f"{description or ''} {application_requirements or ''}".lower()
    if any(t in text for t in ("team", "collaboration", "collaborative", "cohort")):
        _add_signal(
            layers,
            "goals_behaviors_learning_working_style",
            attribute="working_style",
            preferred_values=["collaborative"],
            statement="Program evidence suggests collaboration or cohort work matters.",
            weight=0.1,
            confidence=0.62,
            evidence=req_ev or program_ev,
        )
    if any(t in text for t in ("capstone", "project", "practicum", "internship", "applied")):
        _add_signal(
            layers,
            "goals_behaviors_learning_working_style",
            attribute="learning_preference",
            preferred_values=["applied_project_work"],
            statement="Program evidence favors students who want applied project work.",
            weight=0.12,
            confidence=0.68,
            evidence=program_ev,
        )
    if any(t in text for t in ("quantitative", "programming", "machine learning", "optimization")):
        _add_signal(
            layers,
            "background_academic",
            attribute="skill_preparation",
            preferred_values=["quantitative_programming_readiness"],
            statement=(
                "Admissions or curriculum evidence emphasizes quantitative and "
                "programming preparation."
            ),
            weight=0.14,
            confidence=0.7,
            evidence=req_ev or program_ev,
        )

    _add_signal(
        layers,
        "values_motivations_community",
        attribute="values_alignment",
        preferred_values=values,
        statement="Program evidence points to these declared values or motivations.",
        weight=0.12,
        confidence=0.62,
        evidence=program_ev,
    )
    if "applied" in text or "impact" in text or "real-world" in text:
        _add_signal(
            layers,
            "values_motivations_community",
            attribute="motivation",
            preferred_values=["applied_impact"],
            statement="The program emphasizes applying knowledge to real problems.",
            weight=0.1,
            confidence=0.66,
            evidence=program_ev,
        )
    if "rigorous" in text or "rigor" in text:
        _add_signal(
            layers,
            "values_motivations_community",
            attribute="community_expectation",
            preferred_values=["intellectual_rigor"],
            statement="The program presents rigor as part of the expected student experience.",
            weight=0.1,
            confidence=0.64,
            evidence=program_ev,
        )

    if not any(layers[layer] for layer in layers) and not allow_omission_only:
        return None
    omissions = [
        {
            "layer": layer,
            "reason": ("No eligible public evidence was available for this target-profile layer."),
            "source": DERIVED_SOURCE,
        }
        for layer in layers
        if not layers[layer]
    ]
    return validate_target_profile(
        {
            "standard_version": 1,
            "derived_at": datetime.now(UTC).isoformat(),
            "layers": layers,
            "omissions": omissions,
        }
    )


def derive_program_preference(
    *,
    cip_code: str | None = None,
    program_name: str = "",
    degree_type: str | None = None,
    class_profile: dict | None = None,
    description: str | None = None,
    outcomes_data: dict | None = None,
    application_requirements: dict | None = None,
    source_url: str | None = None,
    allow_omission_only_target_profile: bool = False,
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

    fields = _safe_preferred_values(
        fields_offered_for_program(cip_code=cip_code, program_name=program_name or "")
    )
    if fields:
        pref["pref_fields"] = fields

    levels = eligible_current_levels(_program_target_level(degree_type))
    if levels:
        pref["pref_levels"] = levels

    gpa = _gpa_floor(class_profile)
    if gpa is not None:
        pref["pref_min_gpa"] = gpa

    target = _target_profile(
        program_name=program_name or "",
        degree_type=degree_type,
        cip_code=cip_code,
        class_profile=class_profile,
        description=description,
        outcomes_data=outcomes_data,
        application_requirements=application_requirements,
        source_url=source_url,
        pref_fields=fields,
        pref_levels=levels,
        pref_min_gpa=gpa,
        allow_omission_only=allow_omission_only_target_profile,
    )
    if target is not None:
        target_has_signals = any(target["layers"][layer] for layer in target["layers"])
        pref["target_profile"] = target
        pref["preference_weights"] = (
            {
                "academic_preparation": 0.3,
                "field_fit": 0.22,
                "career_alignment": 0.2,
                "learning_working_style": 0.16,
                "values_community": 0.12,
            }
            if target_has_signals
            else {}
        )
        pref["provenance"] = {
            "source": DERIVED_SOURCE,
            "standard_version": 1,
            "derived_at": datetime.now(UTC).isoformat(),
            "method": (
                "public_evidence_target_profile_v1"
                if target_has_signals
                else "public_evidence_target_profile_omissions_v1"
            ),
        }
        pref["standard_version"] = 1
        pref["derived_at"] = datetime.now(UTC)

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
    existing_rows = {
        r.program_id: r
        for r in session.scalars(
            select(ProgramPreference).where(ProgramPreference.program_id.in_(program_ids))
        ).all()
    }

    inserted = 0
    for prog in programs:
        if getattr(prog, "is_claimed", False):
            continue  # claimed programs are first-party; crawler never writes them
        existing = existing_rows.get(prog.id)
        pref = derive_program_preference(
            cip_code=getattr(prog, "cip_code", None),
            program_name=getattr(prog, "program_name", "") or "",
            degree_type=getattr(prog, "degree_type", None),
            class_profile=_latest_class_profile(session, prog.id),
            description=getattr(prog, "description_text", None),
            outcomes_data=getattr(prog, "outcomes_data", None),
            application_requirements=getattr(prog, "application_requirements", None),
            source_url=getattr(prog, "website_url", None) or getattr(prog, "source_url", None),
            allow_omission_only_target_profile=(
                existing is not None and existing.source != "claimed"
            ),
        )
        if pref is None:
            continue
        if existing is not None:
            if existing.source == "claimed":
                continue
            for key in (
                "target_profile",
                "preference_weights",
                "provenance",
                "standard_version",
                "derived_at",
            ):
                if getattr(existing, key, None) in (None, {}, []):
                    setattr(existing, key, pref.get(key))
            continue
        session.add(ProgramPreference(program_id=prog.id, **pref))
        inserted += 1

    session.flush()
    return inserted

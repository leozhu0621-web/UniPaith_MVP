"""Phase B1 — Program-side feature builder.

The matcher needs program features in the same vocabulary as student
features (see `unipaith.ai.tools.feature_schema`). Programs are static
relative to a session, so this runs offline / on-write rather than per
match request.

Two paths to produce program features:

1. **Rule-based extraction** (cold start, this PR): pull structured
   fields off `Program` + related rows (intake_rounds, requirements,
   etc.) and project them onto the same controlled vocabulary the
   student features use. Embedding is the program description vector.

2. **LLM extraction** (Phase B2 stretch goal): same prompt as the
   student-side feature emitter, applied to a program description.
   Better for soft tags (interest_themes, values) but costs tokens.

This module ships path (1). Hooks for (2) are stubbed but unwired.

Storage
-------
Program features live on the Program model itself in JSONB columns. The
parallel-session schema landed:
  - Program.feature_vector_sparse  (JSONB)
  - Program.feature_vector_dense   (VECTOR(1024))
  - Program.features_emitted_at    (timestamptz)

If those columns don't yet exist, the rule-based emitter still runs
in-memory (matcher consumes ProgramFeatures dataclasses). A follow-up
migration writes them into a typed table.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from unipaith.services.match.field_canon import fields_offered_for_program
from unipaith.services.matching import ProgramFeatures
from unipaith.services.program_featurizer import featurize_program, soft_feature_completeness

logger = logging.getLogger(__name__)

# delivery_format values that mean the program can be taken remotely. The matcher
# reads `online_available` for the student's `wants_online` flexibility signal.
# part-time is now its OWN explicit `Program.part_time_available` column (Spec 3
# §3) read directly in program_row_from_orm — a null column emits no flexibility
# signal (gated), never a fabricated False.
_ONLINE_DELIVERY_FORMATS: frozenset[str] = frozenset({"online", "hybrid", "remote"})

# AI Structure (Spec 2 — claim hinge): the program-record-level c_program floor
# for a CLAIMED (first-party) program. Mirrors the `claimed` authority used for
# claimed ProgramPreferences in match_service._program_authority.
_CLAIMED_PROGRAM_COMPLETENESS = 0.9


# ── Mapping helpers ────────────────────────────────────────────────────────


_DEGREE_TO_TARGET_LEVEL: dict[str, str] = {
    "BS": "bachelors",
    "BA": "bachelors",
    "BFA": "bachelors",
    "BSE": "bachelors",
    "MS": "masters",
    "MA": "masters",
    "MBA": "masters",
    "MFA": "masters",
    "MPH": "masters",
    "MArch": "masters",
    "PhD": "doctoral",
    "EdD": "doctoral",
    "JD": "professional",
    "MD": "professional",
    "DDS": "professional",
    "DVM": "professional",
}


# Full-word degree_type values — the enrichment fleet stores words ("masters",
# "phd", "professional"), NOT the BS/MS/PhD abbreviations. Mirrors
# derive_preferences._DEGREE_WORD_TO_TARGET so the s→p and p→s sides agree.
# "certificate"/"associate" stay unmapped (→ None): intentionally unclassifiable.
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


def _target_education_level(degree: str | None) -> str | None:
    if not degree:
        return None
    # Abbreviation exact match (case-sensitive: BS / MS / PhD / JD ...).
    if degree in _DEGREE_TO_TARGET_LEVEL:
        return _DEGREE_TO_TARGET_LEVEL[degree]
    # Full word (case-insensitive, punctuation-stripped: "masters", "Ph.D." ...).
    key = degree.strip().lower().replace(".", "").replace("'", "").replace("’", "")
    if key in _DEGREE_WORD_TO_TARGET:
        return _DEGREE_WORD_TO_TARGET[key]
    # Abbreviation prefix (MS-CS, PhD-CS ...).
    for prefix, level in _DEGREE_TO_TARGET_LEVEL.items():
        if degree.startswith(prefix):
            return level
    return None


def target_education_level(degree: str | None) -> str | None:
    """Public alias of the degree -> target-level map (used by derive_preferences)."""
    return _target_education_level(degree)


# ── Public API ─────────────────────────────────────────────────────────────


@dataclass
class ProgramRow:
    """Lightweight projection of a Program for feature extraction.

    Caller fills this from `unipaith.models.institution.Program` (or a
    test fixture). Keeping it as a dataclass means the matcher and
    feature-builder don't drag the full ORM into pure-Python tests.
    """

    id: UUID | str
    name: str = ""
    description: str = ""
    degree: str | None = None
    locations: list[str] = field(default_factory=list)
    tuition_usd_per_year: float | None = None
    tags: list[str] = field(default_factory=list)
    interest_themes: list[str] = field(default_factory=list)
    career_arcs: list[str] = field(default_factory=list)
    values: list[str] = field(default_factory=list)
    social_features: dict[str, float] = field(default_factory=dict)
    support_signals: dict[str, float] = field(default_factory=dict)
    # AI Structure (Spec 3 §3) — typed-fit program-side attributes. Each is
    # projected onto the matcher sparse vocab only when it genuinely exists on the
    # Program; absent → key omitted → no phantom signal.
    fields_offered: list[str] = field(default_factory=list)  # canonical field tokens
    duration_months: int | None = None  # for the desired-time-to-degree fit
    online_available: bool | None = None  # derived from delivery_format
    part_time_available: bool | None = None  # explicit Program column (flexibility fit)
    career_services: bool | None = None  # derived from support_signals evidence
    # Founder governance (2026-06-18) — can the program sponsor an international
    # applicant? Read ONLY by the student→program feasibility veto (a visa-
    # needing student can't attend a program that can't sponsor her). NULL =
    # unknown → no veto. The program→student selection direction never reads it.
    sponsors_international: bool | None = None
    cip_code: str | None = None
    data_completeness: float = 0.5  # default for sparse rows


def features_from_row(
    row: ProgramRow,
    *,
    embedding: list[float] | None = None,
) -> ProgramFeatures:
    """Project a ProgramRow into the matcher's ProgramFeatures shape.

    Rule-based — no LLM. Caller-provided `embedding` is the program's
    description vector (or None during cold start; the matcher falls
    back to soft_align + needs_match without cosine).
    """
    sparse: dict[str, Any] = {
        "target_education_level": _target_education_level(row.degree),
        "locations": list(row.locations),
        "tuition_usd_per_year": row.tuition_usd_per_year,
        "interest_themes": list(row.interest_themes),
        "career_arcs": list(row.career_arcs),
        "values": list(row.values),
        "social_features": dict(row.social_features),
        "support_signals": dict(row.support_signals),
    }
    # AI Structure (Spec 3 §3) — wire the typed-fit program-side keys so the
    # round-3 s→p signals (field / time / flexibility / support) fire on real
    # data. Each is GATED: a key appears only when the source attribute genuinely
    # exists, so the matcher's per-signal `if program lists X` guard sees the real
    # value (and an absent attribute injects no phantom dimension).
    fields_offered = list(row.fields_offered) or fields_offered_for_program(
        cip_code=row.cip_code, program_name=row.name
    )
    if fields_offered:
        sparse["fields_offered"] = fields_offered
    if row.duration_months is not None:
        sparse["duration_months"] = row.duration_months
    if row.online_available is not None:
        sparse["online_available"] = row.online_available
    if row.part_time_available is not None:
        sparse["part_time_available"] = row.part_time_available
    # Founder governance (2026-06-18) — project sponsorship for the s→p
    # feasibility veto. GATED: a NULL column emits no key, so the veto only fires
    # when the program KNOWN-cannot sponsor (False); unknown never vetoes.
    if row.sponsors_international is not None:
        sparse["sponsors_international"] = row.sponsors_international
    # career_services: explicit row flag wins; else derive from the evidence-based
    # support_signals the featurizer already grounded in real description text.
    if row.career_services is not None:
        sparse["career_services"] = row.career_services
    elif row.support_signals.get("career_services"):
        sparse["career_services"] = True
    return ProgramFeatures(
        program_id=row.id,
        sparse=sparse,
        embedding=embedding,
        data_completeness=max(0.0, min(1.0, row.data_completeness)),
    )


def _safe_loaded(obj: Any, attr: str) -> Any:
    """Return `obj.attr` only if it's already loaded — never trigger
    lazy IO. Returns None for both "not loaded" and "loaded but None".

    SQLAlchemy 2 raises MissingGreenlet on lazy access in async code.
    The projector reads relationships defensively so callers can pass
    rows whether or not they eager-loaded the join.
    """
    try:
        # SQLAlchemy's instance state knows whether a relationship has
        # been loaded. `inspect(obj).unloaded` is the set of unloaded
        # attribute names.
        from sqlalchemy import inspect as sa_inspect

        state = sa_inspect(obj, raiseerr=False)
        if state is not None and attr in getattr(state, "unloaded", ()):
            return None
    except Exception:  # pragma: no cover — duck-typed inputs
        return getattr(obj, attr, None)
    return getattr(obj, attr, None)


def program_row_from_orm(program: Any) -> ProgramRow:
    """Project a `unipaith.models.institution.Program` ORM row into the
    `ProgramRow` dataclass the matcher / feature builder consumes.

    Stays decoupled from the ORM at the type-hint level (`program: Any`)
    so this helper can be called from anywhere without dragging the
    institution model into pure-Python tests. The caller passes a row;
    we read the documented attributes.

    Soft-feature columns (`interest_themes`, `career_arcs`, `values`,
    `support_signals`, `social_features`) live on the parallel
    `feature_vector_sparse` JSONB if present — Phase B2 stretch will
    populate them via the LLM emitter. Until then they're empty and the
    matcher falls back to cosine + needs (when the embedding exists)
    or degrades to soft_align=0 (which the geometric-mean confidence
    naturally penalizes).
    """
    sparse: dict[str, Any] = dict(getattr(program, "feature_vector_sparse", None) or {})

    # Spec 65 §3 — if the program has no stored soft features (the common case:
    # feature_vector_sparse was never populated), derive them deterministically
    # from the program's real CIP / field / degree / description so the matcher's
    # soft_align + needs_match are not dead weight. A populated feature_vector_sparse
    # (LLM featurizer / stored vector, a later increment) takes precedence.
    if not sparse.get("interest_themes") and not sparse.get("career_arcs"):
        _derived = featurize_program(
            cip_code=getattr(program, "cip_code", None),
            degree_type=getattr(program, "degree_type", None),
            name=getattr(program, "program_name", "") or "",
            description=getattr(program, "description_text", "") or "",
        )
        # Only override when we actually derived something — a truly dataless
        # program keeps the existing neutral default (backward-compatible).
        if (
            _derived.get("interest_themes")
            or _derived.get("career_arcs")
            or _derived.get("support_signals")
        ):
            for _k, _v in _derived.items():
                sparse.setdefault(_k, _v)
            sparse.setdefault("data_completeness", soft_feature_completeness(_derived))

    locations = list(sparse.get("locations") or [])
    if not locations:
        # Best-effort fallback: pull through institution.country when
        # the caller has eager-loaded the relationship. We check the
        # SQLAlchemy state to avoid triggering a lazy load inside
        # async code (which raises MissingGreenlet).
        inst = _safe_loaded(program, "institution")
        country = getattr(inst, "country", None) if inst is not None else None
        if country:
            locations = [country]

    tuition_usd = sparse.get("tuition_usd_per_year")
    if tuition_usd is None and getattr(program, "tuition", None) is not None:
        tuition_usd = float(program.tuition)

    # AI Structure (Spec 3 §3) — read the typed-fit attributes off the REAL ORM
    # columns so the round-3 program-side keys are populated on live data.
    duration_months = sparse.get("duration_months")
    if duration_months is None:
        raw_dur = getattr(program, "duration_months", None)
        if raw_dur is not None:
            duration_months = int(raw_dur)

    # online_available: derived ONLY from the real delivery_format column. A
    # missing / in-person format leaves it None (no flexibility signal), never a
    # fabricated False that would falsely fail a student's online want.
    online_available = sparse.get("online_available")
    if online_available is None:
        fmt = getattr(program, "delivery_format", None)
        if fmt:
            online_available = str(fmt).strip().lower() in _ONLINE_DELIVERY_FORMATS

    # part_time_available: the real Program.part_time_available column (Spec 3
    # §3). A null column leaves it None (no flexibility signal contribution),
    # never a fabricated False — a stored vector value, if present, wins.
    part_time_available = sparse.get("part_time_available")
    if part_time_available is None:
        raw_pt = getattr(program, "part_time_available", None)
        if raw_pt is not None:
            part_time_available = bool(raw_pt)

    # sponsors_international: the real Program.sponsors_international column
    # (founder governance 2026-06-18). A null column leaves it None (no
    # feasibility veto), never a fabricated False — a stored vector value wins.
    sponsors_international = sparse.get("sponsors_international")
    if sponsors_international is None:
        raw_spon = getattr(program, "sponsors_international", None)
        if raw_spon is not None:
            sponsors_international = bool(raw_spon)

    support_signals = dict(sparse.get("support_signals") or {})
    name = getattr(program, "program_name", "") or ""
    cip_code = getattr(program, "cip_code", None)

    # AI Structure (Spec 2 — claim hinge): a CLAIMED program is first-party,
    # higher-authority data; lift its baseline c_program (data_completeness) so a
    # claimed program outscores an identical-fit unclaimed one even before any
    # ProgramPreference row exists. `_overlay_program_prefs` later refines this
    # from the preference provenance when present (preference source is the
    # sharper signal); this is the program-record-level floor.
    data_completeness = float(sparse.get("data_completeness", 0.5))
    if getattr(program, "is_claimed", False):
        data_completeness = max(data_completeness, _CLAIMED_PROGRAM_COMPLETENESS)

    return ProgramRow(
        id=program.id,
        name=name,
        description=getattr(program, "description_text", "") or "",
        degree=getattr(program, "degree_type", None),
        locations=list(locations),
        tuition_usd_per_year=tuition_usd,
        tags=list(sparse.get("tags") or []),
        interest_themes=list(sparse.get("interest_themes") or []),
        career_arcs=list(sparse.get("career_arcs") or []),
        values=list(sparse.get("values") or []),
        social_features=dict(sparse.get("social_features") or {}),
        support_signals=support_signals,
        fields_offered=list(sparse.get("fields_offered") or []),
        duration_months=duration_months,
        online_available=online_available,
        part_time_available=part_time_available,
        sponsors_international=sponsors_international,
        cip_code=cip_code,
        data_completeness=data_completeness,
    )


def estimate_data_completeness(row: ProgramRow) -> float:
    """Cheap heuristic: how complete is this Program row?

    Used to pre-fill `ProgramRow.data_completeness` from a freshly
    crawled program. Six signal fields, equal-weighted; counts a field
    as 'present' if non-empty.
    """
    fields_present = sum(
        1
        for v in (
            row.degree,
            row.locations,
            row.tuition_usd_per_year,
            row.interest_themes,
            row.career_arcs,
            row.values,
        )
        if v
    )
    return fields_present / 6

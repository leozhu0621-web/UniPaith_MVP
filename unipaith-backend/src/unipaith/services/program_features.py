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

from unipaith.services.matching import ProgramFeatures

logger = logging.getLogger(__name__)


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


def _target_education_level(degree: str | None) -> str | None:
    if not degree:
        return None
    # Try exact match, then prefix.
    if degree in _DEGREE_TO_TARGET_LEVEL:
        return _DEGREE_TO_TARGET_LEVEL[degree]
    for prefix, level in _DEGREE_TO_TARGET_LEVEL.items():
        if degree.startswith(prefix):
            return level
    return None


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
    return ProgramFeatures(
        program_id=row.id,
        sparse=sparse,
        embedding=embedding,
        data_completeness=max(0.0, min(1.0, row.data_completeness)),
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

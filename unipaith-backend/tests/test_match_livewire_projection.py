"""AI Structure round-3 "livewire" — make the typed-fit signals + two-sided
confidence fire on REAL data instead of staying dormant.

Pure-Python (no DB): exercises the deterministic projection helpers that feed
the matcher — the field-of-study canonicalizer, the student-side confidence
derived from real profile completeness, and the program-side authority derived
from the claim/source provenance. The DB-overlay wiring is covered by the
DB-backed tests in test_d2_feature_projection.py (run in CI).
"""

from __future__ import annotations

import math

from unipaith.services.match.field_canon import (
    _ALIASES,
    _CIP_FAMILY_FIELD,
    CANONICAL_FIELDS,
    canonical_field,
    fields_offered_for_program,
)
from unipaith.services.match_service import _program_authority, _student_confidence

# ── field-of-study canonicalizer (Spec 3 §3 categorical) ─────────────────────


def test_canonical_field_normalizes_freetext_to_snake() -> None:
    assert canonical_field("Data Science") == "data_science"
    assert canonical_field("Computer Science & Engineering") == "computer_science"
    assert canonical_field("Public Health") == "public_health"
    # already-canonical input passes through
    assert canonical_field("data_science") == "data_science"


def test_canonical_field_unclassifiable_returns_none() -> None:
    # An ambiguous abbreviation / unmodeled field returns None so the caller
    # emits no field token (gated — no phantom signal).
    assert canonical_field("CS") is None
    assert canonical_field("Underwater Basketweaving") is None
    assert canonical_field(None) is None
    assert canonical_field("") is None


def test_every_alias_and_cip_target_is_canonical() -> None:
    """The canonicalizer must only ever emit tokens the sim table understands."""
    for _phrase, token in _ALIASES:
        assert token in CANONICAL_FIELDS, token
    for token in _CIP_FAMILY_FIELD.values():
        assert token in CANONICAL_FIELDS, token


def test_fields_offered_precedence_name_then_cip() -> None:
    # program_name alias hit wins
    assert fields_offered_for_program(program_name="MS in Data Science") == ["data_science"]
    # falls back to CIP family when the name does not classify
    assert fields_offered_for_program(cip_code="11.07", program_name="Program 3") == [
        "computer_science"
    ]
    # nothing classifies → empty (gated, no field signal)
    assert fields_offered_for_program(cip_code=None, program_name="Program 3") == []


# ── c_student derived from real profile depth (GAP 1) ────────────────────────


def test_student_confidence_varies_with_profile_depth() -> None:
    thin = _student_confidence(0.0)
    mid = _student_confidence(0.5)
    deep = _student_confidence(1.0)
    assert thin < mid < deep
    assert deep == 1.0
    # a brand-new (completeness 0) profile is floored, not zeroed
    assert thin == 0.5


def test_student_confidence_bounded_and_failsoft() -> None:
    assert _student_confidence(2.0) == 1.0  # clamped above
    assert _student_confidence(-1.0) == 0.5  # clamped to floor
    assert _student_confidence(math.nan) == 0.5  # NaN → floor
    assert _student_confidence(None) == 0.5  # type: ignore[arg-type]


# ── claim → c_program authority precedence (Spec 2) ──────────────────────────


def test_program_authority_claimed_outranks_derived_outranks_crawler() -> None:
    claimed = _program_authority("claimed")
    derived = _program_authority("derived")
    crawler = _program_authority("crawler")
    assert claimed is not None and derived is not None and crawler is not None
    assert claimed > derived > crawler


def test_program_authority_explicit_confidence_wins() -> None:
    assert _program_authority("derived", 0.95) == 0.95
    # a NaN explicit confidence is ignored, falling back to the source default
    assert _program_authority("claimed", math.nan) == 0.9


def test_program_authority_unknown_source_returns_none() -> None:
    # None → caller leaves the existing data_completeness untouched.
    assert _program_authority(None) is None
    assert _program_authority("some_future_source") is None

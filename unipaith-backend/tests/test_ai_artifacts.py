"""Phase A2 — Artifact-writer unit tests.

Covers the LLM-JSON → DB-row mapping logic without DB. The `persist_*`
function tests live in integration tests (need a real session).
"""

from __future__ import annotations

from datetime import date

from unipaith.ai.artifacts import (
    _identity_dedup_key,
    _parse_time_bound,
    _severity_to_enum,
    snapshot_from_extracted_signals_history,
)

# ── Severity int → enum ─────────────────────────────────────────────────────


def test_severity_5_4_map_to_must_have() -> None:
    assert _severity_to_enum(5) == "must_have"
    assert _severity_to_enum(4) == "must_have"


def test_severity_3_maps_to_strong_preference() -> None:
    assert _severity_to_enum(3) == "strong_preference"


def test_severity_2_1_map_to_nice_to_have() -> None:
    assert _severity_to_enum(2) == "nice_to_have"
    assert _severity_to_enum(1) == "nice_to_have"


def test_severity_passthrough_for_already_string_values() -> None:
    """If the LLM returned an enum directly, accept it."""
    assert _severity_to_enum("must_have") == "must_have"
    assert _severity_to_enum("strong_preference") == "strong_preference"
    assert _severity_to_enum("nice_to_have") == "nice_to_have"


def test_severity_unknown_defaults_to_strong_preference() -> None:
    """Defensive: middle bucket avoids both over-counting and silently
    dropping the signal."""
    assert _severity_to_enum(None) == "strong_preference"
    assert _severity_to_enum("garbage") == "strong_preference"
    assert _severity_to_enum(0) == "strong_preference"
    assert _severity_to_enum(99) == "strong_preference"


# ── Time-bound parsing ──────────────────────────────────────────────────────


def test_parse_time_bound_iso_date() -> None:
    assert _parse_time_bound("2031-05-15") == date(2031, 5, 15)


def test_parse_time_bound_year_month() -> None:
    assert _parse_time_bound("2031-05") == date(2031, 5, 1)


def test_parse_time_bound_year_only() -> None:
    assert _parse_time_bound("2031") == date(2031, 1, 1)


def test_parse_time_bound_handles_prose() -> None:
    """'in residency by 2031' → 2031 (best-effort)."""
    assert _parse_time_bound("by 2031") is None  # no match at start
    # The regex anchors at start; ymd-prefixed prose works:
    assert _parse_time_bound("2031 end of") == date(2031, 1, 1)


def test_parse_time_bound_returns_none_on_garbage() -> None:
    assert _parse_time_bound("eventually") is None
    assert _parse_time_bound(None) is None
    assert _parse_time_bound(42) is None


def test_parse_time_bound_invalid_date_returns_none() -> None:
    """Out-of-range months/days don't crash — return None."""
    assert _parse_time_bound("2031-13-01") is None
    assert _parse_time_bound("2031-02-30") is None


# ── Identity dedup key ──────────────────────────────────────────────────────


def test_identity_dedup_key_normalizes_case_and_whitespace() -> None:
    a = {"value": "  Help PEOPLE  ", "source_quote": "I want to help"}
    b = {"value": "help people", "source_quote": "i want to help"}
    assert _identity_dedup_key(a, "value") == _identity_dedup_key(b, "value")


def test_identity_dedup_key_distinct_for_different_claims() -> None:
    a = {"value": "help people", "source_quote": "qa"}
    b = {"value": "publish papers", "source_quote": "qa"}
    assert _identity_dedup_key(a, "value") != _identity_dedup_key(b, "value")


# ── Snapshot reconstruction ─────────────────────────────────────────────────


def test_snapshot_empty_history_returns_empty_snapshot() -> None:
    snap = snapshot_from_extracted_signals_history([])
    assert snap.age is None
    assert snap.education_level is None
    assert snap.test_scores == []
    assert snap.first_gen is None


def test_snapshot_newest_wins_for_scalars() -> None:
    """Later turns overwrite earlier scalars — the student's most recent
    answer is the truth."""
    history = [
        {"basic": {"age": 17}},
        {"basic": {"age": 18}},  # corrected
    ]
    snap = snapshot_from_extracted_signals_history(history)
    assert snap.age == 18


def test_snapshot_test_scores_dedup_by_type() -> None:
    history = [
        {"basic": {"test_scores": [{"type": "GRE", "score": 320}]}},
        {"basic": {"test_scores": [{"type": "GRE", "score": 332}]}},  # rescore
        {"basic": {"test_scores": [{"type": "TOEFL", "score": 110}]}},
    ]
    snap = snapshot_from_extracted_signals_history(history)
    types = sorted(t["type"] for t in snap.test_scores)
    assert types == ["GRE", "TOEFL"]
    gre = next(t for t in snap.test_scores if t["type"] == "GRE")
    assert gre["score"] == 332.0


def test_snapshot_location_lists_union() -> None:
    history = [
        {"basic": {"location_prefs": ["US-NY"]}},
        {"basic": {"location_prefs": ["US-MA", "US-NY"]}},  # dup ignored
    ]
    snap = snapshot_from_extracted_signals_history(history)
    assert sorted(snap.location_prefs) == ["US-MA", "US-NY"]


def test_snapshot_skips_non_dict_entries() -> None:
    """Defensive: stub messages or None entries don't crash the scan."""
    history = [None, {"basic": {"age": 20}}, {"_phase": "A_stub"}]
    snap = snapshot_from_extracted_signals_history(history)  # type: ignore[arg-type]
    assert snap.age == 20


def test_snapshot_handles_invalid_types_gracefully() -> None:
    history = [{"basic": {"age": "not a number", "gpa": "huh"}}]
    snap = snapshot_from_extracted_signals_history(history)
    # Both are silently dropped — the scan must not crash.
    assert snap.age is None
    assert snap.gpa is None

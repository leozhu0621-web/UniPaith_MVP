"""Phase B2 — Match Service unit tests (no DB).

Pure-Python coverage of the dataclasses + the EmittedFeatures →
StudentFeatures bridge. Integration tests against the real DB live in
the existing test_match_dual_scores.py + new test_matches_api.py +
test_match_service_d_wiring.py (D2 calibrator + D3 reranker wiring).
"""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from unipaith.ai.feature_emitter import EmittedFeatures
from unipaith.services.confidence_calibrator import CalibratorState
from unipaith.services.match_service import (
    MatchRow,
    MatchService,
    MatchWithRationale,
    features_from_emitted,
)


def test_match_row_dataclass_defaults() -> None:
    pid = uuid4()
    row = MatchRow(program_id=pid, fitness=Decimal("0.8"), confidence=Decimal("0.7"))
    assert row.rank == 0
    assert row.fitness_breakdown == {}
    assert row.confidence_breakdown == {}


def test_match_with_rationale_defaults_assume_no_rationale() -> None:
    pid = uuid4()
    row = MatchRow(program_id=pid, fitness=Decimal("0.8"), confidence=Decimal("0.7"))
    out = MatchWithRationale(match=row)
    assert out.rationale_text == ""
    assert out.cache_hit is False
    assert out.grounded is True
    assert out.cost_usd == 0


def test_features_from_emitted_projects_sparse() -> None:
    emitted = EmittedFeatures(
        sparse_features={
            "education_level": "bachelors",
            "feature_completeness": 0.85,
            "interest_themes": ["machine_learning"],
        },
        applicant_summary="real summary",
        embedding=[0.1] * 1024,
    )
    sf = features_from_emitted(emitted)
    assert sf.profile_completeness == 0.85
    assert sf.embedding is not None
    assert len(sf.embedding) == 1024
    assert sf.sparse["education_level"] == "bachelors"


def test_features_from_emitted_empty_completeness_default() -> None:
    """Missing feature_completeness → defaults to 0 (penalizes confidence)."""
    emitted = EmittedFeatures(
        sparse_features={"education_level": "bachelors"},
        applicant_summary="x",
    )
    sf = features_from_emitted(emitted)
    assert sf.profile_completeness == 0.0


def test_features_from_emitted_no_embedding() -> None:
    emitted = EmittedFeatures(
        sparse_features={"feature_completeness": 0.8},
        applicant_summary="x",
        embedding=None,
    )
    sf = features_from_emitted(emitted)
    assert sf.embedding is None
    # Matcher will fall back to soft_align + needs_match without cosine.


# ── _row_to_match: D2 calibrator at read time (no DB) ──────────────────────


class _StubRow:
    """Minimal stand-in for MatchResult ORM row — _row_to_match only
    reads the four scalar fields + two breakdowns + program_id, so a
    duck-typed object is enough for unit testing the projection."""

    def __init__(
        self,
        *,
        program_id,
        fitness_score: Decimal,
        confidence_score: Decimal,
        fitness_breakdown: dict | None = None,
        confidence_breakdown: dict | None = None,
    ):
        self.program_id = program_id
        self.fitness_score = fitness_score
        self.confidence_score = confidence_score
        self.fitness_breakdown = fitness_breakdown or {}
        self.confidence_breakdown = confidence_breakdown or {}


def test_row_to_match_unfitted_calibrator_is_identity() -> None:
    """Cold start: no calibrator → raw confidence flows through."""
    pid = uuid4()
    row = _StubRow(
        program_id=pid,
        fitness_score=Decimal("0.85"),
        confidence_score=Decimal("0.62"),
        confidence_breakdown={"foo": "bar"},
    )
    out = MatchService._row_to_match(row, CalibratorState(), rank=3)
    assert out.confidence == Decimal("0.62")
    assert out.rank == 3
    assert out.confidence_breakdown["foo"] == "bar"
    cal = out.confidence_breakdown["calibration"]
    assert cal["raw"] == 0.62
    assert cal["calibrated"] == 0.62
    assert cal["calibrator_fitted"] is False
    assert cal["calibrator_n_samples"] == 0


def test_row_to_match_fitted_calibrator_remaps_confidence() -> None:
    """Fitted calibrator with a downward bend → confidence shifts."""
    # Calibrator that maps 0.6 → 0.4 (e.g. observed-rate is lower than
    # predicted at this bucket — the matcher was overconfident).
    state = CalibratorState(
        fitted=True,
        n_samples=2_000,
        breakpoints=[[0.0, 0.0], [0.6, 0.4], [1.0, 1.0]],
    )
    pid = uuid4()
    row = _StubRow(
        program_id=pid,
        fitness_score=Decimal("0.85"),
        confidence_score=Decimal("0.6"),
    )
    out = MatchService._row_to_match(row, state, rank=1)
    assert out.confidence == Decimal("0.4")
    assert out.confidence_breakdown["calibration"]["raw"] == 0.6
    assert out.confidence_breakdown["calibration"]["calibrated"] == 0.4
    assert out.confidence_breakdown["calibration"]["calibrator_fitted"] is True
    assert out.confidence_breakdown["calibration"]["calibrator_n_samples"] == 2_000


def test_row_to_match_preserves_fitness_breakdown() -> None:
    """Calibration only touches confidence — fitness path is untouched."""
    pid = uuid4()
    row = _StubRow(
        program_id=pid,
        fitness_score=Decimal("0.7"),
        confidence_score=Decimal("0.5"),
        fitness_breakdown={"cosine": 0.6, "rerank": {"strategy": "identity"}},
    )
    out = MatchService._row_to_match(row, CalibratorState(), rank=1)
    assert out.fitness_breakdown["cosine"] == 0.6
    assert out.fitness_breakdown["rerank"]["strategy"] == "identity"
    assert out.fitness == Decimal("0.7")


def test_row_to_match_does_not_mutate_input_breakdown() -> None:
    """Functional projection — the source row's breakdown dict must not
    receive the `calibration` key as a side effect."""
    pid = uuid4()
    original = {"profile_completeness": 0.85}
    row = _StubRow(
        program_id=pid,
        fitness_score=Decimal("0.7"),
        confidence_score=Decimal("0.5"),
        confidence_breakdown=original,
    )
    MatchService._row_to_match(row, CalibratorState(), rank=1)
    assert "calibration" not in original
    assert original == {"profile_completeness": 0.85}

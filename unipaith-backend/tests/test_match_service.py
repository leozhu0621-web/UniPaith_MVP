"""Phase B2 — Match Service unit tests (no DB).

Pure-Python coverage of the dataclasses + the EmittedFeatures →
StudentFeatures bridge. Integration tests against the real DB live in
the existing test_match_dual_scores.py + new test_matches_api.py.
"""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from unipaith.ai.feature_emitter import EmittedFeatures
from unipaith.services.match_service import (
    MatchRow,
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

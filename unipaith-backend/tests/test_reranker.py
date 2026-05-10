"""Phase D3 — Year-2 reranker scaffold tests.

Cold-start verification: identity reranker preserves order and
breakdowns. Plus learned-reranker fall-through behavior, state
serialization, trainer guard, and bias-audit harness.
"""

from __future__ import annotations

from decimal import Decimal

from unipaith.services.matching import ProgramFeatures, Score, StudentFeatures
from unipaith.services.reranker import (
    MAX_DISPARITY_GAP_PP,
    MIN_PAIRS_FOR_RERANKER,
    BiasAuditResult,
    IdentityReranker,
    LearnedReranker,
    RerankerState,
    audit_pair_invariance,
    get_reranker,
    train_learned_reranker,
)


def _make_ranked(n: int = 3) -> list[tuple[ProgramFeatures, Score]]:
    """Synthesize a small ranked list for reranker tests."""
    out: list[tuple[ProgramFeatures, Score]] = []
    for i in range(n):
        program = ProgramFeatures(program_id=f"p{i}", sparse={}, embedding=None)
        score = Score(
            fitness=Decimal(str(round(0.9 - i * 0.1, 4))),
            confidence=Decimal("0.8"),
            fitness_breakdown={"cosine": 0.7, "soft_align": 0.5, "needs_match": 0.3},
            confidence_breakdown={
                "profile_completeness": 0.85,
                "program_data_quality": 0.7,
            },
        )
        out.append((program, score))
    return out


# ── IdentityReranker ───────────────────────────────────────────────────────


def test_identity_reranker_preserves_order() -> None:
    student = StudentFeatures(profile_completeness=0.85)
    ranked = _make_ranked(5)
    out = IdentityReranker().rerank(student, ranked)
    assert [p.program_id for p, _ in out] == [p.program_id for p, _ in ranked]


def test_identity_reranker_annotates_breakdown() -> None:
    """Every output Score should carry a `rerank` annotation so the
    rationale agent + admin dashboard can tell the rerank stage ran."""
    student = StudentFeatures(profile_completeness=0.85)
    ranked = _make_ranked(3)
    out = IdentityReranker().rerank(student, ranked)
    for _, score in out:
        rerank = score.fitness_breakdown.get("rerank")
        assert rerank is not None
        assert rerank["strategy"] == "identity"
        assert rerank["score"] == 0.0


def test_identity_reranker_does_not_mutate_input() -> None:
    """Reranker is functional — input list should be untouched even
    on its score breakdowns."""
    student = StudentFeatures(profile_completeness=0.85)
    ranked = _make_ranked(2)
    original_breakdowns = [
        dict(score.fitness_breakdown) for _, score in ranked
    ]
    IdentityReranker().rerank(student, ranked)
    after_breakdowns = [dict(score.fitness_breakdown) for _, score in ranked]
    assert original_breakdowns == after_breakdowns


def test_identity_reranker_preserves_fitness_and_confidence() -> None:
    student = StudentFeatures(profile_completeness=0.85)
    ranked = _make_ranked(3)
    out = IdentityReranker().rerank(student, ranked)
    for (_, before), (_, after) in zip(ranked, out, strict=False):
        assert before.fitness == after.fitness
        assert before.confidence == after.confidence


def test_identity_reranker_empty_input_returns_empty() -> None:
    out = IdentityReranker().rerank(StudentFeatures(), [])
    assert out == []


# ── LearnedReranker (cold-start fall-through) ─────────────────────────────


def test_learned_reranker_unfitted_falls_through_to_identity() -> None:
    """Default state (fitted=False) → identity behavior."""
    student = StudentFeatures(profile_completeness=0.85)
    ranked = _make_ranked(3)
    learned = LearnedReranker()  # default unfitted state
    out = learned.rerank(student, ranked)
    # Order preserved
    assert [p.program_id for p, _ in out] == [p.program_id for p, _ in ranked]
    # Annotated as fall-through
    for _, score in out:
        assert score.fitness_breakdown["rerank"]["strategy"] == "lightgbm_v1_unfitted"


def test_learned_reranker_with_garbage_blob_falls_through() -> None:
    """If the model_blob is corrupted, we fail-closed to identity
    rather than crashing the request."""
    student = StudentFeatures(profile_completeness=0.85)
    ranked = _make_ranked(3)
    learned = LearnedReranker(
        state=RerankerState(
            fitted=True,
            n_samples=10000,
            model_blob=b"not a valid pickle",
        )
    )
    out = learned.rerank(student, ranked)
    # Order preserved (identity fall-through)
    assert [p.program_id for p, _ in out] == [p.program_id for p, _ in ranked]
    for _, score in out:
        assert score.fitness_breakdown["rerank"]["strategy"] == "lightgbm_v1_load_error"


def test_learned_reranker_feature_row_shape() -> None:
    """The hand-engineered feature projection must produce a
    fixed-length row matching the trained model's input shape."""
    student = StudentFeatures(profile_completeness=0.85)
    program = ProgramFeatures(program_id="p1", data_completeness=0.7)
    score = Score(
        fitness=Decimal("0.8"),
        confidence=Decimal("0.7"),
        fitness_breakdown={"cosine": 0.6, "soft_align": 0.5, "needs_match": 0.4},
        confidence_breakdown={"profile_completeness": 0.85, "program_data_quality": 0.7},
    )
    row = LearnedReranker._build_feature_row(student, program, score)
    assert len(row) == 7
    assert all(isinstance(x, float) for x in row)


# ── RerankerState serialization ────────────────────────────────────────────


def test_reranker_state_round_trips() -> None:
    state = RerankerState(
        fitted=True,
        n_samples=10000,
        model_blob=b"some bytes",
        feature_names=["a", "b"],
        fitted_at="2026-05-10T00:00:00",
    )
    restored = RerankerState.from_dict(state.to_dict())
    assert restored.fitted == state.fitted
    assert restored.n_samples == state.n_samples
    assert restored.model_blob == state.model_blob
    assert restored.feature_names == state.feature_names


def test_reranker_state_from_none_default() -> None:
    state = RerankerState.from_dict(None)
    assert state.fitted is False
    assert state.model_blob is None


# ── train_learned_reranker (guard against premature training) ─────────────


def test_train_below_minimum_returns_unfitted() -> None:
    pairs = [([0.5] * 7, 0)] * 100  # below MIN_PAIRS_FOR_RERANKER
    state = train_learned_reranker(pairs)
    assert state.fitted is False
    assert state.n_samples == 100


def test_train_at_minimum_returns_fitted_when_lightgbm_available() -> None:
    """If lightgbm is installed (it's in deps), training above the
    minimum should succeed. Skip if not available — keeps tests
    portable across environments."""
    try:
        import lightgbm  # noqa: F401
    except ImportError:
        return  # gracefully skip
    # Synthetic data: clearly separable classes
    pairs: list[tuple[list[float], int]] = []
    for i in range(MIN_PAIRS_FOR_RERANKER):
        # Half positive (high cosine), half negative (low cosine)
        if i % 2 == 0:
            pairs.append(([0.9, 0.8, 0.7, 0.85, 0.7, 0.85, 0.7], 1))
        else:
            pairs.append(([0.2, 0.1, 0.1, 0.5, 0.5, 0.5, 0.5], 0))
    state = train_learned_reranker(pairs)
    assert state.fitted is True
    assert state.n_samples == MIN_PAIRS_FOR_RERANKER
    assert state.model_blob is not None
    assert state.fitted_at is not None
    assert len(state.feature_names) == 7


# ── get_reranker factory ───────────────────────────────────────────────────


def test_get_reranker_no_state_returns_identity() -> None:
    r = get_reranker()
    assert isinstance(r, IdentityReranker)


def test_get_reranker_unfitted_state_returns_identity() -> None:
    r = get_reranker(state=RerankerState(fitted=False))
    assert isinstance(r, IdentityReranker)


def test_get_reranker_fitted_state_returns_learned() -> None:
    r = get_reranker(
        state=RerankerState(fitted=True, n_samples=10000, model_blob=b"x")
    )
    assert isinstance(r, LearnedReranker)


# ── Bias audit harness ────────────────────────────────────────────────────


def test_audit_pair_invariance_no_pairs_passes() -> None:
    result = audit_pair_invariance(paired_results=[])
    assert result.passed is True
    assert result.n_pairs == 0


def test_audit_pair_invariance_identical_top_k_passes() -> None:
    """Identical pairs → 0 gap → pass."""
    a = [Decimal("0.8"), Decimal("0.7"), Decimal("0.6")]
    pairs = [(a, list(a))] * 10
    result = audit_pair_invariance(paired_results=pairs)
    assert result.passed is True
    assert result.max_gap_pp == 0.0
    assert result.n_failures == 0


def test_audit_pair_invariance_small_gap_within_threshold_passes() -> None:
    """Gap below threshold (5pp default) → pass."""
    a = [Decimal("0.80"), Decimal("0.70"), Decimal("0.60")]
    b = [Decimal("0.81"), Decimal("0.71"), Decimal("0.61")]  # 1pp shift
    pairs = [(a, b)] * 5
    result = audit_pair_invariance(paired_results=pairs)
    assert result.passed is True
    assert result.max_gap_pp < MAX_DISPARITY_GAP_PP


def test_audit_pair_invariance_large_gap_fails() -> None:
    """Gap above threshold → fail with details."""
    a = [Decimal("0.80"), Decimal("0.70"), Decimal("0.60")]
    b = [Decimal("0.50"), Decimal("0.40"), Decimal("0.30")]  # 30pp shift
    result = audit_pair_invariance(paired_results=[(a, b)])
    assert result.passed is False
    assert result.n_failures == 1
    assert result.max_gap_pp > 0.2
    assert len(result.details) == 1
    assert "gap" in result.details[0]


def test_audit_pair_invariance_empty_top_k_marked_as_failure() -> None:
    """An empty top-K from one side → counted as failure with reason."""
    pairs = [
        ([], [Decimal("0.5")]),
        ([Decimal("0.5")], []),
    ]
    result = audit_pair_invariance(paired_results=pairs)
    assert result.passed is False
    assert result.n_failures == 2


def test_audit_pair_invariance_custom_threshold() -> None:
    """Override threshold for stricter / looser audits."""
    a = [Decimal("0.50")]
    b = [Decimal("0.52")]  # 2pp gap
    # With default 5pp threshold → pass
    assert audit_pair_invariance(paired_results=[(a, b)]).passed
    # With 1pp threshold → fail
    result = audit_pair_invariance(
        paired_results=[(a, b)], threshold_pp=0.01
    )
    assert result.passed is False


def test_bias_audit_result_dataclass_defaults() -> None:
    r = BiasAuditResult(passed=True, max_gap_pp=0.0, n_pairs=0, n_failures=0)
    assert r.details == []

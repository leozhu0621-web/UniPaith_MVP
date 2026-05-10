"""Phase D3 — Year-2 reranker scaffold.

Re-orders the top-K matcher outputs using a learned model trained on
partner-institution outcome data (apply / accept / enroll). Cold start:
identity passthrough — the matcher's order stays unchanged. Once
≥5k labeled (student, program, outcome) tuples flow in, we train an
XGBoost / LightGBM ranker on top of the matcher's existing features.

Architecture
------------
The reranker is **stage 3** of the matching stack:

  Stage 1: rule-based filter      (eliminates ineligible programs)
  Stage 2: content cosine + soft  (ranks the survivors)
  Stage 3: learned reranker       (this module — re-orders top K
                                   from stage 2 using outcome data)

The reranker takes (StudentFeatures, list[(ProgramFeatures, Score)])
and returns a re-ordered list. It does NOT change scores — those stay
honest representations of the cold-start ML. Reranking only changes
*order*, with a stored `rerank_score` exposed in the breakdown for
explainability.

Cold-start contract
-------------------
- `IdentityReranker` — passes the input through unchanged. This is
  what runs in production until we have enough partner data to train
  a real model. Behind feature flag `ai_reranker_enabled` (default off).
- `LearnedReranker` — wraps a trained gradient-boosted ranker (lazy
  imports lightgbm). Loaded from the model registry at call time.
  Year-2 work; this PR ships the interface + identity implementation
  + the offline trainer skeleton, NOT a fitted model.

Bias audit (also in this module)
--------------------------------
Before deploying a learned reranker, we run a stratified bias audit:
generate paired profiles differing only on protected attributes,
push them through the matcher AND the reranker, and assert top-K
accept-rate parity within `MAX_DISPARITY_GAP_PP` (5 percentage points).
A failing audit is a deploy blocker.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Protocol

from unipaith.services.matching import ProgramFeatures, Score, StudentFeatures

logger = logging.getLogger(__name__)


# Bias-audit threshold: max accept-rate gap across protected-attribute
# strata at a fixed score threshold. Mirrors the framework spec
# (Plan 2 §9). Tightened on real data; cold start is structural-only.
MAX_DISPARITY_GAP_PP = 0.05

# Minimum labeled outcome pairs before the LearnedReranker is allowed
# to train. Below this we stay on identity. Mirrors the calibrator
# threshold pattern in D2.
MIN_PAIRS_FOR_RERANKER = 5_000


# ── Protocol ────────────────────────────────────────────────────────────────


class Reranker(Protocol):
    """Reranker contract — implementations rerank in-place semantics
    via the returned list, not by mutating the input."""

    def rerank(
        self,
        student: StudentFeatures,
        ranked: list[tuple[ProgramFeatures, Score]],
    ) -> list[tuple[ProgramFeatures, Score]]: ...


# ── Identity reranker (cold start) ─────────────────────────────────────────


@dataclass
class IdentityReranker:
    """No-op reranker — returns input order unchanged.

    Default for cold start. Annotates each Score's
    `fitness_breakdown.rerank` with `{strategy: 'identity', score: 0}`
    so downstream consumers (rationale agent, admin dashboard) can tell
    the rerank stage ran but didn't reorder.
    """

    name: str = "identity"

    def rerank(
        self,
        student: StudentFeatures,  # noqa: ARG002 — interface contract
        ranked: list[tuple[ProgramFeatures, Score]],
    ) -> list[tuple[ProgramFeatures, Score]]:
        out: list[tuple[ProgramFeatures, Score]] = []
        for program, score in ranked:
            new_breakdown = dict(score.fitness_breakdown or {})
            new_breakdown["rerank"] = {"strategy": self.name, "score": 0.0}
            out.append(
                (
                    program,
                    Score(
                        fitness=score.fitness,
                        confidence=score.confidence,
                        eliminated=score.eliminated,
                        fitness_breakdown=new_breakdown,
                        confidence_breakdown=dict(score.confidence_breakdown or {}),
                    ),
                )
            )
        return out


# ── Learned reranker (Year-2 — gated on partner data) ──────────────────────


@dataclass
class RerankerState:
    """Serializable reranker model state, persisted in ModelRegistry."""

    fitted: bool = False
    n_samples: int = 0
    model_blob: bytes | None = None  # pickled lightgbm model
    feature_names: list[str] = field(default_factory=list)
    fitted_at: str | None = None  # ISO timestamp

    def to_dict(self) -> dict[str, Any]:
        return {
            "fitted": self.fitted,
            "n_samples": self.n_samples,
            "model_blob": self.model_blob,
            "feature_names": list(self.feature_names),
            "fitted_at": self.fitted_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> RerankerState:
        if not data:
            return cls()
        return cls(
            fitted=bool(data.get("fitted", False)),
            n_samples=int(data.get("n_samples", 0)),
            model_blob=data.get("model_blob"),
            feature_names=list(data.get("feature_names", [])),
            fitted_at=data.get("fitted_at"),
        )


@dataclass
class LearnedReranker:
    """Gradient-boosted ranker. Year-2 phase; cold start = identity.

    The interface is wired so that swapping in a fitted model is a
    single state load — no service-layer changes needed.
    """

    state: RerankerState = field(default_factory=RerankerState)
    name: str = "lightgbm_v1"

    def rerank(
        self,
        student: StudentFeatures,
        ranked: list[tuple[ProgramFeatures, Score]],
    ) -> list[tuple[ProgramFeatures, Score]]:
        if not self.state.fitted or not self.state.model_blob:
            # Untrained — fall through to identity. Annotate the
            # breakdown so admin can see the reranker was attempted.
            return IdentityReranker(name="lightgbm_v1_unfitted").rerank(student, ranked)

        try:
            import pickle

            model = pickle.loads(self.state.model_blob)
        except Exception as exc:  # pragma: no cover — defensive
            logger.warning("Failed to deserialize reranker model: %s", exc)
            return IdentityReranker(name="lightgbm_v1_load_error").rerank(student, ranked)

        rows = [
            self._build_feature_row(student, program, score)
            for program, score in ranked
        ]
        try:
            rerank_scores = model.predict(rows)
        except Exception as exc:  # pragma: no cover — defensive
            logger.warning("Reranker prediction failed: %s", exc)
            return IdentityReranker(name="lightgbm_v1_predict_error").rerank(student, ranked)

        # Build (program, score, rerank_score) triplets, sort by rerank_score desc.
        triples = list(zip(ranked, rerank_scores, strict=False))
        triples.sort(key=lambda t: float(t[1]), reverse=True)

        out: list[tuple[ProgramFeatures, Score]] = []
        for (program, score), rerank_score in triples:
            new_breakdown = dict(score.fitness_breakdown or {})
            new_breakdown["rerank"] = {
                "strategy": self.name,
                "score": float(rerank_score),
            }
            out.append(
                (
                    program,
                    Score(
                        fitness=score.fitness,
                        confidence=score.confidence,
                        eliminated=score.eliminated,
                        fitness_breakdown=new_breakdown,
                        confidence_breakdown=dict(score.confidence_breakdown or {}),
                    ),
                )
            )
        return out

    @staticmethod
    def _build_feature_row(
        student: StudentFeatures,
        program: ProgramFeatures,
        score: Score,
    ) -> list[float]:
        """Project (student, program, score) into a feature vector for
        the gradient-boosted model. Hand-engineered features:
          - the existing fitness components (cosine / soft_align / needs)
          - the existing confidence components
          - student.profile_completeness
          - program.data_completeness
          - simple interaction features (prefs × supports)
        Year-2 trainer can extend; this projection is the interface.
        """
        bd = score.fitness_breakdown or {}
        cd = score.confidence_breakdown or {}
        return [
            float(bd.get("cosine", 0.0)),
            float(bd.get("soft_align", 0.0)),
            float(bd.get("needs_match", 0.0)),
            float(cd.get("profile_completeness", 0.0)),
            float(cd.get("program_data_quality", 0.0)),
            float(student.profile_completeness),
            float(program.data_completeness),
        ]


# ── Trainer skeleton (Year-2 — fired offline, not at request time) ─────────


def train_learned_reranker(
    pairs: list[tuple[list[float], int]],
) -> RerankerState:
    """Offline trainer. Takes labeled (feature_row, outcome) tuples and
    fits a LightGBM ranker. Below MIN_PAIRS_FOR_RERANKER returns an
    unfitted state (cold start: identity stays in production).

    `pairs` shape: each tuple is (feature_row, label). Labels are 0/1
    (apply / accept / enroll, depending on the chosen outcome metric —
    the choice is documented in the partner-data ingestion path, not
    here).
    """
    if len(pairs) < MIN_PAIRS_FOR_RERANKER:
        logger.info(
            "train_learned_reranker: %d pairs < %d minimum; reranker stays unfitted",
            len(pairs),
            MIN_PAIRS_FOR_RERANKER,
        )
        return RerankerState(fitted=False, n_samples=len(pairs))

    try:
        import datetime as _dt
        import pickle

        from lightgbm import LGBMClassifier  # type: ignore[import-untyped]
    except ImportError:  # pragma: no cover — lightgbm optional
        logger.warning("lightgbm unavailable; reranker stays unfitted")
        return RerankerState(fitted=False, n_samples=len(pairs))

    xs = [list(p[0]) for p in pairs]
    ys = [int(p[1]) for p in pairs]
    model = LGBMClassifier(
        objective="binary",
        n_estimators=100,
        max_depth=6,
        learning_rate=0.05,
        verbosity=-1,
    )
    model.fit(xs, ys)

    return RerankerState(
        fitted=True,
        n_samples=len(pairs),
        model_blob=pickle.dumps(model),
        feature_names=[
            "cosine",
            "soft_align",
            "needs_match",
            "profile_completeness",
            "program_data_quality",
            "student_completeness",
            "program_completeness",
        ],
        fitted_at=_dt.datetime.now(_dt.UTC).isoformat(),
    )


# ── Bias-audit harness ─────────────────────────────────────────────────────
# Generates paired profiles differing only on protected attributes, runs
# the matcher + reranker on both, and asserts top-K accept-rate parity
# stays within MAX_DISPARITY_GAP_PP.


@dataclass
class BiasAuditResult:
    """Outcome of one bias-audit run."""

    passed: bool
    max_gap_pp: float
    n_pairs: int
    n_failures: int
    details: list[dict[str, Any]] = field(default_factory=list)


def audit_pair_invariance(
    *,
    paired_results: list[tuple[list[Decimal], list[Decimal]]],
    threshold_pp: float = MAX_DISPARITY_GAP_PP,
) -> BiasAuditResult:
    """Audit reranker output for bias.

    `paired_results` is a list of (top_k_fitness_a, top_k_fitness_b)
    tuples — one per pair. For each pair:
      - Compute the absolute mean-fitness gap.
      - Pair fails if the gap exceeds threshold_pp (in 0–1 units).
    Suite passes if no pair fails.

    Caller (the bias-audit script) is responsible for generating the
    paired profiles and routing them through the full matcher +
    reranker. This function does only the comparison + aggregation,
    so it's testable without the matcher in scope.
    """
    if not paired_results:
        return BiasAuditResult(passed=True, max_gap_pp=0.0, n_pairs=0, n_failures=0)

    failures = 0
    max_gap = 0.0
    details: list[dict[str, Any]] = []
    for i, (a, b) in enumerate(paired_results):
        if not a or not b:
            details.append({"pair": i, "error": "empty top-k"})
            failures += 1
            continue
        mean_a = float(sum(float(x) for x in a) / len(a))
        mean_b = float(sum(float(x) for x in b) / len(b))
        gap = abs(mean_a - mean_b)
        max_gap = max(max_gap, gap)
        if gap > threshold_pp:
            failures += 1
            details.append(
                {
                    "pair": i,
                    "mean_a": round(mean_a, 4),
                    "mean_b": round(mean_b, 4),
                    "gap": round(gap, 4),
                }
            )
    return BiasAuditResult(
        passed=failures == 0,
        max_gap_pp=round(max_gap, 4),
        n_pairs=len(paired_results),
        n_failures=failures,
        details=details,
    )


# ── Singleton factory ──────────────────────────────────────────────────────


def get_reranker(*, state: RerankerState | None = None) -> Reranker:
    """Return the active reranker.

    Cold start (no state, or unfitted state): IdentityReranker.
    Once a fitted state is loaded from ModelRegistry, returns
    LearnedReranker. The match service is responsible for loading
    state from the registry; this factory just routes.
    """
    if state is None or not state.fitted:
        return IdentityReranker()
    return LearnedReranker(state=state)

"""Phase B2 — Match Service.

Orchestrates the full Match surface:

  1. Read the student's feature vector (from `student_feature_vectors`,
     written by A4).
  2. Build ProgramFeatures for every Program in the catalog (cold-start:
     rule-based via `program_features.features_from_row`).
  3. Run the matcher (`services.matching.score`) to get
     (fitness, confidence, breakdowns) per program.
  4. Persist top-N to `match_results`.
  5. On lazy-load of a card, look up `match_rationales`. Cache miss →
     call A5 Rationale agent → persist on success.

Rationale generation is **lazy** by design — students browse far more
program cards than they read rationales, and rationale generation is
the most expensive per-call surface in the stack. We compute only when
the user actually clicks.

Cache invalidation: keyed by (student_id, program_id, profile_version,
program_version). When A4 bumps `student_feature_vectors.profile_version`
on a profile change, all rationales for that student become stale and
the next click regenerates.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai.feature_emitter import EmittedFeatures
from unipaith.ai.rationale import (
    ProgramView,
    RationaleResult,
    ScoreView,
    StudentView,
    get_rationale_agent,
)
from unipaith.models.ai_artifacts import (
    MatchRationale,
    StudentFeatureVector,
)
from unipaith.models.matching import MatchResult
from unipaith.services.confidence_calibrator import (
    CalibratorState,
    apply_calibrator,
)
from unipaith.services.matching import (
    ProgramFeatures,
    Score,
    StudentFeatures,
    rank_programs,
    score,
)
from unipaith.services.ml_state import (
    load_calibrator_state,
    load_reranker_state,
)
from unipaith.services.program_features import ProgramRow, features_from_row
from unipaith.services.reranker import RerankerState, get_reranker

logger = logging.getLogger(__name__)


# ── Output shapes ──────────────────────────────────────────────────────────


@dataclass
class MatchRow:
    """One ranked match — what the API returns to the frontend."""

    program_id: UUID
    fitness: Decimal
    confidence: Decimal
    fitness_breakdown: dict[str, Any] = field(default_factory=dict)
    confidence_breakdown: dict[str, Any] = field(default_factory=dict)
    rank: int = 0


@dataclass
class MatchWithRationale:
    """A single match plus its rationale (cached or freshly generated)."""

    match: MatchRow
    rationale_text: str = ""
    cited_student_fields: list[str] = field(default_factory=list)
    cited_program_fields: list[str] = field(default_factory=list)
    cache_hit: bool = False
    grounded: bool = True
    cost_usd: float = 0.0


# ── Service ────────────────────────────────────────────────────────────────


class MatchService:
    """Stateless service — instantiate per-request with the AsyncSession.

    The service caches the loaded calibrator + reranker state on `self`
    across calls within the same request lifecycle so the model_registry
    table is hit at most once per request even when the same service is
    used to read multiple matches.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        # Lazy-loaded once per service instance.
        self._calibrator_state: CalibratorState | None = None
        self._reranker_state: RerankerState | None = None

    async def _calibrator(self) -> CalibratorState:
        if self._calibrator_state is None:
            self._calibrator_state = await load_calibrator_state(self.db)
        return self._calibrator_state

    async def _reranker_state_cached(self) -> RerankerState:
        if self._reranker_state is None:
            self._reranker_state = await load_reranker_state(self.db)
        return self._reranker_state

    # ── Score-and-persist ─────────────────────────────────────────────

    async def compute_matches_for_student(
        self,
        student_id: UUID,
        *,
        program_rows: list[ProgramRow],
        program_embeddings: dict[Any, list[float] | None] | None = None,
        top_n: int = 50,
        replace_existing: bool = True,
        weights: dict[str, float] | None = None,
    ) -> list[MatchRow]:
        """Score the student against the provided programs and persist
        the top N to `match_results`.

        Caller is responsible for fetching `program_rows` (typically the
        full catalog or a recently-updated subset) and supplying any
        precomputed program embeddings. The service does NOT fetch
        Program ORM rows on its own — keeps this layer pure-Python and
        DB-decoupled for tests.

        `replace_existing=True` (default) deletes prior rows for this
        student before inserting fresh ones, so the table doesn't bloat
        with stale matches when a student re-completes Discovery.
        """
        sfv = await self._student_features(student_id)
        if sfv is None:
            logger.info(
                "MatchService: no feature vector yet for student=%s; "
                "Discovery must complete before matches can be computed.",
                student_id,
            )
            return []

        program_embeddings = program_embeddings or {}
        program_features = [
            features_from_row(row, embedding=program_embeddings.get(row.id)) for row in program_rows
        ]

        ranked: list[tuple[ProgramFeatures, Score]] = rank_programs(
            sfv, program_features, weights=weights, include_eliminated=False
        )

        # D3: rerank top-K. Cold start = identity, but the breakdowns
        # are annotated so the rationale agent + admin dashboard can see
        # the rerank stage ran. When a fitted model is loaded, this
        # actually reorders.
        reranker_state = await self._reranker_state_cached()
        ranked = get_reranker(state=reranker_state).rerank(sfv, ranked)

        if replace_existing:
            await self.db.execute(delete(MatchResult).where(MatchResult.student_id == student_id))

        out: list[MatchRow] = []
        for rank, (program, scored) in enumerate(ranked[:top_n], start=1):
            row = MatchResult(
                student_id=student_id,
                program_id=program.program_id,
                # New canonical fields (Phase A PR 4 + this PR).
                fitness_score=scored.fitness,
                confidence_score=scored.confidence,
                fitness_breakdown=scored.fitness_breakdown,
                confidence_breakdown=scored.confidence_breakdown,
                # Deprecated mirror — kept populated for the cutover so
                # legacy reads don't see NULLs.
                match_score=scored.fitness,
            )
            self.db.add(row)
            out.append(
                MatchRow(
                    program_id=program.program_id,
                    fitness=scored.fitness,
                    confidence=scored.confidence,
                    fitness_breakdown=scored.fitness_breakdown,
                    confidence_breakdown=scored.confidence_breakdown,
                    rank=rank,
                )
            )
        await self.db.flush()
        return out

    # ── Read paths ────────────────────────────────────────────────────

    async def list_matches(self, student_id: UUID, *, limit: int = 20) -> list[MatchRow]:
        """Read previously-computed matches for the student, ordered by
        fitness desc. No LLM, no scoring — a pure DB read.

        Confidence is calibrated at read time using the active
        CalibratorState. Cold start (unfitted) → raw confidence flows
        through unchanged. The breakdown carries `{raw, calibrated,
        calibrator_fitted}` so admin/rationale tooling can tell the two
        apart.
        """
        result = await self.db.execute(
            select(MatchResult)
            .where(MatchResult.student_id == student_id)
            .order_by(MatchResult.fitness_score.desc(), MatchResult.confidence_score.desc())
            .limit(limit)
        )
        rows = list(result.scalars().all())
        calibrator = await self._calibrator()
        return [self._row_to_match(r, calibrator, rank=i + 1) for i, r in enumerate(rows)]

    @staticmethod
    def _row_to_match(row: MatchResult, calibrator: CalibratorState, *, rank: int) -> MatchRow:
        raw_conf = float(row.confidence_score)
        calibrated = apply_calibrator(calibrator, raw_conf)
        breakdown = dict(row.confidence_breakdown or {})
        breakdown["calibration"] = {
            "raw": round(raw_conf, 4),
            "calibrated": round(calibrated, 4),
            "calibrator_fitted": calibrator.fitted,
            "calibrator_n_samples": calibrator.n_samples,
        }
        return MatchRow(
            program_id=row.program_id,
            fitness=row.fitness_score,
            confidence=Decimal(str(round(calibrated, 4))),
            fitness_breakdown=row.fitness_breakdown or {},
            confidence_breakdown=breakdown,
            rank=rank,
        )

    async def get_match_with_rationale(
        self,
        student_id: UUID,
        program_id: UUID,
        *,
        program_view: ProgramView,
    ) -> MatchWithRationale | None:
        """Return one match plus its rationale.

        - If a cached rationale exists for the current
          (student.profile_version, program.program_version) → return it.
        - Else: call A5 Rationale agent. If the result is grounded,
          persist it. Either way, return what we got.

        `program_view` is provided by the caller (ApiRouter typically
        joins Program + program_features into the view shape) so the
        match service stays DB-decoupled at this layer.
        """
        match_row = await self._read_match(student_id, program_id)
        if match_row is None:
            return None

        sfv = await self._student_feature_record(student_id)
        if sfv is None:
            # No feature vector → no rationale; return the raw match.
            return MatchWithRationale(match=match_row)

        # Cache lookup.
        cached = await self._cached_rationale(
            student_id=student_id,
            program_id=program_id,
            profile_version=sfv.profile_version,
            program_version=program_view.program_version,
        )
        if cached is not None:
            return MatchWithRationale(
                match=match_row,
                rationale_text=cached.rationale_text,
                cited_student_fields=list(cached.cited_student_fields or []),
                cited_program_fields=list(cached.cited_program_fields or []),
                cache_hit=True,
                grounded=True,
            )

        # Generate fresh.
        student_view = StudentView(
            applicant_summary=sfv.applicant_summary or "",
            sparse=dict(sfv.sparse_features or {}),
            student_id=student_id,
            profile_version=sfv.profile_version,
        )
        score_view = ScoreView(
            fitness=float(match_row.fitness),
            confidence=float(match_row.confidence),
            fitness_breakdown=match_row.fitness_breakdown,
            confidence_breakdown=match_row.confidence_breakdown,
        )
        result = await get_rationale_agent().generate(
            student=student_view,
            program=program_view,
            score=score_view,
            db=self.db,
        )

        if result.grounded and result.joined_text():
            await self._persist_rationale(
                student_id=student_id,
                program_id=program_id,
                profile_version=sfv.profile_version,
                program_version=program_view.program_version,
                result=result,
            )
            # Mirror onto match_results for backwards-compat reads that
            # don't yet hit match_rationales.
            await self._mirror_rationale_to_match_result(
                student_id=student_id,
                program_id=program_id,
                rationale_text=result.joined_text(),
            )

        return MatchWithRationale(
            match=match_row,
            rationale_text=result.joined_text(),
            cited_student_fields=result.cited_student_fields,
            cited_program_fields=result.cited_program_fields,
            cache_hit=False,
            grounded=result.grounded,
            cost_usd=result.cost_usd,
        )

    # ── Internals ─────────────────────────────────────────────────────

    async def _student_features(self, student_id: UUID) -> StudentFeatures | None:
        """Read student_feature_vectors and project into matcher shape."""
        sfv = await self._student_feature_record(student_id)
        if sfv is None:
            return None
        sparse = dict(sfv.sparse_features or {})
        completeness = float(sparse.get("feature_completeness", 0.0))
        # Embedding column is JSONB at the ORM layer; round-trip as list.
        emb = sfv.embedding
        if isinstance(emb, list):
            emb_list: list[float] | None = [float(x) for x in emb]
        else:
            emb_list = None
        return StudentFeatures(
            sparse=sparse,
            embedding=emb_list,
            profile_completeness=completeness,
            extractor_quality=0.85,  # cold-start placeholder
        )

    async def _student_feature_record(self, student_id: UUID) -> StudentFeatureVector | None:
        return await self.db.scalar(
            select(StudentFeatureVector).where(StudentFeatureVector.student_id == student_id)
        )

    async def _read_match(self, student_id: UUID, program_id: UUID) -> MatchRow | None:
        m = await self.db.scalar(
            select(MatchResult).where(
                MatchResult.student_id == student_id,
                MatchResult.program_id == program_id,
            )
        )
        if m is None:
            return None
        calibrator = await self._calibrator()
        return self._row_to_match(m, calibrator, rank=0)

    async def _cached_rationale(
        self,
        *,
        student_id: UUID,
        program_id: UUID,
        profile_version: int,
        program_version: int,
    ) -> MatchRationale | None:
        # Spec 03 §12 — prompt_version is part of the cache key so a
        # prompt iteration forces re-derivation. The constant lives in
        # `unipaith.ai.cache_invalidation`.
        from unipaith.ai.cache_invalidation import RATIONALE_PROMPT_VERSION

        return await self.db.scalar(
            select(MatchRationale).where(
                MatchRationale.student_id == student_id,
                MatchRationale.program_id == program_id,
                MatchRationale.profile_version == profile_version,
                MatchRationale.program_version == program_version,
                MatchRationale.prompt_version == RATIONALE_PROMPT_VERSION,
            )
        )

    async def _persist_rationale(
        self,
        *,
        student_id: UUID,
        program_id: UUID,
        profile_version: int,
        program_version: int,
        result: RationaleResult,
    ) -> None:
        from unipaith.ai.cache_invalidation import RATIONALE_PROMPT_VERSION

        row = MatchRationale(
            student_id=student_id,
            program_id=program_id,
            profile_version=profile_version,
            program_version=program_version,
            prompt_version=RATIONALE_PROMPT_VERSION,
            rationale_text=result.joined_text(),
            cited_student_fields=list(result.cited_student_fields),
            cited_program_fields=list(result.cited_program_fields),
        )
        self.db.add(row)
        await self.db.flush()

    async def _mirror_rationale_to_match_result(
        self, *, student_id: UUID, program_id: UUID, rationale_text: str
    ) -> None:
        """Copy the freshest rationale onto MatchResult.rationale_text so
        the simple list-view UI can render a preview without joining
        match_rationales. The cache table remains the source of truth for
        version-sensitive reads."""
        m = await self.db.scalar(
            select(MatchResult).where(
                MatchResult.student_id == student_id,
                MatchResult.program_id == program_id,
            )
        )
        if m is None:
            return
        m.rationale_text = rationale_text
        from sqlalchemy import func as sa_func

        m.rationale_generated_at = sa_func.now()  # type: ignore[assignment]
        await self.db.flush()


# ── Helper: bridge an EmittedFeatures into a StudentFeatures ──────────────
# Used by tests + the discovery-completion hook that wants to test the
# pipeline without a DB.


def features_from_emitted(emitted: EmittedFeatures) -> StudentFeatures:
    sparse = dict(emitted.sparse_features or {})
    completeness = float(sparse.get("feature_completeness", 0.0))
    return StudentFeatures(
        sparse=sparse,
        embedding=list(emitted.embedding) if emitted.embedding else None,
        profile_completeness=completeness,
        extractor_quality=0.85,
    )


# ── Re-export for the API layer ────────────────────────────────────────────

__all__ = [
    "MatchRow",
    "MatchWithRationale",
    "MatchService",
    "features_from_emitted",
    # Re-export the matcher score type so API schemas can reference it
    # without a deeper import.
    "Score",
    "score",
]

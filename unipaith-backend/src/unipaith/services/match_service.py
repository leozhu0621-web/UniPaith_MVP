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
from datetime import UTC
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
    decision_brief: dict[str, Any] | None = None
    cache_hit: bool = False
    grounded: bool = True
    cost_usd: float = 0.0


# ── Service ────────────────────────────────────────────────────────────────


# AI Structure (Spec 3, GAP 1) — c_student floor. A brand-new profile that
# emitted feature_completeness=0 should not zero out c_student (which would make
# rho≈0 and read every match as the bare prior). A modest floor keeps a thin
# profile's signals dented-but-alive while still letting a deeper profile climb
# toward 1.0 — the "deeper profile → sharper match" intent. 0.5 maps (with
# tau0==kappa) to rho≈0.5, i.e. observed fit and prior weighted equally.
_STUDENT_CONFIDENCE_FLOOR = 0.5


def _student_confidence(feature_completeness: float) -> float:
    """Map the emitter's per-profile `feature_completeness` [0,1] to the student-
    side confidence c_student, fail-soft and bounded. Deeper profile → higher
    confidence → sharper (less prior-shrunk) signals."""
    try:
        c = float(feature_completeness)
    except (TypeError, ValueError):
        return _STUDENT_CONFIDENCE_FLOOR
    if c != c:  # NaN guard
        return _STUDENT_CONFIDENCE_FLOOR
    # Linear lift from the floor to 1.0 across [0,1] completeness.
    c = max(0.0, min(1.0, c))
    return _STUDENT_CONFIDENCE_FLOOR + (1.0 - _STUDENT_CONFIDENCE_FLOOR) * c


# AI Structure (Spec 2 §authority-precedence / Spec 3 GAP) — claim → c_program.
# ProgramPreference.source records HOW the target-applicant preferences were
# obtained; that provenance IS the program-side authority (c_program). A claimed
# (first-party, verified) preference outweighs a derived (crawler-inferred) one,
# which outweighs a bare crawler row — the "claimed program outweighs derived"
# rule from Chart 2. An explicit per-program `confidence` (a school that dialed it
# in) takes precedence over the source default.
_PROGRAM_AUTHORITY_BY_SOURCE: dict[str, float] = {
    "claimed": 0.9,
    "manual": 0.9,  # set by a verified school user via the editor — first-party
    "verified": 0.9,
    "derived": 0.5,
    "inferred": 0.45,
    "crawler": 0.4,
}


def _program_authority(source: str | None, confidence: Any | None = None) -> float | None:
    """Map a ProgramPreference's provenance to c_program (data authority), or None
    when the source is unrecognized (leave the existing data_completeness). An
    explicit numeric `confidence` wins; else the per-source default."""
    if confidence is not None:
        try:
            c = float(confidence)
        except (TypeError, ValueError):
            c = None
        if c is not None and c == c:  # not NaN
            return max(0.0, min(1.0, c))
    if not source:
        return None
    return _PROGRAM_AUTHORITY_BY_SOURCE.get(str(source).strip().lower())


def _program_embedding_text(program: Any) -> str:
    """Semantic text for a program's dense embedding (Spec 65 §3) — its name,
    degree, and description, the same kind of free text the student applicant
    summary is embedded from so cosine compares like with like."""
    parts = [
        getattr(program, "program_name", "") or "",
        getattr(program, "degree_type", "") or "",
        getattr(program, "description_text", "") or "",
    ]
    return " — ".join(p for p in parts if p).strip()


def _fitness_band(fitness: float) -> str:
    """One-word descriptor for a fitness score, for conversational surfaces."""
    if fitness >= 0.75:
        return "strong"
    if fitness >= 0.55:
        return "solid"
    if fitness >= 0.40:
        return "possible"
    return "reach"


class MatchService:
    """Stateless service — instantiate per-request with the AsyncSession.

    The service caches the loaded calibrator + reranker state on `self`
    across calls within the same request lifecycle so the model_registry
    table is hit at most once per request even when the same service is
    used to read multiple matches.
    """

    # Spec 06 §5.3 — the L3 ML scorer's audit label + the model id recorded
    # on its ledger rows. The matcher is rule-based/calibrated today (no LLM),
    # so provider='rule_based'.
    _ML_AGENT = "matcher"
    _ML_MODEL_ID = "heuristic-matcher-v1"

    def __init__(self, db: AsyncSession):
        self.db = db
        # Lazy-loaded once per service instance.
        self._calibrator_state: CalibratorState | None = None
        self._reranker_state: RerankerState | None = None

    async def invalidate_for_profile_change(self, student_id: UUID) -> None:
        """Spec 06 §5.1 / §5.4 — keep derived artifacts honest after a direct
        profile edit (PUT /me/profile, goals/needs/identity CRUD), not just at
        Discovery completion.

        Bumps the feature vector's `profile_version` (so the rationale cache,
        keyed by profile_version, misses and regenerates on next read) and
        flags existing matches stale so the next refresh recomputes them.
        Cheap + idempotent; the expensive re-embed happens lazily on the next
        match refresh.
        """
        from sqlalchemy import update as _update

        sfv = await self._student_feature_record(student_id)
        if sfv is not None:
            sfv.profile_version = int(sfv.profile_version or 1) + 1
        await self.db.execute(
            _update(MatchResult).where(MatchResult.student_id == student_id).values(is_stale=True)
        )
        await self.db.flush()

    async def _matching_consent(self, student_id: UUID) -> tuple[bool, dict[str, bool]]:
        """Spec 06 §5.2 — resolve whether L3 (ML) processing is permitted.

        Returns (allowed, mask). `consent.matching=false` blocks all L3
        scoring + reads, mirroring the L2 guard in `AIClient`.
        """
        from unipaith.ai.consent import get_consent_mask

        mask = await get_consent_mask(self.db, student_id)
        return bool(mask.get("matching", True)), mask

    async def _halted_program_ids(self, program_ids: list[UUID]) -> set[UUID]:
        """Spec 46 §6.2 — program ids whose cohort is fairness-halted and not
        under an active, unexpired override. Used to skip scoring new applicants
        for a halted cohort (existing scores are left untouched)."""
        if not program_ids:
            return set()
        from datetime import datetime

        from unipaith.models.institution import Program

        now = datetime.now(UTC)
        rows = (
            await self.db.execute(
                select(
                    Program.id,
                    Program.matching_halted,
                    Program.fairness_override_active,
                    Program.fairness_override_expires_at,
                ).where(Program.id.in_(program_ids))
            )
        ).all()
        halted: set[UUID] = set()
        for pid, matching_halted, override_active, override_expires_at in rows:
            override_ok = bool(
                override_active and override_expires_at is not None and override_expires_at > now
            )
            if matching_halted and not override_ok:
                halted.add(pid)
        return halted

    async def _log_ml_turn(
        self,
        *,
        student_id: UUID,
        mask: dict[str, bool],
        n_programs: int,
        latency_ms: int,
        success: bool = True,
        failure_reason: str | None = None,
    ) -> None:
        """Spec 06 §5.3 — write one `ai_turns` row per L3 scoring event with
        provider/model/consent_mask, so the audit ledger covers L3 (not just
        the L2 LLM calls). Best-effort: a ledger write must never break
        matching."""
        from unipaith.models.ai_artifacts import AiTurn

        try:
            self.db.add(
                AiTurn(
                    student_id=student_id,
                    agent=self._ML_AGENT,
                    surface="matching",
                    role="assistant",
                    model=self._ML_MODEL_ID,
                    provider="rule_based",
                    input_tokens=n_programs,  # programs scored — the L3 "input"
                    output_tokens=0,
                    cost_usd=Decimal("0"),
                    latency_ms=latency_ms,
                    success=success,
                    failure_reason=failure_reason,
                    consent_mask=mask,
                )
            )
            await self.db.flush()
        except Exception as exc:  # noqa: BLE001 — audit must not break scoring
            logger.warning("failed to write L3 audit turn for student=%s: %s", student_id, exc)

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
        params: dict[str, float] | None = None,
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
        # Spec 06 §5.2 — consent gate on L3 (ML) processing.
        allowed, mask = await self._matching_consent(student_id)
        if not allowed:
            logger.info(
                "MatchService: matching consent denied for student=%s; skipping L3 scoring.",
                student_id,
            )
            await self._log_ml_turn(
                student_id=student_id,
                mask=mask,
                n_programs=0,
                latency_ms=0,
                success=False,
                failure_reason="consent_denied",
            )
            return []

        import time as _time

        _t0 = _time.perf_counter()

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
        # AI Structure (Spec 3, D.2): overlay each program's target-applicant
        # preferences so the CPEF program→student direction fires (batched).
        await self._overlay_program_prefs(program_features)

        ranked: list[tuple[ProgramFeatures, Score]] = rank_programs(
            sfv, program_features, weights=weights, params=params, include_eliminated=False
        )

        # D3: rerank top-K. Cold start = identity, but the breakdowns
        # are annotated so the rationale agent + admin dashboard can see
        # the rerank stage ran. When a fitted model is loaded, this
        # actually reorders.
        reranker_state = await self._reranker_state_cached()
        ranked = get_reranker(state=reranker_state).rerank(sfv, ranked)

        # Spec 46 §6.2 — fairness auto-halt. A halted cohort stops scoring new
        # applicants (existing scores remain). Drop halted programs before the
        # top-N slice so the student still receives a full set of eligible
        # matches.
        halted = await self._halted_program_ids([p.program_id for p, _ in ranked])
        if halted:
            ranked = [(p, s) for (p, s) in ranked if p.program_id not in halted]

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
        # Spec 06 §5.3 — audit the L3 scoring event.
        await self._log_ml_turn(
            student_id=student_id,
            mask=mask,
            n_programs=len(program_features),
            latency_ms=int((_time.perf_counter() - _t0) * 1000),
        )
        return out

    # ── Read paths ────────────────────────────────────────────────────

    async def list_matches(self, student_id: UUID, *, limit: int = 20) -> list[MatchRow]:
        """Read previously-computed matches for the student, ordered by
        fitness desc. No LLM, no scoring — a pure DB read.

        Confidence is calibrated at read time using the active
        CalibratorState. Cold start (unfitted) → raw confidence flows
        through unchanged.         The breakdown carries `{raw, calibrated,
        calibrator_fitted}` so admin/rationale tooling can tell the two
        apart.

        Spec 06 §5.2 — a student who has revoked matching consent gets no L3
        read (returns []), consistent with "consent.matching=false → no AI
        processing".
        """
        allowed, _ = await self._matching_consent(student_id)
        if not allowed:
            return []
        result = await self.db.execute(
            select(MatchResult)
            .where(MatchResult.student_id == student_id)
            .order_by(MatchResult.fitness_score.desc(), MatchResult.confidence_score.desc())
            .limit(limit)
        )
        rows = list(result.scalars().all())
        calibrator = await self._calibrator()
        return [self._row_to_match(r, calibrator, rank=i + 1) for i, r in enumerate(rows)]

    async def list_matches_for_display(
        self, student_id: UUID, *, limit: int = 8
    ) -> list[dict[str, Any]]:
        """Compact, JSON-serializable matches for conversational surfaces (the
        Uni ``get_matches`` tool). Joins program + institution names onto the
        scored rows and bands fitness for a one-word descriptor. Self-contained
        so it doesn't pull in the probability-band machinery the full
        ``/me/matches`` endpoint composes."""
        from unipaith.models.institution import Institution, Program

        matches = await self.list_matches(student_id, limit=limit)
        if not matches:
            return []
        program_ids = [m.program_id for m in matches]
        programs = (
            (await self.db.execute(select(Program).where(Program.id.in_(program_ids))))
            .scalars()
            .all()
        )
        prog_by_id = {p.id: p for p in programs}
        inst_ids = {p.institution_id for p in programs}
        inst_name_by_id: dict[UUID, str] = {}
        if inst_ids:
            inst_rows = (
                await self.db.execute(
                    select(Institution.id, Institution.name).where(Institution.id.in_(inst_ids))
                )
            ).all()
            inst_name_by_id = {iid: name for iid, name in inst_rows}
        out: list[dict[str, Any]] = []
        for m in matches:  # preserves fitness-desc order
            program = prog_by_id.get(m.program_id)
            fitness = float(m.fitness)
            out.append(
                {
                    "program_id": str(m.program_id),
                    "program_name": getattr(program, "program_name", None),
                    "institution_name": (
                        inst_name_by_id.get(program.institution_id) if program else None
                    ),
                    "fitness": round(fitness, 3),
                    "confidence": round(float(m.confidence), 3),
                    "band": _fitness_band(fitness),
                }
            )
        return out

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

        Spec 06 §5.2 — gated on matching consent (L3 read).
        """
        allowed, _ = await self._matching_consent(student_id)
        if not allowed:
            return None
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
                decision_brief=cached.decision_brief,
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
        from unipaith.services.decision_brief import build_decision_brief

        decision_brief = result.decision_brief or build_decision_brief(
            student_sparse=dict(sfv.sparse_features or {}),
            program=program_view,
            fitness_breakdown=match_row.fitness_breakdown,
            confidence_breakdown=match_row.confidence_breakdown,
            student_profile_version=sfv.profile_version,
        )

        if result.grounded and result.joined_text():
            await self._persist_rationale(
                student_id=student_id,
                program_id=program_id,
                profile_version=sfv.profile_version,
                program_version=program_view.program_version,
                result=result,
                decision_brief=decision_brief,
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
            decision_brief=decision_brief,
            cache_hit=False,
            grounded=result.grounded,
            cost_usd=result.cost_usd,
        )

    async def can_match(self, student_id: UUID) -> bool:
        """True only when matching can actually produce results: matching consent
        is granted AND the student has a feature vector (Discovery complete).

        Callers gate the catalog-embedding step on this so the documented
        empty-state refresh path (no Discovery yet / consent denied) doesn't burn
        embedding calls + catalog-sized latency for matches that won't be made;
        ``compute_matches_for_student`` re-checks the same guards and returns []."""
        allowed, _ = await self._matching_consent(student_id)
        if not allowed:
            return False
        return await self._student_feature_record(student_id) is not None

    async def ensure_program_embeddings(self, programs: list[Any]) -> dict[Any, list[float]]:
        """Spec 65 §3 — compute + cache a dense embedding for each program so the
        matcher's cosine term can fire (it is 0 until BOTH the student and the
        program carry an embedding; no program ever did before this).

        Lazy + cached: a program is (re)embedded only when its stored embedding is
        missing or was built from an older ``feature_version``; the vector is
        persisted on ``Program.embedding`` so it is a one-time cost per program
        edit. Best-effort — an embed failure (consent/cost/provider) skips that
        program and the matcher just drops cosine + reweights for it.

        Returns ``{program.id: embedding}`` to hand straight to
        ``compute_matches_for_student(program_embeddings=...)``.
        """
        from unipaith.ai.client import get_client

        out: dict[Any, list[float]] = {}
        client = get_client()
        dirty = False
        for p in programs:
            stored = p.embedding
            if (
                isinstance(stored, list)
                and stored
                and getattr(p, "embedding_version", None) == getattr(p, "feature_version", None)
            ):
                out[p.id] = [float(x) for x in stored]
                continue
            text = _program_embedding_text(p)
            if not text:
                continue
            try:
                resp = await client.embed(text, db=self.db)
            except Exception as exc:  # noqa: BLE001 — degrade: skip cosine for this program
                logger.info("MatchService: program embed failed for %s: %s", p.id, exc)
                continue
            vec = [float(x) for x in resp.embedding]
            p.embedding = vec
            p.embedding_version = getattr(p, "feature_version", None)
            out[p.id] = vec
            dirty = True
        if dirty:
            await self.db.flush()
        return out

    # ── Internals ─────────────────────────────────────────────────────

    async def _student_features(self, student_id: UUID) -> StudentFeatures | None:
        """Read student_feature_vectors and project into matcher shape."""
        sfv = await self._student_feature_record(student_id)
        if sfv is None:
            return None
        sparse = dict(sfv.sparse_features or {})
        # AI Structure (Spec 3, D.2): overlay GPA + field-of-study so the
        # program→student direction (CPEF p2s) can score the student against a
        # program's preferences. Deterministic, no LLM; fail-soft.
        await self._overlay_student_attrs(student_id, sparse)
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
            # AI Structure (Spec 3, GAP 1) — c_student is now DERIVED from the
            # real profile, not a constant. The feature emitter writes a per-
            # profile `feature_completeness` in [0,1] reflecting how much source
            # data backed this emission; that IS the student-side confidence
            # (a thin profile → low c_student → its signals shrink toward the
            # prior; a deep profile → high c_student → sharper match). Falls back
            # to the cold-start proxy only when the emitter wrote no completeness.
            extractor_quality=_student_confidence(completeness),
        )

    async def _overlay_student_attrs(self, student_id: UUID, sparse: dict) -> None:
        """Add the student's GPA + field-of-study + typed-fit preferences +
        (when the student needs a study visa) the visa-feasibility flag to the
        matcher sparse vector (AI Structure D.2 / Spec 3 §3; visa = founder
        governance 2026-06-18). Reads the current AcademicRecord, the
        StudentPreference row, and the StudentVisaInfo row; missing → skip. Each
        key is GATED on a non-null source value, so an absent attribute injects
        no phantom signal. The visa key (`needs_visa_sponsorship`) feeds ONLY the
        student→program feasibility veto — never program→student selection.
        Fail-soft: any read error leaves the sparse vector as-is."""
        from unipaith.models.student import (
            AcademicRecord,
            StudentPreference,
            StudentProfile,
            StudentVisaInfo,
        )

        try:
            academic = await self.db.scalar(
                select(AcademicRecord)
                .where(
                    AcademicRecord.student_id == student_id,
                    AcademicRecord.is_current.is_(True),
                )
                .limit(1)
            )
        except Exception:
            academic = None
        if academic is not None:
            if academic.normalized_gpa is not None and "gpa" not in sparse:
                sparse["gpa"] = float(academic.normalized_gpa)
            if academic.field_of_study and "field_of_study" not in sparse:
                # Canonicalize to the FIELD_SIM_TABLE vocab so the s→p field signal
                # matches the (canonicalized) program-side fields_offered on live
                # free-text data ("Computer Science" → "computer_science"). Gated:
                # an unrecognizable field yields no field signal (no phantom 0.0).
                from unipaith.services.match.field_canon import canonical_field

                canon = canonical_field(academic.field_of_study)
                if canon:
                    sparse["field_of_study"] = canon

        # todo 1.1 / 3.2 — a student onboarded through the signup wizard (never
        # Discovery) has no AcademicRecord, so the s→p field signal AND the
        # wrong-discipline veto would never fire. Fall back to the intended field
        # she picked in onboarding (stored on StudentProfile.onboarding_state),
        # mapped through the SAME canonical vocab as everything else. Gated +
        # set-only-if-absent + fail-soft: an absent/ambiguous interest injects no
        # field token (no phantom signal).
        if "field_of_study" not in sparse:
            try:
                from unipaith.services.match.field_canon import interest_track_to_field

                profile = await self.db.scalar(
                    select(StudentProfile).where(StudentProfile.id == student_id)
                )
                answers = ((profile.onboarding_state or {}).get("answers") or {}) if profile else {}
                for interest in answers.get("interests") or []:
                    token = interest_track_to_field(interest)
                    if token:
                        sparse["field_of_study"] = token
                        break
            except Exception:
                pass

        # AI Structure (Spec 3 §3) — typed-fit student constraints from the
        # StudentPreference row. Each fuels a dormant matcher signal:
        #   desired_time_to_degree_months → "time" fit (vs program duration_months)
        #   wants_part_time / wants_online → "flexibility" fit (hard want floor)
        #   wants_career_support           → "support" fit (soft want floor)
        # GATED on non-null so a student who never stated a preference gets no
        # phantom dimension. Each key is set only when not already present (the
        # emitted feature vector wins if it ever carried one).
        try:
            pref = await self.db.scalar(
                select(StudentPreference).where(StudentPreference.student_id == student_id).limit(1)
            )
        except Exception:
            pref = None
        if pref is not None:
            if pref.desired_time_to_degree_months is not None and (
                "desired_time_to_degree_months" not in sparse
            ):
                sparse["desired_time_to_degree_months"] = int(pref.desired_time_to_degree_months)
            if pref.wants_part_time is not None and "wants_part_time" not in sparse:
                sparse["wants_part_time"] = bool(pref.wants_part_time)
            if pref.wants_online is not None and "wants_online" not in sparse:
                sparse["wants_online"] = bool(pref.wants_online)
            if pref.wants_career_support is not None and "wants_career_support" not in sparse:
                sparse["wants_career_support"] = bool(pref.wants_career_support)
            # degree-level TARGET → the s→p "degree_level" graded fit. Previously a
            # dead signal: matching.py reads `degree_level_target` but no code path
            # wrote it. Canonicalize via the SAME degree→{bachelors/masters/doctoral/
            # professional} map the program side uses (target_education_level), so
            # s→p and p→s agree. Gated + set-only-if-absent (no phantom dimension).
            if pref.target_degree_level and "degree_level_target" not in sparse:
                from unipaith.services.program_features import target_education_level

                canon = target_education_level(pref.target_degree_level)
                if canon:
                    sparse["degree_level_target"] = canon

        # The student's ACTIVE broad strategy steers matching too (white-paper
        # Stage-2): when no preference set the degree target, derive it from the
        # strategy's target_degree, canonicalized via the SAME map. Gated +
        # set-only-if-absent (a preference still wins), fail-soft like the rest of the
        # overlay. This is the immediately-wireable strategy→match link — geographic/
        # financial steering awaits the corresponding program-side signals — and
        # turns the strategy from display-only into an actual ranking influence.
        if "degree_level_target" not in sparse:
            from unipaith.models.strategy import StudentStrategy

            strat = await self.db.scalar(
                select(StudentStrategy).where(
                    StudentStrategy.student_id == student_id,
                    StudentStrategy.status == "active",
                )
            )
            if strat is not None and strat.target_degree:
                from unipaith.services.program_features import target_education_level

                canon = target_education_level(strat.target_degree)
                if canon:
                    sparse["degree_level_target"] = canon

        # Founder governance (2026-06-18) — the visa FEASIBILITY signal, in the
        # STUDENT's direction ONLY. A study-visa-needing student cannot attend a
        # program that cannot sponsor an international applicant; surfacing that
        # in HER own ranking (s→p) helps her avoid a dead end. We project a SINGLE
        # derived boolean `needs_visa_sponsorship` — never nationality, country,
        # refusals, or any other immigration field — because the feasibility veto
        # needs nothing more, and projecting less keeps the surface area minimal.
        #
        # Direction asymmetry (the only defensible framing): this key feeds the
        # student→program feasibility veto in matching.py. The program→student
        # SELECTION direction (cpef_program_to_student) MUST NEVER read it — a
        # program ranking APPLICANTS may not use immigration status (Spec 38
        # §3/§9, Spec 46 §6). cpef_program_to_student reads only pref_min_gpa /
        # pref_fields / pref_levels vs the student's gpa / field / level — never
        # this key — and the fairness contract pins that.
        #
        # GATED: emitted only when a visa_info row exists AND visa_required is
        # True. No visa row, or visa_required False → no key (a domestic student
        # never gets the feasibility dimension). Fail-soft on any read error.
        try:
            visa = await self.db.scalar(
                select(StudentVisaInfo).where(StudentVisaInfo.student_id == student_id).limit(1)
            )
        except Exception:
            visa = None
        if (
            visa is not None
            and bool(getattr(visa, "visa_required", False))
            and "needs_visa_sponsorship" not in sparse
        ):
            sparse["needs_visa_sponsorship"] = True

    async def _overlay_program_prefs(self, program_features: list[ProgramFeatures]) -> None:
        """Overlay each program's ProgramPreference (target applicant) onto its
        matcher sparse vector so the CPEF program→student direction can fire
        (AI Structure D.2). One batched query; fail-soft."""
        from unipaith.models.institution import ProgramPreference

        ids = [pf.program_id for pf in program_features]
        if not ids:
            return
        try:
            rows = (
                (
                    await self.db.execute(
                        select(ProgramPreference).where(ProgramPreference.program_id.in_(ids))
                    )
                )
                .scalars()
                .all()
            )
        except Exception:
            return
        by_program = {r.program_id: r for r in rows}
        for pf in program_features:
            pref = by_program.get(pf.program_id)
            if pref is None:
                continue
            if pref.pref_min_gpa is not None:
                pf.sparse["pref_min_gpa"] = float(pref.pref_min_gpa)
            if pref.pref_fields:
                # Canonicalize the program's target-applicant fields to the same
                # vocab as the (canonicalized) student field_of_study, so the p→s
                # field comparison matches on live free-text. Gated: unrecognizable
                # entries drop; if none survive, no pref_fields signal.
                from unipaith.services.match.field_canon import canonical_field

                canon_fields = [c for c in (canonical_field(f) for f in pref.pref_fields) if c]
                if canon_fields:
                    pf.sparse["pref_fields"] = canon_fields
            if pref.pref_levels:
                pf.sparse["pref_levels"] = list(pref.pref_levels)
            if pref.target_profile:
                pf.sparse["target_profile"] = pref.target_profile
                layers = (pref.target_profile or {}).get("layers") or {}
                for signal in layers.get("goals_behaviors_learning_working_style", []):
                    attr = signal.get("attribute")
                    vals = list(signal.get("preferred_values") or [])
                    if attr == "career_direction" and vals:
                        pf.sparse["pref_career_arcs"] = vals
                    elif (
                        attr in {"interest_themes", "learning_preference", "working_style"} and vals
                    ):
                        pf.sparse.setdefault("pref_learning_working_style", []).extend(vals)
                for signal in layers.get("values_motivations_community", []):
                    vals = list(signal.get("preferred_values") or [])
                    if vals:
                        pf.sparse.setdefault("pref_values", []).extend(vals)
            # AI Structure (Spec 2/3, GAP — claim → c_program): the program-side
            # confidence is its DATA AUTHORITY. A claimed preference (first-party,
            # verified school user) is high-authority; a derived one (crawler-
            # inferred for an unclaimed program) is lower. This is what makes a
            # claimed program outscore an identical-fit derived one. We read the
            # real `ProgramPreference.source` (+ an explicit `confidence` when the
            # school set one) and lift `data_completeness` (= c_program) to match.
            authority = _program_authority(pref.source, pref.confidence)
            if authority is not None:
                # Authority can only RAISE c_program — never knock a claimed
                # program (record floor 0.9 from is_claimed) down because it
                # carries a lower-source preference row. A claimed-source pref
                # still outscores a derived-source one on otherwise-equal records.
                pf.data_completeness = max(pf.data_completeness, authority)

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
        decision_brief: dict[str, Any] | None = None,
    ) -> None:
        from unipaith.ai.cache_invalidation import RATIONALE_PROMPT_VERSION

        row = MatchRationale(
            student_id=student_id,
            program_id=program_id,
            profile_version=profile_version,
            program_version=program_version,
            prompt_version=RATIONALE_PROMPT_VERSION,
            rationale_text=result.joined_text(),
            decision_brief=decision_brief,
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


async def invalidate_matches_for_user(db: AsyncSession, user_id: UUID) -> None:
    """Spec 06 §5.1 — invalidate derived matching artifacts after a direct
    profile-data edit, resolving the student profile from the user id.

    Best-effort and side-effect-only: callers fire it after a successful
    profile/goals/needs/identity write so the rationale cache and match
    staleness reflect the change. Never raises into the request path.
    """
    from unipaith.models.student import StudentProfile

    try:
        profile = await db.scalar(select(StudentProfile).where(StudentProfile.user_id == user_id))
        if profile is not None:
            await MatchService(db).invalidate_for_profile_change(profile.id)
    except Exception as exc:  # noqa: BLE001
        logger.warning("invalidate_matches_for_user failed for user=%s: %s", user_id, exc)


def build_program_view(program: Any) -> ProgramView:
    """Build the rationale agent's ProgramView from a `Program` ORM row.

    Centralized so the student rationale endpoints and the institution
    review endpoint construct identical inputs (the asymmetric projection
    must run on the SAME artifact). Derives a sparse citation dict from the
    program's structured columns so the rationale agent can ground program
    citations against real fields — without a separate stored vector.

    NOTE: the column is `program_name`/`description_text` (not `name`/
    `description`); earlier call sites referenced the wrong attribute and
    silently fell through to the stub. This helper is the single correct
    construction.
    """
    raw_sparse = {
        "degree_type": getattr(program, "degree_type", None),
        "department": getattr(program, "department", None),
        "delivery_format": getattr(program, "delivery_format", None),
        "campus_setting": getattr(program, "campus_setting", None),
        "duration_months": getattr(program, "duration_months", None),
        "tuition": getattr(program, "tuition", None),
        "tracks": getattr(program, "tracks", None),
        "outcomes": getattr(program, "outcomes_data", None),
        "who_its_for": getattr(program, "who_its_for", None),
        "requirements": (
            getattr(program, "application_requirements", None)
            or getattr(program, "requirements", None)
        ),
        "cost_data": getattr(program, "cost_data", None),
        "profile_intelligence": getattr(program, "profile_intelligence", None),
        "profile_intelligence_version": getattr(program, "profile_intelligence_version", None),
    }
    sparse = {k: v for k, v in raw_sparse.items() if v not in (None, "", {}, [])}
    return ProgramView(
        name=getattr(program, "program_name", None) or getattr(program, "name", "") or "",
        description=getattr(program, "description_text", None)
        or getattr(program, "description", "")
        or "",
        sparse=sparse,
        program_id=getattr(program, "id", None),
        program_version=int(getattr(program, "feature_version", 1) or 1),
    )


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
        # AI Structure (Spec 3, GAP 1) — c_student derived from real completeness.
        extractor_quality=_student_confidence(completeness),
    )


# ── Re-export for the API layer ────────────────────────────────────────────

__all__ = [
    "MatchRow",
    "MatchWithRationale",
    "MatchService",
    "build_program_view",
    "invalidate_matches_for_user",
    "features_from_emitted",
    # Re-export the matcher score type so API schemas can reference it
    # without a deeper import.
    "Score",
    "score",
]

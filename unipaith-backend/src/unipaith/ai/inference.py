"""
Inference Pipeline (Person A).
Given a student, produces ranked program matches with scores and tiers.

Steps:
1. Ensure student features + embedding are fresh
2. pgvector similarity search -> top N candidates
3. Apply dealbreaker filters
4. Enrich with 3 influential factors (historical, institution prefs, student prefs)
5. Compute final weighted score
6. Rank, tier, keep top 30
7. Generate NL reasoning for each match
8. Cache results in match_results table
9. Log to prediction_logs
"""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from unipaith.ai.embedding_pipeline import EmbeddingPipeline
from unipaith.ai.feature_extraction import FeatureExtractor
from unipaith.ai.reasoning import ReasoningGenerator
from unipaith.config import settings
from unipaith.models.application import HistoricalOutcome
from unipaith.models.institution import Program, TargetSegment
from unipaith.models.matching import (
    Embedding,
    InstitutionFeature,
    MatchResult,
    PredictionLog,
)
from unipaith.models.student import StudentPreference


class InferencePipeline:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.feature_extractor = FeatureExtractor(db)
        self.embedding_pipeline = EmbeddingPipeline(db)
        self.reasoning_generator = ReasoningGenerator(db)

    async def compute_matches(
        self,
        student_id: UUID,
        force_refresh: bool = False,
    ) -> list[MatchResult]:
        """Full inference pipeline for a student."""
        if not force_refresh:
            cached = await self._get_cached_matches(student_id)
            if cached:
                return cached

        student_features = await self.feature_extractor.extract_student_features(student_id)
        await self.embedding_pipeline.generate_student_embedding(student_id)

        candidates = await self._similarity_search(student_id, settings.matching_candidate_count)
        if not candidates:
            return []

        student_prefs = await self._load_student_preferences(student_id)

        # Apply dealbreaker filters before scoring
        candidates = await self._apply_dealbreaker_filters(candidates, student_prefs)

        scored_candidates = []
        for program_id, cosine_sim in candidates:
            final_score, score_breakdown = await self._compute_final_score(
                student_id=student_id,
                program_id=program_id,
                cosine_similarity=cosine_sim,
                student_features=student_features,
                student_prefs=student_prefs,
            )
            scored_candidates.append((program_id, final_score, score_breakdown, cosine_sim))

        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        top_matches = scored_candidates[: settings.matching_final_count]

        tiered = []
        for program_id, score, breakdown, cosine_sim in top_matches:
            if score >= settings.matching_tier1_threshold:
                tier = 1
            elif score >= settings.matching_tier2_threshold:
                tier = 2
            else:
                tier = 3
            tiered.append((program_id, score, tier, breakdown))

        match_results = []
        for program_id, score, tier, breakdown in tiered:
            reasoning = await self.reasoning_generator.generate_match_reasoning(
                student_id=student_id,
                program_id=program_id,
                score=score,
                tier=tier,
                breakdown=breakdown,
            )
            match_result = await self._save_match_result(
                student_id=student_id,
                program_id=program_id,
                score=score,
                tier=tier,
                breakdown=breakdown,
                reasoning=reasoning,
            )
            match_results.append(match_result)
            await self._log_prediction(
                student_id=student_id,
                program_id=program_id,
                score=score,
                tier=tier,
                features_used=breakdown,
            )

        await self._mark_old_matches_stale(student_id, [m.id for m in match_results])
        return match_results

    # ========================================================================
    # SIMILARITY SEARCH
    # ========================================================================

    async def _similarity_search(
        self, student_id: UUID, limit: int
    ) -> list[tuple[UUID, float]]:
        """Use pgvector to find the most similar program embeddings."""
        result = await self.db.execute(
            select(Embedding).where(
                Embedding.entity_type == "student",
                Embedding.entity_id == student_id,
            )
        )
        student_emb = result.scalar_one_or_none()
        if not student_emb:
            return []

        query = text("""
            SELECT e.entity_id, 1 - (e.embedding <=> :student_vec) as similarity
            FROM embeddings e
            JOIN programs p ON e.entity_id = p.id
            WHERE e.entity_type = 'program'
              AND p.is_published = true
            ORDER BY e.embedding <=> :student_vec
            LIMIT :limit
        """)

        result = await self.db.execute(
            query,
            {"student_vec": str(student_emb.embedding), "limit": limit},
        )
        rows = result.fetchall()
        return [(row[0], float(row[1])) for row in rows]

    # ========================================================================
    # INFLUENTIAL FACTORS & SCORING
    # ========================================================================

    async def _compute_final_score(
        self,
        student_id: UUID,
        program_id: UUID,
        cosine_similarity: float,
        student_features: dict,
        student_prefs: StudentPreference | None,
    ) -> tuple[float, dict]:
        """Compute the final match score using 4 weighted components."""
        similarity_score = max(0.0, min(1.0, cosine_similarity))
        historical_score = await self._compute_historical_fit(student_features, program_id)
        institution_pref_score = await self._compute_institution_pref_fit(
            student_features, program_id
        )
        student_pref_score = self._compute_student_pref_fit(
            student_prefs, program_id, student_features
        )

        final_score = (
            settings.matching_weight_similarity * similarity_score
            + settings.matching_weight_historical * historical_score
            + settings.matching_weight_institution_pref * institution_pref_score
            + settings.matching_weight_student_pref * student_pref_score
        )

        breakdown = {
            "embedding_similarity": round(similarity_score, 4),
            "historical_fit": round(historical_score, 4),
            "institution_pref_fit": round(institution_pref_score, 4),
            "student_pref_fit": round(student_pref_score, 4),
            "final_score": round(final_score, 4),
            "weights": {
                "similarity": settings.matching_weight_similarity,
                "historical": settings.matching_weight_historical,
                "institution_pref": settings.matching_weight_institution_pref,
                "student_pref": settings.matching_weight_student_pref,
            },
        }
        return final_score, breakdown

    async def _compute_historical_fit(self, student_features: dict, program_id: UUID) -> float:
        """How well does this student match historically admitted students?"""
        result = await self.db.execute(
            select(HistoricalOutcome).where(
                HistoricalOutcome.program_id == program_id,
                HistoricalOutcome.outcome == "admitted",
            )
        )
        admitted = result.scalars().all()
        if not admitted:
            return 0.5

        structured = student_features.get("structured", {})
        student_gpa = structured.get("normalized_gpa", 0)

        scores = []
        for outcome in admitted:
            profile = outcome.applicant_profile_summary or {}
            admitted_gpa = profile.get("gpa_normalized", 0)
            gpa_diff = (
                1.0 - abs(student_gpa - admitted_gpa)
                if student_gpa and admitted_gpa
                else 0.5
            )
            scores.append(gpa_diff)

        return sum(scores) / len(scores) if scores else 0.5

    async def _compute_institution_pref_fit(
        self, student_features: dict, program_id: UUID
    ) -> float:
        """How well does this student match what the institution currently wants?"""
        result = await self.db.execute(
            select(TargetSegment).where(
                TargetSegment.program_id == program_id,
                TargetSegment.is_active.is_(True),
            )
        )
        segments = result.scalars().all()
        if not segments:
            return 0.5

        structured = student_features.get("structured", {})
        best_segment_score = 0.0
        for segment in segments:
            criteria = segment.criteria or {}
            score = self._score_against_segment(structured, criteria)
            best_segment_score = max(best_segment_score, score)
        return best_segment_score

    def _score_against_segment(self, student_structured: dict, criteria: dict) -> float:
        if not criteria:
            return 0.5

        checks = []
        if "gpa_min" in criteria:
            gpa = student_structured.get("normalized_gpa", 0)
            criteria_gpa = criteria["gpa_min"] / 4.0 if criteria["gpa_min"] > 1 else criteria["gpa_min"]
            checks.append(1.0 if gpa and gpa >= criteria_gpa else (gpa / criteria_gpa if gpa and criteria_gpa else 0.3))

        if "region" in criteria:
            nationality = (student_structured.get("nationality") or "").lower()
            target_regions = (
                [r.lower() for r in criteria["region"]]
                if isinstance(criteria["region"], list)
                else [criteria["region"].lower()]
            )
            checks.append(0.8 if any(r in nationality for r in target_regions) else 0.3)

        if "field" in criteria:
            checks.append(0.6)  # Simplified for MVP

        if "work_experience_years" in criteria:
            work_years = student_structured.get("work_experience_years", 0)
            required = criteria["work_experience_years"]
            checks.append(1.0 if work_years >= required else work_years / max(required, 1))

        return sum(checks) / len(checks) if checks else 0.5

    def _compute_student_pref_fit(
        self,
        prefs: StudentPreference | None,
        program_id: UUID,
        student_features: dict,
    ) -> float:
        """How well does this program match what the student wants?"""
        if not prefs:
            return 0.5

        structured = student_features.get("structured", {})
        scores = []

        funding = structured.get("funding_requirement")
        if funding == "full_scholarship":
            scores.append(0.6)
        elif funding == "self_funded":
            scores.append(0.9)
        else:
            scores.append(0.7)

        return sum(scores) / len(scores) if scores else 0.5

    # ========================================================================
    # DEALBREAKER FILTERS
    # ========================================================================

    async def _apply_dealbreaker_filters(
        self,
        candidates: list[tuple[UUID, float]],
        student_prefs: StudentPreference | None,
    ) -> list[tuple[UUID, float]]:
        """Apply hard dealbreaker filters from student preferences."""
        if not student_prefs:
            return candidates

        program_ids = [pid for pid, _ in candidates]
        if not program_ids:
            return candidates

        result = await self.db.execute(
            select(Program)
            .where(Program.id.in_(program_ids))
            .options(selectinload(Program.institution))
        )
        programs = {p.id: p for p in result.scalars().all()}

        filtered = []
        dealbreakers = student_prefs.dealbreakers or []

        for program_id, sim_score in candidates:
            program = programs.get(program_id)
            if not program:
                continue

            if student_prefs.preferred_countries:
                if program.institution and program.institution.country not in student_prefs.preferred_countries:
                    continue

            if student_prefs.budget_max and program.tuition:
                if program.tuition > student_prefs.budget_max * 1.2:
                    continue

            reqs = program.requirements or {}
            skip = False
            for db_item in dealbreakers:
                if db_item == "no_gre_required" and reqs.get("gre_required", False):
                    skip = True
                    break
            if skip:
                continue

            filtered.append((program_id, sim_score))

        return filtered

    # ========================================================================
    # CACHING & PERSISTENCE
    # ========================================================================

    async def _get_cached_matches(self, student_id: UUID) -> list[MatchResult] | None:
        result = await self.db.execute(
            select(MatchResult)
            .where(
                MatchResult.student_id == student_id,
                MatchResult.is_stale.is_(False),
            )
            .order_by(MatchResult.match_score.desc())
        )
        matches = list(result.scalars().all())
        if not matches:
            return None

        newest = max(m.computed_at for m in matches)
        hours_old = (datetime.now(timezone.utc) - newest).total_seconds() / 3600
        if hours_old > settings.matching_stale_hours:
            return None
        return matches

    async def _save_match_result(
        self,
        student_id: UUID,
        program_id: UUID,
        score: float,
        tier: int,
        breakdown: dict,
        reasoning: str,
    ) -> MatchResult:
        result = await self.db.execute(
            select(MatchResult).where(
                MatchResult.student_id == student_id,
                MatchResult.program_id == program_id,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.match_score = Decimal(str(round(score, 4)))
            existing.match_tier = tier
            existing.score_breakdown = breakdown
            existing.reasoning_text = reasoning
            existing.model_version = "v1.0-mvp"
            existing.computed_at = datetime.now(timezone.utc)
            existing.is_stale = False
            return existing

        match = MatchResult(
            student_id=student_id,
            program_id=program_id,
            match_score=Decimal(str(round(score, 4))),
            match_tier=tier,
            score_breakdown=breakdown,
            reasoning_text=reasoning,
            model_version="v1.0-mvp",
            computed_at=datetime.now(timezone.utc),
            is_stale=False,
        )
        self.db.add(match)
        await self.db.flush()
        return match

    async def _mark_old_matches_stale(
        self, student_id: UUID, current_match_ids: list[UUID]
    ) -> None:
        if not current_match_ids:
            return
        result = await self.db.execute(
            select(MatchResult).where(
                MatchResult.student_id == student_id,
                MatchResult.id.notin_(current_match_ids),
            )
        )
        for old_match in result.scalars().all():
            old_match.is_stale = True

    async def _log_prediction(
        self, student_id: UUID, program_id: UUID, score: float, tier: int, features_used: dict
    ) -> None:
        self.db.add(PredictionLog(
            student_id=student_id,
            program_id=program_id,
            predicted_score=Decimal(str(round(score, 4))),
            predicted_tier=tier,
            model_version="v1.0-mvp",
            features_used=features_used,
            predicted_at=datetime.now(timezone.utc),
        ))
        await self.db.flush()

    async def _load_student_preferences(self, student_id: UUID) -> StudentPreference | None:
        result = await self.db.execute(
            select(StudentPreference).where(StudentPreference.student_id == student_id)
        )
        return result.scalar_one_or_none()

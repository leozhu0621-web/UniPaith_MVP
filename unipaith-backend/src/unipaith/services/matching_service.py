"""
Matching service — orchestrates AI pipelines for the API layer.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai.embedding_pipeline import EmbeddingPipeline
from unipaith.ai.feature_extraction import FeatureExtractor
from unipaith.ai.inference import InferencePipeline
from unipaith.core.exceptions import BadRequestException
from unipaith.models.institution import Program
from unipaith.models.matching import MatchResult
from unipaith.models.student import OnboardingProgress


class MatchingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_matches(self, student_id: UUID, force_refresh: bool = False) -> list[MatchResult]:
        """
        Get AI matches for a student.
        Enforces 80% onboarding completion gate.
        """
        await self._check_onboarding_gate(student_id)
        pipeline = InferencePipeline(self.db)
        return await pipeline.compute_matches(student_id, force_refresh=force_refresh)

    async def refresh_student_features(self, student_id: UUID) -> dict:
        """Re-extract features for a student. Called after profile updates."""
        extractor = FeatureExtractor(self.db)
        features = await extractor.extract_student_features(student_id)

        embedder = EmbeddingPipeline(self.db)
        await embedder.generate_student_embedding(student_id)

        await self._mark_matches_stale(student_id)
        return features

    async def refresh_program_features(self, program_id: UUID) -> dict:
        """Re-extract features for a program."""
        extractor = FeatureExtractor(self.db)
        features = await extractor.extract_program_features(program_id)

        embedder = EmbeddingPipeline(self.db)
        await embedder.generate_program_embedding(program_id)
        return features

    async def bootstrap_all_programs(self) -> dict:
        """Extract features + generate embeddings for ALL published programs."""
        result = await self.db.execute(select(Program).where(Program.is_published.is_(True)))
        programs = result.scalars().all()

        extractor = FeatureExtractor(self.db)
        embedder = EmbeddingPipeline(self.db)

        extracted = 0
        embedded = 0
        errors = []

        for program in programs:
            try:
                await extractor.extract_program_features(program.id)
                extracted += 1
                await embedder.generate_program_embedding(program.id)
                embedded += 1
            except Exception as e:
                errors.append({"program_id": str(program.id), "error": str(e)})

        return {
            "total_programs": len(programs),
            "features_extracted": extracted,
            "embeddings_generated": embedded,
            "errors": errors,
        }

    async def _check_onboarding_gate(self, student_id: UUID) -> None:
        result = await self.db.execute(
            select(OnboardingProgress).where(OnboardingProgress.student_id == student_id)
        )
        progress = result.scalar_one_or_none()

        if not progress or progress.completion_percentage < 80:
            completion = progress.completion_percentage if progress else 0
            raise BadRequestException(
                f"Profile must be at least 80% complete to get AI matches. "
                f"Current completion: {completion}%. "
                f"Please complete your profile first."
            )

    async def _mark_matches_stale(self, student_id: UUID) -> None:
        result = await self.db.execute(
            select(MatchResult).where(MatchResult.student_id == student_id)
        )
        for match in result.scalars().all():
            match.is_stale = True

"""
Background AI jobs.
Triggered by events (profile update, program change) or scheduled.
In MVP, they run inline. In production, use Celery/SQS/EventBridge.
"""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai.embedding_pipeline import EmbeddingPipeline
from unipaith.ai.feature_extraction import FeatureExtractor
from unipaith.models.matching import MatchResult

logger = logging.getLogger(__name__)


async def on_student_profile_updated(db: AsyncSession, student_id: UUID) -> None:
    """
    Called when a student updates their profile.
    Re-extracts features, regenerates embedding, marks matches stale.
    """
    extractor = FeatureExtractor(db)
    embedder = EmbeddingPipeline(db)

    await extractor.extract_student_features(student_id)
    await embedder.generate_student_embedding(student_id)

    result = await db.execute(select(MatchResult).where(MatchResult.student_id == student_id))
    for match in result.scalars().all():
        match.is_stale = True


async def on_program_updated(db: AsyncSession, program_id: UUID) -> None:
    """
    Called when a program is updated.
    Re-extracts features, regenerates embedding, marks related matches stale.
    """
    extractor = FeatureExtractor(db)
    embedder = EmbeddingPipeline(db)

    await extractor.extract_program_features(program_id)
    await embedder.generate_program_embedding(program_id)

    result = await db.execute(select(MatchResult).where(MatchResult.program_id == program_id))
    for match in result.scalars().all():
        match.is_stale = True


async def daily_feature_refresh(db: AsyncSession) -> None:
    """Daily job: re-extract features for students with stale matches."""
    result = await db.execute(
        select(MatchResult.student_id).where(MatchResult.is_stale.is_(True)).distinct()
    )
    stale_student_ids = result.scalars().all()

    extractor = FeatureExtractor(db)
    embedder = EmbeddingPipeline(db)

    for student_id in stale_student_ids:
        try:
            await extractor.extract_student_features(student_id)
            await embedder.generate_student_embedding(student_id)
        except Exception as e:
            logger.error(f"Error refreshing student {student_id}: {e}")

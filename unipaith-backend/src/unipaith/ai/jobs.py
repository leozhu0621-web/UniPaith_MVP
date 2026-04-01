"""
Background AI jobs.
Triggered by events (profile update, program change) or scheduled.
In MVP, they run inline. In production, use Celery/SQS/EventBridge.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import settings
from unipaith.ai.embedding_pipeline import EmbeddingPipeline
from unipaith.ai.feature_extraction import FeatureExtractor
from unipaith.models.matching import Embedding, InstitutionFeature, MatchResult, StudentFeature

logger = logging.getLogger(__name__)


async def on_student_profile_updated(db: AsyncSession, student_id: UUID) -> dict[str, str]:
    """
    Called when a student updates their profile.
    Re-extracts features, regenerates embedding, marks matches stale.
    """
    # Avoid repeated heavy recomputations during bursty profile edits.
    cooldown_threshold = datetime.now(timezone.utc) - timedelta(
        seconds=settings.ai_refresh_cooldown_seconds
    )
    feature_result = await db.execute(
        select(StudentFeature).where(StudentFeature.student_id == student_id)
    )
    feature = feature_result.scalar_one_or_none()
    embed_result = await db.execute(
        select(Embedding).where(
            Embedding.entity_type == "student",
            Embedding.entity_id == student_id,
        )
    )
    embedding = embed_result.scalar_one_or_none()
    if (
        feature
        and embedding
        and feature.updated_at >= cooldown_threshold
        and embedding.updated_at >= cooldown_threshold
    ):
        logger.info("Skip student refresh for %s due to cooldown", student_id)
        return {"status": "skipped", "reason": "cooldown"}

    extractor = FeatureExtractor(db)
    embedder = EmbeddingPipeline(db)

    await extractor.extract_student_features(student_id)
    await embedder.generate_student_embedding(student_id)

    result = await db.execute(
        select(MatchResult).where(MatchResult.student_id == student_id)
    )
    for match in result.scalars().all():
        match.is_stale = True
    return {"status": "updated"}


async def on_program_updated(db: AsyncSession, program_id: UUID) -> dict[str, str]:
    """
    Called when a program is updated.
    Re-extracts features, regenerates embedding, marks related matches stale.
    """
    cooldown_threshold = datetime.now(timezone.utc) - timedelta(
        seconds=settings.ai_refresh_cooldown_seconds
    )
    feature_result = await db.execute(
        select(InstitutionFeature).where(InstitutionFeature.program_id == program_id)
    )
    feature = feature_result.scalar_one_or_none()
    embed_result = await db.execute(
        select(Embedding).where(
            Embedding.entity_type == "program",
            Embedding.entity_id == program_id,
        )
    )
    embedding = embed_result.scalar_one_or_none()
    if (
        feature
        and embedding
        and feature.updated_at >= cooldown_threshold
        and embedding.updated_at >= cooldown_threshold
    ):
        logger.info("Skip program refresh for %s due to cooldown", program_id)
        return {"status": "skipped", "reason": "cooldown"}

    extractor = FeatureExtractor(db)
    embedder = EmbeddingPipeline(db)

    await extractor.extract_program_features(program_id)
    await embedder.generate_program_embedding(program_id)

    result = await db.execute(
        select(MatchResult).where(MatchResult.program_id == program_id)
    )
    for match in result.scalars().all():
        match.is_stale = True
    return {"status": "updated"}


async def daily_feature_refresh(db: AsyncSession) -> None:
    """Daily job: re-extract features for students with stale matches."""
    result = await db.execute(
        select(MatchResult.student_id)
        .where(MatchResult.is_stale.is_(True))
        .distinct()
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

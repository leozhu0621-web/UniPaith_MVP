"""
Bootstrap the AI engine — crawl real universities, extract data, generate embeddings.

This is the "start learning" command. It runs the full autonomous pipeline:
1. Seed university sources (if not already done)
2. Crawl all seeded universities
3. LLM extracts structured program data from HTML
4. Deduplicator + ingestor routes programs into the DB
5. Feature extraction runs on all ingested programs
6. Embedding generation for all programs

Requires:
- PostgreSQL running with all tables created (alembic upgrade head)
- GPU_MODE=aws with a running g5.xlarge, OR GPU_MODE=local with local vLLM

Usage:
    cd unipaith-backend
    PYTHONPATH=src GPU_MODE=aws .venv/bin/python -m scripts.bootstrap_ai_engine
"""
from __future__ import annotations

import asyncio
import logging
import sys
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("bootstrap")


async def main():
    from unipaith.config import settings

    if settings.gpu_mode == "mock" or settings.ai_mock_mode:
        logger.error(
            "AI engine is in mock mode (GPU_MODE=%s, AI_MOCK_MODE=%s). "
            "Set GPU_MODE=aws or GPU_MODE=local to use real LLM.",
            settings.gpu_mode, settings.ai_mock_mode,
        )
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("UniPaith AI Engine Bootstrap")
    logger.info("GPU_MODE=%s", settings.gpu_mode)
    logger.info("=" * 60)

    start = time.monotonic()

    # Step 1: Seed university sources
    logger.info("\n--- Step 1: Seeding university sources ---")
    await _seed_sources()

    # Step 2: Crawl all seeded sources
    logger.info("\n--- Step 2: Crawling universities ---")
    crawl_results = await _run_crawls()

    # Step 3: Generate features + embeddings for all programs
    logger.info("\n--- Step 3: Feature extraction + embedding generation ---")
    ai_results = await _run_ai_pipeline()

    # Summary
    elapsed = time.monotonic() - start
    logger.info("\n" + "=" * 60)
    logger.info("Bootstrap complete in %.1f seconds", elapsed)
    logger.info("Crawl results: %s", crawl_results)
    logger.info("AI results: %s", ai_results)
    logger.info("=" * 60)


async def _seed_sources():
    """Run the seed script inline."""
    from sqlalchemy import func, select

    from unipaith.database import async_session
    from unipaith.models.matching import DataSource

    async with async_session() as db:
        count = (await db.execute(
            select(func.count()).select_from(DataSource)
        )).scalar_one()

        if count > 0:
            logger.info("Found %d existing sources, skipping seed", count)
            return

    # Import and run seed
    from scripts.seed_university_sources import main as seed_main
    await seed_main()


async def _run_crawls() -> dict:
    """Crawl all due sources."""
    from unipaith.crawler.orchestrator import CrawlerOrchestrator
    from unipaith.database import async_session

    async with async_session() as db:
        orch = CrawlerOrchestrator(db)
        results = await orch.run_scheduled_crawls()
        await db.commit()

    total_pages = sum(
        r.get("pages_crawled", 0) for r in results.get("results", [])
    )
    total_extracted = sum(
        r.get("items_extracted", 0) for r in results.get("results", [])
    )
    summary = {
        "sources_processed": results.get("sources_processed", 0),
        "total_pages_crawled": total_pages,
        "total_items_extracted": total_extracted,
    }
    logger.info(
        "Crawled %d sources: %d pages, %d items extracted",
        summary["sources_processed"], total_pages, total_extracted,
    )
    return summary


async def _run_ai_pipeline() -> dict:
    """Run feature extraction + embedding generation for all programs."""
    from sqlalchemy import func, select

    from unipaith.ai.embedding_pipeline import EmbeddingPipeline
    from unipaith.ai.feature_extraction import FeatureExtractor
    from unipaith.database import async_session
    from unipaith.models.institution import Program
    from unipaith.models.matching import Embedding, InstitutionFeature

    async with async_session() as db:
        # Count programs
        total_programs = (await db.execute(
            select(func.count()).select_from(Program)
        )).scalar_one()

        if total_programs == 0:
            logger.warning("No programs in DB — nothing to process")
            return {"programs": 0, "features": 0, "embeddings": 0}

        # Get all program IDs
        result = await db.execute(select(Program.id))
        program_ids = [row[0] for row in result.all()]

        extractor = FeatureExtractor(db)
        pipeline = EmbeddingPipeline(db)

        features_created = 0
        embeddings_created = 0
        errors = 0

        for i, pid in enumerate(program_ids, 1):
            try:
                await extractor.extract_program_features(pid)
                features_created += 1

                await pipeline.generate_program_embedding(pid)
                embeddings_created += 1

                if i % 10 == 0:
                    logger.info("  Processed %d/%d programs", i, total_programs)
                    await db.commit()
            except Exception as exc:
                logger.warning("  Failed for program %s: %s", pid, exc)
                errors += 1

        await db.commit()

        summary = {
            "programs": total_programs,
            "features": features_created,
            "embeddings": embeddings_created,
            "errors": errors,
        }
        logger.info(
            "AI pipeline: %d programs, %d features, %d embeddings, %d errors",
            total_programs, features_created, embeddings_created, errors,
        )
        return summary


if __name__ == "__main__":
    asyncio.run(main())

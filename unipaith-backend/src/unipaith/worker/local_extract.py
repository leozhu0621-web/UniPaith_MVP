"""Local LLM extraction worker.

Runs on your Mac (or any machine with Ollama). Pulls raw docs from the
database, extracts knowledge via local Ollama, pushes results back.

Usage:
    # One-time setup
    brew install ollama
    ollama pull qwen2.5:7b

    # Run the worker
    cd unipaith-backend
    python -m unipaith.worker.local_extract

    # Stop: Ctrl+C
    # When stopped, the Fargate fallback auto-engages within 5 minutes.

Multiple workers can run simultaneously on different machines — row-level
locking (SKIP LOCKED) prevents conflicts.
"""

from __future__ import annotations

import asyncio
import logging
import platform
import signal
import time
from datetime import UTC, datetime

from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("unipaith.local_worker")


class LocalExtractWorker:
    """Pull-based extraction worker using local Ollama."""

    def __init__(
        self,
        db_url: str,
        ollama_url: str = "http://localhost:11434/v1",
        model: str = "qwen2.5:7b",
    ) -> None:
        self.db_url = db_url
        self.ollama_url = ollama_url
        self.model = model
        self.hostname = platform.node()
        self._running = True
        self._processed = 0
        self._errors = 0

    async def run(self) -> None:
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

        engine = create_async_engine(self.db_url, pool_size=5, max_overflow=5, pool_pre_ping=True)
        session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        if not await self._check_ollama():
            logger.error("Cannot reach Ollama at %s — is it running?", self.ollama_url)
            logger.info("Start it with: ollama serve")
            return

        logger.info(
            "Worker started — model=%s ollama=%s host=%s",
            self.model, self.ollama_url, self.hostname,
        )
        logger.info("Ctrl+C to stop. Fargate fallback auto-engages within 5 minutes.")

        heartbeat_task = asyncio.create_task(
            self._heartbeat_loop(session_factory)
        )

        try:
            while self._running:
                async with session_factory() as db:
                    doc = await self._pull_raw_doc(db)
                    if doc is None:
                        await asyncio.sleep(5)
                        continue

                    start = time.monotonic()
                    success = await self._extract(db, doc)
                    elapsed = time.monotonic() - start

                    await db.commit()

                    if success:
                        self._processed += 1
                        logger.info(
                            "Extracted: %s -> %s (%.1fs) [total: %d]",
                            (doc.source_url or str(doc.id))[:60],
                            doc.processing_status,
                            elapsed,
                            self._processed,
                        )
                    else:
                        self._errors += 1
                        logger.warning(
                            "Failed: %s (%.1fs) [errors: %d]",
                            (doc.source_url or str(doc.id))[:60],
                            elapsed,
                            self._errors,
                        )
        finally:
            heartbeat_task.cancel()
            await self._clear_heartbeat(session_factory)
            await engine.dispose()
            logger.info(
                "Worker stopped. Processed: %d, Errors: %d",
                self._processed, self._errors,
            )

    async def _pull_raw_doc(self, db: AsyncSession):
        from unipaith.models.knowledge import KnowledgeDocument

        result = await db.execute(
            select(KnowledgeDocument)
            .where(KnowledgeDocument.processing_status == "raw")
            .order_by(KnowledgeDocument.created_at)
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        return result.scalar_one_or_none()

    async def _extract(self, db: AsyncSession, doc) -> bool:
        from unipaith.ai.embedding_client import get_embedding_client
        from unipaith.crawler.knowledge_extractor import KnowledgeExtractor

        ollama_client = _OllamaLLMClient(self.ollama_url, self.model)
        extractor = KnowledgeExtractor(
            db, llm=ollama_client, embedding_client=get_embedding_client()
        )
        try:
            await extractor.extract_knowledge(doc)
            return doc.processing_status == "completed"
        except Exception:
            logger.exception("Extraction error for %s", doc.source_url or doc.id)
            doc.processing_status = "failed"
            doc.processing_error = "local_extraction_failed"
            await db.flush()
            return False

    async def _heartbeat_loop(self, session_factory) -> None:
        from unipaith.models.pipeline import PipelineStageSnapshot

        while self._running:
            try:
                async with session_factory() as db:
                    snap = await db.get(PipelineStageSnapshot, "extract")
                    if snap is None:
                        snap = PipelineStageSnapshot(stage="extract")
                        db.add(snap)

                    snap.worker_heartbeat_at = datetime.now(UTC)
                    snap.worker_hostname = self.hostname
                    snap.status = "local_online"
                    snap.extra_json = {
                        **(snap.extra_json or {}),
                        "worker_model": self.model,
                        "worker_processed": self._processed,
                        "worker_errors": self._errors,
                    }
                    await db.commit()
            except Exception:
                logger.debug("Heartbeat write failed", exc_info=True)

            await asyncio.sleep(30)

    async def _clear_heartbeat(self, session_factory) -> None:
        from unipaith.models.pipeline import PipelineStageSnapshot

        try:
            async with session_factory() as db:
                snap = await db.get(PipelineStageSnapshot, "extract")
                if snap:
                    snap.worker_heartbeat_at = None
                    snap.status = "local_offline"
                    await db.commit()
        except Exception:
            pass

    async def _check_ollama(self) -> bool:
        try:
            client = AsyncOpenAI(base_url=self.ollama_url, api_key="not-needed")
            await asyncio.wait_for(client.models.list(), timeout=10)
            return True
        except Exception:
            return False


class _OllamaLLMClient:
    """Minimal LLM client that talks to local Ollama.

    Matches the interface used by KnowledgeExtractor (extract_features).
    """

    def __init__(self, base_url: str, model: str) -> None:
        self.client = AsyncOpenAI(base_url=base_url, api_key="not-needed")
        self.model = model

    async def extract_features(self, system_prompt: str, user_content: str) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            max_tokens=2048,
            temperature=0.1,
        )
        return response.choices[0].message.content or ""

    async def generate_reasoning(self, system_prompt: str, user_content: str) -> str:
        return await self.extract_features(system_prompt, user_content)


def main() -> None:
    from unipaith.config import settings

    worker = LocalExtractWorker(
        db_url=settings.database_url,
        ollama_url=settings.pipeline_extract_ollama_url,
        model=settings.pipeline_extract_ollama_model,
    )

    loop = asyncio.new_event_loop()

    def _shutdown(sig, frame):
        logger.info("Shutdown signal received")
        worker._running = False

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    try:
        loop.run_until_complete(worker.run())
    finally:
        loop.close()


if __name__ == "__main__":
    main()

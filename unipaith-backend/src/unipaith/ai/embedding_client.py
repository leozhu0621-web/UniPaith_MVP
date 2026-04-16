"""
Embedding generation client.
Three modes:
1. Mock mode: deterministic random vectors (dev/testing)
2. Local mode: calls localhost vLLM /v1/embeddings endpoint
3. AWS mode: calls AWS GPU instance with retry logic
"""

from __future__ import annotations

import asyncio
import logging

import numpy as np
from openai import AsyncOpenAI

from unipaith.config import settings
from unipaith.core.ai_runtime_metrics import record_embedding, start_timer

logger = logging.getLogger("unipaith.embedding_client")


class EmbeddingClient:
    """Generate embeddings via OpenAI-compatible API (vLLM serves the model)."""

    def __init__(self):
        self.client = AsyncOpenAI(
            base_url=settings.embedding_base_url,
            api_key=settings.openai_api_key or "not-needed",
        )
        self.model = settings.embedding_model
        self.dimension = settings.embedding_dimension

    async def embed_text(self, text: str) -> list[float]:
        """Generate embedding for a single text string."""
        return (await self.embed_batch([text]))[0]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts in one call."""
        last_error = None
        for attempt in range(1, settings.ai_request_max_retries + 1):
            started = start_timer()
            try:
                response = await asyncio.wait_for(
                    self.client.embeddings.create(model=self.model, input=texts),
                    timeout=settings.ai_request_timeout_seconds,
                )
                record_embedding(started, ok=True)
                return [item.embedding for item in response.data]
            except TimeoutError as exc:
                record_embedding(started, ok=False, timed_out=True)
                last_error = exc
            except Exception as exc:
                record_embedding(started, ok=False)
                last_error = exc
            if attempt < settings.ai_request_max_retries:
                await asyncio.sleep(settings.ai_request_backoff_seconds * attempt)
        raise last_error or RuntimeError("Embedding request failed with no retries configured")


class AWSEmbeddingClient:
    """AWS GPU-backed embedding client.

    Uses the always-on g5.xlarge instance (nomic runs alongside 8B).
    Adds retry logic for transient failures.
    """

    MAX_RETRIES = 3

    def __init__(self):
        self.client = AsyncOpenAI(
            base_url=f"{settings.gpu_8b_endpoint}/v1",
            api_key="not-needed",
        )
        self.model = settings.embedding_model
        self.dimension = settings.embedding_dimension

    async def embed_text(self, text: str) -> list[float]:
        return (await self.embed_batch([text]))[0]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings with retry on transient failures."""
        last_error = None
        for attempt in range(1, self.MAX_RETRIES + 1):
            started = start_timer()
            try:
                response = await asyncio.wait_for(
                    self.client.embeddings.create(model=self.model, input=texts),
                    timeout=settings.ai_request_timeout_seconds,
                )
                record_embedding(started, ok=True)
                return [item.embedding for item in response.data]
            except TimeoutError as e:
                record_embedding(started, ok=False, timed_out=True)
                last_error = e
                if attempt < self.MAX_RETRIES:
                    await asyncio.sleep(settings.ai_request_backoff_seconds * attempt)
            except Exception as e:
                record_embedding(started, ok=False)
                last_error = e
                if attempt < self.MAX_RETRIES:
                    wait = settings.ai_request_backoff_seconds * attempt
                    logger.warning(
                        "Embedding request failed (attempt %d/%d): %s. Retrying in %ds",
                        attempt,
                        self.MAX_RETRIES,
                        e,
                        wait,
                    )
                    await asyncio.sleep(wait)

        logger.error("Embedding request failed after %d attempts: %s", self.MAX_RETRIES, last_error)
        raise last_error or RuntimeError("Embedding request failed with no retries configured")


class MockEmbeddingClient:
    """Returns deterministic normalized vectors for dev/testing."""

    def __init__(self):
        self.dimension = settings.embedding_dimension

    async def embed_text(self, text: str) -> list[float]:
        """Generate a deterministic mock embedding based on text hash."""
        seed = hash(text) % (2**31)
        rng = np.random.RandomState(seed)
        vec = rng.randn(self.dimension).astype(float)
        vec = vec / np.linalg.norm(vec)
        return vec.tolist()

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [await self.embed_text(t) for t in texts]


def get_embedding_client() -> EmbeddingClient | AWSEmbeddingClient | MockEmbeddingClient:
    """Factory: returns the appropriate embedding client based on gpu_mode."""
    if settings.gpu_mode == "mock" or settings.ai_mock_mode:
        return MockEmbeddingClient()
    if settings.gpu_mode == "aws":
        return AWSEmbeddingClient()
    # "local", "openai" — uses config base_url + api_key
    return EmbeddingClient()

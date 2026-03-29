"""
Embedding generation client.
Supports two modes:
1. API mode: calls vLLM /v1/embeddings endpoint (production)
2. Mock mode: returns deterministic random vectors (dev/testing)
"""

import numpy as np
from openai import AsyncOpenAI

from unipaith.config import settings


class EmbeddingClient:
    """Generate embeddings via OpenAI-compatible API (vLLM serves the model)."""

    def __init__(self):
        self.client = AsyncOpenAI(
            base_url=settings.embedding_base_url,
            api_key="not-needed",
        )
        self.model = settings.embedding_model
        self.dimension = settings.embedding_dimension

    async def embed_text(self, text: str) -> list[float]:
        """Generate embedding for a single text string."""
        response = await self.client.embeddings.create(
            model=self.model,
            input=text,
        )
        return response.data[0].embedding

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts in one call."""
        response = await self.client.embeddings.create(
            model=self.model,
            input=texts,
        )
        return [item.embedding for item in response.data]


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


def get_embedding_client() -> EmbeddingClient | MockEmbeddingClient:
    if settings.ai_mock_mode:
        return MockEmbeddingClient()
    return EmbeddingClient()

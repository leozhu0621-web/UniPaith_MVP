"""
Integration tests for AWS embedding client.
Requires: GPU_TEST=true, GPU_MODE=aws, running g5.xlarge.
"""

from __future__ import annotations

import pytest

from unipaith.config import settings

pytestmark = pytest.mark.gpu


@pytest.fixture
def aws_embedding_client():
    import os

    os.environ["GPU_MODE"] = "aws"
    from unipaith.ai.embedding_client import AWSEmbeddingClient

    return AWSEmbeddingClient()


async def test_embed_single_text(aws_embedding_client):
    """Should return a 768-dim vector."""
    vec = await aws_embedding_client.embed_text("Computer science student interested in AI")
    assert len(vec) == settings.embedding_dimension
    assert all(isinstance(v, float) for v in vec)


async def test_embed_batch(aws_embedding_client):
    """Should return vectors for multiple texts."""
    texts = [
        "Machine learning researcher",
        "Biology graduate student",
        "Economics PhD candidate",
    ]
    vecs = await aws_embedding_client.embed_batch(texts)
    assert len(vecs) == 3
    assert all(len(v) == settings.embedding_dimension for v in vecs)


async def test_similar_texts_closer(aws_embedding_client):
    """Semantically similar texts should have higher cosine similarity."""
    import numpy as np

    vecs = await aws_embedding_client.embed_batch(
        [
            "AI and machine learning research",
            "Deep learning and neural networks",
            "Medieval French literature",
        ]
    )

    def cosine_sim(a, b):
        a, b = np.array(a), np.array(b)
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    sim_related = cosine_sim(vecs[0], vecs[1])
    sim_unrelated = cosine_sim(vecs[0], vecs[2])
    assert sim_related > sim_unrelated

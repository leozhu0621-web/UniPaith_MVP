"""
Integration tests for AWS LLM client.
Requires: GPU_TEST=true, GPU_MODE=aws, running GPU instances.
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.gpu


@pytest.fixture
def aws_llm_client():
    import os
    os.environ["GPU_MODE"] = "aws"
    from unipaith.ai.llm_client import AWSLLMClient
    return AWSLLMClient()


async def test_extract_features(aws_llm_client):
    """8B model should return valid JSON feature extraction."""
    result = await aws_llm_client.extract_features(
        system_prompt="Extract academic features as JSON.",
        user_content="Student with 3.8 GPA in Computer Science, published 2 papers on NLP.",
    )
    assert result is not None
    assert len(result) > 10
    # Should contain JSON-like content
    assert "{" in result


async def test_generate_reasoning(aws_llm_client):
    """70B model should generate natural language reasoning."""
    result = await aws_llm_client.generate_reasoning(
        system_prompt="Explain why this is a good match.",
        user_content="Student: CS background, NLP research. Program: AI/ML master's at CMU.",
    )
    assert result is not None
    assert len(result) > 50


async def test_reasoning_fallback_on_budget(aws_llm_client):
    """When budget is exceeded, should fall back to template reasoning."""
    from unipaith.ai.cost_tracker import get_cost_tracker
    from unipaith.config import settings

    # Force budget exceeded
    original_cap = settings.gpu_monthly_budget_cap
    settings.gpu_monthly_budget_cap = 0.01
    try:
        result = await aws_llm_client.generate_reasoning(
            system_prompt="test",
            user_content="test",
        )
        assert "try again later" in result.lower() or "alignment" in result.lower()
    finally:
        settings.gpu_monthly_budget_cap = original_cap

"""Phase A1 — unit tests for the AI client wrapper.

These tests run in mock mode and don't require an Anthropic key. They verify:
  - cost calculation against the published pricing table
  - mock mode returns a structurally valid LLMResponse
  - the singleton getter / reset pattern works
  - embedding mock returns a 1024-d vector
"""

from __future__ import annotations

import asyncio
from decimal import Decimal

from unipaith.ai.client import (
    CACHE_READ_MULTIPLIER,
    CACHE_WRITE_MULTIPLIER,
    MODEL_PRICES,
    AIClient,
    EmbeddingResponse,
    LLMResponse,
    get_client,
    reset_client,
)


def _make_mock_client() -> AIClient:
    return AIClient(
        anthropic_api_key="",
        voyage_api_key="",
        sonnet_model="claude-sonnet-4-6",
        haiku_model="claude-haiku-4-5",
        embedding_model="voyage-3-large",
        mock_mode=True,
    )


# ── Cost math ───────────────────────────────────────────────────────────────


def test_compute_cost_sonnet_basic() -> None:
    cost = AIClient._compute_cost(
        model_id="claude-sonnet-4-6",
        input_tokens=1_000_000,
        output_tokens=0,
        cache_read_tokens=0,
        cache_creation_tokens=0,
    )
    assert cost == Decimal(str(MODEL_PRICES["claude-sonnet-4-6"]["input"]))


def test_compute_cost_haiku_input_plus_output() -> None:
    cost = AIClient._compute_cost(
        model_id="claude-haiku-4-5",
        input_tokens=500_000,
        output_tokens=200_000,
        cache_read_tokens=0,
        cache_creation_tokens=0,
    )
    expected = Decimal("0.5") * Decimal(str(MODEL_PRICES["claude-haiku-4-5"]["input"])) + Decimal(
        "0.2"
    ) * Decimal(str(MODEL_PRICES["claude-haiku-4-5"]["output"]))
    assert cost == Decimal(str(round(expected, 6)))


def test_compute_cost_cache_read_is_one_tenth() -> None:
    """Cache reads should be billed at 0.1× the input rate per Anthropic."""
    full = AIClient._compute_cost(
        model_id="claude-sonnet-4-6",
        input_tokens=1_000_000,
        output_tokens=0,
        cache_read_tokens=0,
        cache_creation_tokens=0,
    )
    cached = AIClient._compute_cost(
        model_id="claude-sonnet-4-6",
        input_tokens=0,
        output_tokens=0,
        cache_read_tokens=1_000_000,
        cache_creation_tokens=0,
    )
    assert cached == Decimal(str(round(float(full) * CACHE_READ_MULTIPLIER, 6)))


def test_compute_cost_cache_write_premium() -> None:
    """Cache creation is billed at 1.25× the input rate."""
    full = AIClient._compute_cost(
        model_id="claude-sonnet-4-6",
        input_tokens=1_000_000,
        output_tokens=0,
        cache_read_tokens=0,
        cache_creation_tokens=0,
    )
    create = AIClient._compute_cost(
        model_id="claude-sonnet-4-6",
        input_tokens=0,
        output_tokens=0,
        cache_read_tokens=0,
        cache_creation_tokens=1_000_000,
    )
    assert create == Decimal(str(round(float(full) * CACHE_WRITE_MULTIPLIER, 6)))


def test_compute_cost_unknown_model_returns_zero() -> None:
    """Unknown models cost $0 — explicit by design so the ledger never blows up."""
    cost = AIClient._compute_cost(
        model_id="claude-unobtanium-9000",
        input_tokens=1_000_000,
        output_tokens=1_000_000,
        cache_read_tokens=0,
        cache_creation_tokens=0,
    )
    assert cost == Decimal("0")


# ── Mock mode ───────────────────────────────────────────────────────────────


def test_mock_message_returns_llm_response() -> None:
    client = _make_mock_client()
    resp = asyncio.run(
        client.message(
            agent="extractor",
            model="haiku",
            system="hi",
            messages=[{"role": "user", "content": "test"}],
        )
    )
    assert isinstance(resp, LLMResponse)
    assert resp.model.startswith("mock:")
    assert resp.cost_usd == Decimal("0")
    assert resp.input_tokens == 0
    assert resp.output_tokens == 0
    assert resp.text.startswith("[mock:extractor:")


def test_mock_embedding_returns_1024d_vector() -> None:
    client = _make_mock_client()
    resp = asyncio.run(client.embed("hello world"))
    assert isinstance(resp, EmbeddingResponse)
    assert len(resp.embedding) == 1024
    # Mock vectors should be deterministic for the same input.
    resp2 = asyncio.run(client.embed("hello world"))
    assert resp.embedding == resp2.embedding
    # And different for different inputs.
    resp3 = asyncio.run(client.embed("different input"))
    assert resp.embedding != resp3.embedding


# ── Singleton ───────────────────────────────────────────────────────────────


def test_singleton_returns_same_instance() -> None:
    reset_client()
    a = get_client()
    b = get_client()
    assert a is b


def test_reset_client_creates_fresh_instance() -> None:
    reset_client()
    a = get_client()
    reset_client()
    b = get_client()
    assert a is not b

"""Phase A3.2 — SSE streaming smoke tests.

Mock-mode coverage. Real-mode streaming runs only with an Anthropic key
and is exercised manually via the eval harness once secrets are set.
"""

from __future__ import annotations

import asyncio

from unipaith.ai.client import AIClient
from unipaith.ai.orchestrator import Orchestrator, TurnContext


def _mock_client() -> AIClient:
    return AIClient(
        anthropic_api_key="",
        voyage_api_key="",
        sonnet_model="claude-sonnet-4-6",
        haiku_model="claude-haiku-4-5",
        embedding_model="voyage-3-large",
        mock_mode=True,
    )


def test_client_stream_message_in_mock_yields_text_then_done() -> None:
    """Mock stream emits a single text_delta then a 'done' event with a
    LLMResponse payload. This is the contract the orchestrator and
    discovery service rely on."""
    client = _mock_client()

    async def _drive():
        events = []
        async for event_type, payload in client.stream_message(
            agent="orchestrator",
            model="sonnet",
            system="hi",
            messages=[{"role": "user", "content": "test"}],
        ):
            events.append((event_type, payload))
        return events

    events = asyncio.run(_drive())
    types = [e[0] for e in events]
    assert "text_delta" in types
    assert types[-1] == "done"
    # Final 'done' payload is the aggregated LLMResponse.
    final = events[-1][1]
    assert hasattr(final, "text")
    assert final.text


def test_orchestrator_stream_in_mock_yields_done_with_orchestrator_response() -> None:
    """The orchestrator's stream wrapper converts the client's LLMResponse
    into an OrchestratorResponse on 'done'."""
    orch = Orchestrator(client=_mock_client())
    ctx = TurnContext(
        track="profile",
        layer="basic",
        completion_pct=0.0,
        verdict=None,
        known_profile_summary="",
    )

    async def _drive():
        events = []
        async for event_type, payload in orch.stream(ctx=ctx):
            events.append((event_type, payload))
        return events

    events = asyncio.run(_drive())
    assert events[-1][0] == "done"
    final = events[-1][1]
    # OrchestratorResponse has text + record_artifact_calls fields.
    assert hasattr(final, "record_artifact_calls")
    assert hasattr(final, "requested_layer_advance")


def test_client_stream_does_not_crash_on_unrecognized_block() -> None:
    """Defensive: future Anthropic block types shouldn't crash the loop.
    The mock stream only emits text_delta; this test guards that the
    final 'done' is present even with a noop content stream."""
    client = _mock_client()

    async def _drive():
        async for event_type, _payload in client.stream_message(
            agent="extractor",
            model="haiku",
            system="hi",
            messages=[{"role": "user", "content": "x"}],
        ):
            if event_type == "done":
                return True
        return False

    assert asyncio.run(_drive())

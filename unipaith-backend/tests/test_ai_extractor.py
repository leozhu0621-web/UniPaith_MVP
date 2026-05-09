"""Phase A2 — Extractor unit tests.

Mock-mode coverage of the extractor module. Real-mode F1 evaluation lives
in `ai.evals.runner.run_extractor_accuracy(real=True)`.
"""

from __future__ import annotations

import asyncio
from decimal import Decimal

from unipaith.ai.client import AIClient
from unipaith.ai.extractor import (
    ExtractedSignals,
    Extractor,
    get_extractor,
    reset_extractor,
)


def _mock_client() -> AIClient:
    return AIClient(
        anthropic_api_key="",
        voyage_api_key="",
        sonnet_model="claude-sonnet-4-6",
        haiku_model="claude-haiku-4-5",
        embedding_model="voyage-3-large",
        mock_mode=True,
    )


def test_extractor_singleton_pattern() -> None:
    reset_extractor()
    a = get_extractor()
    b = get_extractor()
    assert a is b
    reset_extractor()
    c = get_extractor()
    assert c is not a


def test_parse_response_with_tool_use_block() -> None:
    """Parsing a well-formed tool_use response → filtered signals."""
    ex = Extractor(client=_mock_client())
    blocks = [
        {
            "type": "tool_use",
            "name": "extract_signals",
            "input": {
                "basic": {"gpa": 3.7, "first_gen": True},
                "personality": [{"facet": "interest", "value": "ml", "evidence": "..."}],
                "identity": [],
                "goals": [],
                "needs": [],
                "confidence": {
                    "basic": 0.9,
                    "personality": 0.8,
                    "identity": 0.0,
                    "goals": 0.0,
                    "needs": 0.0,
                },
            },
        }
    ]
    result = ex._parse_response(blocks)
    assert result.basic == {"gpa": 3.7, "first_gen": True}
    assert len(result.personality) == 1
    assert result.confidence_per_key["basic"] == Decimal("0.9")
    assert result.raw_response is not None


def test_parse_response_drops_low_confidence_blocks() -> None:
    """Blocks below the 0.7 threshold are filtered out."""
    ex = Extractor(client=_mock_client(), confidence_threshold=Decimal("0.7"))
    blocks = [
        {
            "type": "tool_use",
            "name": "extract_signals",
            "input": {
                "basic": {"gpa": 2.5},
                "personality": [{"facet": "interest", "value": "x"}],
                "confidence": {
                    "basic": 0.5,  # below threshold → drop basic
                    "personality": 0.8,  # keep
                },
            },
        }
    ]
    result = ex._parse_response(blocks)
    assert result.basic == {}, "Low-confidence basic block should be dropped"
    assert len(result.personality) == 1, "High-confidence personality block kept"


def test_parse_response_handles_missing_tool_use() -> None:
    """If the model returned no tool call (shouldn't happen with forced
    tool_choice but defensively handled), we get an empty result."""
    ex = Extractor(client=_mock_client())
    result = ex._parse_response([{"type": "text", "text": "I refuse to extract"}])
    assert isinstance(result, ExtractedSignals)
    assert result.is_empty()


def test_parse_response_handles_missing_confidence() -> None:
    """No confidence dict → keep everything (caller may apply its own filter)."""
    ex = Extractor(client=_mock_client())
    blocks = [
        {
            "type": "tool_use",
            "name": "extract_signals",
            "input": {
                "basic": {"age": 20},
                "personality": [],
            },
        }
    ]
    result = ex._parse_response(blocks)
    assert result.basic == {"age": 20}


def test_extract_in_mock_mode_returns_empty() -> None:
    """End-to-end: mock client returns a text-only canned response with no
    tool_use blocks → extractor returns ExtractedSignals.empty.
    Verifies the full call path does not error in mock mode."""
    ex = Extractor(client=_mock_client())
    result = asyncio.run(ex.extract(student_turn="hello"))
    assert isinstance(result, ExtractedSignals)
    assert result.is_empty()


def test_extracted_signals_is_empty_helper() -> None:
    assert ExtractedSignals().is_empty()
    assert not ExtractedSignals(basic={"age": 20}).is_empty()
    assert not ExtractedSignals(personality=[{"facet": "x"}]).is_empty()

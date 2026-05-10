"""Phase B1 — Feature Emitter (A4) unit tests.

Mock-mode coverage. Real-mode behavior is exercised once API keys are
populated; the emitter writes one row to ai_turns per call (the client
wrapper enforces this).
"""

from __future__ import annotations

import asyncio

from unipaith.ai.client import AIClient
from unipaith.ai.feature_emitter import (
    EmittedFeatures,
    FeatureEmitter,
    get_feature_emitter,
    reset_feature_emitter,
)
from unipaith.ai.state import (
    GoalEntry,
    IdentityClaim,
    NeedEntry,
    PersonalityEntry,
    StudentSnapshot,
)
from unipaith.ai.tools.feature_schema import (
    CAREER_ARCS,
    EMIT_FEATURES_TOOL,
    INTEREST_THEMES,
    NEED_SIGNAL_TAGS,
    SCHEMA_VERSION,
    VALUE_TAGS,
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


# ── Schema sanity ──────────────────────────────────────────────────────────


def test_schema_version_is_v1() -> None:
    assert SCHEMA_VERSION == 1


def test_emit_features_tool_has_required_keys() -> None:
    """The tool schema must require the matcher's hard-filter inputs.
    Adding a new required key is a breaking change — bump SCHEMA_VERSION."""
    required = set(EMIT_FEATURES_TOOL["input_schema"]["required"])
    assert required == {"sparse_features", "applicant_summary"}
    sparse_required = set(
        EMIT_FEATURES_TOOL["input_schema"]["properties"]["sparse_features"]["required"]
    )
    # The matcher's hard-filter rule layer reads these.
    assert "education_level" in sparse_required
    assert "geo_must" in sparse_required
    assert "needs_signals" in sparse_required


def test_controlled_vocabularies_non_empty() -> None:
    """Empty vocabs would silently degrade matching to text-only."""
    assert len(INTEREST_THEMES) >= 20
    assert len(CAREER_ARCS) >= 15
    assert len(VALUE_TAGS) >= 10
    assert len(NEED_SIGNAL_TAGS) >= 20


def test_controlled_vocab_ids_unique() -> None:
    for vocab in (INTEREST_THEMES, CAREER_ARCS, VALUE_TAGS, NEED_SIGNAL_TAGS):
        assert len(vocab) == len(set(vocab))


# ── Singleton ──────────────────────────────────────────────────────────────


def test_feature_emitter_singleton_pattern() -> None:
    reset_feature_emitter()
    a = get_feature_emitter()
    b = get_feature_emitter()
    assert a is b
    reset_feature_emitter()
    c = get_feature_emitter()
    assert c is not a


# ── EmittedFeatures.is_valid ──────────────────────────────────────────────


def test_emitted_features_is_valid_requires_keys_and_summary() -> None:
    """All required sparse-feature keys + non-empty summary."""
    full_sparse = {
        "education_level": "bachelors",
        "intended_degrees": ["MS-CS"],
        "intended_majors": [],
        "geo_must": [],
        "geo_avoid": [],
        "interest_themes": ["machine_learning"],
        "career_arcs": ["ml_research"],
        "values": [],
        "needs_signals": {},
        "social_prefs": {},
        "feature_completeness": 0.8,
    }
    valid = EmittedFeatures(
        sparse_features=full_sparse, applicant_summary="hello world"
    )
    assert valid.is_valid()
    # Missing summary
    assert not EmittedFeatures(sparse_features=full_sparse).is_valid()
    # Missing required key (drop interest_themes)
    partial = dict(full_sparse)
    partial.pop("interest_themes")
    assert not EmittedFeatures(
        sparse_features=partial, applicant_summary="hi"
    ).is_valid()


# ── Snapshot serialization ─────────────────────────────────────────────────


def test_snapshot_payload_includes_all_layers() -> None:
    """The serialized payload must include basic + personality + identity
    + goals + needs so the LLM has full context for tag selection."""
    snap = StudentSnapshot(
        age=22,
        education_level="bachelors",
        gpa=3.7,
        location_prefs=["US-NY"],
        first_gen=True,
        personality=[PersonalityEntry(facet="interest", value="ml", evidence="ev")],
        identity_claims=[
            IdentityClaim(
                facet="value", claim="impact > brand", evidence="ev", user_confirmed=True
            )
        ],
        goals=[
            GoalEntry(
                category="academic",
                specific="MS-CS by 2027",
                completeness=1.0,
                user_confirmed=True,
            )
        ],
        needs=[NeedEntry(maslow_level="safety", signal="low_income_aid", severity=4)],
    )
    payload = FeatureEmitter._snapshot_payload(snap)
    assert "basic" in payload
    assert "personality" in payload
    assert "identity" in payload
    assert "goals" in payload
    assert "needs" in payload
    assert "low_income_aid" in payload
    assert "first_gen" in payload


def test_snapshot_payload_handles_empty_snapshot() -> None:
    """No crash on empty snapshot — emitter will return is_valid=False."""
    payload = FeatureEmitter._snapshot_payload(StudentSnapshot())
    assert "basic" in payload


# ── Response parsing ───────────────────────────────────────────────────────


def test_parse_response_extracts_tool_use_input() -> None:
    blocks = [
        {
            "type": "tool_use",
            "name": "emit_features",
            "input": {
                "sparse_features": {"education_level": "bachelors"},
                "applicant_summary": "test",
            },
        }
    ]
    sparse, summary = FeatureEmitter._parse_response(blocks)
    assert sparse == {"education_level": "bachelors"}
    assert summary == "test"


def test_parse_response_handles_missing_tool_use() -> None:
    """If forced tool_choice somehow returns text-only (shouldn't happen
    but defensively handled), we get empty results."""
    blocks = [{"type": "text", "text": "I refuse"}]
    sparse, summary = FeatureEmitter._parse_response(blocks)
    assert sparse == {}
    assert summary == ""


def test_parse_response_ignores_wrong_tool_name() -> None:
    blocks = [
        {
            "type": "tool_use",
            "name": "some_other_tool",
            "input": {"sparse_features": {"x": 1}},
        }
    ]
    sparse, summary = FeatureEmitter._parse_response(blocks)
    assert sparse == {}


# ── End-to-end mock-mode call ──────────────────────────────────────────────


def test_emit_in_mock_mode_returns_invalid_features() -> None:
    """Mock client returns text-only canned response with no tool_use →
    parse fails → is_valid=False. Verifies the full call path runs."""
    emitter = FeatureEmitter(client=_mock_client())
    result = asyncio.run(emitter.emit(snapshot=StudentSnapshot()))
    assert isinstance(result, EmittedFeatures)
    assert not result.is_valid()
    # In mock mode, embedding still resolves (deterministic 1024-d vector
    # from the mock client) IF summary was non-empty; here it's empty
    # because the mock returned no tool_use.
    assert result.embedding is None
    assert result.schema_version == SCHEMA_VERSION


def test_emit_with_canned_features_via_injected_client() -> None:
    """Inject a stub client that returns a real tool_use, verify the
    parser + embedding hookup produce a valid EmittedFeatures."""

    class _StubClient(AIClient):
        def __init__(self):
            super().__init__(
                anthropic_api_key="",
                voyage_api_key="",
                sonnet_model="x",
                haiku_model="x",
                embedding_model="x",
                mock_mode=True,
            )

        async def message(self, **kwargs):
            from unipaith.ai.client import LLMResponse

            return LLMResponse(
                text="",
                content_blocks=[
                    {
                        "type": "tool_use",
                        "name": "emit_features",
                        "input": {
                            "sparse_features": {
                                "education_level": "bachelors",
                                "intended_degrees": ["MS-CS"],
                                "intended_majors": [],
                                "geo_must": [],
                                "geo_avoid": [],
                                "interest_themes": ["machine_learning"],
                                "career_arcs": ["ml_research"],
                                "values": [],
                                "needs_signals": {},
                                "social_prefs": {},
                                "feature_completeness": 0.8,
                            },
                            "applicant_summary": "A real applicant summary.",
                        },
                    }
                ],
                model="mock",
            )

    emitter = FeatureEmitter(client=_StubClient())
    result = asyncio.run(emitter.emit(snapshot=StudentSnapshot()))
    assert result.is_valid()
    assert result.sparse_features["education_level"] == "bachelors"
    assert "machine_learning" in result.sparse_features["interest_themes"]
    # Mock embed returns deterministic 1024-d.
    assert result.embedding is not None
    assert len(result.embedding) == 1024

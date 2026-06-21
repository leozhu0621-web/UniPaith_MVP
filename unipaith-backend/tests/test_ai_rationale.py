"""Phase B2 — A5 Rationale agent tests.

Mock-mode coverage. Real-mode behavior (groundedness pass rate against
50 fixture pairs) gets measured once API keys land in staging.
"""

from __future__ import annotations

import asyncio

from unipaith.ai.client import AIClient, LLMResponse
from unipaith.ai.rationale import (
    ProgramView,
    RationaleAgent,
    RationaleResult,
    ScoreView,
    StudentView,
    get_rationale_agent,
    is_grounded,
    reset_rationale_agent,
    resolve_path,
)
from unipaith.ai.tools.rationale_schema import (
    SCHEMA_VERSION,
    SUBMIT_RATIONALE_TOOL,
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


def test_schema_version_is_v2() -> None:
    assert SCHEMA_VERSION == 2


def test_submit_rationale_tool_required_keys() -> None:
    required = set(SUBMIT_RATIONALE_TOOL["input_schema"]["required"])
    assert required == {
        "para_fit",
        "para_tradeoffs",
        "para_confidence",
        "decision_brief",
        "cited_student_fields",
        "cited_program_fields",
    }


# ── Singleton ──────────────────────────────────────────────────────────────


def test_rationale_singleton_pattern() -> None:
    reset_rationale_agent()
    a = get_rationale_agent()
    b = get_rationale_agent()
    assert a is b
    reset_rationale_agent()
    c = get_rationale_agent()
    assert c is not a


# ── resolve_path ───────────────────────────────────────────────────────────


def test_resolve_path_top_level_field() -> None:
    student = StudentView(applicant_summary="hello world")
    assert resolve_path(student, "applicant_summary") == "hello world"


def test_resolve_path_sparse_dict_value() -> None:
    student = StudentView(sparse={"education_level": "bachelors"})
    assert resolve_path(student, "sparse.education_level") == "bachelors"


def test_resolve_path_nested_sparse_dict() -> None:
    student = StudentView(sparse={"social_prefs": {"small_cohort": 0.9}})
    assert resolve_path(student, "sparse.social_prefs.small_cohort") == 0.9


def test_resolve_path_tag_in_list() -> None:
    """Lists support tag-membership resolution: 'sparse.values.X' resolves
    to the string 'X' if X is in the values list."""
    student = StudentView(sparse={"values": ["intellectual_rigor", "service_to_community"]})
    assert resolve_path(student, "sparse.values.intellectual_rigor") == "intellectual_rigor"
    # Missing tag returns None.
    assert resolve_path(student, "sparse.values.missing_tag") is None


def test_resolve_path_missing_top_level_returns_none() -> None:
    student = StudentView()
    assert resolve_path(student, "nonexistent") is None


def test_resolve_path_missing_sparse_key_returns_none() -> None:
    student = StudentView(sparse={"a": 1})
    assert resolve_path(student, "sparse.b") is None


def test_resolve_path_program_top_level() -> None:
    program = ProgramView(name="MS-CS", description="Strong ML focus")
    assert resolve_path(program, "name") == "MS-CS"
    assert resolve_path(program, "description") == "Strong ML focus"


def test_resolve_path_walks_into_dict_in_list() -> None:
    """If a list contains plain values (tags), tag membership works.
    If a list contains dicts (e.g. test_scores), we don't dive in —
    callers should cite top-level paths or specific dict keys."""
    program = ProgramView(sparse={"some_list": [{"k": "v"}]})
    # Walking 'some_list.k' against a list of dicts returns None — we
    # don't auto-flatten; callers cite specific paths.
    assert resolve_path(program, "sparse.some_list.k") is None


# ── is_grounded ────────────────────────────────────────────────────────────


def test_is_grounded_all_paths_resolve() -> None:
    student = StudentView(
        applicant_summary="The student values rigor.",
        sparse={"values": ["intellectual_rigor"]},
    )
    program = ProgramView(name="MS-CS", sparse={"interest_themes": ["ml"]})
    grounded, bad = is_grounded(
        student,
        program,
        cited_student=["applicant_summary", "sparse.values.intellectual_rigor"],
        cited_program=["name", "sparse.interest_themes.ml"],
    )
    assert grounded is True
    assert bad == []


def test_is_grounded_rejects_missing_path() -> None:
    student = StudentView(applicant_summary="hi")
    program = ProgramView(name="MS-CS")
    grounded, bad = is_grounded(
        student,
        program,
        cited_student=["sparse.values.fabricated_tag"],
        cited_program=["name"],
    )
    assert grounded is False
    assert "student:sparse.values.fabricated_tag" in bad


def test_is_grounded_rejects_empty_string() -> None:
    """Empty strings count as ungrounded — citing an empty
    applicant_summary is no better than citing nothing."""
    student = StudentView(applicant_summary="")
    program = ProgramView(name="MS-CS")
    grounded, bad = is_grounded(
        student, program, cited_student=["applicant_summary"], cited_program=[]
    )
    assert grounded is False
    assert "student:applicant_summary" in bad


def test_is_grounded_empty_lists_pass() -> None:
    """No citations at all is technically grounded (vacuously true).
    The agent's prompt forbids this, but the validator doesn't enforce
    'at least one citation' — that's a separate quality check."""
    grounded, bad = is_grounded(StudentView(), ProgramView(), cited_student=[], cited_program=[])
    assert grounded is True
    assert bad == []


def test_is_grounded_mixed_resolves_partially() -> None:
    """If some paths resolve and some don't, grounded=False with the
    failing paths in the bad list."""
    student = StudentView(applicant_summary="real summary", sparse={"values": ["rigor"]})
    program = ProgramView(name="MS-CS")
    grounded, bad = is_grounded(
        student,
        program,
        cited_student=["applicant_summary", "sparse.values.fabricated"],
        cited_program=["name"],
    )
    assert grounded is False
    assert bad == ["student:sparse.values.fabricated"]


# ── Response parsing ──────────────────────────────────────────────────────


def test_parse_response_extracts_three_paragraphs_and_citations() -> None:
    blocks = [
        {
            "type": "tool_use",
            "name": "submit_rationale",
            "input": {
                "para_fit": "fits because X",
                "para_tradeoffs": "tradeoff is Y",
                "para_confidence": "raise by Z",
                "cited_student_fields": ["applicant_summary"],
                "cited_program_fields": ["name"],
            },
        }
    ]
    result = RationaleAgent._parse_response(blocks)
    assert result.para_fit == "fits because X"
    assert result.para_tradeoffs == "tradeoff is Y"
    assert result.para_confidence == "raise by Z"
    assert result.cited_student_fields == ["applicant_summary"]


def test_parse_response_handles_missing_tool_use() -> None:
    """Defensive: forced tool_choice should always return a tool_use, but
    text-only response shouldn't crash."""
    blocks = [{"type": "text", "text": "I refuse."}]
    result = RationaleAgent._parse_response(blocks)
    assert result.para_fit == ""
    assert result.cited_student_fields == []


def test_parse_response_ignores_wrong_tool_name() -> None:
    blocks = [
        {
            "type": "tool_use",
            "name": "wrong_tool",
            "input": {"para_fit": "x"},
        }
    ]
    result = RationaleAgent._parse_response(blocks)
    assert result.para_fit == ""


# ── joined_text ────────────────────────────────────────────────────────────


def test_joined_text_concatenates_three_paragraphs() -> None:
    result = RationaleResult(para_fit="fit", para_tradeoffs="trade", para_confidence="conf")
    text = result.joined_text()
    assert "fit" in text
    assert "trade" in text
    assert "conf" in text
    assert text.count("\n\n") == 2


def test_joined_text_skips_empty_paragraphs() -> None:
    result = RationaleResult(para_fit="only fit", para_tradeoffs="", para_confidence="")
    assert result.joined_text() == "only fit"


def test_joined_text_empty_returns_empty() -> None:
    assert RationaleResult().joined_text() == ""


# ── End-to-end mock-mode call ──────────────────────────────────────────────


def test_generate_in_mock_mode_returns_ungrounded_result() -> None:
    """Mock client returns text-only canned response → parser returns
    empty fields → grounded=True (no citations to validate) but no
    text. Verifies the full call path runs without error."""
    agent = RationaleAgent(client=_mock_client(), max_retries=0)
    result = asyncio.run(
        agent.generate(
            student=StudentView(applicant_summary="hi"),
            program=ProgramView(name="MS-CS"),
            score=ScoreView(fitness=0.8, confidence=0.7),
        )
    )
    assert isinstance(result, RationaleResult)
    # Empty cited paths → grounded=True trivially.
    assert result.grounded is True


def test_generate_with_stub_client_full_path() -> None:
    """Inject a stub that returns a real tool_use; verify full path."""

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
            return LLMResponse(
                text="",
                content_blocks=[
                    {
                        "type": "tool_use",
                        "name": "submit_rationale",
                        "input": {
                            "para_fit": "Fits because the program emphasizes ML research.",
                            "para_tradeoffs": "Cohort is larger than the student prefers.",
                            "para_confidence": "More needs-layer signal would tighten this.",
                            "cited_student_fields": ["applicant_summary"],
                            "cited_program_fields": ["name"],
                        },
                    }
                ],
                model="mock",
            )

    agent = RationaleAgent(client=_StubClient(), max_retries=0)
    result = asyncio.run(
        agent.generate(
            student=StudentView(applicant_summary="real summary"),
            program=ProgramView(name="MS-CS"),
            score=ScoreView(fitness=0.85, confidence=0.7),
        )
    )
    assert result.grounded is True
    assert "ML research" in result.para_fit
    text = result.joined_text()
    assert text.count("\n\n") == 2
    assert result.cost_usd >= 0


def test_generate_retries_on_ungrounded_then_returns_ungrounded() -> None:
    """If the agent cites a fabricated path repeatedly, after max_retries
    we return the last (still-ungrounded) result for inspection."""
    call_count = {"n": 0}

    class _BadStubClient(AIClient):
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
            call_count["n"] += 1
            return LLMResponse(
                text="",
                content_blocks=[
                    {
                        "type": "tool_use",
                        "name": "submit_rationale",
                        "input": {
                            "para_fit": "fit",
                            "para_tradeoffs": "trade",
                            "para_confidence": "conf",
                            "cited_student_fields": ["sparse.values.FABRICATED"],
                            "cited_program_fields": [],
                        },
                    }
                ],
                model="mock",
            )

    agent = RationaleAgent(client=_BadStubClient(), max_retries=1)
    result = asyncio.run(
        agent.generate(
            student=StudentView(),
            program=ProgramView(),
            score=ScoreView(),
        )
    )
    assert result.grounded is False
    assert "student:sparse.values.FABRICATED" in result.ungrounded_paths
    # max_retries=1 → 2 total calls.
    assert call_count["n"] == 2

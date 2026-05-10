"""Phase C1 — A6 Workshop Coach + Haiku-as-judge tests.

Mock-mode coverage. Real-mode (the 100% refusal rate across 20
adversarial fixtures) gets exercised via `make eval-ai-real` once
ANTHROPIC_API_KEY is populated.
"""

from __future__ import annotations

import asyncio

from unipaith.ai.client import AIClient, LLMResponse
from unipaith.ai.coach import (
    CoachFeedback,
    CoachResult,
    EssayDraft,
    JudgeVerdict,
    WorkshopCoach,
    _heuristic_leak_score,
    _word_ngrams,
    get_workshop_coach,
    reset_workshop_coach,
)
from unipaith.ai.tools.workshop_schema import (
    SCHEMA_VERSION,
    SCORE_GENERATION_LEAK_TOOL,
    SUBMIT_ESSAY_FEEDBACK_TOOL,
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


def test_essay_feedback_tool_has_no_revised_text_field() -> None:
    """The schema-level guardrail. Adding a `revised_text` field would
    silently break the C1 contract — this test catches it."""
    props = SUBMIT_ESSAY_FEEDBACK_TOOL["input_schema"]["properties"]
    forbidden = {
        "revised_text",
        "rewritten_paragraph",
        "model_answer",
        "alternative_phrasing",
        "rewrite",
        "revised_intro",
        "revised_conclusion",
    }
    assert not (forbidden & set(props.keys())), (
        f"Schema must NOT have any rewrite surfaces. Found: "
        f"{forbidden & set(props.keys())}"
    )


def test_essay_feedback_tool_required_keys() -> None:
    required = set(SUBMIT_ESSAY_FEEDBACK_TOOL["input_schema"]["required"])
    assert required == {
        "rubric_scores",
        "structural_issues",
        "missing_elements",
        "questions_for_student",
        "prompt_alignment_notes",
    }


def test_rubric_scores_constrained_to_one_to_five() -> None:
    """Out-of-range rubric scores would let the coach smuggle weighting
    into the rubric values. Verify the constraint at schema time."""
    rubric = SUBMIT_ESSAY_FEEDBACK_TOOL["input_schema"]["properties"]["rubric_scores"][
        "properties"
    ]
    for dim, schema in rubric.items():
        assert schema["minimum"] == 1
        assert schema["maximum"] == 5
        assert schema["type"] == "integer", f"{dim} must be integer"


def test_judge_tool_required_keys() -> None:
    required = set(SCORE_GENERATION_LEAK_TOOL["input_schema"]["required"])
    assert required == {"score", "evidence", "passed"}


def test_essay_feedback_field_lengths_capped() -> None:
    """All free-text fields must have maxLength caps to discourage
    smuggling generation into prose."""
    props = SUBMIT_ESSAY_FEEDBACK_TOOL["input_schema"]["properties"]
    issue_props = props["structural_issues"]["items"]["properties"]
    assert issue_props["issue"]["maxLength"] <= 240
    assert issue_props["why_it_matters"]["maxLength"] <= 240
    assert (
        props["missing_elements"]["items"]["maxLength"] <= 240
    ), "missing_elements items unbounded"
    assert props["questions_for_student"]["items"]["maxLength"] <= 280
    assert props["prompt_alignment_notes"]["maxLength"] <= 500


# ── Singleton ──────────────────────────────────────────────────────────────


def test_workshop_coach_singleton_pattern() -> None:
    reset_workshop_coach()
    a = get_workshop_coach()
    b = get_workshop_coach()
    assert a is b
    reset_workshop_coach()
    c = get_workshop_coach()
    assert c is not a


# ── Heuristic leak detector ────────────────────────────────────────────────


def test_heuristic_leak_clean_feedback_returns_zero() -> None:
    feedback = CoachFeedback(
        rubric_scores={
            "specificity": 4,
            "voice": 3,
            "structure": 3,
            "prompt_alignment": 4,
            "evidence": 3,
        },
        structural_issues=[
            {
                "paragraph_index": 0,
                "issue": "The opening generalizes; readers want a concrete moment.",
                "why_it_matters": "Calibration depends on specificity.",
            }
        ],
        missing_elements=[],
        questions_for_student=["What was the moment you noticed your interest shift?"],
        prompt_alignment_notes="Addresses the prompt directly.",
    )
    score, evidence = _heuristic_leak_score(feedback, "draft text")
    assert score == 0
    assert evidence == ""


def test_heuristic_leak_banned_phrase_caught() -> None:
    feedback = CoachFeedback(
        structural_issues=[
            {
                "paragraph_index": 0,
                "issue": "Try writing 'When I first opened a calculus textbook...'",
                "why_it_matters": "More vivid",
            }
        ]
    )
    score, evidence = _heuristic_leak_score(feedback, "irrelevant")
    assert score == 3
    assert "try writing" in evidence.lower()


def test_heuristic_leak_long_verbatim_quote_caught() -> None:
    """An 8+ word verbatim span from the draft inside any field is
    suspicious — could be a quote-then-suggest disguise."""
    draft = (
        "I helped tutor my younger sister with math throughout the "
        "entire summer of two thousand twenty when she was struggling "
        "with algebra and trigonometry, which mattered because she had "
        "missed many classes during a difficult family transition that "
        "year, leaving her significantly behind her peers."
    )
    assert len(draft) > 100  # heuristic only runs on long-enough drafts
    feedback = CoachFeedback(
        structural_issues=[
            {
                "paragraph_index": 0,
                "issue": "I helped tutor my younger sister with math",
                "why_it_matters": "...",
            }
        ]
    )
    score, evidence = _heuristic_leak_score(feedback, draft)
    assert score == 2
    assert "verbatim" in evidence.lower()


def test_heuristic_leak_skips_short_drafts() -> None:
    """Short drafts (≤100 chars) skip the verbatim-quote check — too
    much false-positive risk on tiny inputs."""
    feedback = CoachFeedback(
        structural_issues=[{"paragraph_index": 0, "issue": "short", "why_it_matters": "x"}]
    )
    score, _ = _heuristic_leak_score(feedback, "tiny")
    assert score == 0


def test_word_ngrams_helper() -> None:
    grams = _word_ngrams("the quick brown fox jumps over the lazy dog", n=3)
    assert grams[0] == "the quick brown"
    assert grams[-1] == "the lazy dog"
    # 9 words, n=3 → 7 trigrams.
    assert len(grams) == 7


# ── CoachFeedback.is_well_formed ───────────────────────────────────────────


def test_coach_feedback_well_formed_with_complete_rubric() -> None:
    fb = CoachFeedback(
        rubric_scores={
            "specificity": 4,
            "voice": 3,
            "structure": 4,
            "prompt_alignment": 5,
            "evidence": 3,
        }
    )
    assert fb.is_well_formed()


def test_coach_feedback_not_well_formed_missing_rubric() -> None:
    fb = CoachFeedback()
    assert not fb.is_well_formed()


def test_coach_feedback_not_well_formed_partial_rubric() -> None:
    fb = CoachFeedback(rubric_scores={"specificity": 4})
    assert not fb.is_well_formed()


def test_coach_feedback_not_well_formed_out_of_range() -> None:
    fb = CoachFeedback(
        rubric_scores={
            "specificity": 7,  # invalid
            "voice": 3,
            "structure": 3,
            "prompt_alignment": 3,
            "evidence": 3,
        }
    )
    assert not fb.is_well_formed()


# ── CoachResult.passed ─────────────────────────────────────────────────────


def test_coach_result_passes_when_both_layers_clear() -> None:
    fb = CoachFeedback(
        rubric_scores={
            "specificity": 4,
            "voice": 3,
            "structure": 3,
            "prompt_alignment": 4,
            "evidence": 3,
        }
    )
    verdict = JudgeVerdict(score=0, passed=True)
    assert CoachResult(feedback=fb, verdict=verdict).passed


def test_coach_result_fails_when_judge_fails() -> None:
    fb = CoachFeedback(
        rubric_scores={
            "specificity": 4,
            "voice": 3,
            "structure": 3,
            "prompt_alignment": 4,
            "evidence": 3,
        }
    )
    verdict = JudgeVerdict(score=4, passed=False)
    assert not CoachResult(feedback=fb, verdict=verdict).passed


def test_coach_result_fails_when_feedback_malformed() -> None:
    """Even a passing judge can't save malformed feedback."""
    verdict = JudgeVerdict(score=0, passed=True)
    assert not CoachResult(feedback=CoachFeedback(), verdict=verdict).passed


# ── Response parsing ───────────────────────────────────────────────────────


def test_parse_coach_response_extracts_tool_use() -> None:
    class _R:
        cost_usd = 0.0
        latency_ms = 100
        content_blocks = [
            {
                "type": "tool_use",
                "name": "submit_essay_feedback",
                "input": {
                    "rubric_scores": {
                        "specificity": 4,
                        "voice": 3,
                        "structure": 3,
                        "prompt_alignment": 4,
                        "evidence": 3,
                    },
                    "structural_issues": [
                        {"paragraph_index": 0, "issue": "x", "why_it_matters": "y"}
                    ],
                    "missing_elements": ["z"],
                    "questions_for_student": ["q"],
                    "prompt_alignment_notes": "n",
                },
            }
        ]

    fb = WorkshopCoach._parse_coach_response(_R())
    assert fb.is_well_formed()
    assert fb.structural_issues == [
        {"paragraph_index": 0, "issue": "x", "why_it_matters": "y"}
    ]
    assert fb.questions_for_student == ["q"]


def test_parse_judge_response_inconsistent_score_passes_force_failed() -> None:
    """Coach output where the judge says score=4 but passed=true is
    garbage — we treat it as failed regardless of the passed bit."""

    class _R:
        cost_usd = 0.0
        latency_ms = 50
        content_blocks = [
            {
                "type": "tool_use",
                "name": "score_generation_leak",
                "input": {"score": 4, "passed": True, "evidence": "..."},
            }
        ]

    verdict = WorkshopCoach._parse_judge_response(_R())
    assert verdict.score == 4
    assert verdict.passed is False  # forced — score>1 cannot pass


def test_parse_judge_response_score_zero_with_passed_true_passes() -> None:
    class _R:
        cost_usd = 0.0
        latency_ms = 50
        content_blocks = [
            {
                "type": "tool_use",
                "name": "score_generation_leak",
                "input": {"score": 0, "passed": True, "evidence": "clean"},
            }
        ]

    verdict = WorkshopCoach._parse_judge_response(_R())
    assert verdict.score == 0
    assert verdict.passed is True


def test_parse_judge_response_no_tool_use_fails_closed() -> None:
    class _R:
        cost_usd = 0.0
        latency_ms = 0
        content_blocks = [{"type": "text", "text": "hmm"}]

    verdict = WorkshopCoach._parse_judge_response(_R())
    assert verdict.score == 5
    assert verdict.passed is False


# ── End-to-end mock-mode call ─────────────────────────────────────────────


def test_coach_essay_in_mock_mode_returns_unparseable_result() -> None:
    """Mock client returns text-only canned response → coach returns
    not-well-formed feedback. Verifies the full call path runs without
    error in mock mode."""
    coach = WorkshopCoach(client=_mock_client(), run_judge=False)
    result = asyncio.run(
        coach.coach_essay(draft=EssayDraft(draft_text="hello", prompt_text="why?"))
    )
    assert isinstance(result, CoachResult)
    # Mock returns no tool_use → feedback empty → not well-formed.
    assert not result.feedback.is_well_formed()


def test_coach_essay_with_stub_client_full_path() -> None:
    """Inject a stub that returns valid coach output AND clean judge."""

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
            self.calls = 0

        async def message(self, **kwargs):
            self.calls += 1
            agent = kwargs.get("agent", "")
            if agent == "workshop_coach":
                return LLMResponse(
                    text="",
                    content_blocks=[
                        {
                            "type": "tool_use",
                            "name": "submit_essay_feedback",
                            "input": {
                                "rubric_scores": {
                                    "specificity": 3,
                                    "voice": 3,
                                    "structure": 3,
                                    "prompt_alignment": 4,
                                    "evidence": 3,
                                },
                                "structural_issues": [
                                    {
                                        "paragraph_index": 0,
                                        "issue": "Opens with abstraction; readers want detail.",
                                        "why_it_matters": "Specificity drives credibility.",
                                    }
                                ],
                                "missing_elements": [],
                                "questions_for_student": [
                                    "What was the moment your interest shifted?"
                                ],
                                "prompt_alignment_notes": "Addresses the prompt directly.",
                            },
                        }
                    ],
                    model="mock",
                )
            else:  # workshop_judge
                return LLMResponse(
                    text="",
                    content_blocks=[
                        {
                            "type": "tool_use",
                            "name": "score_generation_leak",
                            "input": {
                                "score": 0,
                                "passed": True,
                                "evidence": "no rewrites detected",
                            },
                        }
                    ],
                    model="mock",
                )

    coach = WorkshopCoach(client=_StubClient())
    result = asyncio.run(
        coach.coach_essay(
            draft=EssayDraft(
                draft_text="My essay is about my interest in CS.",
                prompt_text="Tell us about your background.",
            )
        )
    )
    assert result.passed
    assert result.feedback.is_well_formed()
    assert result.verdict.score == 0


def test_coach_essay_judge_blocks_when_score_high() -> None:
    """Coach returns well-formed feedback but judge sees generation
    leak → result.passed is False."""

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
            agent = kwargs.get("agent", "")
            if agent == "workshop_coach":
                return LLMResponse(
                    text="",
                    content_blocks=[
                        {
                            "type": "tool_use",
                            "name": "submit_essay_feedback",
                            "input": {
                                "rubric_scores": {
                                    "specificity": 3,
                                    "voice": 3,
                                    "structure": 3,
                                    "prompt_alignment": 3,
                                    "evidence": 3,
                                },
                                "structural_issues": [
                                    {
                                        "paragraph_index": 0,
                                        # Subtle leak — short rewrite-shaped suggestion.
                                        "issue": "Replace 'I worked on' with 'I led the design of'",
                                        "why_it_matters": "Stronger framing.",
                                    }
                                ],
                                "missing_elements": [],
                                "questions_for_student": [],
                                "prompt_alignment_notes": "ok",
                            },
                        }
                    ],
                    model="mock",
                )
            else:
                return LLMResponse(
                    text="",
                    content_blocks=[
                        {
                            "type": "tool_use",
                            "name": "score_generation_leak",
                            "input": {
                                "score": 3,
                                "passed": False,
                                "evidence": "rewrite suggestion in issue field",
                                "category": "rewrite_in_issue",
                            },
                        }
                    ],
                    model="mock",
                )

    coach = WorkshopCoach(client=_StubClient())
    result = asyncio.run(
        coach.coach_essay(
            draft=EssayDraft(
                draft_text="I worked on a project last summer.",
                prompt_text="Describe a project.",
            )
        )
    )
    assert not result.passed
    assert result.verdict.score == 3
    assert result.verdict.category == "rewrite_in_issue"


def test_coach_essay_heuristic_skips_judge_when_obvious_leak() -> None:
    """When the heuristic catches a banned phrase, we don't waste
    tokens on the judge — we fail fast with the heuristic verdict."""

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
            self.calls = 0

        async def message(self, **kwargs):
            self.calls += 1
            agent = kwargs.get("agent", "")
            if agent == "workshop_coach":
                return LLMResponse(
                    text="",
                    content_blocks=[
                        {
                            "type": "tool_use",
                            "name": "submit_essay_feedback",
                            "input": {
                                "rubric_scores": {
                                    "specificity": 3,
                                    "voice": 3,
                                    "structure": 3,
                                    "prompt_alignment": 3,
                                    "evidence": 3,
                                },
                                "structural_issues": [
                                    {
                                        "paragraph_index": 0,
                                        "issue": (
                                            "Try writing this with more specific "
                                            "details about that project."
                                        ),
                                        "why_it_matters": "...",
                                    }
                                ],
                                "missing_elements": [],
                                "questions_for_student": [],
                                "prompt_alignment_notes": "ok",
                            },
                        }
                    ],
                    model="mock",
                )
            return LLMResponse(text="", content_blocks=[], model="mock")

    client = _StubClient()
    coach = WorkshopCoach(client=client)
    result = asyncio.run(
        coach.coach_essay(draft=EssayDraft(draft_text="x", prompt_text="y"))
    )
    assert not result.passed
    assert "try writing" in result.verdict.evidence.lower()
    # Judge was NOT called — heuristic short-circuited.
    assert client.calls == 1

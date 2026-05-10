"""Phase C2 — Interview + Test-Prep coach tests."""

from __future__ import annotations

import asyncio

from unipaith.ai.client import AIClient, LLMResponse
from unipaith.ai.coach import (
    InterviewCoachResult,
    InterviewFeedback,
    InterviewResponse,
    TestPrepCoachResult,
    TestPrepContext,
    TestPrepFeedback,
    WorkshopCoach,
    _heuristic_leak_score_interview,
    _heuristic_leak_score_test_prep,
)
from unipaith.ai.tools.workshop_schema import (
    SUBMIT_INTERVIEW_FEEDBACK_TOOL,
    SUBMIT_TEST_PREP_GUIDANCE_TOOL,
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


def test_interview_tool_no_revised_response_field() -> None:
    props = SUBMIT_INTERVIEW_FEEDBACK_TOOL["input_schema"]["properties"]
    forbidden = {
        "revised_response",
        "sample_answer",
        "suggested_phrasing",
        "alternative_phrasing",
        "model_response",
    }
    assert not (forbidden & set(props.keys())), (
        f"Interview tool must NOT have rewrite surfaces: {forbidden & set(props.keys())}"
    )


def test_interview_tool_required_keys() -> None:
    required = set(SUBMIT_INTERVIEW_FEEDBACK_TOOL["input_schema"]["required"])
    assert required == {
        "rubric_scores",
        "response_issues",
        "missing_elements",
        "clarifying_questions",
        "delivery_notes",
    }


def test_test_prep_tool_no_practice_or_sample_field() -> None:
    props = SUBMIT_TEST_PREP_GUIDANCE_TOOL["input_schema"]["properties"]
    forbidden = {
        "practice_problems",
        "sample_essay",
        "vocabulary_list",
        "formula_sheet",
        "answer_key",
    }
    assert not (forbidden & set(props.keys()))


def test_test_prep_tool_required_keys() -> None:
    required = set(SUBMIT_TEST_PREP_GUIDANCE_TOOL["input_schema"]["required"])
    assert required == {
        "rubric_scores",
        "section_diagnosis",
        "priorities",
        "resource_categories",
        "timeline_notes",
    }


def test_interview_rubric_constrained_to_one_to_five() -> None:
    rubric = SUBMIT_INTERVIEW_FEEDBACK_TOOL["input_schema"]["properties"][
        "rubric_scores"
    ]["properties"]
    for dim, schema in rubric.items():
        assert schema["minimum"] == 1
        assert schema["maximum"] == 5


def test_test_prep_rubric_constrained_to_one_to_five() -> None:
    rubric = SUBMIT_TEST_PREP_GUIDANCE_TOOL["input_schema"]["properties"][
        "rubric_scores"
    ]["properties"]
    for dim, schema in rubric.items():
        assert schema["minimum"] == 1
        assert schema["maximum"] == 5


# ── Feedback well-formed checks ────────────────────────────────────────────


def test_interview_feedback_well_formed_with_complete_rubric() -> None:
    fb = InterviewFeedback(
        rubric_scores={
            "directness": 4,
            "specificity": 3,
            "structure": 4,
            "evidence": 3,
            "delivery": 3,
        }
    )
    assert fb.is_well_formed()


def test_interview_feedback_partial_rubric_not_well_formed() -> None:
    assert not InterviewFeedback(rubric_scores={"directness": 4}).is_well_formed()


def test_test_prep_feedback_well_formed_with_complete_rubric() -> None:
    fb = TestPrepFeedback(
        rubric_scores={
            "diagnostic_clarity": 4,
            "timeline_realism": 3,
            "resource_diversity": 3,
            "weakness_focus": 4,
            "review_discipline": 3,
        }
    )
    assert fb.is_well_formed()


def test_test_prep_feedback_out_of_range_not_well_formed() -> None:
    fb = TestPrepFeedback(
        rubric_scores={
            "diagnostic_clarity": 7,
            "timeline_realism": 3,
            "resource_diversity": 3,
            "weakness_focus": 4,
            "review_discipline": 3,
        }
    )
    assert not fb.is_well_formed()


# ── Heuristic detectors ────────────────────────────────────────────────────


def test_interview_heuristic_clean_returns_zero() -> None:
    fb = InterviewFeedback(
        response_issues=[
            {"issue": "Hedging language opens the answer", "why_it_matters": "..."}
        ]
    )
    score, _ = _heuristic_leak_score_interview(fb, "short response")
    assert score == 0


def test_interview_heuristic_catches_banned_phrase() -> None:
    fb = InterviewFeedback(
        response_issues=[
            {"issue": "Try writing 'I led the project' instead.", "why_it_matters": "..."}
        ]
    )
    score, evidence = _heuristic_leak_score_interview(fb, "long enough response " * 20)
    assert score == 3
    assert "try writing" in evidence.lower()


def test_test_prep_heuristic_catches_brand_recommendation() -> None:
    fb = TestPrepFeedback(
        priorities=["I recommend Manhattan Prep books for quant drilling"]
    )
    score, evidence = _heuristic_leak_score_test_prep(fb)
    assert score == 3
    assert "manhattan" in evidence.lower()


def test_test_prep_heuristic_catches_vocab_list() -> None:
    fb = TestPrepFeedback(
        timeline_notes="Vocabulary list: aberrant, abjure, abstemious..."
    )
    score, evidence = _heuristic_leak_score_test_prep(fb)
    assert score == 3
    assert "vocabulary list" in evidence.lower()


def test_test_prep_heuristic_clean_returns_zero() -> None:
    fb = TestPrepFeedback(
        timeline_notes="6-week prep is achievable for a 5-point gap with disciplined review.",
        priorities=["High-frequency vocabulary acquisition (any standard list)"],
    )
    score, _ = _heuristic_leak_score_test_prep(fb)
    assert score == 0


# ── End-to-end mock ───────────────────────────────────────────────────────


def test_coach_interview_mock_mode_runs_without_error() -> None:
    coach = WorkshopCoach(client=_mock_client(), run_judge=False)
    result = asyncio.run(
        coach.coach_interview(
            response=InterviewResponse(
                response_text="I work at a startup.",
                question_text="Tell me about yourself.",
            )
        )
    )
    assert isinstance(result, InterviewCoachResult)
    # Mock returns no tool_use → not well-formed.
    assert not result.feedback.is_well_formed()


def test_coach_test_prep_mock_mode_runs_without_error() -> None:
    coach = WorkshopCoach(client=_mock_client(), run_judge=False)
    result = asyncio.run(
        coach.coach_test_prep(
            context=TestPrepContext(test_type="GRE", target_score="325", weeks_to_test=8)
        )
    )
    assert isinstance(result, TestPrepCoachResult)
    assert not result.feedback.is_well_formed()


def test_coach_interview_with_stub_full_path() -> None:
    class _Stub(AIClient):
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
                            "name": "submit_interview_feedback",
                            "input": {
                                "rubric_scores": {
                                    "directness": 3,
                                    "specificity": 3,
                                    "structure": 3,
                                    "evidence": 3,
                                    "delivery": 4,
                                },
                                "response_issues": [
                                    {
                                        "issue": (
                                            "Opening hedges twice before stating role."
                                        ),
                                        "why_it_matters": (
                                            "Interviewer calibrates confidence on opening."
                                        ),
                                    }
                                ],
                                "missing_elements": [],
                                "clarifying_questions": [],
                                "delivery_notes": ["Three uses of 'kind of' in 90 seconds."],
                            },
                        }
                    ],
                    model="mock",
                )
            return LLMResponse(
                text="",
                content_blocks=[
                    {
                        "type": "tool_use",
                        "name": "score_generation_leak",
                        "input": {"score": 0, "passed": True, "evidence": "clean"},
                    }
                ],
                model="mock",
            )

    coach = WorkshopCoach(client=_Stub())
    result = asyncio.run(
        coach.coach_interview(
            response=InterviewResponse(
                response_text="kind of, I work at a startup, kind of as an engineer",
                question_text="Tell me about yourself",
            )
        )
    )
    assert result.passed
    assert result.feedback.is_well_formed()


def test_coach_test_prep_with_stub_full_path() -> None:
    class _Stub(AIClient):
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
                            "name": "submit_test_prep_guidance",
                            "input": {
                                "rubric_scores": {
                                    "diagnostic_clarity": 4,
                                    "timeline_realism": 3,
                                    "resource_diversity": 3,
                                    "weakness_focus": 4,
                                    "review_discipline": 3,
                                },
                                "section_diagnosis": [
                                    {
                                        "section": "GRE Quant",
                                        "observation": (
                                            "Q-150 with 6 weeks to test suggests "
                                            "data-interpretation drag."
                                        ),
                                    }
                                ],
                                "priorities": [
                                    "Section-targeted drilling on data interpretation",
                                    "Untimed full-length practice",
                                ],
                                "resource_categories": [
                                    "official practice tests",
                                    "section-targeted drilling",
                                ],
                                "timeline_notes": (
                                    "5-point gap in 6 weeks is achievable with "
                                    "disciplined review."
                                ),
                            },
                        }
                    ],
                    model="mock",
                )
            return LLMResponse(
                text="",
                content_blocks=[
                    {
                        "type": "tool_use",
                        "name": "score_generation_leak",
                        "input": {"score": 0, "passed": True, "evidence": "clean"},
                    }
                ],
                model="mock",
            )

    coach = WorkshopCoach(client=_Stub())
    result = asyncio.run(
        coach.coach_test_prep(
            context=TestPrepContext(
                test_type="GRE",
                target_score="325",
                current_diagnostic={"Quant": 150, "Verbal": 158},
                weeks_to_test=6,
            )
        )
    )
    assert result.passed
    assert result.feedback.is_well_formed()
    assert "GRE Quant" == result.feedback.section_diagnosis[0]["section"]

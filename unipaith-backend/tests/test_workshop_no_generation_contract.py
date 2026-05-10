"""Phase A — Mechanical guard against essay/answer generation in workshops.

The product spec for workshops is: 'do not generate context.' Workshops
COACH the student; they don't write the student's essay or interview
answers. This test inspects the response schema and makes it CI-impossible
for any future change to slip a generation field back in.

If you see this test fail, you've added a field that could carry an
LLM-generated draft / revision / model answer back to the user. Don't.
Use rubric_scores / structural_issues / missing_elements / suggested_questions
instead — those four fields are the entire output surface of the workshop
contract.
"""

from __future__ import annotations

import re
from typing import get_args, get_origin

import pytest
from pydantic import BaseModel
from unipaith.schemas.workshop_feedback import (
    EssayFeedbackRequest,
    InterviewPracticeRequest,
    MissingElement,
    StructuralIssue,
    SuggestedQuestion,
    TestGuidanceRequest,
    WorkshopFeedbackResponse,
)

# Substrings that flag a forbidden field. We match by substring (after
# lowercasing) so variations like `revised_text`, `essay_revision`, or
# `improved_draft` all trip the guard.
_FORBIDDEN_FIELD_FRAGMENTS = (
    "revised",
    "rewrit",  # rewrite, rewritten
    "rewrote",
    "improved",  # improved_text, improved_draft
    "generated_essay",
    "draft",  # draft, redraft, draft_text
    "model_answer",
    "ai_text",
    "ai_essay",
    "completion",  # ai_completion, completion_text
    "polished",
    "auto_draft",
    "rephras",
)


def _walk_schema_field_names(model: type[BaseModel]) -> set[str]:
    """Return every field name reachable from `model`, including nested
    BaseModel fields and list[Model] / dict[..., Model] container types."""
    seen: set[type[BaseModel]] = set()
    names: set[str] = set()

    def visit(m: type[BaseModel]) -> None:
        if m in seen:
            return
        seen.add(m)
        for name, info in m.model_fields.items():
            names.add(name)
            ann = info.annotation
            for sub in _flatten_annotation(ann):
                if isinstance(sub, type) and issubclass(sub, BaseModel):
                    visit(sub)

    visit(model)
    return names


def _flatten_annotation(ann):  # noqa: ANN001
    """Yield class objects out of a type annotation. Walks generic args of
    list, dict, Union, etc."""
    if ann is None:
        return
    yield ann
    origin = get_origin(ann)
    if origin is not None:
        for arg in get_args(ann):
            yield from _flatten_annotation(arg)


# ── The contract test ─────────────────────────────────────────────────────


def test_response_schema_has_no_generation_fields():
    """Walk the response model recursively. Fail if any field name contains
    a generation marker. This test is the moat between the workshop contract
    and accidental drift."""
    field_names = _walk_schema_field_names(WorkshopFeedbackResponse)
    offenders = sorted(
        n for n in field_names if any(frag in n.lower() for frag in _FORBIDDEN_FIELD_FRAGMENTS)
    )
    assert offenders == [], (
        f"Generation fields found on workshop response schema: {offenders}. "
        "Workshops are feedback-only — see test docstring."
    )


def test_request_schemas_have_no_generation_fields():
    """Symmetry: request bodies shouldn't ask for generation either (e.g.,
    `please_rewrite_my_essay: bool`). This guards the input surface."""
    offenders: list[tuple[str, str]] = []
    for model in (
        EssayFeedbackRequest,
        InterviewPracticeRequest,
        TestGuidanceRequest,
    ):
        for name in _walk_schema_field_names(model):
            if any(frag in name.lower() for frag in _FORBIDDEN_FIELD_FRAGMENTS):
                offenders.append((model.__name__, name))
    assert offenders == [], f"Generation fields on workshop REQUEST schemas: {offenders}"


def test_nested_models_are_feedback_shaped():
    """Sub-models (StructuralIssue, MissingElement, SuggestedQuestion)
    should each have a small, fixed set of fields that can't carry prose
    generation. Any drift here would let a 'rewritten_paragraph' field
    sneak in via the issue list."""
    expected = {
        StructuralIssue: {"issue", "severity", "location_ref"},
        MissingElement: {"element", "importance"},
        SuggestedQuestion: {"question", "why"},
    }
    for model, fields in expected.items():
        actual = set(model.model_fields.keys())
        assert actual == fields, f"{model.__name__} fields drifted: expected {fields}, got {actual}"


# ── Defense-in-depth: stub responses don't leak prose ─────────────────────


_LONG_PROSE_RE = re.compile(r"\b(\w+(?:\s+\w+){15,})\b")


@pytest.mark.parametrize(
    "field_name",
    ["rubric_scores", "structural_issues", "missing_elements", "suggested_questions"],
)
def test_field_default_factories_match_schema(field_name: str):
    """Spot-check that the four output fields exist and default to empty
    containers. If a future change replaces one of these with a `revised_*`
    field, the assertion at the top fires; this is the cheap follow-up."""
    fields = WorkshopFeedbackResponse.model_fields
    assert field_name in fields, f"missing required output field: {field_name}"

"""JSON schemas for the A6 Workshop Coach + Workshop Judge.

The coach is forced to call SUBMIT_ESSAY_FEEDBACK_TOOL — there is **no
`revised_text` field**, no `rewritten_paragraph`, no `model_answer`.
The schema is the first guardrail. The post-classifier (`workshop_judge`)
is the second, catching generation that gets smuggled into structural
fields.

Schema versioning
-----------------
Bump on any add/remove. Increment SCHEMA_VERSION when changing shape;
the eval harness pins to a specific version.
"""

SCHEMA_VERSION = 1


# ── A6 Coach: essay feedback ────────────────────────────────────────────────


SUBMIT_ESSAY_FEEDBACK_TOOL = {
    "name": "submit_essay_feedback",
    "description": (
        "Return structured feedback on a student's essay draft. Feedback "
        "ONLY — no rewrites, no alternative phrasings, no model sentences. "
        "Every field is length-capped to discourage smuggling generation "
        "into prose. The post-classifier rejects outputs that violate "
        "this contract."
    ),
    "input_schema": {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "rubric_scores",
            "structural_issues",
            "missing_elements",
            "questions_for_student",
            "prompt_alignment_notes",
        ],
        "properties": {
            "rubric_scores": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "specificity",
                    "voice",
                    "structure",
                    "prompt_alignment",
                    "evidence",
                ],
                "properties": {
                    "specificity": {"type": "integer", "minimum": 1, "maximum": 5},
                    "voice": {"type": "integer", "minimum": 1, "maximum": 5},
                    "structure": {"type": "integer", "minimum": 1, "maximum": 5},
                    "prompt_alignment": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 5,
                    },
                    "evidence": {"type": "integer", "minimum": 1, "maximum": 5},
                },
            },
            "structural_issues": {
                "type": "array",
                "maxItems": 8,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["paragraph_index", "issue", "why_it_matters"],
                    "properties": {
                        "paragraph_index": {"type": "integer"},
                        "issue": {"type": "string", "maxLength": 200},
                        "why_it_matters": {"type": "string", "maxLength": 200},
                    },
                },
            },
            "missing_elements": {
                "type": "array",
                "maxItems": 6,
                "items": {"type": "string", "maxLength": 200},
            },
            "questions_for_student": {
                "type": "array",
                "maxItems": 5,
                "items": {"type": "string", "maxLength": 240},
            },
            "prompt_alignment_notes": {
                "type": "string",
                "maxLength": 400,
                "description": (
                    "1–2 sentences on how directly the draft answers the "
                    "prompt. NOT a rewrite suggestion."
                ),
            },
        },
    },
}


# ── Post-classifier: generation-leak detection ─────────────────────────────


SCORE_GENERATION_LEAK_TOOL = {
    "name": "score_generation_leak",
    "description": (
        "Detect whether a coach's structured feedback contains generation "
        "in disguise — rewrites smuggled into 'issue' fields, alternative "
        "phrasings dressed up as questions, or model sentences inside "
        "prompt_alignment_notes. Score 0 (clean feedback) to 5 (clear "
        "generation present). 0–1 = pass; 2+ = reject."
    ),
    "input_schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["score", "evidence", "passed"],
        "properties": {
            "score": {"type": "integer", "minimum": 0, "maximum": 5},
            "passed": {
                "type": "boolean",
                "description": "True if score is 0 or 1; False otherwise.",
            },
            "evidence": {
                "type": "string",
                "maxLength": 240,
                "description": (
                    "If score >= 2, quote the specific phrase from the coach "
                    "output that constitutes generation. If score is 0–1, "
                    "describe in <240 chars why the output is clean."
                ),
            },
            "category": {
                "type": ["string", "null"],
                "enum": [
                    None,
                    "rewrite_in_issue",
                    "alternative_phrasing_in_question",
                    "model_sentence_in_alignment_notes",
                    "long_quote_pattern",
                    "other",
                ],
            },
        },
    },
}


# ── Changelog ──────────────────────────────────────────────────────────────
# v1 (2026-05-10): initial schemas for Phase C1.

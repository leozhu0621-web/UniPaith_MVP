"""JSON schema for the DraftSummarizerForReview (`45` §14, Opus) tool call.

The agent is forced to call `submit_review_summary`. Output maps to the
`AIPacketSummary` row + the institution review-workspace UI (spec 32 §2):
an overall summary, evidence-linked strengths/concerns, per-rubric-criterion
assessments, a recommended score, and a confidence level. Spec 45 §14's
`signal_strengths` / `signal_weaknesses` / `rubric_aligned_notes` are
realized as `strengths` / `concerns` / `criterion_assessments` so the
existing packet model + frontend consume them unchanged.
"""

SCHEMA_VERSION = 1


SUBMIT_REVIEW_SUMMARY_TOOL = {
    "name": "submit_review_summary",
    "description": (
        "Return a rubric-aligned admissions review summary for one applicant. "
        "Every strength/concern and every criterion assessment must cite a "
        "real field from the provided applicant packet via source_field / "
        "evidence. Never invent credentials. Feedback only — never a final "
        "decision; the reviewer decides."
    ),
    "input_schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["overall_summary", "strengths", "concerns", "confidence_level"],
        "properties": {
            "overall_summary": {
                "type": "string",
                "minLength": 40,
                "maxLength": 1600,
                "description": "3-6 sentence holistic summary of the applicant.",
            },
            "strengths": {
                "type": "array",
                "maxItems": 5,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["text", "source_field", "evidence"],
                    "properties": {
                        "text": {"type": "string", "maxLength": 300},
                        "source_field": {"type": "string", "maxLength": 80},
                        "evidence": {"type": "string", "maxLength": 300},
                    },
                },
            },
            "concerns": {
                "type": "array",
                "maxItems": 5,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["text", "source_field", "evidence"],
                    "properties": {
                        "text": {"type": "string", "maxLength": 300},
                        "source_field": {"type": "string", "maxLength": 80},
                        "evidence": {"type": "string", "maxLength": 300},
                    },
                },
            },
            "criterion_assessments": {
                "type": "array",
                "maxItems": 12,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["criterion_name", "assessment"],
                    "properties": {
                        "criterion_name": {"type": "string", "maxLength": 120},
                        "score": {"type": ["number", "null"]},
                        "assessment": {"type": "string", "maxLength": 600},
                        "evidence": {
                            "type": "array",
                            "maxItems": 6,
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "required": ["field", "value"],
                                "properties": {
                                    "field": {"type": "string", "maxLength": 80},
                                    "value": {"type": "string", "maxLength": 300},
                                    "citation": {"type": "string", "maxLength": 200},
                                },
                            },
                        },
                    },
                },
            },
            "recommended_score": {
                "type": ["number", "null"],
                "description": "0-10 holistic recommendation, or null if abstaining.",
            },
            "confidence_level": {
                "type": "string",
                "enum": ["high", "medium", "low"],
            },
        },
    },
}


# ── Changelog ──────────────────────────────────────────────────────────────
# v1 (2026-05-30): initial schema for spec 06 §2 review-summary wiring.

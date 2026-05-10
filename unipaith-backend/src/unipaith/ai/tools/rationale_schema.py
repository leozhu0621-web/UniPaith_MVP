"""JSON schema for the A5 Rationale agent's `submit_rationale` tool call.

The agent is forced to call this single tool. Three text fields + two
citation arrays. The runtime validates that every cited path resolves
to a non-empty value in the input (groundedness check).

Schema versioning
-----------------
Bumped on any field add/remove. Citation paths use dot-notation:
  - `applicant_summary`           — top-level student field
  - `sparse.values.intellectual_rigor` — student sparse_features list/dict
  - `description`                 — top-level program field
  - `sparse.support_signals.alumni_network` — program sparse dict key

The validator in `unipaith.ai.rationale.is_grounded` walks each path
and asserts the value is non-empty.
"""

SCHEMA_VERSION = 1


SUBMIT_RATIONALE_TOOL = {
    "name": "submit_rationale",
    "description": (
        "Return a 3-paragraph rationale (~250 words total) explaining why "
        "this program fits this student, what tradeoffs exist, and what "
        "would raise the confidence. Every claim must cite a real input "
        "field via cited_student_fields / cited_program_fields. "
        "Hallucinated paths cause regeneration."
    ),
    "input_schema": {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "para_fit",
            "para_tradeoffs",
            "para_confidence",
            "cited_student_fields",
            "cited_program_fields",
        ],
        "properties": {
            "para_fit": {
                "type": "string",
                "minLength": 30,
                "maxLength": 800,
                "description": (
                    "Why this program fits — cite specific student × "
                    "program field overlaps. ~80 words."
                ),
            },
            "para_tradeoffs": {
                "type": "string",
                "minLength": 30,
                "maxLength": 800,
                "description": (
                    "Tradeoffs / weak spots. If the fit is genuinely "
                    "clean, say so briefly. ~80 words."
                ),
            },
            "para_confidence": {
                "type": "string",
                "minLength": 30,
                "maxLength": 800,
                "description": (
                    "What would raise the confidence — frame around the "
                    "confidence components, not fitness. ~80 words."
                ),
            },
            "cited_student_fields": {
                "type": "array",
                "items": {"type": "string", "maxLength": 200},
                "description": (
                    "Dot-notation paths into the student input. Every "
                    "field referenced in any of the three paragraphs must "
                    "appear here."
                ),
            },
            "cited_program_fields": {
                "type": "array",
                "items": {"type": "string", "maxLength": 200},
                "description": "Dot-notation paths into the program input.",
            },
        },
    },
}


# ── Changelog ──────────────────────────────────────────────────────────────
# v1 (2026-05-10): initial schema for Phase B2.

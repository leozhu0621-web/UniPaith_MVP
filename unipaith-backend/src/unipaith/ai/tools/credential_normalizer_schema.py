"""JSON schema for CredentialNormalizer (Spec 38 §5 / extends 45 §19).

The agent receives the structured grading metadata an admissions officer would
read off a foreign transcript (raw GPA, the grading system, the country, the
degree level) — never raw OCR of the document — and returns a normalized GPA on
the program's scale plus a short interpretation. The calling service always has
the deterministic grading-scale mapper to fall back on, so a malformed/empty
tool call is non-fatal.
"""

SCHEMA_VERSION = 1

SUBMIT_NORMALIZATION_TOOL = {
    "name": "submit_normalization",
    "description": (
        "Map a foreign academic grade to the program's GPA scale for an "
        "admissions reviewer. Use the provided grading system, country, and raw "
        "value. Be conservative; never inflate. The reviewer sees both the raw "
        "and your normalized value and makes the final call."
    ),
    "input_schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["normalized_gpa", "source_scale", "confidence"],
        "properties": {
            "normalized_gpa": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 4.0,
                "description": "The grade on a 4.0 scale.",
            },
            "source_scale": {
                "type": "string",
                "maxLength": 60,
                "description": "Human-readable source the value came from, e.g. '85/100 (China)'.",
            },
            "course_map_note": {
                "type": "string",
                "maxLength": 400,
                "description": "One or two sentences on the grading system / any caveat.",
            },
            "confidence": {
                "type": "string",
                "enum": ["high", "medium", "low"],
                "description": "Confidence in the mapping.",
            },
        },
    },
}

# ── Changelog ──────────────────────────────────────────────────────────────
# v1 (2026-06-01): initial schema for Spec 38 CredentialNormalizer.

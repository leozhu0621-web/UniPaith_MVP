"""JSON schema for DocumentParseTriage (Spec 24 §9 / 45 §19).

The agent receives only *aggregate* validation counts (never the uploaded PII
rows) and returns a short human-readable triage of parse health plus a
recommended next action. The calling DatasetService always has the
deterministic rule-based report to fall back on, so a malformed/empty tool call
is non-fatal.
"""

SCHEMA_VERSION = 1

SUBMIT_TRIAGE_TOOL = {
    "name": "submit_triage",
    "description": (
        "Summarize the parse/validation health of an uploaded institution "
        "dataset for a non-technical admissions user. Base the assessment only "
        "on the provided aggregate counts. Be concise and actionable; never "
        "invent specific row contents."
    ),
    "input_schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["status", "summary", "recommended_action"],
        "properties": {
            "status": {
                "type": "string",
                "enum": ["clean", "minor_issues", "major_issues", "unparseable"],
                "description": "Overall parse health.",
            },
            "summary": {
                "type": "string",
                "maxLength": 400,
                "description": "One or two plain-language sentences for the uploader.",
            },
            "recommended_action": {
                "type": "string",
                "enum": ["proceed", "review_then_proceed", "fix_and_reupload"],
                "description": "What the uploader should do next.",
            },
        },
    },
}

# ── Changelog ──────────────────────────────────────────────────────────────
# v1 (2026-05-31): initial schema for Spec 24 DocumentParseTriage.

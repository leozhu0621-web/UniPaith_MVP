"""JSON schema for the IdentitySummaryAgent's `submit_identity_summary` tool."""

SCHEMA_VERSION = 1

SUBMIT_IDENTITY_SUMMARY_TOOL = {
    "name": "submit_identity_summary",
    "description": (
        "Return a 3–5 sentence (≤180 word) paragraph synthesizing the "
        "student's identity layer (core_values + worldview + "
        "self_awareness). Second person, plain English, evidence-cited "
        "when present, no fabrication."
    ),
    "input_schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["summary"],
        "properties": {
            "summary": {
                "type": "string",
                "minLength": 1,
                "maxLength": 1500,
                "description": (
                    "The paragraph that will sit at the top of the student's Identity tab."
                ),
            },
        },
    },
}

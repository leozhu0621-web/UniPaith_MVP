"""JSON schema for the InboundIntentClassifier's `submit_inbound_intent` tool.

Spec 29 §8 / §14 — output: a *suggested* reason code (+ confidence + short
rationale) for a new inbound applicant message. Suggestion-only: it never
auto-assigns or auto-sends; staff confirms (§14 — ship as a suggestion first).
"""

SCHEMA_VERSION = 1

# Mirror the §4 reason-code vocabulary.
_REASON_CODES = [
    "request_document",
    "request_clarification",
    "interview_invite",
    "status_update",
    "general_reply",
    "decision_notice",
]

SUBMIT_INBOUND_INTENT_TOOL = {
    "name": "submit_inbound_intent",
    "description": (
        "Classify a new inbound applicant message and suggest the reason code "
        "the staff reply will most likely use, with a confidence and a one-line "
        "rationale. This is a suggestion staff can accept or override — never a "
        "decision."
    ),
    "input_schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["reason_code", "confidence"],
        "properties": {
            "reason_code": {
                "type": "string",
                "enum": _REASON_CODES,
                "description": "The most likely reason code for the staff reply.",
            },
            "confidence": {
                "type": "number",
                "minimum": 0,
                "maximum": 1,
                "description": "How confident the classification is (0–1).",
            },
            "rationale": {
                "type": "string",
                "maxLength": 240,
                "description": "One short line explaining the suggested reason code.",
            },
        },
    },
}

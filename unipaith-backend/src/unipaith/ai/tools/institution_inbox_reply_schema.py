"""JSON schema for InstitutionReplyDrafter (Spec 29 / 45)."""

SUBMIT_INSTITUTION_REPLY_TOOL = {
    "name": "submit_institution_reply",
    "description": "Submit a draft reply for an admissions officer to send to an applicant.",
    "input_schema": {
        "type": "object",
        "properties": {
            "draft": {"type": "string", "description": "Primary reply body (plain text)."},
            "tone": {
                "type": "string",
                "enum": ["professional", "warm", "concise"],
            },
            "length": {"type": "string", "enum": ["short", "medium", "long"]},
            "alternate_drafts": {
                "type": "array",
                "items": {"type": "string"},
                "maxItems": 2,
            },
            "suggested_reason_code": {
                "type": "string",
                "enum": [
                    "request_document",
                    "request_clarification",
                    "interview_invite",
                    "status_update",
                    "general_reply",
                    "decision_notice",
                ],
            },
        },
        "required": ["draft"],
    },
}

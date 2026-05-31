"""JSON schema for the InboxReplyDrafter's `submit_inbox_reply` tool.

Spec 45 §13 — output: ``{draft, tone, length, alternate_drafts (max 2)}``.
The student edits the draft before sending; it is never sent automatically.
"""

SCHEMA_VERSION = 1

SUBMIT_INBOX_REPLY_TOOL = {
    "name": "submit_inbox_reply",
    "description": (
        "Return a suggested reply for the student to an admissions inbox "
        "thread, plus up to two alternate-tone drafts. The student reviews "
        "and edits before sending — never claim an action was taken (e.g. "
        "'I have attached…', 'I already sent…') unless the thread shows it. "
        "First person, addressed to the admissions contact."
    ),
    "input_schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["draft", "tone", "length"],
        "properties": {
            "draft": {
                "type": "string",
                "minLength": 1,
                "maxLength": 2000,
                "description": (
                    "The primary suggested reply. Plain text, ready for the "
                    "student to edit and send."
                ),
            },
            "tone": {
                "type": "string",
                "enum": ["professional", "warm", "concise"],
                "description": "The register of the primary draft.",
            },
            "length": {
                "type": "string",
                "enum": ["short", "medium", "long"],
                "description": "Approximate length of the primary draft.",
            },
            "alternate_drafts": {
                "type": "array",
                "maxItems": 2,
                "items": {"type": "string", "minLength": 1, "maxLength": 2000},
                "description": (
                    "Up to two alternate drafts in different tones (e.g. a "
                    "warmer and a more concise version) for the student to "
                    "choose between."
                ),
            },
        },
    },
}

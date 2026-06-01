"""JSON schema for the InstitutionReplyDrafter's `submit_institution_reply` tool.

Spec 29 §8 / 45 — output: ``{draft, tone, length, alternate_drafts (max 2)}``.
The staff member edits the draft before sending; it is never sent
automatically. The draft is written **as the admissions officer**, addressed to
the applicant, and is shaped by the thread's reason code.
"""

SCHEMA_VERSION = 1

SUBMIT_INSTITUTION_REPLY_TOOL = {
    "name": "submit_institution_reply",
    "description": (
        "Return a suggested reply for an admissions staff member to send to an "
        "applicant in the institution inbox, plus up to two alternate-tone "
        "drafts. Staff reviews and edits before sending — never claim an action "
        "was taken on the institution's behalf (e.g. 'I have updated your "
        "file…') unless the thread shows it. Written in first person as the "
        "admissions contact, addressed to the applicant by name when known."
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
                    "The primary suggested reply. Plain text, ready for staff "
                    "to edit and send. Shaped by the reason code: request the "
                    "specific missing item, ask the precise clarification, "
                    "extend the interview invite, or give the status update."
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
                    "warmer and a more concise version) for staff to choose "
                    "between."
                ),
            },
        },
    },
}

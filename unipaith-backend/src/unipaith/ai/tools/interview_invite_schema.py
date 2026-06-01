"""JSON schema for the InterviewInviteDrafter's `submit_interview_invite` tool.

Spec 33 §9 — output: ``{draft, tone, length}``. The staff member edits the
draft before the invite is sent; it is never sent automatically. The draft is
written **as the admissions officer**, addressed to the applicant, and is shaped
by the interview type (live → propose the offered slots; recorded_async /
technical_assessment → state the window deadline).
"""

SCHEMA_VERSION = 1

SUBMIT_INTERVIEW_INVITE_TOOL = {
    "name": "submit_interview_invite",
    "description": (
        "Return a suggested interview-invite message for an admissions staff "
        "member to send to an applicant. Staff reviews and edits before "
        "sending — never claim the interview is already booked. Written in "
        "first person as the admissions contact, addressed to the applicant by "
        "name when known. Shaped by interview type: for live interviews invite "
        "them to pick one of the offered time slots; for recorded_async or "
        "technical_assessment state the submission window and what to do; for "
        "third_party_platform point them to the external platform link."
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
                    "The suggested invite body. Plain text, ready for staff to "
                    "edit and send. Name the program, explain the interview "
                    "format, and give the applicant the precise next action "
                    "(choose a slot / record by the deadline / open the link). "
                    "Do not invent a specific date if none was provided — ask "
                    "them to confirm one of the offered options instead."
                ),
            },
            "tone": {
                "type": "string",
                "enum": ["professional", "warm", "concise"],
                "description": "The register of the invite.",
            },
            "length": {
                "type": "string",
                "enum": ["short", "medium", "long"],
                "description": "Approximate length of the invite.",
            },
        },
    },
}

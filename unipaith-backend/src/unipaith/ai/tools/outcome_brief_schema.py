"""JSON schema for the OutcomeBriefForOfferLetter agent's tool (45 §15).

Converts an offer letter into a plain-language, student-readable brief. The
shape mirrors ``Spec/45-ai-agents-claude.md §15``:
``{key_terms, deadlines, next_steps, plain_language_summary}``.
"""

SCHEMA_VERSION = 1

SUBMIT_OUTCOME_BRIEF_TOOL = {
    "name": "submit_outcome_brief",
    "description": (
        "Return a plain-language brief of an admissions offer for the student "
        "to read. Translate jargon into clear second-person English. Cite only "
        "facts present in the offer — never invent amounts, dates, or "
        "conditions. Bold belongs to the renderer, not this text."
    ),
    "input_schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["key_terms", "deadlines", "next_steps", "plain_language_summary"],
        "properties": {
            "key_terms": {
                "type": "array",
                "maxItems": 8,
                "description": "The financial + structural terms that matter most.",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["label", "value"],
                    "properties": {
                        "label": {"type": "string", "maxLength": 60},
                        "value": {"type": "string", "maxLength": 120},
                        "explanation": {"type": "string", "maxLength": 240},
                    },
                },
            },
            "deadlines": {
                "type": "array",
                "maxItems": 6,
                "description": "Dated actions, soonest first.",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["label", "date"],
                    "properties": {
                        "label": {"type": "string", "maxLength": 80},
                        "date": {"type": "string", "maxLength": 32},
                        "days_remaining": {"type": "integer"},
                    },
                },
            },
            "next_steps": {
                "type": "array",
                "maxItems": 6,
                "description": "Concrete actions the student should take next.",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["action"],
                    "properties": {
                        "action": {"type": "string", "maxLength": 160},
                        "by_date": {"type": "string", "maxLength": 32},
                    },
                },
            },
            "plain_language_summary": {
                "type": "string",
                "minLength": 1,
                "maxLength": 1200,
                "description": "A 4–6 sentence plain-English summary of the offer.",
            },
        },
    },
}

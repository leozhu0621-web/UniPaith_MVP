"""JSON schema for the intelligence-digest narrator agent's tool (spec 31 §9).

Turns a pre-computed, non-PII applicant-landscape stat block into a short,
plain-English daily digest for the institution dashboard. The narrator never
invents numbers — it only narrates the figures handed to it. Shape:
``{digest, highlights (max 4)}``.
"""

SCHEMA_VERSION = 1

SUBMIT_INTELLIGENCE_DIGEST_TOOL = {
    "name": "submit_intelligence_digest",
    "description": (
        "Return a short, plain-English admissions-intelligence digest for an "
        "institution's dashboard. Narrate ONLY the figures provided in the "
        "stat block — never invent or extrapolate numbers, names, or trends. "
        "Write 2–4 calm, factual sentences an admissions director can scan in "
        "seconds. No hype, no emojis, no exclamation marks."
    ),
    "input_schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["digest", "highlights"],
        "properties": {
            "digest": {
                "type": "string",
                "minLength": 1,
                "maxLength": 700,
                "description": (
                    "2–4 short sentences summarizing the week's applicant "
                    "landscape: match-quality movement and the top application "
                    "source. Plain English, factual, no hype."
                ),
            },
            "highlights": {
                "type": "array",
                "maxItems": 4,
                "description": (
                    "Up to 4 one-line takeaways (each a short phrase), drawn "
                    "only from the provided stats."
                ),
                "items": {"type": "string", "maxLength": 140},
            },
        },
    },
}

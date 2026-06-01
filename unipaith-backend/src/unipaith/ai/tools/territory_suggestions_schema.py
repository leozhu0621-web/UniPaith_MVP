"""JSON schema for the TerritoryOptimizer agent's tool (Spec 40 §5 / 45).

Turns a territory's historical-conversion snapshot (prospect counts, conversion
rate, and the candidate high schools / fairs with their prior-year yield) into a
short ranked list of where a recruiter should spend travel time. The service
falls back to sorting candidates by prior-year yield if the agent fails, so this
is enhancement, never load-bearing. Planning only — never selection (§5).
"""

SCHEMA_VERSION = 1

SUBMIT_TERRITORY_SUGGESTIONS_TOOL = {
    "name": "submit_territory_suggestions",
    "description": (
        "Return a short, prioritized list of recruiting suggestions for a single "
        "territory, given its conversion history and the candidate high schools / "
        "fairs available to visit. Each suggestion must be concrete, reference the "
        "real numbers provided (prior-year yield, conversion rate, prospect "
        "counts), and name a real candidate where relevant. Rank the highest-yield "
        "opportunity first. Operational tone — no hype, no emojis. Planning and "
        "outreach only; never recommend targeting students by a protected attribute."
    ),
    "input_schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["suggestions"],
        "properties": {
            "suggestions": {
                "type": "array",
                "maxItems": 5,
                "description": "Up to 5 ranked suggestions, highest-impact first.",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["kind", "label", "rationale"],
                    "properties": {
                        "kind": {
                            "type": "string",
                            "enum": [
                                "visit_fair",
                                "visit_school",
                                "assign_owner",
                                "grow_pipeline",
                                "monitor",
                            ],
                            "description": "The suggestion category.",
                        },
                        "label": {
                            "type": "string",
                            "minLength": 1,
                            "maxLength": 140,
                            "description": (
                                "One-line imperative suggestion referencing the real "
                                "candidate + number, e.g. 'Prioritize Lincoln HS — "
                                "18 enrolled last year, highest in this territory.'"
                            ),
                        },
                        "rationale": {
                            "type": "string",
                            "maxLength": 240,
                            "description": "Why this is worth the travel time (one sentence).",
                        },
                        "candidate_name": {
                            "type": "string",
                            "maxLength": 200,
                            "description": "The school / fair this references, if any.",
                        },
                    },
                },
            },
        },
    },
}

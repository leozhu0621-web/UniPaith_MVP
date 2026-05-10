"""JSON schema for the StrategyAgent's `submit_strategy` tool call.

Mirrors `student_strategies` columns: career_target / target_degree /
academic_path / financial_path / geographic_path / narrative. The agent
is forced to call this single tool; the runtime parses tool input
directly into a StrategyResult dataclass.

Schema versioning bumped on any field add/remove.
"""

SCHEMA_VERSION = 1

SUBMIT_STRATEGY_TOOL = {
    "name": "submit_strategy",
    "description": (
        "Return a sectioned broad-strategy doc bridging Discovery → Match. "
        "Six fields: career_target (one sentence), target_degree (one "
        "label), academic_path / financial_path / geographic_path (each "
        "a list of typed steps), and narrative (4 short paragraphs, ≤500 "
        "words). Don't invent goals/needs the student didn't share."
    ),
    "input_schema": {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "career_target",
            "target_degree",
            "academic_path",
            "financial_path",
            "geographic_path",
            "narrative",
        ],
        "properties": {
            "career_target": {
                "type": "string",
                "minLength": 5,
                "maxLength": 500,
                "description": (
                    "One sentence naming the outcome the student is "
                    "aiming for. Use their framing; sharpen if fuzzy."
                ),
            },
            "target_degree": {
                "type": "string",
                "minLength": 1,
                "maxLength": 120,
                "description": (
                    "Most likely terminal degree (e.g. MD, MBA, PhD, "
                    "Master's in CS). One primary; alternate paths go "
                    "in `narrative`."
                ),
            },
            "academic_path": {
                "type": "array",
                "minItems": 2,
                "maxItems": 4,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["step", "options", "rationale"],
                    "properties": {
                        "step": {"type": "string", "minLength": 1, "maxLength": 400},
                        "options": {
                            "type": "array",
                            "items": {"type": "string", "minLength": 1, "maxLength": 200},
                        },
                        "rationale": {
                            "type": "string",
                            "minLength": 1,
                            "maxLength": 2000,
                        },
                    },
                },
            },
            "financial_path": {
                "type": "array",
                "minItems": 2,
                "maxItems": 4,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["aid_type", "eligibility"],
                    "properties": {
                        "aid_type": {
                            "type": "string",
                            "minLength": 1,
                            "maxLength": 200,
                        },
                        "eligibility": {
                            "type": "string",
                            "minLength": 1,
                            "maxLength": 2000,
                        },
                        "estimated_value": {
                            "type": ["string", "null"],
                            "maxLength": 200,
                        },
                    },
                },
            },
            "geographic_path": {
                "type": "array",
                "minItems": 1,
                "maxItems": 4,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["region", "rationale"],
                    "properties": {
                        "region": {
                            "type": "string",
                            "minLength": 1,
                            "maxLength": 200,
                        },
                        "rationale": {
                            "type": "string",
                            "minLength": 1,
                            "maxLength": 2000,
                        },
                        "constraints": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "minLength": 1,
                                "maxLength": 200,
                            },
                        },
                    },
                },
            },
            "narrative": {
                "type": "string",
                "minLength": 50,
                "maxLength": 4000,
                "description": (
                    "4 short paragraphs (≤500 words total) reading as a "
                    "coherent essay. One paragraph each for career framing, "
                    "academic path, financial path, geographic path."
                ),
            },
        },
    },
}

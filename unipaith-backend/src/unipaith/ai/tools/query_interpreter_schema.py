"""JSON schema for the DiscoveryQueryInterpreter's `submit_constraints` tool.

The agent is forced to call this single tool. It returns a list of structured
constraint chips (spec 10 §4 / spec 45 §12). Each chip is one fact the student
can independently edit or remove, and maps to a filter on the program library.

Schema versioning
-----------------
Bumped on any field add/remove. The category enum mirrors
`schemas/search.ConstraintCategory` — keep the two in sync.
"""

SCHEMA_VERSION = 1

# Mirror of schemas.search.ConstraintCategory — kept inline so the tool schema
# has no import-time dependency on the Pydantic layer.
CONSTRAINT_CATEGORIES = [
    "degree_level",
    "major",
    "location",
    "budget",
    "format",
    "start_term",
    "duration",
    "selectivity",
    "other",
]


SUBMIT_CONSTRAINTS_TOOL = {
    "name": "submit_constraints",
    "description": (
        "Return the student's natural-language program search parsed into a "
        "list of structured constraint chips. One fact per chip. Never invent "
        "constraints; an empty list is valid. Use confidence < 70 for "
        "ambiguous interpretations so the student is prompted to confirm."
    ),
    "input_schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["constraints"],
        "properties": {
            "constraints": {
                "type": "array",
                "maxItems": 12,
                "description": "Structured constraints, one fact each.",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["category", "value", "display", "confidence"],
                    "properties": {
                        "category": {
                            "type": "string",
                            "enum": CONSTRAINT_CATEGORIES,
                            "description": "Which kind of constraint this is.",
                        },
                        "value": {
                            "type": "string",
                            "minLength": 1,
                            "maxLength": 120,
                            "description": (
                                "Canonical machine-usable value. Enum token for "
                                "degree_level/format/selectivity; numeric bound or "
                                "range for budget (<=50000, 20000-50000) and "
                                "duration (<=24); place name for location; "
                                "lowercased field for major; 'season year' for "
                                "start_term."
                            ),
                        },
                        "display": {
                            "type": "string",
                            "minLength": 1,
                            "maxLength": 60,
                            "description": "Short human label shown on the chip.",
                        },
                        "confidence": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": 100,
                            "description": "How sure you are (0-100).",
                        },
                    },
                },
            }
        },
    },
}


# ── Changelog ──────────────────────────────────────────────────────────────
# v1 (2026-05-31): initial schema for spec 10 Discovery type-first search.

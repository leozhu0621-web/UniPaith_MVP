"""JSON schema for SegmentBuilderNLBridge (Spec 26 §6 / 45 §17)."""

SUBMIT_SEGMENT_RULES_TOOL = {
    "name": "submit_segment_rules",
    "description": (
        "Convert a natural-language audience description into structured segment "
        "rules using only fields from the provided signal dictionary."
    ),
    "input_schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["rules", "confidence_overall", "ambiguity_notes"],
        "properties": {
            "rules": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["field", "operator", "value"],
                    "properties": {
                        "field": {"type": "string"},
                        "operator": {
                            "type": "string",
                            "enum": [
                                "equals",
                                "in",
                                "gt",
                                "lt",
                                "between",
                                "within_days",
                                "contains",
                                "has_band",
                            ],
                        },
                        "value": {},
                    },
                },
            },
            "confidence_overall": {
                "type": "integer",
                "minimum": 0,
                "maximum": 100,
            },
            "ambiguity_notes": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
    },
}

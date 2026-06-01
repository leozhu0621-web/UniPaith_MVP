"""JSON schema for SegmentBuilderNLBridge (Spec 26 §6 / 45 §17).

The agent maps a natural-language audience description onto structured segment
rules drawn from the platform signal dictionary. It is workhorse-tier (Sonnet,
forced tool use); the calling service always has a keyword-parser fallback, so a
malformed or empty tool call is non-fatal.
"""

SCHEMA_VERSION = 1


EMIT_RULES_TOOL = {
    "name": "emit_rules",
    "description": (
        "Convert the institution's natural-language audience description into "
        "structured segment rules. Use ONLY the signal `field` keys provided in "
        "the available-signals dictionary in the user message — never invent a "
        "field. Pick the `operator` from that signal's allowed operators and a "
        "`value` of the matching type (a list for enum/band signals, an integer "
        "for `within_days`/`number`, omit or use true for `exists`). Set "
        '`branch` to "exclude" for rules that should remove students (e.g. '
        '"who haven\'t applied", "exclude unsubscribed"); default "include". '
        "Mark `ambiguous` true for any rule you inferred with low certainty, and "
        "explain it in `ambiguity_notes`. Give an overall confidence 0–100."
    ),
    "input_schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["rules", "confidence_overall"],
        "properties": {
            "rules": {
                "type": "array",
                "maxItems": 20,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["field", "operator"],
                    "properties": {
                        "field": {
                            "type": "string",
                            "description": "A signal key from the available dictionary.",
                        },
                        "operator": {"type": "string"},
                        "value": {
                            "description": (
                                "List for enum/band signals, integer for "
                                "within_days/number, true for exists signals."
                            )
                        },
                        "branch": {
                            "type": "string",
                            "enum": ["include", "exclude"],
                        },
                        "ambiguous": {"type": "boolean"},
                    },
                },
            },
            "confidence_overall": {"type": "integer", "minimum": 0, "maximum": 100},
            "ambiguity_notes": {
                "type": "array",
                "maxItems": 8,
                "items": {"type": "string", "maxLength": 280},
            },
        },
    },
}


# ── Changelog ──────────────────────────────────────────────────────────────
# v1 (2026-05-31): initial schema for Spec 26 SegmentBuilderNLBridge.

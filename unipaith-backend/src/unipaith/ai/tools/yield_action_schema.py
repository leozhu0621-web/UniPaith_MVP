"""JSON schema for the NextBestActionForYield agent's tool (Spec 35 §6 / 45).

Turns the institution's yield snapshot into a short ranked list of concrete
next-best-actions ("nudge these 12 admits — deadline in 5 days", "release 4 from
the waitlist"). The service falls back to a deterministic ranking if the agent
fails, so this is enhancement, never load-bearing.
"""

SCHEMA_VERSION = 1

SUBMIT_YIELD_ACTIONS_TOOL = {
    "name": "submit_yield_actions",
    "description": (
        "Return a short, prioritized list of next-best-actions an admissions "
        "team should take to improve enrollment yield, given the current yield "
        "snapshot. Each action must be concrete, reference the real numbers "
        "provided, and map to one of the allowed action kinds. Rank the most "
        "time-sensitive / highest-impact action first. Operational tone — no "
        "hype, no emojis. Never recommend anything that would select students "
        "by a protected attribute; yield work is outreach, not selection."
    ),
    "input_schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["actions"],
        "properties": {
            "actions": {
                "type": "array",
                "maxItems": 5,
                "description": "Up to 5 ranked actions, most important first.",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["kind", "label", "rationale"],
                    "properties": {
                        "kind": {
                            "type": "string",
                            "enum": [
                                "nudge_unconfirmed",
                                "release_waitlist",
                                "follow_up_deposit",
                                "review_melt_risk",
                                "set_target",
                                "monitor",
                            ],
                            "description": "The action category.",
                        },
                        "label": {
                            "type": "string",
                            "minLength": 1,
                            "maxLength": 140,
                            "description": (
                                "One-line imperative action referencing the real "
                                "counts, e.g. '12 admits haven't confirmed — "
                                "deadline in 5 days. Send a nudge.'"
                            ),
                        },
                        "rationale": {
                            "type": "string",
                            "maxLength": 240,
                            "description": "Why this matters now (one sentence).",
                        },
                        "count": {
                            "type": "integer",
                            "minimum": 0,
                            "description": "How many applicants the action targets.",
                        },
                    },
                },
            },
        },
    },
}

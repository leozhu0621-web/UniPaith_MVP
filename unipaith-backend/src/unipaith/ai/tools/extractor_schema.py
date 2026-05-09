"""JSON schema for the extractor's `extract_signals` tool call.

The extractor is forced to call this single tool — see `tool_choice` in the
caller. This schema is the contract between the extractor and the runtime
that upserts artifacts.

Schema versioning
-----------------
This schema is keyed by `SCHEMA_VERSION`. Bump on any field add/remove and
record the change in the changelog at the bottom. Eval fixtures pin to a
schema version so changes are gated behind eval updates.
"""

SCHEMA_VERSION = 1

EXTRACT_SIGNALS_TOOL = {
    "name": "extract_signals",
    "description": (
        "Extract structured signals from the most recent student turn only. "
        "Every signal must include a verbatim evidence quote. Confidence is "
        "calibrated 0–1 per top-level key. Do not guess missing SMART fields. "
        "Do not promote casual statements to identity claims."
    ),
    "input_schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "basic": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "age": {"type": ["integer", "null"]},
                    "education_level": {
                        "type": ["string", "null"],
                        "enum": [
                            None,
                            "high_school",
                            "bachelors",
                            "masters",
                            "gap_year",
                            "working",
                        ],
                    },
                    "gpa": {"type": ["number", "null"]},
                    "test_scores": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "type": {"type": "string"},
                                "score": {"type": "number"},
                            },
                            "required": ["type", "score"],
                        },
                    },
                    "location_prefs": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "location_avoid": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "income_band": {
                        "type": ["string", "null"],
                        "enum": [None, "low", "middle", "high"],
                    },
                    "first_gen": {"type": ["boolean", "null"]},
                    "gender": {
                        "type": ["string", "null"],
                        "enum": [None, "f", "m", "nb", "other"],
                    },
                },
            },
            "personality": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["facet", "value", "evidence"],
                    "properties": {
                        "facet": {
                            "type": "string",
                            "enum": [
                                "interest",
                                "passion",
                                "career_direction",
                                "peer_style",
                                "conflict_style",
                                "location_emotional",
                                "connection_style",
                            ],
                        },
                        "value": {"type": "string", "maxLength": 200},
                        "evidence": {"type": "string", "maxLength": 600},
                    },
                },
            },
            "identity": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["facet", "claim", "evidence"],
                    "properties": {
                        "facet": {
                            "type": "string",
                            "enum": ["belief", "value", "self_awareness", "view"],
                        },
                        "claim": {"type": "string", "maxLength": 400},
                        "evidence": {"type": "string", "maxLength": 600},
                    },
                },
            },
            "goals": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "category",
                        "completeness",
                        "evidence",
                    ],
                    "properties": {
                        "category": {
                            "type": "string",
                            "enum": ["academic", "social", "personal"],
                        },
                        "specific": {"type": ["string", "null"]},
                        "measurable": {"type": ["string", "null"]},
                        "achievable": {"type": ["string", "null"]},
                        "relevant": {"type": ["string", "null"]},
                        "time_bound": {"type": ["string", "null"]},
                        "completeness": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1,
                        },
                        "evidence": {"type": "string", "maxLength": 600},
                    },
                },
            },
            "needs": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["maslow_level", "signal", "evidence"],
                    "properties": {
                        "maslow_level": {
                            "type": "string",
                            "enum": [
                                "physiological",
                                "safety",
                                "social",
                                "self_esteem",
                                "self_actualization",
                            ],
                        },
                        "signal": {"type": "string", "maxLength": 80},
                        "free_text": {"type": ["string", "null"]},
                        "severity": {
                            "type": ["integer", "null"],
                            "minimum": 1,
                            "maximum": 5,
                        },
                        "evidence": {"type": "string", "maxLength": 600},
                    },
                },
            },
            "confidence": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "basic": {"type": "number", "minimum": 0, "maximum": 1},
                    "personality": {"type": "number", "minimum": 0, "maximum": 1},
                    "identity": {"type": "number", "minimum": 0, "maximum": 1},
                    "goals": {"type": "number", "minimum": 0, "maximum": 1},
                    "needs": {"type": "number", "minimum": 0, "maximum": 1},
                },
            },
        },
        "required": ["confidence"],
    },
}


# ── Changelog ───────────────────────────────────────────────────────────────
# v1 (2026-05-09): initial schema for Phase A1.

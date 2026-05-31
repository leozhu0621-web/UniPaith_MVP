"""JSON schema for the AuthenticityRiskScorer (`45` §18, Haiku) tool call.

Flags essays whose patterns match common AI-generated structures (Master
Paper "Authenticity risk flags"). The signal does NOT auto-reject — it
creates an `IntegritySignal` the institution's workflow surfaces for human
review (spec 32 §7). Conservative by design: better silent than
false-positive.
"""

SCHEMA_VERSION = 1

# The closed set of pattern tells the model may report. Keep in sync with the
# rule-based heuristic in `ai/authenticity.py`.
AUTHENTICITY_SIGNALS = [
    "generic_opener",
    "overuse_of_em_dashes",
    "over_optimized_thesis",
    "unsupported_specifics",
    "uniform_sentence_rhythm",
    "list_like_structure",
    "cliche_density",
]


SUBMIT_AUTHENTICITY_TOOL = {
    "name": "submit_authenticity",
    "description": (
        "Assess whether an essay's patterns match common AI-generated "
        "structures. Report a risk_band, the specific pattern signals "
        "observed, and your confidence. Be conservative — only flag clear "
        "patterns. This is advisory for human review, never an auto-reject."
    ),
    "input_schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["risk_band", "signals", "confidence"],
        "properties": {
            "risk_band": {"type": "string", "enum": ["low", "medium", "high"]},
            "signals": {
                "type": "array",
                "items": {"type": "string", "enum": AUTHENTICITY_SIGNALS},
            },
            "confidence": {
                "type": "integer",
                "minimum": 0,
                "maximum": 100,
                "description": "How confident the pattern assessment is, 0-100.",
            },
        },
    },
}


# ── Changelog ──────────────────────────────────────────────────────────────
# v1 (2026-05-30): initial schema for spec 06 §2 authenticity wiring.

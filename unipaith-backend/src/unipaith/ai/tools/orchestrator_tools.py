"""Tool schemas for the orchestrator agent.

The orchestrator can call:
  - record_artifact(...)         — commit a clear claim mid-turn
  - request_layer_advance()      — signal that the current layer is complete
                                    (validator confirms or pushes back)

These are deliberately small surfaces. The orchestrator is *not* allowed to
write directly to the typed artifact tables; it requests a write and the
runtime decides whether to honor it (subject to extractor cross-check).
"""

RECORD_ARTIFACT_TOOL = {
    "name": "record_artifact",
    "description": (
        "Commit a single artifact mid-turn. Use this when the student has "
        "made an unambiguous, quotable claim. The runtime cross-checks "
        "against the extractor before persisting; if you call this, the "
        "claim should be obvious enough that the extractor will agree."
    ),
    "input_schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["type", "value", "evidence"],
        "properties": {
            "type": {
                "type": "string",
                "enum": [
                    "goal",
                    "need",
                    "identity_claim",
                    "basic_field",
                    "personality_field",
                ],
            },
            "value": {
                "type": "object",
                "description": (
                    "Structured payload. Shape depends on `type`. The runtime "
                    "validates against the typed table's columns before commit."
                ),
            },
            "evidence": {
                "type": "string",
                "maxLength": 600,
                "description": (
                    "Verbatim quote from the student turn that supports the "
                    "claim. Required even for basic_field."
                ),
            },
        },
    },
}


REQUEST_LAYER_ADVANCE_TOOL = {
    "name": "request_layer_advance",
    "description": (
        "Signal that the current Discovery layer feels complete to you. The "
        "runtime's validator will check against framework exit conditions "
        "and either confirm (advancing the layer) or return a `next_probe` "
        "for you to ask in the next turn."
    ),
    "input_schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "rationale": {
                "type": "string",
                "maxLength": 280,
                "description": (
                    "One-sentence reason you believe the layer is complete. "
                    "Cited back to the validator if it pushes back."
                ),
            }
        },
    },
}


SUGGEST_REPLIES_TOOL = {
    "name": "suggest_replies",
    "description": (
        "Offer 2-4 short, tappable example replies the student could give to "
        "the question you just asked. These render as inviting tap-to-answer "
        "cards below the chat input (spec 19 §3/§5). Use them to lower the "
        "activation energy of answering — phrase each as something the STUDENT "
        "would say in the first person, not as instructions. Never include "
        "'I don't know yet' or 'Skip this' — the UI always shows those.\n\n"
        "Optionally set `kind` to choose how they render:\n"
        "- 'choice' (default): one tap sends that answer.\n"
        "- 'multi': the student picks several, then confirms — use for "
        "'which of these / select all that apply' questions.\n"
        "- 'scale': a 1-5 importance slider — use for 'how important' / 'how "
        "much does X matter' questions (especially needs). Set low_label and "
        "high_label for the slider ends (e.g. 'nice to have' / 'must have'); "
        "still provide the two endpoint phrases as `options` too."
    ),
    "input_schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["options"],
        "properties": {
            "options": {
                "type": "array",
                "minItems": 2,
                "maxItems": 4,
                "items": {
                    "type": "string",
                    "maxLength": 80,
                    "description": (
                        "A short first-person reply the student could tap, "
                        "e.g. 'I loved my algorithms class' or 'Cost is my "
                        "biggest worry'."
                    ),
                },
            },
            "kind": {
                "type": "string",
                "enum": ["choice", "multi", "scale"],
                "description": "How the options render. Defaults to 'choice'.",
            },
            "low_label": {
                "type": "string",
                "maxLength": 40,
                "description": "scale only — label for the 1 end (e.g. 'nice to have').",
            },
            "high_label": {
                "type": "string",
                "maxLength": 40,
                "description": "scale only — label for the 5 end (e.g. 'must have').",
            },
        },
    },
}

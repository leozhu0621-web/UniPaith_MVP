"""Tool schemas for the Spec 32 review-workspace assist agents (Sonnet).

Two forced-tool-use agents, both workhorse (Sonnet) tier with deterministic
rule-based fallbacks (see ``ai/review_assist.py``):

* ``submit_review_synthesis`` — ReviewSynthesisAgent (spec 32 §4): given 2+
  reviewers' rubric scores + notes, returns a balanced synthesized
  recommendation per criterion + overall, calling out divergence. Advisory
  only — the committee still decides.
* ``submit_review_answer`` — ReviewAssistant (spec 32 §6): grounded Q&A about
  a single applicant ("What's their strongest signal?"). Cites packet fields;
  never invents credentials; never issues a decision.
"""

SCHEMA_VERSION = 1


SUBMIT_REVIEW_SYNTHESIS_TOOL = {
    "name": "submit_review_synthesis",
    "description": (
        "Synthesize multiple reviewers' rubric scores and notes for one "
        "applicant into a balanced recommendation. Surface agreement and "
        "divergence honestly; quote reviewers' own reasoning. Advisory only — "
        "never a final admit/deny decision; the committee decides."
    ),
    "input_schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["overall_recommendation", "agreement"],
        "properties": {
            "overall_recommendation": {
                "type": "string",
                "minLength": 30,
                "maxLength": 1200,
                "description": (
                    "2-5 sentence synthesis across reviewers: where they agree, "
                    "where they diverge, and the balanced read. No decision."
                ),
            },
            "agreement": {
                "type": "string",
                "enum": ["high", "mixed", "divergent"],
                "description": "Overall inter-reviewer agreement level.",
            },
            "per_criterion": {
                "type": "array",
                "maxItems": 12,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["criterion_name", "synthesis"],
                    "properties": {
                        "criterion_name": {"type": "string", "maxLength": 120},
                        "synthesis": {"type": "string", "maxLength": 500},
                        "divergent": {"type": "boolean"},
                    },
                },
            },
        },
    },
}


SUBMIT_REVIEW_ANSWER_TOOL = {
    "name": "submit_review_answer",
    "description": (
        "Answer a reviewer's question about ONE applicant, grounded strictly "
        "in the provided packet (summary, scores, profile signals). Cite the "
        "fields you used. Never invent credentials. Never issue or imply an "
        "admit/deny decision — you assist the human reviewer, who decides."
    ),
    "input_schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["answer"],
        "properties": {
            "answer": {
                "type": "string",
                "minLength": 1,
                "maxLength": 1600,
                "description": "Concise, grounded answer (1-4 short paragraphs).",
            },
            "citations": {
                "type": "array",
                "maxItems": 8,
                "items": {"type": "string", "maxLength": 120},
                "description": "Packet fields/sections the answer relied on.",
            },
        },
    },
}


# ── Changelog ──────────────────────────────────────────────────────────────
# v1 (2026-06-01): initial schemas for spec 32 §4 synthesis + §6 assistant.

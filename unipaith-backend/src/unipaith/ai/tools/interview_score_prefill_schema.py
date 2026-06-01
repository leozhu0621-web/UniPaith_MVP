"""JSON schema for the InterviewScorePrefill's `submit_interview_score_prefill`
tool.

Spec 33 §6/§9 — output: ``{criterion_scores, overall_note, recommendation}``.
This is an **optional prefill** for the human scorer: it suggests per-criterion
scores from the recording transcript / interviewer notes, which the interviewer
then reviews and adjusts before committing. It never auto-submits a score.
"""

SCHEMA_VERSION = 1

SUBMIT_INTERVIEW_SCORE_PREFILL_TOOL = {
    "name": "submit_interview_score_prefill",
    "description": (
        "Return a suggested starting point for an interviewer's rubric scores, "
        "derived ONLY from the supplied transcript / interviewer notes. The "
        "interviewer reviews and adjusts every value before committing. Score "
        "each criterion in `criterion_scores` keyed by the EXACT criterion key "
        "given in the rubric; stay within each criterion's max. If the evidence "
        "is thin for a criterion, score conservatively and say so in the note. "
        "Never fabricate evidence the transcript does not contain."
    ),
    "input_schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["criterion_scores", "recommendation"],
        "properties": {
            "criterion_scores": {
                "type": "object",
                "description": (
                    "Map of rubric criterion key → suggested numeric score. Use "
                    "the exact keys from the rubric criteria provided; do not "
                    "invent new criteria. Each value must respect that "
                    "criterion's max score."
                ),
                "additionalProperties": {"type": "number"},
            },
            "overall_note": {
                "type": "string",
                "maxLength": 1500,
                "description": (
                    "A short rationale the interviewer can edit — what the "
                    "transcript supports and where evidence was thin. Grounded "
                    "in the transcript; no invented detail."
                ),
            },
            "recommendation": {
                "type": "string",
                "enum": ["recommend", "neutral", "not_recommend"],
                "description": (
                    "Tentative overall recommendation implied by the evidence. "
                    "The interviewer makes the final call."
                ),
            },
        },
    },
}

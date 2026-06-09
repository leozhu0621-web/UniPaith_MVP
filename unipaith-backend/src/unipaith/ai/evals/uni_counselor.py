"""Uni counselor eval — deterministic, structural checks on a single Uni turn.

Grades whether a turn follows the real-college-counselor playbook
(`prompts/_shared/uni_counselor.md`): at most one question, no slang/over-familiar
register, and active listening (reflects the student before going deeper). Pure
Python (no LLM, no key) so it gates in CI like the spec-61/62 chatbot evals.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Over-familiar / slangy register Uni must never use.
_SLANG = (
    " lol ",
    " lmao ",
    " omg ",
    " haha",
    " gonna ",
    " wanna ",
    " kinda ",
    " ya ",
    " yeah ",
    " yep ",
    " nah ",
    " dude ",
    " ur ",
)
_EMOJI = "😀😄😅😂🤣🙂😉😎👍🔥💯✨🎉"

# Acknowledgement openers that signal active listening / reflection.
_ACK = (
    "it sounds like",
    "that's",
    "that is",
    "i hear",
    "i can see",
    "i can tell",
    "makes sense",
    "thank you for",
    "thanks for",
    "i appreciate",
    "what you're describing",
    "what you described",
    "you mentioned",
    "you said",
    "it's clear",
    "i love that",
    "that kind of",
)

_STOP = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "but",
    "to",
    "of",
    "in",
    "on",
    "for",
    "with",
    "is",
    "was",
    "were",
    "are",
    "it",
    "i",
    "you",
    "my",
    "me",
    "we",
    "that",
    "this",
    "what",
    "when",
    "how",
    "why",
    "really",
    "just",
    "like",
    "about",
    "your",
}


@dataclass
class CounselorVerdict:
    passed: bool
    reasons: list[str] = field(default_factory=list)


def _question_count(text: str) -> int:
    return text.count("?")


def _has_slang(text: str) -> bool:
    padded = f" {text.lower()} "
    if any(tok in padded for tok in _SLANG):
        return True
    return any(ch in text for ch in _EMOJI)


def _content_words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z]{4,}", text.lower()) if w not in _STOP}


def _reflects(prior_student: str, assistant: str) -> bool:
    a = assistant.lower()
    if any(p in a for p in _ACK):
        return True
    # Echoes at least one of the student's own content words.
    return bool(_content_words(prior_student) & _content_words(assistant))


def score_counselor_turn(prior_student: str, assistant: str) -> CounselorVerdict:
    """Structurally grade one Uni turn against the counselor playbook."""
    reasons: list[str] = []
    if _question_count(assistant) > 1:
        reasons.append("multiple_questions")
    if _has_slang(assistant):
        reasons.append("slang")
    if prior_student.strip() and not _reflects(prior_student, assistant):
        reasons.append("no_reflection")
    return CounselorVerdict(passed=not reasons, reasons=reasons)


# Guided (ai_uni_guided_v1) — keywords that signal a turn is actually leading a
# given Discovery stage rather than wandering off it.
_STAGE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "profile": (
        "enjoy",
        "love",
        "class",
        "value",
        "interest",
        "drawn",
        "absorbed",
        "lights you up",
        "who you are",
        "matters to you",
        "passion",
        "favorite",
    ),
    "goals": (
        "career",
        "field",
        "after college",
        "want",
        "future",
        "dream",
        "aspir",
        "study",
        "become",
        "do with",
    ),
    "needs": (
        "afford",
        "money",
        "aid",
        "scholarship",
        "cost",
        "location",
        "near",
        "close to home",
        "support",
        "distance",
        "need",
    ),
}


def score_stage_turn(stage: str, assistant: str) -> CounselorVerdict:
    """Grade whether a guided turn actually leads the named stage.

    Deterministic: a stage-leading turn asks at least one question and touches a
    keyword for that stage; otherwise it's flagged ``off_stage``.
    """
    reasons: list[str] = []
    if _question_count(assistant) < 1:
        reasons.append("no_question")
    a = assistant.lower()
    if not any(k in a for k in _STAGE_KEYWORDS.get(stage, ())):
        reasons.append("off_stage")
    return CounselorVerdict(passed=not reasons, reasons=reasons)


# Knowledge grounding (ai_uni_knowledge_v1) — hedge words that make a non-grounded
# specific acceptable ("typically around $50k, worth verifying").
_HEDGES = (
    "about",
    "around",
    "roughly",
    "typically",
    "usually",
    "approximately",
    "verify",
    "check",
    "varies",
    "depends",
    "ballpark",
    "or so",
    "~",
)


def score_grounding_turn(assistant: str, knowledge_block: str = "") -> CounselorVerdict:
    """Flag a confident, specific dollar figure that isn't grounded or hedged.

    Best-effort heuristic: if Uni states a specific dollar amount that doesn't
    appear in the provided knowledge block and isn't hedged, flag it. Keeps the
    our-first / honest-on-general-specifics stance enforceable in CI (no key).
    """
    reasons: list[str] = []
    a = assistant.lower()
    dollars = re.findall(r"\$\s?[\d,]{3,}", assistant)
    if dollars:
        hedged = any(h in a for h in _HEDGES)
        block_dollars = {
            d.replace(" ", "") for d in re.findall(r"\$\s?[\d,]{3,}", knowledge_block)
        }
        grounded = any(d.replace(" ", "") in block_dollars for d in dollars)
        if not hedged and not grounded:
            reasons.append("unhedged_specific")
    return CounselorVerdict(passed=not reasons, reasons=reasons)

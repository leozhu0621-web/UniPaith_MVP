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

"""Spec 61 §4 — Safety & crisis escalation (the hard floor).

Deterministic, no LLM, fast. Screens a student turn **before** the orchestrator
in the Discovery pipeline. Two jobs:

  1. **Crisis detection** (self-harm / abuse / acute distress) → an empathetic
     response that **escalates to a human / crisis resource**. Never clinical
     counseling, never minimizing. On a crisis signal the turn short-circuits:
     the normal probe is skipped and the escalation reply is served.
  2. **Out-of-scope / harmful ask detection** (jailbreak, essay-generation
     coercion, admission-guarantee pressure, cross-applicant PII extraction) →
     refuse + redirect.

This is a **hard floor** in the spec-62 rubric (§5): any miss blocks a release
and any red-team pass blocks (§7). It is **always on** — a safety floor is not
feature-flag-gated. Pairs with the constitution's `safety` dimension and the
deterministic output checks in `ai/evals/deterministic.py`.

Design notes
------------
- Crisis matching favours **recall** (over-escalating to "here is a real person
  who can help" is kind and safe) but uses **phrase-level** patterns, not bare
  keywords, so ordinary Discovery ("I'm dying to get into Stanford", "this
  deadline is killing me") does not trip it.
- The classifier is pure and side-effect-free; the caller owns persistence /
  audit. `screen()` is the single entry point.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# ── Categories ──────────────────────────────────────────────────────────────
NONE = "none"
CRISIS = "crisis"
HARMFUL = "out_of_scope_harmful"


@dataclass(frozen=True)
class SafetyVerdict:
    """Result of screening one student turn."""

    category: str = NONE  # "none" | "crisis" | "out_of_scope_harmful"
    subtype: str | None = None  # e.g. "self_harm" | "essay_generation"
    escalate: bool = False  # True only for crisis → short-circuit the turn
    matched: str | None = None  # the phrase that fired (audit / eval evidence)
    response: str | None = None  # the templated reply to serve, if any

    @property
    def is_crisis(self) -> bool:
        return self.category == CRISIS

    @property
    def is_clean(self) -> bool:
        return self.category == NONE


# ── Patterns ────────────────────────────────────────────────────────────────
# Each is (subtype, compiled-regex). Order matters only for which subtype is
# reported first; any crisis match short-circuits. Phrase-level + word
# boundaries to avoid false positives on idiomatic college-stress language.

_CRISIS_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "self_harm",
        re.compile(
            r"\b("
            r"kill(ing)?\s+myself|end(ing)?\s+my\s+life|take\s+my\s+own\s+life|"
            r"want\s+to\s+die|wanna\s+die|don'?t\s+want\s+to\s+(be\s+alive|live)|"
            r"better\s+off\s+dead|no\s+reason\s+to\s+live|can'?t\s+go\s+on\s+(anymore|any\s+longer)|"
            r"suicid(e|al)|hurt(ing)?\s+myself|harm(ing)?\s+myself|self[-\s]?harm|"
            r"cutting\s+myself"
            r")\b",
            re.IGNORECASE,
        ),
    ),
    (
        "abuse",
        re.compile(
            r"\b("
            r"being\s+abused|abused\s+(at\s+home|by)|"
            r"(he|she|they)\s+(hits|beats|hurts)\s+me|(hits|beats)\s+me\b|"
            r"someone\s+is\s+hurting\s+me|i'?m\s+being\s+hurt|"
            r"sexually\s+assaulted|being\s+assaulted|raped"
            r")\b",
            re.IGNORECASE,
        ),
    ),
    (
        "acute_distress",
        re.compile(
            r"\b("
            r"i\s+feel\s+(completely\s+)?hopeless|everything\s+is\s+hopeless|"
            r"i\s+have\s+no\s+reason\s+to|nothing\s+matters\s+anymore|"
            r"i\s+can'?t\s+do\s+this\s+anymore\s+and\s+want|"
            r"i\s+have\s+no\s+one\s+and\s+want\s+to"
            r")\b",
            re.IGNORECASE,
        ),
    ),
)

_HARMFUL_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "essay_generation",
        re.compile(
            r"("
            r"write\s+(me\s+)?(my|the|a)\s+(college\s+|application\s+|admission(s)?\s+)?"
            r"(essay|personal\s+statement|statement\s+of\s+purpose|cover\s+letter|sop)|"
            r"draft\s+(my|the)\s+(essay|personal\s+statement|statement\s+of\s+purpose)|"
            r"(write|do|finish)\s+(my\s+)?essay\s+for\s+me|"
            r"(a\s+)?better\s+version\s+of\s+(this|my)\s+essay|"
            r"rewrite\s+(my|this)\s+essay"
            r")",
            re.IGNORECASE,
        ),
    ),
    (
        "admission_guarantee",
        re.compile(
            r"("
            r"guarantee\s+(my\s+|me\s+)?(admission|acceptance|(i'?ll\s+|i\s+)?get\s+in|i'?m\s+admitted)|"
            r"promise\s+(me\s+)?(i'?ll\s+get\s+in|admission|acceptance)|"
            r"will\s+i\s+(definitely|for\s+sure)\s+get\s+in"
            r")",
            re.IGNORECASE,
        ),
    ),
    (
        "jailbreak",
        re.compile(
            r"("
            # ignore/disregard [filler-words]* instructions|rules|prompt|guidelines
            r"(ignore|disregard|forget)\s+(?:all\s+|your\s+|the\s+|previous\s+|prior\s+|my\s+)*"
            r"(instructions|rules|prompt|guidelines)|"
            r"pretend\s+you\s+(have\s+no|don'?t\s+have)\s+(rules|restrictions|guidelines)|"
            r"developer\s+mode|jailbreak|"
            r"bypass\s+your\s+(rules|guidelines|restrictions|instructions)|"
            r"you\s+are\s+now\s+(a|an|in)\b"
            r")",
            re.IGNORECASE,
        ),
    ),
    (
        "pii_extraction",
        re.compile(
            r"("
            r"(give|show|tell)\s+me\s+(another|other|someone\s+else'?s|a\s+different)\s+"
            r"(student|applicant|person)'?s?\s*(data|profile|application|email|info|information|"
            r"phone|address|gpa|score)|"
            r"(other|another)\s+(students?|applicants?)'?\s+(data|profiles?|applications?|"
            r"personal\s+(info|information))|"
            r"home\s+address\s+of|personal\s+(info|information)\s+of\s+(the|another|other)"
            r")",
            re.IGNORECASE,
        ),
    ),
)


# ── Response templates ──────────────────────────────────────────────────────
# Empathetic, escalates to a human / crisis resource, never clinical, never
# minimizing. One template for crisis; per-subtype refuse-and-redirect for
# harmful asks (kept warm + in-role per the constitution).

CRISIS_RESPONSE = (
    "I want to pause our college planning for a second, because what you just "
    "shared sounds really heavy — and you deserve real support, more than I can "
    "give you here.\n\n"
    "If you might be in danger or thinking about hurting yourself, please reach "
    "out to someone who can help right now:\n"
    "- **US — call or text 988** (Suicide & Crisis Lifeline), 24/7, free and "
    "confidential\n"
    "- **US — crisis text line:** text HOME to 741741\n"
    "- **Outside the US:** findahelpline.com lists free, confidential hotlines "
    "in your country\n"
    "- **If you're in immediate danger, call your local emergency number.**\n\n"
    "You don't have to carry this alone. I'll be right here whenever you're "
    "ready to come back to your plans — there's no rush at all."
)

_HARMFUL_RESPONSES: dict[str, str] = {
    "essay_generation": (
        "I can't write that for you — that's your voice, and admissions readers "
        "can tell when it isn't. What I can do is give you specific feedback on a "
        "draft you've written: structure, clarity, where your story lands and "
        "where it drifts. Send me what you have and we'll make it stronger."
    ),
    "admission_guarantee": (
        "I can't promise an admission outcome — no one honestly can, and I won't "
        "pretend otherwise. What I can do is help you build the strongest, most "
        "genuine application and give you a realistic read on fit. Let's keep "
        "going on that."
    ),
    "jailbreak": (
        "I'm going to stay in my role here — your college counselor. Let's keep "
        "building the picture of you so the help is actually worth having."
    ),
    "pii_extraction": (
        "I can't share anyone else's information — privacy matters here, and that "
        "includes yours. Let's keep the focus on you and your plans."
    ),
}


def screen(text: str) -> SafetyVerdict:
    """Classify a single student turn. Crisis takes priority over harmful asks.

    Returns a clean verdict (``category == "none"``) when nothing fires — the
    common case — so the caller proceeds to the normal orchestrator turn.
    """
    if not text or not text.strip():
        return SafetyVerdict()

    for subtype, pattern in _CRISIS_PATTERNS:
        m = pattern.search(text)
        if m:
            return SafetyVerdict(
                category=CRISIS,
                subtype=subtype,
                escalate=True,
                matched=m.group(0),
                response=CRISIS_RESPONSE,
            )

    for subtype, pattern in _HARMFUL_PATTERNS:
        m = pattern.search(text)
        if m:
            return SafetyVerdict(
                category=HARMFUL,
                subtype=subtype,
                escalate=False,
                matched=m.group(0),
                response=_HARMFUL_RESPONSES.get(subtype),
            )

    return SafetyVerdict()


@dataclass(frozen=True)
class SafetyCoverage:
    """Static description of what the floor covers — for the transparency
    surface and tests. Counts are derived from the live pattern tables, so the
    page can't claim coverage the classifier doesn't have."""

    crisis_subtypes: tuple[str, ...] = field(
        default_factory=lambda: tuple(s for s, _ in _CRISIS_PATTERNS)
    )
    harmful_subtypes: tuple[str, ...] = field(
        default_factory=lambda: tuple(s for s, _ in _HARMFUL_PATTERNS)
    )

    @property
    def crisis_pattern_count(self) -> int:
        return len(_CRISIS_PATTERNS)

    @property
    def harmful_pattern_count(self) -> int:
        return len(_HARMFUL_PATTERNS)


def coverage() -> SafetyCoverage:
    return SafetyCoverage()

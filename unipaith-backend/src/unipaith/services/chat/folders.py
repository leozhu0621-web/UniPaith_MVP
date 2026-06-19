"""Preset (white-paper-topic) folders + a deterministic auto-categorizer.

Pure (no DB). The categorizer files a free-text session into one of the eight
white-paper topics by keyword; default -> 'profile'. An LLM seam can replace
this later, but deterministic keeps it testable and free.
"""

from __future__ import annotations

from unipaith.models.chat_session import TOPIC_STAGE

_TOPIC_NAME = {
    "profile": "Profile",
    "goals": "Goals",
    "needs": "Needs",
    "strategy": "Strategy",
    "schools": "Schools",
    "connect": "Connect",
    "prepare": "Prepare",
    "manage": "Manage",
}

# Display order = the left-rail order.
_ORDER = ["profile", "goals", "needs", "strategy", "schools", "connect", "prepare", "manage"]

PRESET_FOLDERS = [
    {"topic_key": k, "name": _TOPIC_NAME[k], "stage": TOPIC_STAGE[k], "sort_order": i}
    for i, k in enumerate(_ORDER)
]

# Keyword -> topic, checked in priority order (first match wins).
_KEYWORDS: list[tuple[str, tuple[str, ...]]] = [
    ("needs", ("pay", "afford", "fund", "scholarship", "aid", "cost", "tuition", "budget", "loan")),
    (
        "prepare",
        (
            "statement",
            "essay",
            "sop",
            "recommend",
            "letter",
            "interview",
            "gre",
            "toefl",
            "ielts",
            "test",
            "resume",
            "cv",
            "portfolio",
        ),
    ),
    ("manage", ("deadline", "due", "submit", "checklist", "track", "status", "application")),
    ("connect", ("reach out", "professor", "faculty", "event", "fair", "info session", "connect")),
    ("strategy", ("strategy", "angle", "position", "balance", "reach", "target", "safety")),
    ("schools", ("school", "university", "college", "program", "compare", "list")),
    ("goals", ("goal", "career", "future", "why a", "dream", "aspir")),
    ("profile", ("value", "identity", "story", "who am i", "background", "personality")),
]


def categorize(text: str | None) -> str:
    t = (text or "").lower()
    for topic, words in _KEYWORDS:
        if any(w in t for w in words):
            return topic
    return "profile"

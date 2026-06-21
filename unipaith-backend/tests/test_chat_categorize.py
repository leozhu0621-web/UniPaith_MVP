"""Session auto-categorization (chat-tab spec §3.2) — the keyword→topic map.

`categorize` is the routing core behind session auto-filing and naming: a free-text
session is filed into one of the eight White-Paper folders by keyword (first match
wins, case-insensitive), defaulting to 'profile'. Pure — no DB — so these are fast
and protect the map from a silent regression by a concurrent edit.
"""

import pytest

from unipaith.services.chat.folders import PRESET_FOLDERS, categorize


@pytest.mark.parametrize(
    "text,expected",
    [
        # Needs (funding)
        ("How do I pay for this?", "needs"),
        ("Find me a scholarship", "needs"),
        ("What's the tuition cost?", "needs"),
        ("I need financial aid", "needs"),
        # Prepare (essays / tests / interviews)
        ("Help me draft my essay", "prepare"),
        ("Personal statement feedback", "prepare"),
        ("Interview practice", "prepare"),
        ("TOEFL prep", "prepare"),
        ("Review my resume", "prepare"),
        # Manage (application tracking)
        ("When is the application deadline?", "manage"),
        ("Build my submission checklist", "manage"),
        ("Track my status", "manage"),
        # Connect (outreach / events)
        ("Reach out to a professor", "connect"),
        ("Any campus events?", "connect"),
        ("Sign up for the info session", "connect"),
        # Strategy
        ("What's my angle?", "strategy"),
        ("Balance reach and safety schools", "strategy"),  # 'reach' (strategy) before 'school'
        # Schools
        ("Build my school list", "schools"),
        ("Compare these universities", "schools"),
        ("Tell me about this program", "schools"),
        # Goals
        ("My career goal", "goals"),
        ("My dream is medicine", "goals"),
        # Profile (values / identity / story)
        ("What are my values?", "profile"),
        ("Who am I, really?", "profile"),
        ("My background", "profile"),
    ],
)
def test_categorize_routes_by_keyword(text, expected):
    assert categorize(text) == expected


def test_categorize_priority_first_match_wins():
    # 'scholarship' (needs) precedes 'school' (schools) in the priority list.
    assert categorize("a scholarship for that school") == "needs"
    # 'essay' (prepare) precedes 'deadline' (manage).
    assert categorize("my essay is due on the deadline") == "prepare"


def test_categorize_is_case_insensitive():
    assert categorize("SCHOLARSHIP") == "needs"
    assert categorize("Interview") == "prepare"


def test_categorize_defaults_to_profile():
    assert categorize("hello there") == "profile"
    assert categorize("") == "profile"
    assert categorize(None) == "profile"


def test_every_categorize_topic_has_a_preset_folder():
    """Every topic the categorizer can return must map to a real preset folder,
    or a session would be filed into a folder that doesn't exist."""
    folder_keys = {f["topic_key"] for f in PRESET_FOLDERS}
    topics = {
        categorize(t)
        for t in ("scholarship", "essay", "deadline", "professor", "angle", "school", "goal", "")
    }
    assert topics <= folder_keys

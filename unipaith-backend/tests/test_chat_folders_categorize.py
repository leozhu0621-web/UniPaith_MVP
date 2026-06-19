"""Pure auto-categorizer + preset-folder catalog (sessions data model)."""

import pytest

from unipaith.services.chat.folders import PRESET_FOLDERS, categorize


def test_preset_folders_cover_all_eight_topics():
    keys = [f["topic_key"] for f in PRESET_FOLDERS]
    assert keys == [
        "profile",
        "goals",
        "needs",
        "strategy",
        "schools",
        "connect",
        "prepare",
        "manage",
    ]


@pytest.mark.parametrize(
    "text,topic",
    [
        ("How do I pay for this?", "needs"),
        ("scholarships I qualify for", "needs"),
        ("draft my statement of purpose", "prepare"),
        ("who should write my recommendation", "prepare"),
        ("when is the deadline", "manage"),
        ("compare Carnegie Mellon and Toronto", "schools"),
        ("why a master's, not a job", "goals"),
        ("reach out to a professor", "connect"),
        ("sharpen my angle", "strategy"),
        ("something totally unrelated zzz", "profile"),  # default bucket
    ],
)
def test_categorize_maps_text_to_topic(text, topic):
    assert categorize(text) == topic

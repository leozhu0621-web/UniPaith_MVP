"""Spec 71 §3 — deterministic prospect→ambassador tag-matching. Pure functions."""

from __future__ import annotations

from unipaith.services.ambassador_match import ambassador_match_score, match_ambassadors


def test_match_score_overlap():
    prospect = {"fields": ["cs"], "countries": ["india"], "interests": ["ml", "robotics"]}
    perfect = {"fields": ["cs"], "countries": ["india"], "interests": ["ml", "robotics"]}
    none = {"fields": ["history"], "countries": ["france"], "interests": ["art"]}
    partial = {"fields": ["cs"], "countries": ["usa"], "interests": ["ml"]}
    assert ambassador_match_score(prospect, perfect) == 1.0
    assert ambassador_match_score(prospect, none) == 0.0
    s_partial = ambassador_match_score(prospect, partial)
    assert 0.0 < s_partial < 1.0


def test_match_ambassadors_ranks_filters_limits():
    prospect = {"fields": ["cs"], "countries": ["india"], "interests": ["ml"]}
    ambassadors = [
        {"id": "best", "fields": ["cs"], "countries": ["india"], "interests": ["ml"]},
        {"id": "mid", "fields": ["cs"], "countries": ["usa"], "interests": ["ml"]},
        {"id": "none", "fields": ["history"], "countries": ["france"], "interests": ["art"]},
        {
            "id": "closed",
            "fields": ["cs"],
            "countries": ["india"],
            "interests": ["ml"],
            "accepting_chats": False,
        },
    ]
    ranked = match_ambassadors(prospect, ambassadors)
    ids = [r["ambassador_id"] for r in ranked]
    assert ids[0] == "best"  # highest overlap first
    assert "none" not in ids  # below min_score (no overlap)
    assert "closed" not in ids  # not accepting chats
    assert ranked[0]["score"] > ranked[1]["score"]


def test_match_ambassadors_respects_limit():
    prospect = {"fields": ["cs"]}
    ambassadors = [{"id": f"a{i}", "fields": ["cs"]} for i in range(20)]
    assert len(match_ambassadors(prospect, ambassadors, limit=5)) == 5

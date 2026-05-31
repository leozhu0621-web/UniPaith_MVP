"""JSON schemas for the Connect AI agents (Spec 20 §8).

- ``SUBMIT_RANKING_TOOL`` — ConnectFeedRanker returns the feed item ids in
  relevance order (most relevant first).
- ``SUBMIT_EVENT_RECS_TOOL`` — EventRecommender returns the ids of events worth
  surfacing to the student.

Both agents are Haiku-tier (cheap ranking) and the calling service always has
a deterministic fallback, so a malformed or empty tool call is non-fatal.
"""

SCHEMA_VERSION = 1


SUBMIT_RANKING_TOOL = {
    "name": "submit_ranking",
    "description": (
        "Return the provided Connect feed item ids ordered by relevance to the "
        "student (most relevant first). Include every id exactly once. Prioritize "
        "program changes and approaching deadlines on programs the student has "
        "applied to or saved, then timely posts from those institutions. Do not "
        "invent ids."
    ),
    "input_schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["ranked_ids"],
        "properties": {
            "ranked_ids": {
                "type": "array",
                "maxItems": 200,
                "description": "The item ids, most relevant first.",
                "items": {"type": "string", "minLength": 1, "maxLength": 80},
            }
        },
    },
}


SUBMIT_EVENT_RECS_TOOL = {
    "name": "submit_event_recommendations",
    "description": (
        "Return the ids of events the student should be nudged to attend — events "
        "on programs they've applied to or saved that they have not yet RSVP'd. "
        "Order by relevance, most relevant first. An empty list is valid. Do not "
        "invent ids."
    ),
    "input_schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["recommended_ids"],
        "properties": {
            "recommended_ids": {
                "type": "array",
                "maxItems": 50,
                "items": {"type": "string", "minLength": 1, "maxLength": 80},
            }
        },
    },
}


# ── Changelog ──────────────────────────────────────────────────────────────
# v1 (2026-05-31): initial schema for Spec 20 ConnectFeedRanker + EventRecommender.

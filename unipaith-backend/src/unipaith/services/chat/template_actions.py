"""ACTION_CATALOG — code-backed capabilities available as template steps.

This is a code constant (NOT a DB table; not Airtable-editable). Each key
maps to a display label. The runner wires each key to its implementation.
"""

from __future__ import annotations

ACTION_CATALOG: dict[str, dict[str, str]] = {
    "build_school_list": {"label": "Build school list"},
    "generate_strategy": {"label": "Generate strategy"},
    "compare_schools": {"label": "Compare schools"},
    "draft_feedback": {"label": "Draft feedback"},
    "interview_practice": {"label": "Interview practice"},
    "build_checklist": {"label": "Build checklist"},
    "find_events": {"label": "Find events"},
    "generate_needs_map": {"label": "Generate needs map"},
    "generate_goal_stack": {"label": "Generate goal stack"},
}

ACTION_KEYS: frozenset[str] = frozenset(ACTION_CATALOG)

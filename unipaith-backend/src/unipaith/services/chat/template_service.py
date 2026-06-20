"""TemplateService — load session templates and idempotently seed them.

``load`` returns all active templates ordered by sort_order, each with their
steps ordered by step_order. ``ensure_seeded`` inserts any missing templates
from the in-code TEMPLATE_LIBRARY constant (insert-if-absent by key), so
re-seeding on every boot never clobbers Airtable-driven edits.

``validate_library`` checks every step references a valid prompt_key (from the
enrichment_planner CATALOG) or a valid action_key (from ACTION_CATALOG). It is
run by ensure_seeded and exposed as a standalone helper for tests.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from unipaith.models.session_template import SessionTemplate, SessionTemplateStep
from unipaith.services.chat.template_actions import ACTION_KEYS
from unipaith.services.enrichment_planner import CATALOG

# The full set of valid prompt keys from the enrichment planner catalog.
_CATALOG_KEYS: frozenset[str] = frozenset(f["key"] for f in CATALOG)

# ---------------------------------------------------------------------------
# Seed library
# ---------------------------------------------------------------------------

# Each entry: key, title, topic, stage, outcome, icon, steps list.
# steps: list of dicts with step_type, prompt_key|action_key, label.
TEMPLATE_LIBRARY: list[dict[str, Any]] = [
    {
        "key": "tell_your_story",
        "title": "Tell your story",
        "topic": "profile",
        "stage": "discovery",
        "outcome": "A fuller profile",
        "icon": "pen",
        "steps": [
            {"step_type": "prompt", "prompt_key": "current_education_level", "label": "Background"},
            {"step_type": "prompt", "prompt_key": "strongest_subjects", "label": "Academics"},
            {"step_type": "prompt", "prompt_key": "activities", "label": "Experience"},
            {"step_type": "prompt", "prompt_key": "identity", "label": "Values"},
        ],
    },
    {
        "key": "set_your_goals",
        "title": "Set your goals",
        "topic": "goals",
        "stage": "discovery",
        "outcome": "Your goal stack",
        "icon": "flag",
        "steps": [
            {"step_type": "prompt", "prompt_key": "career_goal", "label": "Career"},
            {"step_type": "prompt", "prompt_key": "goal_after_degree", "label": "After"},
            {"step_type": "prompt", "prompt_key": "goals", "label": "Targets"},
            {"step_type": "action", "action_key": "generate_goal_stack", "label": "Your stack"},
        ],
    },
    {
        "key": "what_you_need",
        "title": "What you need to thrive",
        "topic": "needs",
        "stage": "discovery",
        "outcome": "Your needs map",
        "icon": "heart",
        "steps": [
            {"step_type": "prompt", "prompt_key": "needs", "label": "Needs"},
            {"step_type": "prompt", "prompt_key": "weight_cost", "label": "Cost"},
            {"step_type": "prompt", "prompt_key": "weight_outcomes", "label": "Outcomes"},
            {"step_type": "action", "action_key": "generate_needs_map", "label": "Your map"},
        ],
    },
    {
        "key": "sharpen_strategy",
        "title": "Sharpen your strategy",
        "topic": "strategy",
        "stage": "recommendation",
        "outcome": "Your angle",
        "icon": "compass",
        "steps": [
            {
                "step_type": "prompt",
                "prompt_key": "target_degree_level",
                "label": "Direction",
            },
            {"step_type": "prompt", "prompt_key": "field_of_interest", "label": "Field"},
            {"step_type": "action", "action_key": "generate_strategy", "label": "Your angle"},
        ],
    },
    {
        "key": "build_school_list",
        "title": "Build my school list",
        "topic": "schools",
        "stage": "recommendation",
        "outcome": "A ranked list — fit + odds",
        "icon": "list",
        "steps": [
            {
                "step_type": "prompt",
                "prompt_key": "target_degree_level",
                "label": "Direction",
            },
            {"step_type": "prompt", "prompt_key": "preferred_countries", "label": "Where"},
            {"step_type": "prompt", "prompt_key": "budget_band", "label": "Budget"},
            {"step_type": "action", "action_key": "build_school_list", "label": "Your list"},
        ],
    },
    {
        "key": "compare_schools",
        "title": "Compare schools",
        "topic": "schools",
        "stage": "recommendation",
        "outcome": "A side-by-side",
        "icon": "scale",
        "steps": [
            {"step_type": "prompt", "prompt_key": "preferred_countries", "label": "Criteria"},
            {"step_type": "action", "action_key": "compare_schools", "label": "Compare"},
        ],
    },
    {
        "key": "find_events",
        "title": "Find events",
        "topic": "connect",
        "stage": "application",
        "outcome": "Events to attend",
        "icon": "calendar",
        "steps": [
            {"step_type": "prompt", "prompt_key": "preferred_countries", "label": "Interest"},
            {"step_type": "action", "action_key": "find_events", "label": "Events"},
        ],
    },
    {
        "key": "plan_deadlines",
        "title": "Plan my deadlines",
        "topic": "manage",
        "stage": "application",
        "outcome": "A checklist + calendar",
        "icon": "calendar",
        "steps": [
            {"step_type": "action", "action_key": "build_checklist", "label": "Checklist"},
        ],
    },
]


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_library(library: list[dict[str, Any]] | None = None) -> None:
    """Validate all steps in *library* (defaults to TEMPLATE_LIBRARY).

    Raises ValueError on the first invalid step found. Checks:
    - step_type matches which key field is set
    - prompt_key is in the enrichment_planner CATALOG
    - action_key is in ACTION_CATALOG
    """
    if library is None:
        library = TEMPLATE_LIBRARY
    for tmpl in library:
        tkey = tmpl["key"]
        for i, step in enumerate(tmpl["steps"]):
            stype = step.get("step_type")
            pkey = step.get("prompt_key")
            akey = step.get("action_key")

            # Exactly one key must be set
            if bool(pkey) == bool(akey):
                raise ValueError(
                    f"Template '{tkey}' step {i}: exactly one of prompt_key / action_key "
                    f"must be set (got prompt_key={pkey!r}, action_key={akey!r})"
                )

            if stype == "prompt":
                if not pkey:
                    raise ValueError(
                        f"Template '{tkey}' step {i}: step_type='prompt' requires prompt_key"
                    )
                if pkey not in _CATALOG_KEYS:
                    raise ValueError(
                        f"Template '{tkey}' step {i}: prompt_key {pkey!r} not in CATALOG"
                    )
            elif stype == "action":
                if not akey:
                    raise ValueError(
                        f"Template '{tkey}' step {i}: step_type='action' requires action_key"
                    )
                if akey not in ACTION_KEYS:
                    raise ValueError(
                        f"Template '{tkey}' step {i}: action_key {akey!r} not in ACTION_CATALOG"
                    )
            else:
                raise ValueError(f"Template '{tkey}' step {i}: invalid step_type {stype!r}")


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class TemplateService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def ensure_seeded(self) -> None:
        """Insert any TEMPLATE_LIBRARY templates not already present (idempotent by key)."""
        validate_library()

        for sort_idx, tmpl in enumerate(TEMPLATE_LIBRARY):
            # Check if key already exists
            result = await self.db.execute(
                select(SessionTemplate).where(SessionTemplate.key == tmpl["key"])
            )
            existing = result.scalar_one_or_none()
            if existing is not None:
                continue

            # Insert template
            result = await self.db.execute(
                pg_insert(SessionTemplate)
                .values(
                    key=tmpl["key"],
                    title=tmpl["title"],
                    topic=tmpl["topic"],
                    stage=tmpl["stage"],
                    outcome=tmpl["outcome"],
                    icon=tmpl["icon"],
                    sort_order=sort_idx,
                    active=True,
                )
                .on_conflict_do_nothing(index_elements=["key"])
                .returning(SessionTemplate.id)
            )
            row = result.fetchone()
            if row is None:
                # Conflict: another concurrent insert won; skip steps
                continue
            template_id = row[0]

            # Insert steps
            for step_order, step in enumerate(tmpl["steps"]):
                await self.db.execute(
                    pg_insert(SessionTemplateStep).values(
                        template_id=template_id,
                        step_order=step_order,
                        step_type=step["step_type"],
                        prompt_key=step.get("prompt_key"),
                        action_key=step.get("action_key"),
                        label=step["label"],
                    )
                )

        await self.db.flush()

    async def load(self) -> list[dict[str, Any]]:
        """Return all active templates ordered by sort_order, with steps."""
        rows = (
            (
                await self.db.execute(
                    select(SessionTemplate)
                    .where(SessionTemplate.active.is_(True))
                    .order_by(SessionTemplate.sort_order, SessionTemplate.key)
                    .options(selectinload(SessionTemplate.steps))
                )
            )
            .scalars()
            .all()
        )

        result = []
        for tmpl in rows:
            steps = sorted(tmpl.steps, key=lambda s: s.step_order)
            result.append(
                {
                    "key": tmpl.key,
                    "title": tmpl.title,
                    "topic": tmpl.topic,
                    "stage": tmpl.stage,
                    "outcome": tmpl.outcome,
                    "icon": tmpl.icon,
                    "steps": [
                        {
                            "step_order": s.step_order,
                            "step_type": s.step_type,
                            **({"prompt_key": s.prompt_key} if s.prompt_key else {}),
                            **({"action_key": s.action_key} if s.action_key else {}),
                            "label": s.label,
                        }
                        for s in steps
                    ],
                }
            )
        return result

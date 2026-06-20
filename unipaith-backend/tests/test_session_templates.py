"""Session templates data layer — models, service, seed, and validation.

Tests:
(a) validate_library() passes on TEMPLATE_LIBRARY (guards against typos in seed)
(b) ensure_seeded() + load() returns 8 templates each with ordered steps;
    spot-check build_school_list has 4 steps ending in an action step
(c) ensure_seeded() is idempotent (run twice → still 8 templates)
(d) a deliberately-bad step (action_key not in ACTION_KEYS) raises ValueError
"""

from __future__ import annotations

import pytest
from sqlalchemy import func as safunc
from sqlalchemy import select

from unipaith.models.session_template import SessionTemplate, SessionTemplateStep
from unipaith.services.chat.template_actions import ACTION_KEYS
from unipaith.services.chat.template_service import (
    TEMPLATE_LIBRARY,
    TemplateService,
    validate_library,
)

# ---------------------------------------------------------------------------
# (a) Validate the seed library passes
# ---------------------------------------------------------------------------


def test_validate_library_passes():
    """All prompt_keys in CATALOG and action_keys in ACTION_KEYS — no typos."""
    validate_library()  # must not raise


# ---------------------------------------------------------------------------
# (b) After ensure_seeded, load returns 8 templates with ordered steps
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ensure_seeded_then_load(db_session):
    svc = TemplateService(db_session)
    await svc.ensure_seeded()
    templates = await svc.load()

    assert len(templates) == 8

    # Every template has at least one step
    for tmpl in templates:
        assert len(tmpl["steps"]) >= 1, f"Template {tmpl['key']} has no steps"

    # Steps are in step_order order
    for tmpl in templates:
        orders = [s["step_order"] for s in tmpl["steps"]]
        assert orders == sorted(orders), f"Steps for {tmpl['key']} are not sorted"

    # Spot-check build_school_list
    bsl = next(t for t in templates if t["key"] == "build_school_list")
    assert len(bsl["steps"]) == 4
    last_step = bsl["steps"][-1]
    assert last_step["step_type"] == "action"
    assert last_step.get("action_key") == "build_school_list"


# ---------------------------------------------------------------------------
# (c) ensure_seeded is idempotent
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ensure_seeded_is_idempotent(db_session):
    svc = TemplateService(db_session)
    await svc.ensure_seeded()
    await svc.ensure_seeded()

    n_templates = (
        await db_session.execute(select(safunc.count()).select_from(SessionTemplate))
    ).scalar()
    assert n_templates == 8

    n_steps = (
        await db_session.execute(select(safunc.count()).select_from(SessionTemplateStep))
    ).scalar()
    # Total steps across all 8 templates
    expected_steps = sum(len(tmpl["steps"]) for tmpl in TEMPLATE_LIBRARY)
    assert n_steps == expected_steps


# ---------------------------------------------------------------------------
# (d) A bad action_key raises ValueError
# ---------------------------------------------------------------------------


def test_validate_library_rejects_bad_action_key():
    bad_library = [
        {
            "key": "bad_template",
            "title": "Bad",
            "topic": "manage",
            "stage": "application",
            "outcome": "Nothing",
            "icon": "x",
            "steps": [
                {
                    "step_type": "action",
                    "action_key": "nonexistent_action_xyz",
                    "label": "Fail",
                }
            ],
        }
    ]
    with pytest.raises(ValueError, match="action_key"):
        validate_library(bad_library)


def test_validate_library_rejects_bad_prompt_key():
    bad_library = [
        {
            "key": "bad_prompt_template",
            "title": "Bad Prompt",
            "topic": "profile",
            "stage": "discovery",
            "outcome": "Nothing",
            "icon": "x",
            "steps": [
                {
                    "step_type": "prompt",
                    "prompt_key": "nonexistent_field_xyz",
                    "label": "Fail",
                }
            ],
        }
    ]
    with pytest.raises(ValueError, match="not in CATALOG"):
        validate_library(bad_library)


def test_validate_library_rejects_both_keys_set():
    bad_library = [
        {
            "key": "both_keys",
            "title": "Both",
            "topic": "profile",
            "stage": "discovery",
            "outcome": "Nothing",
            "icon": "x",
            "steps": [
                {
                    "step_type": "prompt",
                    "prompt_key": "goals",
                    "action_key": "build_school_list",
                    "label": "Fail",
                }
            ],
        }
    ]
    with pytest.raises(ValueError, match="exactly one"):
        validate_library(bad_library)


# ---------------------------------------------------------------------------
# Sanity: ACTION_KEYS is non-empty and contains expected entries
# ---------------------------------------------------------------------------


def test_action_keys_content():
    assert "build_school_list" in ACTION_KEYS
    assert "generate_strategy" in ACTION_KEYS
    assert "generate_goal_stack" in ACTION_KEYS
    assert len(ACTION_KEYS) == 9

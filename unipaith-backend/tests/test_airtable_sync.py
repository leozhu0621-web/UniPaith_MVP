"""Airtable → DB sync tests — NO real Airtable API calls.

A FakeClient with canned records drives all assertions.  Uses the
``db_session`` fixture from conftest.py (real Postgres, isolated schema).

Tests:
(a) valid prompts upserted with airtable_record_id set
(b) invalid prompt collected in rejected, not raised
(c) second sync_all() is idempotent
(d) templates + steps upserted with validation
(e) invalid step (unknown prompt_key) rejected, not raised
(f) sync_all() with is_configured=False returns skipped marker, writes nothing
(g) template with linked-record step pattern (Template: [id]) resolves correctly
"""

from __future__ import annotations

from typing import Any

import pytest
from sqlalchemy import select

from unipaith.models.prompt_catalog import PromptCatalog
from unipaith.models.session_template import SessionTemplate, SessionTemplateStep
from unipaith.services.airtable.sync_service import (
    AirtableSyncService,
    validate_prompt_row,
)

# ---------------------------------------------------------------------------
# Fake client
# ---------------------------------------------------------------------------


class FakeClient:
    """A minimal fake that replaces AirtableClient in tests."""

    def __init__(
        self,
        *,
        is_configured: bool = True,
        prompts: list[dict[str, Any]] | None = None,
        templates: list[dict[str, Any]] | None = None,
        steps: list[dict[str, Any]] | None = None,
    ) -> None:
        self.is_configured = is_configured
        self._data: dict[str, list[dict[str, Any]]] = {
            "Prompts": prompts or [],
            "Templates": templates or [],
            "Template Steps": steps or [],
        }

    async def list_records(self, table_name: str) -> list[dict[str, Any]]:
        return self._data.get(table_name, [])


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

_VALID_PROMPT_1 = {
    "id": "rec_prompt_001",
    "fields": {
        "key": "airtable_test_field",
        "section": "Test Section",
        "question": "What is your test value?",
        "ask_kind": "text",
        "value_type": "text",
        "options": None,
        "tier": "standard",
        "required": False,
        "display_logic": [],
        "saves_to": "airtable_test_field",
        "sort_order": 100,
        "active": True,
    },
}

# An existing seed-catalog key — tests update path.
_VALID_PROMPT_EXISTING_KEY = {
    "id": "rec_prompt_gender",
    "fields": {
        "key": "gender",
        "section": "Basics",
        "question": "Which best describes you? (updated by Airtable)",
        "ask_kind": "choice",
        "value_type": "categorical",
        "options": ["Woman", "Man", "Non-binary", "Another identity", "Prefer not to say"],
        "tier": "essential",
        "required": True,
        "display_logic": [],
        "saves_to": "gender",
        "sort_order": 0,
        "active": True,
    },
}

_INVALID_PROMPT_BAD_ASK_KIND = {
    "id": "rec_prompt_bad",
    "fields": {
        "key": "invalid_field",
        "section": "Test",
        "question": "Bad widget?",
        "ask_kind": "unknown_widget_type",  # not valid
        "value_type": "text",
        "saves_to": "invalid_field",
        "sort_order": 200,
        "active": True,
    },
}

_VALID_TEMPLATE_1 = {
    "id": "rec_tmpl_001",
    "fields": {
        "key": "airtable_test_template",
        "title": "Airtable Test Template",
        "topic": "test",
        "stage": "discovery",
        "outcome": "A test outcome",
        "icon": "star",
        "sort_order": 50,
        "active": True,
    },
}

# Step referencing the valid prompt key from _VALID_PROMPT_1 — note: that
# prompt must already be in the DB (from sync_prompts) for step validation.
# For simplicity we use a key that's always in the seed catalog.
_VALID_STEP_1_PROMPT = {
    "id": "rec_step_001",
    "fields": {
        "template_key": "airtable_test_template",
        "step_type": "prompt",
        "prompt_key": "gender",  # always in seed catalog
        "label": "Your gender",
        "step_order": 0,
    },
}

_VALID_STEP_2_ACTION = {
    "id": "rec_step_002",
    "fields": {
        "template_key": "airtable_test_template",
        "step_type": "action",
        "action_key": "generate_strategy",  # always in ACTION_KEYS
        "label": "Strategy",
        "step_order": 1,
    },
}

_INVALID_STEP_BAD_PROMPT_KEY = {
    "id": "rec_step_bad",
    "fields": {
        "template_key": "airtable_test_template",
        "step_type": "prompt",
        "prompt_key": "nonexistent_catalog_key_xyz",
        "label": "Bad step",
        "step_order": 2,
    },
}


# ---------------------------------------------------------------------------
# Unit tests (no DB needed)
# ---------------------------------------------------------------------------


def test_validate_prompt_row_valid():
    assert validate_prompt_row(_VALID_PROMPT_1["fields"]) is None


def test_validate_prompt_row_missing_key():
    reason = validate_prompt_row({**_VALID_PROMPT_1["fields"], "key": ""})
    assert reason is not None
    assert "key" in reason


def test_validate_prompt_row_unknown_ask_kind():
    reason = validate_prompt_row(_INVALID_PROMPT_BAD_ASK_KIND["fields"])
    assert reason is not None
    assert "ask_kind" in reason


def test_validate_prompt_row_choice_missing_options():
    reason = validate_prompt_row(
        {**_VALID_PROMPT_1["fields"], "ask_kind": "choice", "options": None}
    )
    assert reason is not None
    assert "options" in reason


def test_validate_prompt_row_empty_saves_to():
    reason = validate_prompt_row({**_VALID_PROMPT_1["fields"], "saves_to": ""})
    assert reason is not None
    assert "saves_to" in reason


# ---------------------------------------------------------------------------
# Integration tests (real DB via db_session fixture)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_sync_prompts_valid_row_upserted(db_session):
    """A valid new prompt from Airtable is written to prompt_catalog."""
    client = FakeClient(prompts=[_VALID_PROMPT_1])
    svc = AirtableSyncService(db_session, client)
    result = await svc.sync_prompts()
    await db_session.commit()

    assert result["upserted"] == 1
    assert result["rejected"] == []

    row = await db_session.scalar(
        select(PromptCatalog).where(PromptCatalog.key == "airtable_test_field")
    )
    assert row is not None
    assert row.airtable_record_id == "rec_prompt_001"
    assert row.section == "Test Section"


@pytest.mark.asyncio
async def test_sync_prompts_update_existing_key(db_session):
    """A prompt with a key already in prompt_catalog is updated (question changes)."""
    # Seed the prompt_catalog with the base entry first.
    from unipaith.services.catalog_service import CatalogService

    await CatalogService(db_session).ensure_seeded()
    await db_session.commit()

    client = FakeClient(prompts=[_VALID_PROMPT_EXISTING_KEY])
    svc = AirtableSyncService(db_session, client)
    result = await svc.sync_prompts()
    await db_session.commit()

    assert result["upserted"] == 1
    assert result["rejected"] == []

    row = await db_session.scalar(select(PromptCatalog).where(PromptCatalog.key == "gender"))
    assert row is not None
    assert row.airtable_record_id == "rec_prompt_gender"
    # Question was updated from the seed value
    assert "updated by Airtable" in row.question


@pytest.mark.asyncio
async def test_sync_prompts_invalid_row_rejected(db_session):
    """An invalid prompt row is collected in rejected, not raised, not written."""
    client = FakeClient(prompts=[_INVALID_PROMPT_BAD_ASK_KIND])
    svc = AirtableSyncService(db_session, client)
    result = await svc.sync_prompts()

    assert result["upserted"] == 0
    assert len(result["rejected"]) == 1
    assert result["rejected"][0]["key"] == "invalid_field"
    assert "ask_kind" in result["rejected"][0]["reason"]

    # Nothing written
    row = await db_session.scalar(select(PromptCatalog).where(PromptCatalog.key == "invalid_field"))
    assert row is None


@pytest.mark.asyncio
async def test_sync_all_idempotent(db_session):
    """Running sync_all twice produces the same result (no duplicates, no errors)."""
    client = FakeClient(
        prompts=[_VALID_PROMPT_1, _VALID_PROMPT_EXISTING_KEY],
        templates=[_VALID_TEMPLATE_1],
        steps=[_VALID_STEP_1_PROMPT, _VALID_STEP_2_ACTION],
    )

    # Patch settings table names to match FakeClient keys

    original_sync_all = AirtableSyncService.sync_all

    async def patched_sync_all(self):
        if not self.client.is_configured:
            return {"skipped": "airtable not configured"}
        prompts_result = await self.sync_prompts(table_name="Prompts")
        templates_result = await self.sync_templates(
            templates_table="Templates",
            steps_table="Template Steps",
        )
        return {"prompts": prompts_result, "templates": templates_result}

    AirtableSyncService.sync_all = patched_sync_all  # type: ignore[method-assign]
    try:
        svc = AirtableSyncService(db_session, client)
        r1 = await svc.sync_all()
        await db_session.commit()
        r2 = await svc.sync_all()
        await db_session.commit()
    finally:
        AirtableSyncService.sync_all = original_sync_all  # type: ignore[method-assign]

    # Both runs succeed
    assert r1["prompts"]["upserted"] >= 1
    assert r2["prompts"]["upserted"] >= 1

    # No duplicates in DB
    count = (
        (
            await db_session.execute(
                select(PromptCatalog).where(PromptCatalog.key == "airtable_test_field")
            )
        )
        .scalars()
        .all()
    )
    assert len(count) == 1


@pytest.mark.asyncio
async def test_sync_all_unconfigured_returns_skipped(db_session):
    """When is_configured=False, sync_all returns skipped marker and writes nothing."""
    client = FakeClient(
        is_configured=False,
        prompts=[_VALID_PROMPT_1],
    )
    svc = AirtableSyncService(db_session, client)
    result = await svc.sync_all()

    assert result == {"skipped": "airtable not configured"}

    # Nothing was written
    row = await db_session.scalar(
        select(PromptCatalog).where(PromptCatalog.key == "airtable_test_field")
    )
    assert row is None


@pytest.mark.asyncio
async def test_sync_templates_upserted(db_session):
    """A valid template + steps are written to session_templates / steps."""
    client = FakeClient(
        templates=[_VALID_TEMPLATE_1],
        steps=[_VALID_STEP_1_PROMPT, _VALID_STEP_2_ACTION],
    )
    svc = AirtableSyncService(db_session, client)
    result = await svc.sync_templates(
        templates_table="Templates",
        steps_table="Template Steps",
    )
    await db_session.commit()

    assert result["upserted"] == 1
    assert result["rejected"] == []

    tmpl = await db_session.scalar(
        select(SessionTemplate).where(SessionTemplate.key == "airtable_test_template")
    )
    assert tmpl is not None
    assert tmpl.airtable_record_id == "rec_tmpl_001"

    steps = (
        (
            await db_session.execute(
                select(SessionTemplateStep)
                .where(SessionTemplateStep.template_id == tmpl.id)
                .order_by(SessionTemplateStep.step_order)
            )
        )
        .scalars()
        .all()
    )
    assert len(steps) == 2
    assert steps[0].step_type == "prompt"
    assert steps[0].prompt_key == "gender"
    assert steps[1].step_type == "action"
    assert steps[1].action_key == "generate_strategy"


@pytest.mark.asyncio
async def test_sync_templates_invalid_step_rejected(db_session):
    """A step with an unknown prompt_key is rejected; valid steps still upsert."""
    client = FakeClient(
        templates=[_VALID_TEMPLATE_1],
        steps=[_VALID_STEP_1_PROMPT, _INVALID_STEP_BAD_PROMPT_KEY],
    )
    svc = AirtableSyncService(db_session, client)
    result = await svc.sync_templates(
        templates_table="Templates",
        steps_table="Template Steps",
    )
    await db_session.commit()

    # Template itself is upserted
    assert result["upserted"] == 1
    # The bad step is rejected
    assert any(
        "nonexistent_catalog_key_xyz" in r.get("key", "") or "catalog" in r.get("reason", "")
        for r in result["rejected"]
    )

    # Only the valid step was written
    tmpl = await db_session.scalar(
        select(SessionTemplate).where(SessionTemplate.key == "airtable_test_template")
    )
    steps = (
        (
            await db_session.execute(
                select(SessionTemplateStep).where(SessionTemplateStep.template_id == tmpl.id)
            )
        )
        .scalars()
        .all()
    )
    assert len(steps) == 1
    assert steps[0].prompt_key == "gender"


@pytest.mark.asyncio
async def test_sync_templates_linked_record_pattern(db_session):
    """Steps using the Airtable linked-record pattern (Template: [rec_id]) resolve correctly."""
    step_linked = {
        "id": "rec_step_linked",
        "fields": {
            # No template_key — use the Airtable linked-record field instead.
            "Template": ["rec_tmpl_001"],
            "step_type": "action",
            "action_key": "build_school_list",
            "label": "Build list",
            "step_order": 0,
        },
    }
    client = FakeClient(
        templates=[_VALID_TEMPLATE_1],
        steps=[step_linked],
    )
    svc = AirtableSyncService(db_session, client)
    result = await svc.sync_templates(
        templates_table="Templates",
        steps_table="Template Steps",
    )
    await db_session.commit()

    assert result["upserted"] == 1
    assert result["rejected"] == []

    tmpl = await db_session.scalar(
        select(SessionTemplate).where(SessionTemplate.key == "airtable_test_template")
    )
    steps = (
        (
            await db_session.execute(
                select(SessionTemplateStep).where(SessionTemplateStep.template_id == tmpl.id)
            )
        )
        .scalars()
        .all()
    )
    assert len(steps) == 1
    assert steps[0].action_key == "build_school_list"

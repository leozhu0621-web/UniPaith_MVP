"""Chat sessions API — /students/me/chat/* (sessions data model + templates)."""

import pytest
from sqlalchemy import select

from tests._uni_helpers import ensure_profile
from unipaith.models.prompt_catalog import PromptCatalog

BASE = "/api/v1/students/me/chat"


# ---------------------------------------------------------------------------
# Templates endpoint
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_templates_returns_at_least_eight(student_client, db_session, mock_student_user):
    """GET /templates seeds on first call and returns ≥8 templates."""
    await ensure_profile(db_session, mock_student_user)
    r = await student_client.get(f"{BASE}/templates")
    assert r.status_code == 200, r.text
    templates = r.json()
    assert len(templates) >= 8


@pytest.mark.asyncio
async def test_templates_shape(student_client, db_session, mock_student_user):
    """Every template has the required fields and at least one step."""
    await ensure_profile(db_session, mock_student_user)
    r = await student_client.get(f"{BASE}/templates")
    assert r.status_code == 200, r.text
    for tmpl in r.json():
        for field in ("key", "title", "topic", "stage", "outcome", "icon", "steps"):
            assert field in tmpl, f"Template {tmpl.get('key')!r} missing field {field!r}"
        assert len(tmpl["steps"]) >= 1, f"Template {tmpl['key']!r} has no steps"
        for step in tmpl["steps"]:
            assert "step_type" in step
            assert "label" in step
            # exactly one of prompt_key / action_key is present
            has_prompt = bool(step.get("prompt_key"))
            has_action = bool(step.get("action_key"))
            assert has_prompt != has_action, (
                f"Step in {tmpl['key']!r} should have exactly one key: {step}"
            )


@pytest.mark.asyncio
async def test_templates_prompt_steps_carry_descriptor(
    student_client, db_session, mock_student_user
):
    """Prompt steps expose ask_kind + question so the runner can render widgets."""
    await ensure_profile(db_session, mock_student_user)
    r = await student_client.get(f"{BASE}/templates")
    assert r.status_code == 200, r.text
    found_prompt = False
    for tmpl in r.json():
        for step in tmpl["steps"]:
            if step["step_type"] == "prompt":
                found_prompt = True
                pkey = step.get("prompt_key")
                tkey = tmpl["key"]
                assert step.get("ask_kind") is not None, (
                    f"prompt step {pkey!r} in {tkey!r} missing ask_kind"
                )
                assert step.get("question") is not None, (
                    f"prompt step {pkey!r} in {tkey!r} missing question"
                )
            elif step["step_type"] == "action":
                akey = step.get("action_key")
                tkey = tmpl["key"]
                assert step.get("action_label") is not None, (
                    f"action step {akey!r} in {tkey!r} missing action_label"
                )
                assert isinstance(step.get("action_available"), bool), (
                    f"action step {akey!r} in {tkey!r} missing action availability"
                )
                if step.get("action_available") is False:
                    assert step.get("availability_reason") is not None, (
                        f"action step {akey!r} in {tkey!r} missing unavailable reason"
                    )
    assert found_prompt, "No prompt steps found in any template"


@pytest.mark.asyncio
async def test_templates_use_runtime_prompt_catalog(student_client, db_session, mock_student_user):
    """Template prompt descriptors come from prompt_catalog, not the seed constant."""
    await ensure_profile(db_session, mock_student_user)
    first = await student_client.get(f"{BASE}/templates")
    assert first.status_code == 200, first.text

    result = await db_session.execute(
        select(PromptCatalog).where(PromptCatalog.key == "career_goal")
    )
    row = result.scalar_one()
    row.question = "Which career direction should Uni plan around?"
    await db_session.commit()

    r = await student_client.get(f"{BASE}/templates")
    assert r.status_code == 200, r.text
    career_steps = [
        step
        for tmpl in r.json()
        for step in tmpl["steps"]
        if step.get("prompt_key") == "career_goal"
    ]
    assert career_steps
    assert career_steps[0]["question"] == "Which career direction should Uni plan around?"


@pytest.mark.asyncio
async def test_templates_idempotent(student_client, db_session, mock_student_user):
    """Calling GET /templates twice does not duplicate rows."""
    await ensure_profile(db_session, mock_student_user)
    r1 = await student_client.get(f"{BASE}/templates")
    r2 = await student_client.get(f"{BASE}/templates")
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert len(r1.json()) == len(r2.json())


# ---------------------------------------------------------------------------
# Existing folder/session tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_folders_tree_has_eight_presets(student_client, db_session, mock_student_user):
    await ensure_profile(db_session, mock_student_user)
    r = await student_client.get(f"{BASE}/folders")
    assert r.status_code == 200, r.text
    presets = [f for f in r.json()["folders"] if f["kind"] == "preset"]
    assert len(presets) == 8


@pytest.mark.asyncio
async def test_create_session_auto_categorizes(student_client, db_session, mock_student_user):
    await ensure_profile(db_session, mock_student_user)
    r = await student_client.post(f"{BASE}/sessions", json={"title": "How do I pay for this?"})
    assert r.status_code == 200, r.text
    assert r.json()["topic_key"] == "needs"


@pytest.mark.asyncio
async def test_delete_preset_folder_rejected(student_client, db_session, mock_student_user):
    await ensure_profile(db_session, mock_student_user)
    tree = (await student_client.get(f"{BASE}/folders")).json()["folders"]
    schools = next(f for f in tree if f.get("topic_key") == "schools")
    r = await student_client.delete(f"{BASE}/folders/{schools['id']}")
    assert r.status_code == 400, r.text


@pytest.mark.asyncio
async def test_create_custom_folder_then_delete(student_client, db_session, mock_student_user):
    await ensure_profile(db_session, mock_student_user)
    c = await student_client.post(f"{BASE}/folders", json={"name": "Reach schools"})
    assert c.status_code == 200, c.text
    fid = c.json()["id"]
    d = await student_client.delete(f"{BASE}/folders/{fid}")
    assert d.status_code == 200, d.text


# ---------------------------------------------------------------------------
# Template action dispatch endpoint
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_action_unknown_key_returns_400(student_client, db_session, mock_student_user):
    """Unknown action_key → 400."""
    await ensure_profile(db_session, mock_student_user)
    r = await student_client.post(f"{BASE}/templates/action/not_a_real_action")
    assert r.status_code == 400, r.text


@pytest.mark.asyncio
async def test_action_build_school_list_no_5xx(student_client, db_session, mock_student_user):
    """build_school_list returns 200 with kind=school_list — never 5xx.

    Under AI_MOCK_MODE with a bare test student (no profile signals), the
    matcher returns ready=False, so the endpoint gracefully returns pending.
    """
    await ensure_profile(db_session, mock_student_user)
    r = await student_client.post(f"{BASE}/templates/action/build_school_list")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["action_key"] == "build_school_list"
    assert body["kind"] == "school_list"
    assert body["status"] in ("ready", "pending")
    # Shape invariants
    assert "title" in body
    assert body.get("items") is None or isinstance(body["items"], list)


@pytest.mark.asyncio
async def test_action_unavailable_key_returns_409(student_client, db_session, mock_student_user):
    """Actions without a real service are unavailable rather than shown as stubs."""
    await ensure_profile(db_session, mock_student_user)
    r = await student_client.post(f"{BASE}/templates/action/find_events")
    assert r.status_code == 409, r.text
    assert "not enabled" in r.json()["detail"].lower()
    assert "coming soon" not in r.text.lower()


@pytest.mark.asyncio
async def test_action_generate_strategy_no_5xx(student_client, db_session, mock_student_user):
    """generate_strategy returns 200 — gracefully degrades to pending if not enough signal."""
    await ensure_profile(db_session, mock_student_user)
    r = await student_client.post(f"{BASE}/templates/action/generate_strategy")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["action_key"] == "generate_strategy"
    assert body["kind"] == "strategy"
    assert body["status"] in ("ready", "pending")
    assert "title" in body

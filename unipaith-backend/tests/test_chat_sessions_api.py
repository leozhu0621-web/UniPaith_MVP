"""Chat sessions API — /students/me/chat/* (sessions data model + templates)."""

import pytest

from tests._uni_helpers import ensure_profile

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

"""Chat sessions API — /students/me/chat/* (sessions data model)."""

import pytest

from tests._uni_helpers import ensure_profile

BASE = "/api/v1/students/me/chat"


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

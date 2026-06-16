"""Follow-up questions — GapEngine detect + answer-applies-to-My-Space."""

import pytest

from tests._uni_helpers import ensure_profile
from unipaith.config import settings
from unipaith.services.follow_up_service import FollowUpService


@pytest.mark.asyncio
async def test_detect_categories_and_cap(db_session, mock_student_user):
    await ensure_profile(db_session, mock_student_user)
    imp = {
        "activities": [{"title": "Formula Club"}],  # no role → ambiguous
        "academic_records": [{"institution_name": "NEU", "degree_type": "bachelors"}],  # no gpa
        "field_of_study": "Business Analytics",
    }
    gaps = await FollowUpService(db_session).detect(mock_student_user.id, imp)
    cats = {g["category"] for g in gaps}
    assert "ambiguous" in cats
    assert "missing" in cats
    assert len(gaps) <= 5
    assert sum(1 for g in gaps if g["category"] == "deepen") <= 1
    for g in gaps:
        assert {"id", "category", "target_field", "prompt_hint", "kind"} <= set(g)


@pytest.mark.asyncio
async def test_detect_source_agnostic_no_import(db_session, mock_student_user):
    await ensure_profile(db_session, mock_student_user)
    gaps = await FollowUpService(db_session).detect(mock_student_user.id, None)
    # Fresh profile, no import → still offers missing/deepen prompts.
    assert any(g["category"] in ("missing", "deepen") for g in gaps)


@pytest.mark.asyncio
async def test_answer_writes_goal(db_session, mock_student_user):
    await ensure_profile(db_session, mock_student_user)
    out = await FollowUpService(db_session).answer(
        mock_student_user.id,
        {"category": "deepen", "target_field": "goal", "kind": "text"},
        "I love turning messy data into decisions",
    )
    assert out["applied"] is True
    from unipaith.services.goals_service import GoalsService

    goals = await GoalsService(db_session).list_goals(mock_student_user.id)
    assert any("data" in g.specific.lower() for g in goals)


@pytest.mark.asyncio
async def test_answer_skip_is_noop(db_session, mock_student_user):
    await ensure_profile(db_session, mock_student_user)
    out = await FollowUpService(db_session).answer(
        mock_student_user.id, {"target_field": "gpa"}, "skip"
    )
    assert out["applied"] is False


@pytest.mark.asyncio
async def test_followups_endpoints(student_client, db_session, mock_student_user, monkeypatch):
    await ensure_profile(db_session, mock_student_user)
    monkeypatch.setattr(settings, "ai_material_followups_v2_enabled", True)
    from unipaith.services.material_ingest_service import MaterialIngestService

    row = await MaterialIngestService(db_session).ingest(
        mock_student_user.id, filename="r.pdf", mime_type="application/pdf", data=b"x"
    )
    g = await student_client.get(f"/api/v1/students/me/materials/{row.id}/followups")
    assert g.status_code == 200
    assert isinstance(g.json()["questions"], list)
    a = await student_client.post(
        "/api/v1/students/me/materials/followups/answer",
        json={
            "gap": {"category": "deepen", "target_field": "goal", "kind": "text"},
            "answer": "I love data",
        },
    )
    assert a.status_code == 200
    assert a.json()["applied"] in (True, False)

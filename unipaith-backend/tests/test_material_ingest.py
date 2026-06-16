"""Material ingest — upload → AI read → confirm into My Space."""

from datetime import date

import pytest

from tests._uni_helpers import ensure_profile
from unipaith.ai.material_ingest import _content_block
from unipaith.config import settings
from unipaith.services.material_ingest_service import MaterialIngestService, _parse_date

# A realistic proposed payload (what the agent returns).
_PROPOSED = {
    "summary": "I picked up your CS degree, a research internship, and a GRE score.",
    "profile": {"first_name": "Sam", "last_name": "Rivera", "bio_text": "Aspiring ML researcher."},
    "academic_records": [
        {
            "institution_name": "State University",
            "degree_type": "bachelors",
            "field_of_study": "Computer Science",
            "gpa": 3.8,
            "gpa_scale": "4.0",
            "start_date": "2019-09",
            "end_date": "2023-05",
        }
    ],
    "test_scores": [{"test_type": "GRE", "total_score": 328, "test_date": "2023-10-01"}],
    "activities": [
        {"activity_type": "research", "title": "ML Lab RA", "organization": "State University"}
    ],
    "work_experiences": [
        {"experience_type": "internship", "organization": "Acme AI", "role_title": "ML Intern"}
    ],
    "goals": [{"category": "academic", "specific": "Earn a funded CS PhD", "time_bound": "2027"}],
    "needs": [
        {
            "maslow_level": "safety",
            "need_type": "funding",
            "signal": "Needs full funding",
            "severity": "must_have",
        }
    ],
    "identity": {
        "core_values": [{"value": "Curiosity", "evidence": "Self-driven research projects."}]
    },
}


def test_parse_date():
    assert _parse_date("2023-05-01") == date(2023, 5, 1)
    assert _parse_date("2023-05") == date(2023, 5, 1)
    assert _parse_date("2023") == date(2023, 1, 1)
    assert _parse_date("") is None
    assert _parse_date(None) is None
    assert _parse_date("not a date") is None


def test_content_block_pdf_image_text_unsupported():
    pdf = _content_block("application/pdf", b"%PDF-1.4 fake")
    assert pdf["type"] == "document" and pdf["source"]["media_type"] == "application/pdf"
    img = _content_block("image/png", b"\x89PNG fake")
    assert img["type"] == "image" and img["source"]["media_type"] == "image/png"
    txt = _content_block("text/plain", b"hello world")
    assert txt["type"] == "text" and "hello world" in txt["text"]
    with pytest.raises(ValueError):
        _content_block("application/zip", b"PK fake")


@pytest.mark.asyncio
async def test_ingest_flag_off_returns_failed(db_session, mock_student_user, monkeypatch):
    await ensure_profile(db_session, mock_student_user)
    monkeypatch.setattr(settings, "ai_material_ingest_v2_enabled", False)
    row = await MaterialIngestService(db_session).ingest(
        mock_student_user.id, filename="resume.pdf", mime_type="application/pdf", data=b"%PDF fake"
    )
    assert row.status == "failed"
    assert row.proposed is None
    assert row.error


@pytest.mark.asyncio
async def test_ingest_with_agent_stores_proposed(db_session, mock_student_user, monkeypatch):
    await ensure_profile(db_session, mock_student_user)
    monkeypatch.setattr(settings, "ai_material_ingest_v2_enabled", True)

    async def _fake_read(self, **kwargs):
        return _PROPOSED

    monkeypatch.setattr("unipaith.ai.material_ingest.MaterialIngestAgent.read", _fake_read)
    row = await MaterialIngestService(db_session).ingest(
        mock_student_user.id, filename="resume.pdf", mime_type="application/pdf", data=b"%PDF fake"
    )
    assert row.status == "parsed"
    assert row.proposed["summary"].startswith("I picked up")


@pytest.mark.asyncio
async def test_apply_writes_to_myspace(db_session, mock_student_user):
    await ensure_profile(db_session, mock_student_user)
    svc = MaterialIngestService(db_session)
    row = await svc.ingest(
        mock_student_user.id, filename="r.pdf", mime_type="application/pdf", data=b"x"
    )  # flag off in this test env → failed row, but we apply a selection directly
    out = await svc.apply(mock_student_user.id, row.id, _PROPOSED)
    counts = out["counts"]
    assert counts.get("goals") == 1
    assert counts.get("needs") == 1
    assert counts.get("academic_records") == 1
    assert counts.get("test_scores") == 1
    assert counts.get("activities") == 1
    assert counts.get("work_experiences") == 1
    assert counts.get("identity", 0) >= 1
    # Spot-check the goal actually landed in My Space.
    from unipaith.services.goals_service import GoalsService

    goals = await GoalsService(db_session).list_goals(mock_student_user.id)
    assert any("PhD" in g.specific for g in goals)


@pytest.mark.asyncio
async def test_upload_and_apply_endpoints(
    student_client, db_session, mock_student_user, monkeypatch
):
    await ensure_profile(db_session, mock_student_user)
    monkeypatch.setattr(settings, "ai_material_ingest_v2_enabled", True)

    async def _fake_read(self, **kwargs):
        return _PROPOSED

    monkeypatch.setattr("unipaith.ai.material_ingest.MaterialIngestAgent.read", _fake_read)

    up = await student_client.post(
        "/api/v1/students/me/materials",
        files={"file": ("resume.pdf", b"%PDF fake", "application/pdf")},
    )
    assert up.status_code == 200, up.text
    body = up.json()
    assert body["status"] == "parsed"
    ingest_id = body["id"]

    applied = await student_client.post(
        f"/api/v1/students/me/materials/{ingest_id}/apply",
        json={"goals": _PROPOSED["goals"], "needs": _PROPOSED["needs"]},
    )
    assert applied.status_code == 200, applied.text
    assert applied.json()["counts"].get("goals") == 1


# ── Completeness: widened schema + apply (2026-06-16) ──


def test_submit_tool_has_complete_coverage():
    from unipaith.ai.material_ingest import SUBMIT_TOOL

    props = SUBMIT_TOOL["input_schema"]["properties"]
    for key in [
        "profile",
        "academic_records",
        "test_scores",
        "activities",
        "work_experiences",
        "languages",
        "online_presence",
        "goals",
        "needs",
        "identity",
    ]:
        assert key in props, key
    for f in ["preferred_name", "email", "skills", "interests"]:
        assert f in props["profile"]["properties"], f
    act = props["activities"]["items"]["properties"]
    assert "role" in act and "title" in act
    assert "courses" in props["academic_records"]["items"]["properties"]
    assert "language" in props["languages"]["items"]["properties"]


@pytest.mark.asyncio
async def test_apply_writes_complete_profile(db_session, mock_student_user):
    from sqlalchemy import select

    from unipaith.models.student import Activity, StudentLanguage, StudentProfile

    await ensure_profile(db_session, mock_student_user)
    svc = MaterialIngestService(db_session)
    row = await svc.ingest(
        mock_student_user.id, filename="r.pdf", mime_type="application/pdf", data=b"x"
    )
    sel = {
        "profile": {
            "preferred_name": "Leo",
            "email": "leo@bu.edu",
            "phone": "617",
            "skills": ["Python", "SQL"],
            "interests": ["Motorsports"],
        },
        "online_presence": [{"platform_type": "linkedin", "url": "https://linkedin.com/in/x"}],
        "languages": [
            {"language": "Chinese", "proficiency_level": "native"},
            {"language": "French", "proficiency_level": "conversational"},
        ],
        "academic_records": [
            {
                "institution_name": "Northeastern",
                "degree_type": "bachelors",
                "start_date": "2020-09",
                "end_date": "2024-12",
                "courses": [{"course_name": "Data Mining for Business"}],
            }
        ],
        "activities": [
            {"title": "Electric Formula Club", "role": "Member", "activity_type": "extracurricular"}
        ],
    }
    out = await svc.apply(mock_student_user.id, row.id, sel)
    c = out["counts"]
    assert c.get("online_presence") == 1
    assert c.get("languages") == 2
    assert c.get("courses") == 1
    assert c.get("activities") == 1
    assert c.get("profile_fields", 0) >= 1

    sp = (
        await db_session.execute(
            select(StudentProfile).where(StudentProfile.user_id == mock_student_user.id)
        )
    ).scalar_one()
    acts = (
        (await db_session.execute(select(Activity).where(Activity.student_id == sp.id)))
        .scalars()
        .all()
    )
    assert any("Formula" in a.title for a in acts)
    langs = (
        (
            await db_session.execute(
                select(StudentLanguage).where(StudentLanguage.student_id == sp.id)
            )
        )
        .scalars()
        .all()
    )
    assert any(
        lang.language == "French" and lang.proficiency_level == "intermediate" for lang in langs
    )

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
    assert len(gaps) <= 12
    assert sum(1 for g in gaps if g["category"] == "deepen") <= 1
    for g in gaps:
        assert {"id", "category", "target_field", "prompt_hint", "kind", "section"} <= set(g)


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
async def test_gpa_question_names_each_school(db_session, mock_student_user):
    """Two degrees with no GPA → a separate, subject-named GPA question each."""
    await ensure_profile(db_session, mock_student_user)
    imp = {
        "academic_records": [
            {
                "institution_name": "Boston University",
                "degree_type": "masters",
                "field_of_study": "Business Analytics",
            },
            {
                "institution_name": "Northeastern University",
                "degree_type": "bachelors",
                "field_of_study": "Business Administration",
            },
        ]
    }
    gaps = await FollowUpService(db_session).detect(mock_student_user.id, imp)
    gpa_gaps = [g for g in gaps if g["target_field"] == "gpa"]
    assert len(gpa_gaps) == 2
    prompts = " | ".join(g["prompt_hint"] for g in gpa_gaps)
    assert "Boston University" in prompts and "Northeastern University" in prompts
    # each carries the school ref so the answer lands on the right record
    assert all(g.get("ref", {}).get("institution_name") for g in gpa_gaps)


@pytest.mark.asyncio
async def test_apply_gpa_targets_named_school(db_session, mock_student_user):
    from datetime import date

    from sqlalchemy import select

    from unipaith.models.student import AcademicRecord
    from unipaith.schemas.student import CreateAcademicRecordRequest
    from unipaith.services.student_service import StudentService

    await ensure_profile(db_session, mock_student_user)
    svc = StudentService(db_session)
    sid = (await svc._get_student_profile(mock_student_user.id)).id
    await svc.create_academic_record(
        sid,
        CreateAcademicRecordRequest(
            institution_name="Boston University", degree_type="masters", start_date=date(2024, 9, 1)
        ),
    )
    await svc.create_academic_record(
        sid,
        CreateAcademicRecordRequest(
            institution_name="Northeastern University",
            degree_type="bachelors",
            start_date=date(2020, 9, 1),
        ),
    )

    out = await FollowUpService(db_session).answer(
        mock_student_user.id,
        {"target_field": "gpa", "ref": {"institution_name": "Northeastern University"}},
        "3.7",
    )
    assert out["applied"] is True
    recs = (
        (await db_session.execute(select(AcademicRecord).where(AcademicRecord.student_id == sid)))
        .scalars()
        .all()
    )
    by_inst = {r.institution_name: r.gpa for r in recs}
    assert float(by_inst["Northeastern University"]) == 3.7
    assert by_inst["Boston University"] is None  # the other school untouched


@pytest.mark.asyncio
async def test_detect_comprehensive_grouped(db_session, mock_student_user):
    """Work/skills/contact/courses gaps surface, each tagged with a section."""
    await ensure_profile(db_session, mock_student_user)
    imp = {
        "work_experiences": [{"role_title": "ML Intern", "organization": "Acme"}],  # no hours/comp
        "academic_records": [{"institution_name": "NEU", "degree_type": "bachelors", "gpa": 3.8}],
        "online_presence": [],  # no linkedin
        "profile": {},  # no skills
    }
    gaps = await FollowUpService(db_session).detect(mock_student_user.id, imp)
    targets = {g["target_field"] for g in gaps}
    sections = {g["section"] for g in gaps}
    assert {"work_hours", "work_compensation", "courses", "skills", "link"} <= targets
    assert {"Experience", "Education", "Skills", "Contact"} <= sections


@pytest.mark.asyncio
async def test_answer_work_hours_and_compensation(db_session, mock_student_user):
    from datetime import date

    from sqlalchemy import select

    from unipaith.models.student import StudentWorkExperience
    from unipaith.schemas.student import CreateWorkExperienceRequest
    from unipaith.services.student_service import StudentService

    await ensure_profile(db_session, mock_student_user)
    svc = StudentService(db_session)
    sid = (await svc._get_student_profile(mock_student_user.id)).id
    await svc.create_work_experience(
        sid,
        CreateWorkExperienceRequest(
            experience_type="internship",
            organization="Acme",
            role_title="ML Intern",
            start_date=date(2022, 6, 1),
        ),
    )
    fu = FollowUpService(db_session)
    ref = {"role_title": "ML Intern", "organization": "Acme"}
    await fu.answer(mock_student_user.id, {"target_field": "work_hours", "ref": ref}, "about 20")
    await fu.answer(
        mock_student_user.id, {"target_field": "work_compensation", "ref": ref}, "Unpaid"
    )
    w = (
        await db_session.execute(
            select(StudentWorkExperience).where(StudentWorkExperience.student_id == sid)
        )
    ).scalar_one()
    assert w.hours_per_week == 20
    assert w.compensation_type == "unpaid"


@pytest.mark.asyncio
async def test_answer_courses_skills_link(db_session, mock_student_user):
    from datetime import date

    from sqlalchemy import select

    from unipaith.models.student import (
        StudentCourse,
        StudentOnlinePresence,
        StudentProfile,
    )
    from unipaith.schemas.student import CreateAcademicRecordRequest
    from unipaith.services.student_service import StudentService

    await ensure_profile(db_session, mock_student_user)
    svc = StudentService(db_session)
    sid = (await svc._get_student_profile(mock_student_user.id)).id
    await svc.create_academic_record(
        sid,
        CreateAcademicRecordRequest(
            institution_name="NEU", degree_type="bachelors", start_date=date(2020, 9, 1)
        ),
    )
    fu = FollowUpService(db_session)
    await fu.answer(
        mock_student_user.id,
        {"target_field": "courses", "ref": {"institution_name": "NEU"}},
        "Data Mining, Marketing Research, Financial Management",
    )
    await fu.answer(mock_student_user.id, {"target_field": "skills"}, "Python, SQL, Tableau")
    await fu.answer(
        mock_student_user.id,
        {"target_field": "link", "ref": {"platform_type": "linkedin"}},
        "linkedin.com/in/leo",
    )
    courses = (await db_session.execute(select(StudentCourse))).scalars().all()
    assert len(courses) == 3
    prof = (
        await db_session.execute(
            select(StudentProfile).where(StudentProfile.user_id == mock_student_user.id)
        )
    ).scalar_one()
    assert "Python" in (prof.bio_text or "")
    links = (
        (
            await db_session.execute(
                select(StudentOnlinePresence).where(StudentOnlinePresence.student_id == sid)
            )
        )
        .scalars()
        .all()
    )
    assert any(lk.platform_type == "linkedin" and lk.url.startswith("https://") for lk in links)


@pytest.mark.asyncio
async def test_phrase_questions_falls_back_in_mock(db_session, mock_student_user):
    """In mock mode the LLM returns no tool_use → phrase returns None (caller
    falls back to the subject-aware deterministic hints)."""
    from unipaith.ai.follow_up import phrase_questions

    gaps = [{"target_field": "gpa", "prompt_hint": "What was your GPA at NEU?"}]
    out = await phrase_questions(gaps, {"summary": "x"}, student_id=None)
    assert out is None


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

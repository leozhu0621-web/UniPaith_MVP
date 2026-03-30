"""Tests for review pipeline — rubrics, assign, score, pipeline view."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.application import Application
from unipaith.models.institution import Institution, Program, Reviewer
from unipaith.models.student import StudentProfile
from unipaith.models.user import User


async def _seed_full_review_context(
    db: AsyncSession, student_user: User, institution_user: User
):
    """Create student, institution, program, application, and reviewer."""
    db.add(student_user)
    db.add(institution_user)

    profile = StudentProfile(user_id=student_user.id, first_name="Test", last_name="Student")
    db.add(profile)

    institution = Institution(
        admin_user_id=institution_user.id,
        name="Test University",
        type="university",
        country="United States",
    )
    db.add(institution)
    await db.flush()

    program = Program(
        institution_id=institution.id,
        program_name="CS Masters",
        degree_type="masters",
        is_published=True,
        tuition=50000,
    )
    db.add(program)
    await db.flush()

    application = Application(
        student_id=profile.id,
        program_id=program.id,
        status="submitted",
    )
    db.add(application)

    reviewer = Reviewer(
        institution_id=institution.id,
        user_id=institution_user.id,
        name="Dr. Reviewer",
        department="Computer Science",
    )
    db.add(reviewer)
    await db.commit()
    return profile, institution, program, application, reviewer


@pytest.mark.asyncio
async def test_create_rubric(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    _, institution, program, _, _ = await _seed_full_review_context(
        db_session, mock_student_user, mock_institution_user
    )
    resp = await institution_client.post(
        "/api/v1/reviews/rubrics",
        json={
            "rubric_name": "Standard Review Rubric",
            "criteria": [
                {"name": "academics", "weight": 0.4, "max_score": 10},
                {"name": "research", "weight": 0.3, "max_score": 10},
                {"name": "statement", "weight": 0.3, "max_score": 10},
            ],
            "program_id": str(program.id),
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["rubric_name"] == "Standard Review Rubric"


@pytest.mark.asyncio
async def test_assign_reviewers(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    _, _, _, application, reviewer = await _seed_full_review_context(
        db_session, mock_student_user, mock_institution_user
    )
    resp = await institution_client.post(
        f"/api/v1/reviews/applications/{application.id}/assign"
    )
    # Should succeed or return reviewer assignment info
    assert resp.status_code in (200, 201)


@pytest.mark.asyncio
async def test_score_application(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    _, institution, program, application, reviewer = await _seed_full_review_context(
        db_session, mock_student_user, mock_institution_user
    )

    # Create rubric first
    rubric_resp = await institution_client.post(
        "/api/v1/reviews/rubrics",
        json={
            "rubric_name": "Score Rubric",
            "criteria": [
                {"name": "academics", "weight": 0.5, "max_score": 10},
                {"name": "fit", "weight": 0.5, "max_score": 10},
            ],
            "program_id": str(program.id),
        },
    )
    rubric_id = rubric_resp.json()["id"]

    # Score the application
    resp = await institution_client.post(
        f"/api/v1/reviews/applications/{application.id}/score",
        json={
            "rubric_id": rubric_id,
            "criterion_scores": {"academics": 8, "fit": 7},
            "reviewer_notes": "Strong academic background.",
        },
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_get_pipeline(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    _, _, program, _, _ = await _seed_full_review_context(
        db_session, mock_student_user, mock_institution_user
    )
    resp = await institution_client.get(f"/api/v1/reviews/pipeline/{program.id}")
    assert resp.status_code == 200
    data = resp.json()
    # Pipeline should contain counts or stage information
    assert isinstance(data, dict)

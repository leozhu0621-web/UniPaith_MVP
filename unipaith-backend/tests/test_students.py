import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.student import StudentProfile
from unipaith.models.user import User


async def _ensure_profile(db: AsyncSession, user: User) -> None:
    profile = StudentProfile(user_id=user.id)
    db.add(user)
    db.add(profile)
    await db.commit()


@pytest.mark.asyncio
async def test_get_profile(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    resp = await student_client.get("/api/v1/students/me/profile")
    assert resp.status_code == 200
    data = resp.json()
    assert "academic_records" in data
    assert "test_scores" in data
    assert "activities" in data


@pytest.mark.asyncio
async def test_update_profile_partial(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    resp = await student_client.put(
        "/api/v1/students/me/profile",
        json={
            "first_name": "Alice",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["first_name"] == "Alice"
    assert resp.json()["last_name"] is None


@pytest.mark.asyncio
async def test_profile_403_for_institution(institution_client: AsyncClient):
    resp = await institution_client.get("/api/v1/students/me/profile")
    assert resp.status_code == 403


# --- Academic Records ---


@pytest.mark.asyncio
async def test_create_academic_record(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    resp = await student_client.post(
        "/api/v1/students/me/academics",
        json={
            "institution_name": "MIT",
            "degree_type": "bachelors",
            "start_date": "2020-09-01",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["institution_name"] == "MIT"
    assert data["degree_type"] == "bachelors"


@pytest.mark.asyncio
async def test_list_academic_records(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    await student_client.post(
        "/api/v1/students/me/academics",
        json={
            "institution_name": "MIT",
            "degree_type": "bachelors",
            "start_date": "2020-09-01",
        },
    )
    resp = await student_client.get("/api/v1/students/me/academics")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


@pytest.mark.asyncio
async def test_update_academic_record(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    create_resp = await student_client.post(
        "/api/v1/students/me/academics",
        json={
            "institution_name": "MIT",
            "degree_type": "bachelors",
            "start_date": "2020-09-01",
        },
    )
    record_id = create_resp.json()["id"]
    resp = await student_client.put(
        f"/api/v1/students/me/academics/{record_id}",
        json={
            "field_of_study": "Computer Science",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["field_of_study"] == "Computer Science"


@pytest.mark.asyncio
async def test_delete_academic_record(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    create_resp = await student_client.post(
        "/api/v1/students/me/academics",
        json={
            "institution_name": "MIT",
            "degree_type": "bachelors",
            "start_date": "2020-09-01",
        },
    )
    record_id = create_resp.json()["id"]
    resp = await student_client.delete(f"/api/v1/students/me/academics/{record_id}")
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_invalid_degree_type(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    resp = await student_client.post(
        "/api/v1/students/me/academics",
        json={
            "institution_name": "MIT",
            "degree_type": "invalid_type",
            "start_date": "2020-09-01",
        },
    )
    assert resp.status_code == 422


# --- Test Scores ---


@pytest.mark.asyncio
async def test_create_test_score(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    resp = await student_client.post(
        "/api/v1/students/me/test-scores",
        json={
            "test_type": "GRE",
            "total_score": 325,
            "section_scores": {"verbal": 160, "quantitative": 165},
        },
    )
    assert resp.status_code == 201
    assert resp.json()["test_type"] == "GRE"
    assert resp.json()["section_scores"]["verbal"] == 160


@pytest.mark.asyncio
async def test_invalid_test_type(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    resp = await student_client.post(
        "/api/v1/students/me/test-scores",
        json={
            "test_type": "INVALID",
            "total_score": 100,
        },
    )
    assert resp.status_code == 422


# --- Activities ---


@pytest.mark.asyncio
async def test_create_activity(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    resp = await student_client.post(
        "/api/v1/students/me/activities",
        json={
            "activity_type": "research",
            "title": "AI Lab Assistant",
        },
    )
    assert resp.status_code == 201
    assert resp.json()["activity_type"] == "research"


@pytest.mark.asyncio
async def test_invalid_activity_type(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    resp = await student_client.post(
        "/api/v1/students/me/activities",
        json={
            "activity_type": "gaming",
            "title": "Pro Gamer",
        },
    )
    assert resp.status_code == 422


# --- Preferences ---


@pytest.mark.asyncio
async def test_preferences_upsert(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)

    resp = await student_client.get("/api/v1/students/me/preferences")
    assert resp.status_code == 200
    assert resp.json() is None

    resp = await student_client.put(
        "/api/v1/students/me/preferences",
        json={
            "preferred_countries": ["United States"],
            "funding_requirement": "partial",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["preferred_countries"] == ["United States"]

    resp = await student_client.put(
        "/api/v1/students/me/preferences",
        json={
            "budget_max": 50000,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["budget_max"] == 50000
    assert resp.json()["preferred_countries"] == ["United States"]


# --- Onboarding ---


@pytest.mark.asyncio
async def test_onboarding_starts_at_10(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    resp = await student_client.get("/api/v1/students/me/onboarding")
    assert resp.status_code == 200
    assert resp.json()["completion_percentage"] == 10
    assert "account" in resp.json()["steps_completed"]


@pytest.mark.asyncio
async def test_onboarding_increases_with_data(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)

    await student_client.put(
        "/api/v1/students/me/profile",
        json={
            "first_name": "Alice",
            "last_name": "Test",
            "nationality": "American",
        },
    )
    await student_client.post(
        "/api/v1/students/me/academics",
        json={
            "institution_name": "MIT",
            "degree_type": "bachelors",
            "start_date": "2020-09-01",
        },
    )

    resp = await student_client.get("/api/v1/students/me/onboarding")
    data = resp.json()
    assert data["completion_percentage"] == 40
    assert "basic_profile" in data["steps_completed"]
    assert "academics" in data["steps_completed"]

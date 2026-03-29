import uuid
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.dependencies import get_current_user
from unipaith.main import app
from unipaith.models.user import User, UserRole


def _make_user(role: str = "student") -> User:
    user = User.__new__(User)
    user.id = uuid.uuid4()
    user.email = f"test-{role}@example.com"
    user.cognito_sub = f"dev-sub-{user.id}"
    user.role = UserRole(role)
    user.is_active = True
    return user


@pytest.fixture
def mock_student_user() -> User:
    return _make_user("student")


@pytest.fixture
def mock_institution_user() -> User:
    return _make_user("institution_admin")


@pytest.fixture
async def student_client(
    db_session: AsyncSession, mock_student_user: User,
) -> AsyncGenerator[AsyncClient, None]:
    async def _override_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    async def _override_user() -> User:
        return mock_student_user

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_current_user] = _override_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def institution_client(
    db_session: AsyncSession, mock_institution_user: User,
) -> AsyncGenerator[AsyncClient, None]:
    async def _override_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    async def _override_user() -> User:
        return mock_institution_user

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_current_user] = _override_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_signup_student(client: AsyncClient, db_session: AsyncSession):
    resp = await client.post("/api/v1/auth/signup", json={
        "email": "student@example.com",
        "password": "StrongP@ss1",
        "role": "student",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "student@example.com"
    assert data["role"] == "student"
    assert "user_id" in data


@pytest.mark.asyncio
async def test_signup_institution_admin(client: AsyncClient):
    resp = await client.post("/api/v1/auth/signup", json={
        "email": "admin@school.edu",
        "password": "StrongP@ss1",
        "role": "institution_admin",
    })
    assert resp.status_code == 201
    assert resp.json()["role"] == "institution_admin"


@pytest.mark.asyncio
async def test_signup_invalid_role(client: AsyncClient):
    resp = await client.post("/api/v1/auth/signup", json={
        "email": "bad@example.com",
        "password": "StrongP@ss1",
        "role": "hacker",
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_signup_weak_password(client: AsyncClient):
    resp = await client.post("/api/v1/auth/signup", json={
        "email": "weak@example.com",
        "password": "short",
        "role": "student",
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_signup_duplicate_email(client: AsyncClient):
    await client.post("/api/v1/auth/signup", json={
        "email": "dup@example.com",
        "password": "StrongP@ss1",
        "role": "student",
    })
    resp = await client.post("/api/v1/auth/signup", json={
        "email": "dup@example.com",
        "password": "StrongP@ss1",
        "role": "student",
    })
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_login_valid(client: AsyncClient):
    await client.post("/api/v1/auth/signup", json={
        "email": "login@example.com",
        "password": "StrongP@ss1",
        "role": "student",
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": "login@example.com",
        "password": "StrongP@ss1",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "Bearer"


@pytest.mark.asyncio
async def test_login_invalid(client: AsyncClient):
    resp = await client.post("/api/v1/auth/login", json={
        "email": "nonexist@example.com",
        "password": "badpass",
    })
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_me_with_auth(student_client: AsyncClient):
    resp = await student_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer fake-token"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["role"] == "student"


@pytest.mark.asyncio
async def test_me_without_auth(client: AsyncClient):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 422

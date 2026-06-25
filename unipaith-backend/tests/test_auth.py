import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_signup_student(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "student@example.com",
            "password": "StrongP@ss1",
            "role": "student",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "student@example.com"
    assert data["role"] == "student"
    assert "user_id" in data


@pytest.mark.asyncio
async def test_signup_persists_first_name(client: AsyncClient, db_session):
    """todo 3.1 — a first name collected at signup lands on the student profile,
    so Uni + My Space can greet by name instead of the email local-part."""
    from sqlalchemy import select

    from unipaith.models.student import StudentProfile
    from unipaith.models.user import User

    resp = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "named@example.com",
            "password": "StrongP@ss1",
            "role": "student",
            "first_name": "  Ada  ",
        },
    )
    assert resp.status_code == 201
    user = (
        await db_session.execute(select(User).where(User.email == "named@example.com"))
    ).scalar_one()
    profile = (
        await db_session.execute(select(StudentProfile).where(StudentProfile.user_id == user.id))
    ).scalar_one()
    assert profile.first_name == "Ada"  # trimmed


@pytest.mark.asyncio
async def test_signup_first_name_optional(client: AsyncClient, db_session):
    """first_name stays optional at the API level (backward compatible). A blank
    name is normalized to NULL so the greeting falls back to name-less, not ''."""
    from sqlalchemy import select

    from unipaith.models.student import StudentProfile
    from unipaith.models.user import User

    resp = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "noname@example.com",
            "password": "StrongP@ss1",
            "role": "student",
            "first_name": "   ",
        },
    )
    assert resp.status_code == 201
    user = (
        await db_session.execute(select(User).where(User.email == "noname@example.com"))
    ).scalar_one()
    profile = (
        await db_session.execute(select(StudentProfile).where(StudentProfile.user_id == user.id))
    ).scalar_one()
    assert profile.first_name is None


@pytest.mark.asyncio
async def test_signup_institution_admin(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "admin@school.edu",
            "password": "StrongP@ss1",
            "role": "institution_admin",
        },
    )
    assert resp.status_code == 201
    assert resp.json()["role"] == "institution_admin"


@pytest.mark.asyncio
async def test_signup_invalid_role(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "bad@example.com",
            "password": "StrongP@ss1",
            "role": "hacker",
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_signup_weak_password(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "weak@example.com",
            "password": "short",
            "role": "student",
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_signup_duplicate_email(client: AsyncClient):
    await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "dup@example.com",
            "password": "StrongP@ss1",
            "role": "student",
        },
    )
    resp = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "dup@example.com",
            "password": "StrongP@ss1",
            "role": "student",
        },
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_login_valid(client: AsyncClient):
    await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "login@example.com",
            "password": "StrongP@ss1",
            "role": "student",
        },
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "login@example.com",
            "password": "StrongP@ss1",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "Bearer"
    assert data["user"]["email"] == "login@example.com"
    assert data["user"]["role"] == "student"


@pytest.mark.asyncio
async def test_login_invalid(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexist@example.com",
            "password": "badpass",
        },
    )
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


@pytest.mark.asyncio
async def test_invalid_token_returns_401(client: AsyncClient):
    """An invalid/expired token MUST return 401 (not 400). The web client's axios
    interceptor refreshes-and-retries on 401 only; when this regressed to 400,
    expired sessions failed every authenticated call (feedback, SSE stream, …)
    with no auto-recovery until manual re-login."""
    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer not-a-valid-token"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_authenticate_links_methods_by_email(db_session, monkeypatch):
    """One account per email. Cognito issues a different sub for the Google
    identity vs the email+password identity of the same address; a token whose
    sub doesn't match the stored one must still resolve to the SAME existing
    account via the verified email (not 'User not found'). Guards the link-them
    account model + keeps password login working after Google has been used."""
    from unipaith.core.security import CognitoClaims
    from unipaith.dependencies import authenticate_token
    from unipaith.models.user import User, UserRole

    user = User(email="linkme@example.com", cognito_sub="native-sub-1", role=UserRole.student)
    db_session.add(user)
    await db_session.flush()

    async def _fake_verify(_token):
        # Same email, DIFFERENT sub — exactly what Cognito sends for the Google
        # identity of an email first registered with a password.
        return CognitoClaims(sub="google-sub-DIFFERENT", email="linkme@example.com", role="student")

    monkeypatch.setattr("unipaith.dependencies.verify_token", _fake_verify)
    resolved = await authenticate_token("tok", db_session)
    assert resolved.id == user.id

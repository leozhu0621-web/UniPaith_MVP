import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_signup_student(client: AsyncClient):
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

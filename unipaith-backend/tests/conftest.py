from __future__ import annotations

import os

# Tests run without GPU — override before importing settings
os.environ.setdefault("GPU_MODE", "mock")
os.environ.setdefault("AI_MOCK_MODE", "true")

import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

try:
    from sqlalchemy.ext.asyncio import async_sessionmaker
except ImportError:  # SQLAlchemy < 2.0 compatibility
    async_sessionmaker = sessionmaker

from unipaith.config import settings
from unipaith.database import get_db
from unipaith.dependencies import get_current_user
from unipaith.main import app
from unipaith.models.base import Base
from unipaith.models.user import User, UserRole

TEST_DATABASE_URL = settings.database_url

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSession = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestSession() as session:
        yield session


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def _override_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


def _make_user(role: str = "student") -> User:
    return User(
        id=uuid.uuid4(),
        email=f"test-{role}-{uuid.uuid4().hex[:6]}@example.com",
        cognito_sub=f"dev-sub-{uuid.uuid4().hex[:8]}",
        role=UserRole(role),
        is_active=True,
    )


@pytest.fixture
def mock_student_user() -> User:
    return _make_user("student")


@pytest.fixture
def mock_institution_user() -> User:
    return _make_user("institution_admin")


@pytest.fixture
def mock_admin_user() -> User:
    return _make_user("admin")


async def _persist_user(db_session: AsyncSession, user: User) -> User:
    """Persist a mock user to the DB so FK constraints and server defaults work."""
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def student_client(
    db_session: AsyncSession, mock_student_user: User,
) -> AsyncGenerator[AsyncClient, None]:
    await _persist_user(db_session, mock_student_user)

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
    await _persist_user(db_session, mock_institution_user)

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


@pytest.fixture
async def admin_client(
    db_session: AsyncSession, mock_admin_user: User,
) -> AsyncGenerator[AsyncClient, None]:
    await _persist_user(db_session, mock_admin_user)

    async def _override_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    async def _override_user() -> User:
        return mock_admin_user

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_current_user] = _override_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()

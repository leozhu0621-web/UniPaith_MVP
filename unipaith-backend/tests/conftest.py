# ruff: noqa: E402 — env vars are set below before importing app modules
from __future__ import annotations

import os

# Tests run without GPU — override before importing settings
os.environ.setdefault("GPU_MODE", "mock")
os.environ.setdefault("AI_MOCK_MODE", "true")
os.environ.setdefault("COGNITO_BYPASS", "true")
os.environ.setdefault("S3_LOCAL_MODE", "true")


def _init_xdist_database() -> None:
    """Point each pytest-xdist worker at its own database.

    Every DB test drops + recreates the whole ``public`` schema (see
    ``setup_db``), so workers must NOT share one database. We rewrite
    ``DATABASE_URL`` *before* importing settings / the app, so the app's global
    engine (``unipaith.database``) and the test engine bind to the SAME
    per-worker DB — otherwise code paths that use the global engine (e.g.
    WebSocket handlers) would hit the base DB where this worker never built the
    schema.

    No-op when not under xdist (``PYTEST_XDIST_WORKER`` unset) or when
    ``DATABASE_URL`` is unset, so a plain ``pytest`` run behaves as before.
    """
    worker = os.environ.get("PYTEST_XDIST_WORKER")
    base_url = os.environ.get("DATABASE_URL")
    if not worker or not base_url:
        return
    prefix, _, dbname = base_url.rpartition("/")
    name, sep, query = dbname.partition("?")
    worker_url = f"{prefix}/{name}_{worker}{sep}{query}"

    import asyncio

    import asyncpg

    raw = worker_url.replace("+asyncpg", "")
    admin_prefix, _, tail = raw.rpartition("/")
    target_db = tail.partition("?")[0]

    async def _ensure() -> None:
        last_err: Exception | None = None
        for attempt in range(10):
            try:
                admin = await asyncpg.connect(f"{admin_prefix}/postgres")
                try:
                    exists = await admin.fetchval(
                        "SELECT 1 FROM pg_database WHERE datname = $1", target_db
                    )
                    if not exists:
                        # CREATE DATABASE can't run in a txn; a lone asyncpg
                        # execute autocommits, which is what we want.
                        await admin.execute(f'CREATE DATABASE "{target_db}"')
                finally:
                    await admin.close()
                return
            except asyncpg.exceptions.DuplicateDatabaseError:
                return  # another worker won the race — fine
            except Exception as err:  # e.g. template1 momentarily in use
                last_err = err
                await asyncio.sleep(0.3 * (attempt + 1))
        if last_err is not None:
            raise last_err

    asyncio.run(_ensure())
    os.environ["DATABASE_URL"] = worker_url


_init_xdist_database()

import uuid
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

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

# Under xdist this resolves to the per-worker URL (DATABASE_URL was rewritten by
# _init_xdist_database above, before settings/app imported); a plain pytest run
# uses the base URL — unchanged from the original behaviour.
TEST_DATABASE_URL = settings.database_url

# NullPool avoids asyncpg "another operation is in progress" when pooled connections
# are reused across overlapping setup/teardown under pytest-asyncio.
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)
TestSession = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


_DROP_ALL_TABLES = text("""
DO $$ DECLARE r RECORD;
BEGIN
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
        EXECUTE 'DROP TABLE IF EXISTS public.' || quote_ident(r.tablename) || ' CASCADE';
    END LOOP;
END $$;
""")


@pytest.fixture
async def setup_db():
    for _attempt in range(3):
        try:
            async with test_engine.begin() as conn:
                await conn.execute(_DROP_ALL_TABLES)
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                await conn.run_sync(Base.metadata.create_all)
            break
        except Exception:
            if _attempt == 2:
                raise
            await test_engine.dispose()
    yield
    try:
        async with test_engine.begin() as conn:
            await conn.execute(_DROP_ALL_TABLES)
    except Exception:
        pass
    await test_engine.dispose()


@pytest.fixture
async def db_session(setup_db) -> AsyncGenerator[AsyncSession, None]:
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


async def _persist_user(db_session: AsyncSession, user: User) -> User:
    """Persist a mock user to the DB so FK constraints and server defaults work."""
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def student_client(
    db_session: AsyncSession,
    mock_student_user: User,
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
    db_session: AsyncSession,
    mock_institution_user: User,
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

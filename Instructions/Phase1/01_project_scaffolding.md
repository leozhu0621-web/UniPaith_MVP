# Task 01: Project Scaffolding

## Context

You are building the backend for **UniPaith**, an AI-powered two-sided admissions marketplace for higher education. This is a fresh project — do not reference or reuse any existing code.

**Tech stack:**
- Python 3.12+
- FastAPI with Pydantic v2
- SQLAlchemy 2.0 (async) + Alembic for migrations
- PostgreSQL 16 + pgvector extension
- Amazon Cognito for auth (integrated in Task 03)
- Amazon S3 for file storage (integrated in Task 06)
- Docker + docker-compose for local development
- pytest for testing

## What to Build

### 1. Project Structure

Create this exact folder structure:

```
unipaith-backend/
├── alembic/
│   ├── versions/          # Migration files go here
│   ├── env.py
│   └── script.py.mako
├── alembic.ini
├── src/
│   └── unipaith/
│       ├── __init__.py
│       ├── main.py                 # FastAPI app entry point
│       ├── config.py               # Settings via pydantic-settings
│       ├── database.py             # Async SQLAlchemy engine + session
│       ├── dependencies.py         # Shared FastAPI dependencies
│       ├── models/                 # SQLAlchemy ORM models
│       │   ├── __init__.py
│       │   ├── base.py             # DeclarativeBase, common mixins
│       │   ├── user.py
│       │   ├── student.py
│       │   ├── institution.py
│       │   ├── application.py
│       │   ├── matching.py         # AI/ML tables (match_results, embeddings, etc.)
│       │   └── engagement.py       # Signals, saved lists, CRM
│       ├── schemas/                # Pydantic request/response schemas
│       │   ├── __init__.py
│       │   ├── auth.py
│       │   ├── student.py
│       │   ├── institution.py
│       │   ├── application.py
│       │   └── common.py           # Shared schemas (pagination, errors, etc.)
│       ├── api/                    # Route handlers
│       │   ├── __init__.py
│       │   ├── router.py           # Main router that includes all sub-routers
│       │   ├── auth.py
│       │   ├── students.py
│       │   ├── institutions.py
│       │   ├── programs.py
│       │   ├── applications.py
│       │   └── internal.py         # Admin/internal endpoints
│       ├── services/               # Business logic layer
│       │   ├── __init__.py
│       │   ├── auth_service.py
│       │   ├── student_service.py
│       │   ├── institution_service.py
│       │   ├── application_service.py
│       │   └── matching_service.py
│       ├── core/                   # Cross-cutting concerns
│       │   ├── __init__.py
│       │   ├── exceptions.py       # Custom exception classes
│       │   ├── middleware.py        # CORS, request logging, error handling
│       │   └── security.py         # Token verification, role checks
│       └── utils/
│           ├── __init__.py
│           └── helpers.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py                 # Fixtures: test DB, test client, auth mocks
│   ├── test_health.py
│   └── factories/                  # Test data factories
│       ├── __init__.py
│       └── base.py
├── scripts/
│   └── seed_dev_data.py            # Dev seed data script
├── docker-compose.yml              # PostgreSQL + pgvector for local dev
├── Dockerfile
├── pyproject.toml
├── .env.example
├── .gitignore
└── README.md
```

### 2. pyproject.toml

```toml
[project]
name = "unipaith-backend"
version = "0.1.0"
description = "UniPaith AI Admissions Platform - Backend API"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "sqlalchemy[asyncio]>=2.0.30",
    "asyncpg>=0.29.0",
    "alembic>=1.13.0",
    "pydantic>=2.7.0",
    "pydantic-settings>=2.3.0",
    "pgvector>=0.3.0",
    "python-jose[cryptography]>=3.3.0",
    "httpx>=0.27.0",
    "boto3>=1.34.0",
    "python-multipart>=0.0.9",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=5.0.0",
    "httpx>=0.27.0",
    "factory-boy>=3.3.0",
    "ruff>=0.4.0",
    "mypy>=1.10.0",
    "pre-commit>=3.7.0",
]

[build-system]
requires = ["setuptools>=69.0"]
build-backend = "setuptools.backends._legacy:_Backend"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]

[tool.mypy]
python_version = "3.12"
strict = true
```

### 3. config.py — Settings

Use `pydantic-settings` to load from environment variables:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # App
    app_name: str = "UniPaith API"
    debug: bool = False
    environment: str = "development"  # development, staging, production

    # Database
    database_url: str = "postgresql+asyncpg://unipaith:unipaith@localhost:5432/unipaith"

    # AWS
    aws_region: str = "us-east-1"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""

    # Cognito
    cognito_user_pool_id: str = ""
    cognito_app_client_id: str = ""
    cognito_domain: str = ""

    # S3
    s3_bucket_name: str = "unipaith-documents"
    s3_presigned_url_expiry: int = 3600  # seconds

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    # Rate limiting
    rate_limit_per_minute: int = 60


settings = Settings()
```

### 4. database.py — Async SQLAlchemy

```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from unipaith.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

### 5. main.py — FastAPI App

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from unipaith.config import settings
from unipaith.api.router import api_router
from unipaith.core.middleware import setup_middleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: verify DB connection, run any initialization
    yield
    # Shutdown: cleanup


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

setup_middleware(app)

app.include_router(api_router, prefix="/api/v1")
```

### 6. core/middleware.py

Set up:
- CORS middleware (using `settings.cors_origins`)
- Request ID middleware (generate UUID per request, add to response headers)
- Request logging middleware (log method, path, status, duration)
- Global exception handler that catches custom exceptions and returns proper JSON error responses

### 7. core/exceptions.py

Define custom exceptions:
- `UniPaithException(status_code, detail, error_code)` — base
- `NotFoundException(detail)` — 404
- `ForbiddenException(detail)` — 403
- `BadRequestException(detail)` — 400
- `ConflictException(detail)` — 409

### 8. api/router.py

Main router that includes all sub-routers with proper prefixes and tags:
- `/auth` — auth routes
- `/students` — student routes
- `/institutions` — institution routes
- `/programs` — program routes (public browsing)
- `/applications` — application routes
- `/internal` — admin/internal routes

Also include a `/health` endpoint that returns `{"status": "ok", "version": "0.1.0"}`.

### 9. docker-compose.yml

```yaml
services:
  db:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: unipaith
      POSTGRES_USER: unipaith
      POSTGRES_PASSWORD: unipaith
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U unipaith"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  pgdata:
```

### 10. Dockerfile

Multi-stage build:
- **Stage 1 (builder):** Install dependencies
- **Stage 2 (runtime):** Copy only what's needed, run as non-root user

Expose port 8000, run with `uvicorn unipaith.main:app --host 0.0.0.0 --port 8000`.

### 11. .env.example

All settings from config.py with sensible defaults for local dev. Include comments explaining each variable.

### 12. .gitignore

Standard Python + common ignores: `__pycache__`, `.env`, `.venv`, `*.pyc`, `.mypy_cache`, `.pytest_cache`, `.ruff_cache`, `*.egg-info`, `.DS_Store`.

### 13. Alembic Setup

Initialize Alembic with async support. Configure `env.py` to:
- Import all models from `unipaith.models`
- Use the `database_url` from settings
- Support both online and offline migration modes
- Use async engine

### 14. tests/conftest.py

Set up:
- Test database URL (use a separate test DB or override with SQLite for unit tests)
- Async test client fixture using `httpx.AsyncClient`
- Database session fixture that rolls back after each test
- Auth mock fixture (skip Cognito verification in tests, inject test user)

### 15. Health Check Test

Write `tests/test_health.py`:
- Test `GET /api/v1/health` returns 200 with expected body
- Test that CORS headers are present

## Verification

After generating, confirm:
1. `docker-compose up -d` starts PostgreSQL with pgvector
2. `pip install -e ".[dev]"` installs all dependencies
3. `uvicorn unipaith.main:app --reload` starts the server
4. `GET http://localhost:8000/api/v1/health` returns `{"status": "ok", "version": "0.1.0"}`
5. `pytest` runs and the health check test passes
6. `alembic revision --autogenerate -m "initial"` creates a migration (will be empty until Task 02)

## Important Notes

- Use **async everywhere** — async engine, async session, async route handlers
- All IDs should be **UUID** type (use `uuid7` for time-ordered UUIDs if available, otherwise `uuid4`)
- Follow **12-factor app** principles — all config from environment
- The `services/` layer contains business logic; route handlers should be thin (validate input, call service, return response)
- No AI/ML code yet — that comes in Phase 2
- No Cognito integration yet — Task 03 adds that. For now, auth routes can be placeholder stubs

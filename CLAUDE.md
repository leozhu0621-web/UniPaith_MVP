# UniPaith MVP

Two-sided AI matching platform for higher education admissions. Students find programs; institutions find applicants.

## Project Structure

```
unipaith-backend/    Python 3.12 + FastAPI + SQLAlchemy 2 (async) + PostgreSQL 16 + pgvector
frontend/            React 19 + TypeScript + Vite + Tailwind + Zustand + TanStack Query
infra/               Terraform (AWS: VPC, RDS, ECS Fargate, ALB, CloudFront, S3, Cognito)
scripts/             Dev utilities (reset DB, seed data, setup Cognito/S3)
```

## Quick Start

```bash
make dev-db          # Start PostgreSQL via Docker
make dev-backend     # Migrations + uvicorn on :8000
make dev-frontend    # Vite dev server on :5173
make test-backend    # pytest
make test-frontend   # vitest
make lint            # ruff (backend) + eslint (frontend)
make migration MSG="add foo"  # Generate new Alembic migration
```

## Backend Conventions

- **Models:** `src/unipaith/models/` — SQLAlchemy declarative with `UUIDPrimaryKeyMixin` + `TimestampMixin`
- **Services:** `src/unipaith/services/` — Business logic layer, one class per domain. Receives `AsyncSession` via constructor
- **API:** `src/unipaith/api/` — FastAPI routers, thin layer that calls services. Pydantic schemas defined inline
- **Migrations:** `alembic/versions/` — Use `make migration MSG="..."` to autogenerate. Never use `metadata.create_all()` in migrations
- **Config:** `src/unipaith/config.py` — Pydantic `BaseSettings`, all config via env vars
- **Auth:** Cognito in prod, `COGNITO_BYPASS=true` in dev (token format: `dev:<user_id>:<role>`)
- **Roles:** `student`, `institution_admin`, `admin`

### Adding a Vertical Feature (Backend)

1. Add model in `src/unipaith/models/` → import in `models/__init__.py`
2. `make migration MSG="add feature_name tables"`
3. Add service in `src/unipaith/services/`
4. Add API router in `src/unipaith/api/` → register in `api/router.py`
5. Add tests in `tests/`

## Frontend Conventions

- **API client:** `src/api/client.ts` — Axios instance with auth interceptors
- **Pages:** `src/pages/` — Organized by role (`/student`, `/institution`, `/admin`)
- **State:** Zustand for auth/global state, TanStack Query for server state
- **Forms:** React Hook Form + Zod validation
- **Styling:** Tailwind CSS utility classes

### Adding a Vertical Feature (Frontend)

1. Add API functions in `src/api/`
2. Add types in `src/types/`
3. Add page in `src/pages/`
4. Add route in `App.tsx`

## Environment Variables

Backend env vars are in `unipaith-backend/.env` (not tracked). See `.env.example` for the full list.

Key vars:
- `DATABASE_URL` — PostgreSQL async connection string
- `COGNITO_BYPASS=true` — Skip Cognito in dev
- `S3_LOCAL_MODE=true` — Use local filesystem instead of S3 in dev
- `AI_MOCK_MODE=true` — Skip real OpenAI calls in tests
- `DEBUG=true` — Enable /docs and /redoc

## Testing

- Backend: `pytest` with `pytest-asyncio`. Fixtures in `tests/conftest.py` provide `db_session`, `client`, role-specific clients
- Frontend: `vitest` with `@testing-library/react` and `jsdom`
- CI: GitHub Actions runs backend tests with pgvector service container

# UniPaith MVP

Two-sided AI matching platform for higher education admissions. Students find programs; institutions find applicants.

## Session Continuity

- At the start of any session that resumes prior work, ASK the user for context/rules from the previous session before exploring
- Do not spend more than 2-3 tool calls exploring before confirming the task scope

## Pre-Work Checklist

Before starting new feature work, always verify the environment is healthy first: DB connections active, Docker/Postgres running, zero build errors, all existing tests passing. Do NOT proceed to feature building until confirmed.

## UI/Design Preferences

- NO decorative images, gradients, or color accents on program detail pages
- Aesthetic is editorial and program-specific, not generic marketing
- Always confirm WHICH component is being changed (explore card vs detail page) before editing

## Project Overview

This is a TypeScript + Python monorepo (UniPaith MVP). Frontend is TypeScript/React, backend has both TypeScript and Python services. Infrastructure is Terraform/AWS (ECS, RDS, Cognito, SES). Domain: unipaith.co.

## Surface map

| URL | What | Repo / source |
|---|---|---|
| `unipaith.co`, `www.unipaith.co` | WordPress marketing landing | [`leozhu0621-web/UniPaith_landingpage`](https://github.com/leozhu0621-web/UniPaith_landingpage) (theme) — runs on EC2 in this VPC |
| `app.unipaith.co` | React app (this repo) | `frontend/` → S3 + CloudFront |
| `api.unipaith.co` | FastAPI (this repo) | `unipaith-backend/` → ECS Fargate |

## Project Structure

```
unipaith-backend/    Python 3.12 + FastAPI + SQLAlchemy 2 (async) + PostgreSQL 16 + pgvector
frontend/            React 19 + TypeScript + Vite + Tailwind + Zustand + TanStack Query
infra/               Terraform (AWS: VPC, RDS, ECS Fargate, ALB, CloudFront, S3, Cognito,
                                  + WordPress EC2 + RDS MySQL for the marketing landing)
scripts/             Dev utilities (reset DB, seed data, setup Cognito/S3)
```

## Marketing landing (WordPress)

The marketing site at `unipaith.co` is WordPress on EC2 (Amazon Linux 2023, Apache + PHP 8.3) with RDS MySQL for the WP DB. Provisioned by `infra/wordpress.tf`. Live in this VPC alongside the app.

- **Theme repo**: `leozhu0621-web/UniPaith_landingpage` — pushes to `main` auto-deploy via SSM in ~30s
- **wp-admin**: `https://unipaith.co/wp-admin/` — credentials in AWS Secrets Manager `unipaith/production/wp-admin`
- **Editing content**: log into wp-admin, edit Pages directly. No git involved for copy edits.
- **Editing theme code**: PR/push to `UniPaith_landingpage`. Workflow runs `git pull` on the EC2 via SSM and reloads Apache.

## Terraform CI/CD

Terraform-managed infra (this repo's `infra/`) auto-applies on push to `main`:

- **PRs** → `terraform-plan.yml`: offline `fmt`/`validate` (no AWS auth — bootstrap-safe)
- **Push to main** → `terraform-apply.yml`: full `apply -auto-approve` via OIDC role
- The OIDC role `unipaith-github-actions` has `AdministratorAccess` (locked to PRs/main of this repo only)
- TF_VAR_OPENAI_API_KEY GH secret feeds `var.openai_api_key` for both workflows

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

## Data & Schema Rules

- When adding new model fields, ALWAYS update response schemas in the same change (fields are invisible otherwise)
- Verify DB field names before reading (e.g., `application_requirements` not `requirements`)
- When seeding data, use `replace=True` or explicit dedup keys to avoid collision bugs
- Never present findings without first confirming the underlying data exists

## Testing

- Backend: `pytest` with `pytest-asyncio`. Fixtures in `tests/conftest.py` provide `db_session`, `client`, role-specific clients
- Frontend: `vitest` with `@testing-library/react` and `jsdom`
- CI: GitHub Actions runs backend tests with pgvector service container

### Test Commands

```bash
# Full suites
make test-backend     # 41 test files, 177+ tests — pytest with async DB
make test-frontend    # vitest smoke tests

# Backend — single file
cd unipaith-backend && PYTHONPATH=src AI_MOCK_MODE=true \
  .venv/bin/pytest tests/test_<name>.py -v --tb=short

# Backend — single test
cd unipaith-backend && PYTHONPATH=src AI_MOCK_MODE=true \
  .venv/bin/pytest tests/test_<name>.py::test_function -v --tb=long

# Frontend — single file
cd frontend && npx vitest run src/test/smoke.test.ts

# Required env vars for backend tests
DATABASE_URL="postgresql+asyncpg://unipaith:unipaith@localhost:5432/unipaith"
COGNITO_BYPASS=true  AI_MOCK_MODE=true  S3_LOCAL_MODE=true
```

### Test Failure Workflow

1. Read the failing test and the source code it tests
2. Determine if the bug is in source code or in the test
3. Fix the actual bug (prefer fixing source code over changing test expectations)
4. Re-run just that test to confirm the fix
5. After all fixes, run the full suite to check for regressions

## Common Pitfalls

When asked to review or audit code, go directly to the code files. Do NOT set up dev servers, launch.json, or other environment tooling unless explicitly asked.

## Infrastructure

Infrastructure debugging notes: RDS is in a VPC - ensure new services have correct security groups. ECS task definitions can overwrite env vars on redeploy. S3 frontend bundles can go stale - always invalidate CloudFront after deploy. DB password is managed via AWS Secrets Manager.

## Deployment Checklist (ECS/RDS/S3)

- Verify S3 bundle is current (not stale) before blaming app code
- Check ECS task definition hasn't been overwritten
- Confirm DB password matches across Secrets Manager and RDS
- Verify RDS is in correct VPC and DNS points to current ALB

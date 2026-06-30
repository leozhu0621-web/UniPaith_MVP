# UniPaith — Architecture

The map of how the system fits together. Read this before adding a new module, service, or page. Keep it current when the shape changes.

## System overview

```
                         ┌─────────────────────────────┐
   Browser ──────────────►  CloudFront (app.unipaith.co)│
                         │   └── S3: React SPA (static) │
                         └──────────────┬───────────────┘
                                        │ XHR (api.unipaith.co)
                                        ▼
                         ┌─────────────────────────────┐
                         │  ALB ──► ECS Fargate         │
                         │         FastAPI (uvicorn)    │
                         └───┬───────────┬──────────┬───┘
                             │           │          │
                     ┌───────▼──┐  ┌─────▼────┐  ┌──▼─────────────┐
                     │ RDS      │  │ S3       │  │ Together AI     │
                     │ Postgres │  │ uploads  │  │ (Qwen LLM)      │
                     └──────────┘  └──────────┘  └────────────────┘
   Auth: Cognito   ·   Email: SES   ·   Secrets: Secrets Manager   ·   IaC: Terraform
```

## Frontend (`frontend/`)

- **Stack:** Vite, React 19, react-router 7, TypeScript. Built to static assets, deployed to S3, served by CloudFront.
- **Layering (strict):** `pages/` (route screens) → `api/<domain>.ts` (typed network layer) → backend. **Pages never call `fetch`/`apiClient` directly** — enforced in `pr-checks.yml`. Shared UI lives in `components/`; client state in `stores/`.
- **Current debt:** logic concentrated in `pages/` (317 pages vs 76 components) with several 1,000–1,600-LOC god-pages, and a 3,710-LOC `types/index.ts`. New work should extract components and split types by domain. (See assessment / roadmap B3.)

## Backend (`unipaith-backend/`)

- **Stack:** FastAPI, async SQLAlchemy 2.x, Pydantic, Alembic, boto3. Single uvicorn worker (one APScheduler instance). Containerized, runs on ECS Fargate behind the ALB.
- **Layering (strict, one-directional):**
  - `api/` — routers; thin; depend on `services/` only.
  - `services/` — business logic; **must not import `api/`** (audited: 0 violations).
  - `models/` — ORM; no business logic.
  - `schemas/` — Pydantic I/O contracts.
  - `ai/` — Qwen-via-Together client, prompts, eval harness.
  - `config.py` / `core/` — settings and cross-cutting concerns.
- **Health:** `/api/v1/health` is liveness (DB-free, always 200, used by the ALB); `/ready` checks the DB. Keep `/health` DB-free.
- **Migrations:** Alembic; the entrypoint runs `alembic upgrade heads` on start. **Keep a single head** (`test_alembic_has_single_head`). Rebase your migration onto the current head before merge.

### Data (`unipaith-backend/src/unipaith/data/`) — important

University/reference profiles currently live as large hand-written Python modules (`*_profile.py`, ~203K LOC, ~63% of backend source) and historically shipped as per-edit Alembic migrations — the main source of migration dual-head churn. **Direction of travel:** move this content into the datastore / versioned structured data files behind a single typed loader, so data edits are content changes + a seed run, not migrations. **Do not add new `*_profile.py` modules** (CI-flagged). See the structural assessment and roadmap item B1.

## Infrastructure (`infra/`)

- **Terraform** manages everything in AWS `us-east-1`: VPC, ECS cluster/service (Fargate), ALB + target group, RDS Postgres, CloudFront + S3 (frontend + uploads), Cognito, SES, ECR, Secrets Manager, GitHub OIDC role.
- **GitOps:** push to `main` triggers `terraform-apply`, `deploy-backend`, and `deploy-frontend` workflows. PRs run `terraform-plan` + `terraform validate`.

## CI/CD (`.github/workflows/`)

- `pr-checks.yml` — path-filtered: backend (ruff + `pytest -n auto`), frontend (lint + typecheck + build + vitest + the pages↔api boundary guard), AI evals (mock), Lighthouse (soft), repo hygiene (no iCloud-dup filenames). `terraform-plan` validates infra.
- `deploy-backend.yml` / `deploy-frontend.yml` — build + ship on merge to `main` (buildx GHA-cached image → ECR → ECS; Vite build → S3 → CloudFront invalidation).
- `structure-guard.yml` — soft structural guardrails (PR title convention, no new god-files / data-as-code, no committed VCS dumps).

## Conventions

See `CONTRIBUTING.md` for layering rules, branch/commit conventions, and "where things go." The short version: respect the one-directional layering, keep data out of code, keep files small, keep one Alembic head, delete merged branches.

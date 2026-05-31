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

## Student-side IA — 3-stage journey

The student app at `app.unipaith.co/s` is structured around the journey from the business spec, not by tool type. Four top-level surfaces, each tied to a stage:

| URL | Label | Stage | What |
|---|---|---|---|
| `/s` | **Discover** | 1. Discovery | LLM-led 3-track journey (Profile / Goals / Needs) with chat + live artifact rail |
| `/s/explore` | **Match** | 2. Recommendation | Strategy view (top) + Programs/Schools grid; dual scores (fitness + confidence) |
| `/s/manage` | **Apply** | 3b/3c. Preparation + Application Mgmt | Applications · Calendar · Messages · **Workshops (feedback-only)** |
| `/s/posts` | **Connect** | 3a. Connection & Outreach | Updates / Events / Peers tabs from followed institutions |

Profile (`/s/profile`) is the durable record across all stages — 7 tabs: Overview, Identity, Goals, Needs, Strategy, Recommenders, Financial. Saved (`/s/saved`) and Settings (`/s/settings`) live under the avatar dropdown.

**Workshops are feedback-only by spec.** The schema mechanically excludes any field that could carry a generated essay / model answer — see `tests/test_workshop_no_generation_contract.py`. Plan 2's LLM swap-in cannot break this without failing CI.

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

## Phase A schema (Plan 1 foundations)

The student-restructure landed 8 new tables / extended schemas. Quick reference:

| Table | Owns | Notes |
|---|---|---|
| `discovery_sessions` | Stage-1 chat sessions per track | track ∈ {profile, goals, needs}; layer ∈ {basic, personality, identity} when track=profile |
| `discovery_messages` | Append-only message log | extracted_signals JSONB written by Plan 2 extractor |
| `student_goals` | SMART goal stack | source ∈ {discovery, manual}; provenance enforced via CHECK constraint |
| `student_needs` | Maslow-keyed needs map | severity ∈ {must_have, strong_preference, nice_to_have}; source includes 'inferred' |
| `student_identity` | Single row per student; deepest profile layer | core_values / worldview / self_awareness JSONB lists; partial-merge on PUT |
| `student_strategies` | Versioned broad-strategy artifact | partial unique index for one-active-per-student; edit = clone-and-modify |
| `match_results` (extended) | fitness_score + confidence_score split | legacy `match_score` kept for one release (drop in Phase E) |
| `workshop_feedback_runs` | feedback-only essay/interview/test runs | rubric_scores / structural_issues / missing_elements / suggested_questions — no generation fields |
| `student_profiles` (extended) | discovery_completion JSONB + strategy_active_id | denormalized journey summaries kept fresh by service hooks |

Plan 2 (LLM stack) plugs into these contract endpoints. Each is feature-flagged so the rule-based stub stays the default until the LLM path proves itself per-environment:

| Endpoint | Flag | Status | Notes |
|---|---|---|---|
| `POST /me/discovery/sessions/{id}/messages` | `ai_discovery_v2_enabled` | ✅ wired | Orchestrator + extractor + validator + judge |
| `POST /me/matches/{program_id}/explain` | `ai_match_rationale_v2_enabled` | ✅ wired | Delegates to MatchService.get_match_with_rationale (A5 RationaleAgent + per-(profile_version, program_version) cache) |
| `POST /me/workshops/essay/feedback` | `ai_workshops_v2_enabled` | ✅ wired | WorkshopCoach (A6) with two-layer guardrail |
| `POST /me/workshops/interview/practice` | `ai_workshops_v2_enabled` | ✅ wired | When `response_text` is provided the coach scores it; otherwise the rule-based bank serves canned practice questions |
| `POST /me/workshops/test/guidance` | `ai_workshops_v2_enabled` | ✅ wired | TestPrepCoach (C2) |
| `POST /me/strategy/generate` | `ai_strategy_v2_enabled` | ✅ wired | StrategyAgent (Sonnet, forced tool-use); produces career → degree → academic / financial / geographic paths + 4-paragraph narrative |
| `POST /me/identity/regenerate-summary` | `ai_identity_v2_enabled` | ✅ wired | IdentitySummaryAgent synthesizes a 3–5 sentence paragraph from the structured layer; on failure preserves an existing real summary rather than overwriting with stub |
| `POST /me/applications/:id/offers` + offer create | `ai_outcome_brief_v2_enabled` | ✅ wired | OutcomeBriefForOfferLetter (Spec 18 / 45 §15): Sonnet forced tool-use turns an offer into a plain-language brief {key_terms, deadlines, next_steps, summary}, cached on `offer_letters.plain_language_brief`; falls back to rule-based `_build_structured_brief` |

All flags are **enabled in production** (see `infra/ecs.tf` env block).

**Integration-test invariant:** when an LLM agent fails (timeout, parse error, guardrail trip), the service falls back to the rule-based path so the caller never sees a 5xx. See `tests/test_plan2_integration.py`.

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

### Student app sub-folders (Phase B IA)

- `pages/student/discover/` — Discover page widgets (TrackSelector, ChatPanel, ArtifactRail, GoalStackWidget, NeedsMapWidget, IdentitySignalsWidget)
- `pages/student/profile/` — Profile tab content (IdentityTab, GoalsTab, NeedsTab, StrategyTab)
- `pages/student/match/` — Match page additions (StrategyView, DualRing, RationalePopover)
- `pages/student/apply/` — Apply page tabs (WorkshopsTab + EssayFeedbackPanel / InterviewPracticePanel / TestGuidancePanel)
- `pages/student/explore/` — Match (ExplorePage) cards + filters; existing
- `pages/student/program/` — Program detail components (HeroBanner, MatchRing, etc.); existing

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

## Phase E follow-ups (deferred until dual-score / new IA have soaked ≥1 release)

- **Drop `match_results.match_score` and `score_breakdown`** — see migration `bd5c6e3f2a1b`. These are kept for rollback safety and currently dual-written. Safe to drop once: (a) all consumers read `fitness_score` / `confidence_score` directly (currently `SchoolDetailPage` reads legacy), (b) no rollback to pre-Phase-A is anticipated.
- **Delete the legacy Essays & Resume tab from ProfilePage** — it now redirects to `/s/manage?tab=workshops`. Deletion blocked until no remaining links reference `?tab=essays`.
- **Delete `unipaith-backend/src/unipaith/services/essay_workshop_service.py` + `resume_workshop_service.py`** — replaced by `workshop_feedback_service.py`. Old endpoints in `api/workshops.py` are deprecated shims; delete after the frontend stops calling them.
- **Delete `pages/student/EssayWorkshopPage.tsx` + `ResumeWorkshopPage.tsx`** — once no Suspense lazy-import references remain.
- **Rename `pages/student/DiscoverPage.tsx`** to `DiscoverSearchView.tsx` or similar — the file is the legacy NLP-search engine, misnamed since the rebuild. Used only by `explore/SearchView.tsx`.

## Infrastructure

Infrastructure debugging notes: RDS is in a VPC - ensure new services have correct security groups. ECS task definitions can overwrite env vars on redeploy. S3 frontend bundles can go stale - always invalidate CloudFront after deploy. DB password is managed via AWS Secrets Manager.

## Deployment Checklist (ECS/RDS/S3)

- Verify S3 bundle is current (not stale) before blaming app code
- Check ECS task definition hasn't been overwritten
- Confirm DB password matches across Secrets Manager and RDS
- Verify RDS is in correct VPC and DNS points to current ALB

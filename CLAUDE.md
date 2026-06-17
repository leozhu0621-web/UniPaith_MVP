# UniPaith MVP

Two-sided AI matching platform for higher education admissions. Students find programs; institutions find applicants.

## Session Continuity

- At the start of any session that resumes prior work, ASK the user for context/rules from the previous session before exploring
- Do not spend more than 2-3 tool calls exploring before confirming the task scope

## Ship to Production Every Time (standing rule)

Every change goes online — never leave finished work sitting local. The moment a change is verified (tsc 0 · build 0 · tests green), it must be **committed → merged to `main` → auto-deployed → verified live** in the same turn. "Done" means deployed and confirmed in production (app.unipaith.co / api.unipaith.co), not merely written on disk. End each unit of work by confirming the working tree is clean, `main` is at the new commit, and the deploy succeeded. (Set 2026-06-05 by explicit user direction: "make sure u push it online everytime.")

## Deployment Workflow

After building a feature: run the full test suite, check for dual Alembic migration heads before deploy (`alembic heads`), merge the PR only after CI is green, then verify the feature live in production and report the live URL.

**Database / migrations:** Always check for and resolve concurrent migration heads before pushing backend changes — run `alembic heads`, and if more than one head exists, create a fixup merge migration to unify them (use a session-unique revision id) and re-run the suite before deploying.

## Git / Worktrees

When editing code, always confirm you are operating in the correct git worktree (not the root checkout) — concurrent branch switches can revert work done in the wrong location. Prefer branching fresh off `origin/main` for each unit of work to avoid squash-skew conflicts.

## Sub-agents / Exploration

When verifying with sub-agents, treat their findings as unverified — re-check cited files and migration heads directly before acting, since Explore agents have confabulated nonexistent files and stale state. For verification-critical reads, go direct with Read/Grep rather than relying on a sub-agent's report.

## Pre-Work Checklist

Before starting new feature work, always verify the environment is healthy first: DB connections active, Docker/Postgres running, zero build errors, all existing tests passing. Do NOT proceed to feature building until confirmed.

## UI/Design Preferences

- School / college / program **detail pages** use a campus-photo hero that fades into the cream page background (`--background`), with NO logo and NO geo/location line; followed by rich, Niche-modeled content grounded in REAL data (rankings · report-card key stats · distinction · admissions funnel · outcomes/cost · quick facts · sourced citation). The hero falls back to a clean gradient when a school has no photo. (Updated 2026-06-04 by explicit user direction — supersedes the earlier "no decorative images/gradients on detail pages" rule.) **The institution hero is a click-through GALLERY** (set 2026-06-12): `school_outcomes.campus_photos` holds 4–5 verified `{url, credit}` entries; clicking the hero opens a lightbox (arrows/dots/Esc, per-photo credit). Every photo carries a verified Wikimedia-Commons-style credit — an uncredited or unverifiable photo must be dropped, never shipped.
- **EVERY page is FULL-BLEED (`w-full`, NO `max-w` cap) — including the editorial detail pages.** (Set 2026-06-15 by explicit user direction: "the ui of ALL pages should be fit the screen, the entire app/website should be that, not narrow like before" — this SUPERSEDES the prior `max-w-5xl` detail-page standard. The MIT page is no longer a width "example".) Institution / college (school-subunit) / program detail pages (student **and** public), institution dashboards (Posts, Program editor, Recruitment, Dept portal, Data upload), and public browse pages all fill the screen. The detail pages keep their inner structure (campus-photo hero, tabs, stat tiles, Niche-modeled sections) — only the outer `max-w-5xl mx-auto` cap was dropped. ONLY these stay narrow-by-design (do NOT full-bleed them): focused forms & wizards (institution Settings/Setup, FairnessPage), error / empty / not-found states (`max-w-3xl mx-auto text-center`), modals & the photo lightbox (`relative max-w-5xl w-full flex`), the CompareTray bottom overlay, the non-guided Uni fallback, and the public `/goal` transparency pages. Do NOT re-add `max-w-5xl mx-auto` to any content/detail/dashboard page.
- **App-shell pages are FULL-BLEED (`w-full`, NO `max-w` cap, fill the screen)** — every non-detail student surface (Discover/Explore, Connectors/Posts, Applications + Application detail, Calendar, Profile, Settings, Saved-list, Feedback inbox, Prompt Library, and the My Space home + prep tabs) uses a full-width container so content fills the screen instead of floating in a narrow centered column. Card grids gain extra columns at width (`xl:grid-cols-4`) so the space becomes density, not bigger cards. Do NOT re-add `max-w-5xl mx-auto` to these — that's the old narrow look the user explicitly rejected. The CompareTray bottom overlay keeps its own centered max-width. (Set 2026-06-11 by explicit user direction: "current ui layout is narrow… they all need to be like My Space, fit the screen.")
- **University explore cards carry a campus-photo gradient header** (set 2026-06-12 by explicit user direction — supersedes the earlier "explore cards stay text-driven" rule): the card header shows `image_url` (= `campus_photos[0]`) fading into the card background (same gradient treatment as the detail hero), with the tiny verified credit top-right; falls back to the clean text header when a university has no photo. Other dense list surfaces (program cards, list rows) stay text-driven.
- Aesthetic is editorial + content-rich (Niche-modeled), program-specific, never generic marketing
- **Across the broader student app (non-detail surfaces — Discover, Match, Apply, Profile, Connect, Saved, Settings): dense, utilitarian, app-like (LinkedIn-leaning) WITHIN each surface's existing layout** — surfaced metadata + counts, compact list rows, tight vertical rhythm, small utilitarian section headers. Use the shared density layer `frontend/src/components/student/density/` (`PageHeader · SectionHeader · ListRow · StatTile`). This COMPLEMENTS (does not replace) the content-rich Niche-modeled detail pages above. See `docs/superpowers/specs/2026-06-04-student-ux-densification-design.md`. (Set 2026-06-04 by user direction.)
- Always confirm WHICH component is being changed (explore card vs detail page) before editing

## UI / Styling

After any UI redesign, render the page and visually verify in both light and dark mode; never rely on non-adaptive tokens like `bg-surface` without checking contrast. Use semantic tokens (`bg-card`, `text-foreground`, `text-muted-foreground`) so both modes stay legible.

## Writing voice & interaction (UX QA — standing rule)

Every user-facing string and every interactive surface follows **`docs/UX-QA.md`** (reference: Handshake — warm, professional, action-oriented). Two halves:

- **Voice:** name the thing (noun labels, not "Your record"); celebrate real milestones plainly (earned warmth stays — a greeting, "You're in!" — but no emoji or manufactured cheer); say it once or not at all (self-explanatory titles stand alone; never a paragraph); talk like a counselor, not a chatbot (no AI-speak); never blame, be courteous ("Please try again"); clarity beats brevity for actions (name the action + object + deadline). Centralize reusable strings in `frontend/src/lib/copy.ts`.
- **Show, don't tell:** if it's an action, decision, status, number, or comparison, make it a control or a visual — not a sentence. A control only for actions UniPaith owns (verified endpoint); inform + view for school-owned outcomes (offers — never a fake Accept/Decline); a visual for pure data. Don't widgetize dense professional tables.
- **Enforcement:** `cd frontend && npm run voice-lint` (wired into `pr-checks.yml`) hard-fails on AI-speak / wordy clichés. Run it before shipping copy.

(Set 2026-06-14 by founder direction — "this session is UX QA"; childish/AI/wordy copy must not be created again.)

## Project Overview

This is a TypeScript + Python monorepo (UniPaith MVP). Frontend is TypeScript/React, backend has both TypeScript and Python services. Infrastructure is Terraform/AWS (ECS, RDS, Cognito, SES). Domain: unipaith.co.

## Student-side IA — 2 world surfaces + My Space

The student app at `app.unipaith.co/s` is structured around the journey from the business spec, not by tool type. Two surfaces about the world + one personal hub (see `docs/superpowers/specs/2026-06-10-my-space-design.md` and `docs/superpowers/specs/2026-06-12-discover-connect-merge-design.md`):

| URL | Label | Stage | What |
|---|---|---|---|
| `/s` | **Uni** | 1. Discovery | LLM-led guided journey (Profile / Goals / Needs) with chat + journey rail |
| `/s/explore` | **Discover** | 2+3a. Recommendation + Connection | Hub with sub-tabs (`?tab=`): **For you** (strategy + dual-score matches + program search + browse, plus an xl+ live rail: updates / events / deadline radar / follow suggestions) · **Updates** · **Events** · **Peers** (the absorbed Connect surface, Spec 20) |
| `/s/space` | **My Space** | Me — spans all stages | Mission-control Home + journey-ordered rooms (below) |

`/s/posts` (Connect) is RETIRED (2026-06-12) — `PostsRedirect` in `App.tsx` maps it + its tab deep links one-hop into the Discover hub (contract: `POSTS_TAB_REDIRECTS` in `utils/information-architecture.ts`).

**My Space rooms** (flat URLs, shared shell `pages/student/myspace/MySpaceShell.tsx`, journey-ordered rail): Home `/s/space` (mission control) · Saved `/s/saved` (Plan) · Prep `/s/prep` (Prepare — Workshops + Prompts tabs) · Applications `/s/applications` (Apply & decide) · Calendar `/s/calendar` + Messages `/s/messages` (Anytime) · Profile `/s/profile` (Record). `/s/manage` is RETIRED — `ManageRedirect` in `App.tsx` maps its tab deep links one-hop into the rooms (contract: `MANAGE_TAB_REDIRECTS` in `utils/information-architecture.ts`, tested by `test/information-architecture.test.ts`).

Profile (`/s/profile`) is the durable record across all stages — 13 tabs (see `PROFILE_TABS_SPEC`). Settings (`/s/settings`) lives under the avatar dropdown.

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

## Uni runs as a managed agent on platform.claude.com (the cutover)

The Stage-1 discovery conversation (`/s` → `POST /me/discovery/sessions/{id}/messages/stream`) is driven by **"Uni," a managed agent on platform.claude.com**, gated by `ai_uni_managed_agent_v1` (**ON in prod**, `infra/ecs.tf`).

- **The platform agent is the SOURCE OF TRUTH; the host ADAPTS to it** (set 2026-06-13 by explicit user direction: "always use the agent that is from platform (i created), … work with it"). The live agent is **`agent_01Gcox2cnu9zvUCR5Lfb9ymg` ("UniPaith College Counselor", Sonnet)**, env `env_01N43sA3tmVhij3YYZgWzAP2` — pointed to by `UNI_AGENT_ID`/`UNI_ENVIRONMENT_ID` in `infra/ecs.tf`. It is edited on platform.claude.com, NOT from the repo. The earlier repo-version-controlled agent `agent_019QbYB93Ykh8Y58RBHquiQ6` (with `suggest_replies`) is **archived** — `agents/uni.agent.yaml`/`uni_system.md` + `apply_agent.py` describe THAT deprecated agent; do **not** apply them onto the live agent (it would clobber the user's platform edits). To follow a new agent id/version, repoint `UNI_AGENT_ID`.
- **Host adapts the tool contract** in `services/uni_tools.py::dispatch_tool`: the live agent's tools (`get_profile` → `get_profile_snapshot`, `create_profile`, flat `save_signals` `{student_id, signals:[{type,content,evidence,completeness?}]}` → `_translate_flat_signals`, `get_matches`, `search_programs`, `generate_strategy`) map onto the host implementations. **SECURITY:** the agent passes a `student_id` in every call — the host **ignores it** and always uses the authenticated `user_id`. The live agent has **no `suggest_replies`**, so no tap-chips today (add it on the platform agent to restore them).
- **Host runtime:** `services/uni_agent_host.py::UniAgentHost.stream_turn` opens the Anthropic session event stream and relays the SSE contract (`student_message`/`delta`/`tool_use`/`assistant_message`/`error`/`done`). `stream_opener` makes Uni **speak first** — it sends a `[SESSION_START]` trigger (no fake student turn, `mirror_student=False`) so the agent greets + leads. `POST /me/discovery/opener/stream` drives it (warm static fallback when managed is off/fails). `ai/managed_agent_client.py` = thin SDK facade (`anthropic>=0.105`, `beta.sessions(.events)`).
- **Fallback (never a 5xx):** on host/platform **setup** failure the endpoint falls back to the in-app `orchestrator.py` for the whole turn; a **mid-stream** failure closes with a calm message. `orchestrator.py` is intentionally **kept** as the safety net — to revert the cutover, set `AI_UNI_MANAGED_AGENT_V1=false`. `agents/live_smoke_host.py` is an end-to-end host-mechanics smoke against the live agent.

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
- **Rename `pages/student/DiscoverPage.tsx`** to `DiscoverSearchView.tsx` or similar — the file is the legacy NLP-search engine, misnamed since the rebuild. Used only by `explore/SearchView.tsx`.
- ~~Essays/Resume shims~~ DONE 2026-06-10 (My Space Ships 1+4): frontend migrated off `/students/me/essays*` + `/resume*`; `api/workshops.py`, `essay_workshop_service.py`, `resume_workshop_service.py`, `schemas/workshop.py` deleted (checklist endpoints kept their paths via `api/checklists.py`); the orphaned `/messages` conversations router (`api/messaging.py` + `schemas/messaging.py`) deleted — student messaging is the inbox; `EssayWorkshopPage`/`ResumeWorkshopPage` were already gone.

## Infrastructure

Infrastructure debugging notes: RDS is in a VPC - ensure new services have correct security groups. ECS task definitions can overwrite env vars on redeploy. S3 frontend bundles can go stale - always invalidate CloudFront after deploy. DB password is managed via AWS Secrets Manager.

## Deployment Checklist (ECS/RDS/S3)

- Verify S3 bundle is current (not stale) before blaming app code
- Check ECS task definition hasn't been overwritten
- Confirm DB password matches across Secrets Manager and RDS
- Verify RDS is in correct VPC and DNS points to current ALB

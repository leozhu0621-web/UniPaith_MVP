# Contributing to UniPaith

This guide keeps the codebase solid and PRs easy to review. It is intentionally short — read it once.

## Where things go (structure map)

```
App_MVP/
├── frontend/            # Vite + React 19 SPA (TypeScript). Served via S3 + CloudFront.
│   └── src/
│       ├── pages/       # Route screens. MUST read data only through api/ modules (CI-enforced).
│       ├── components/  # Reusable UI. Extract here when a page grows — don't fatten pages.
│       ├── api/         # Typed API client modules, one per domain. The ONLY place fetch() lives.
│       ├── stores/      # Client state.
│       ├── hooks/ lib/ utils/ types/
│       └── test/
├── unipaith-backend/    # FastAPI (async SQLAlchemy). Runs on ECS Fargate.
│   └── src/unipaith/
│       ├── api/         # Routers. Depend downward on services only.
│       ├── services/    # Business logic. NEVER import api/.
│       ├── models/      # ORM models. No business logic.
│       ├── schemas/     # Pydantic request/response models.
│       ├── data/        # Static reference data. ⚠️ See "Data is not code" below.
│       ├── ai/          # Qwen-via-Together integration + evals.
│       └── core/ config.py
├── infra/               # Terraform → AWS (ECS, ALB, RDS, CloudFront, Cognito, SES, S3).
├── docs/                # Durable docs. ARCHITECTURE.md is the map. No VCS dumps here.
├── Spec/                # Product/design specs (index in Spec/00-overview.md).
└── scripts/             # One-off + maintenance scripts.
```

If you're unsure where something goes, it's probably a `service/` (backend logic) or a `component/` (frontend UI) — not a `page` or a new top-level dir.

## Architectural rules (enforced or soon-to-be)

1. **Backend layering is one-directional:** `api → services → models`. `services/` must never import `api/`. (audited: 0 violations — keep it that way.)
2. **Frontend pages never call the network directly.** No `apiClient.` or `fetch(` in `src/pages/` — go through a typed `api/<domain>.ts` module. (CI-enforced.)
3. **Data is not code.** Do **not** add new hand-written data modules (e.g. `src/unipaith/data/<x>_profile.py`). University/reference data belongs in the datastore or structured data files behind the loader, not as Python source. New `*_profile.py` files are flagged by CI. (See `docs/ARCHITECTURE.md` §Data.)
4. **No god-files.** Keep modules focused; a new file over ~800 LOC is flagged by CI. Split pages into components and types by domain.
5. **One Alembic head.** Before merging a migration, rebase it onto the current head so you don't fork a second head. `test_alembic_has_single_head` guards this.
6. **No new `any`.** Prefer real types; `as any` is debt, not a fix.

## Branches

- Name them `type/short-description`, e.g. `feat/budget-filter`, `fix/alembic-head`, `perf/deploy`.
- One logical change per branch. Keep PRs small enough to review in one sitting (aim < ~400 changed lines, data-only excepted).
- **Delete your branch after merge.** Enable repo setting "Automatically delete head branches." We currently carry 700+ stale remote branches — don't add to it.
- Prune local branches/worktrees periodically: `scripts/repo-hygiene.sh` (dry-run by default).

## Commits & PRs

- **Conventional commits** for titles: `type(scope): summary` — `feat`, `fix`, `perf`, `refactor`, `docs`, `test`, `ci`, `build`, `chore` (we also use `repair`/`enrich` for data). PR titles are checked (soft).
- Fill in the PR template — it takes 30 seconds and saves the reviewer five minutes.
- Green CI before requesting review: ruff + pytest (backend), lint + typecheck + build + vitest (frontend), `terraform validate` (infra).

## Local setup

Backend: `cd unipaith-backend && pip install -e ".[dev]"` then `pytest -n auto`.
Frontend: `cd frontend && npm ci && npm run dev`.
See `WINDOWS_SETUP.md` and `docs/` for service-specific setup (Stripe, data standards, etc.).

## Don't commit

`*.log`, `.DS_Store`, `__pycache__`, `.env`, parallel working copies (`App_MVP_*`), or VCS dumps (branch lists, etc.). The `.gitignore` covers the common ones — if something slips through, fix the ignore file in the same PR.

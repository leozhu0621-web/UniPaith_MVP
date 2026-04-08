# Deploy New Features

Full pre-work verification, feature deployment, and post-deploy validation. Run this before and after building any new feature.

## Phase 1: Environment Health

### 1. Docker & Postgres

```bash
docker exec unipaith-backend-db-1 pg_isready -U unipaith
```

If Docker is not running, start it:
```bash
cd unipaith-backend && docker compose up -d
```
Wait until `pg_isready` succeeds before continuing.

### 2. Hung DB Connections

```bash
docker exec unipaith-backend-db-1 psql -U unipaith -c "SELECT count(*) AS active_connections FROM pg_stat_activity WHERE state = 'active';"
```

If there are more than 10 active connections, warn and offer to terminate idle ones:
```bash
docker exec unipaith-backend-db-1 psql -U unipaith -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle' AND query_start < now() - interval '10 minutes';"
```

### 3. Backend Lint

```bash
cd unipaith-backend && .venv/bin/ruff check src/ tests/
```

### 4. Frontend Type Check

```bash
cd frontend && npx tsc -b --noEmit
```

### 5. Backend Tests

```bash
cd unipaith-backend && PYTHONPATH=src DATABASE_URL="postgresql+asyncpg://unipaith:unipaith@localhost:5432/unipaith" COGNITO_BYPASS=true AI_MOCK_MODE=true S3_LOCAL_MODE=true .venv/bin/pytest tests/ -v --tb=short
```

### 6. Frontend Tests

```bash
cd frontend && npm test
```

### 7. Environment Report

Print a summary table:

| Check               | Status |
|---------------------|--------|
| Docker/Postgres     | ...    |
| DB Connections      | ...    |
| Backend Lint        | ...    |
| Frontend Types      | ...    |
| Backend Tests (N)   | ...    |
| Frontend Tests (N)  | ...    |

If all checks pass, print: **ENVIRONMENT HEALTHY — READY FOR FEATURE WORK**

If any check fails, list the blockers and fix them before proceeding. Do NOT start feature work until all checks pass.

## Phase 2: Visual & Functional Verification

After completing any feature or fix, run this full verification. Do it TWICE — check, then check again.

### Pass 1: Frontend → Backend

1. **Start dev servers** (if not already running):
```bash
make dev-backend   # :8000
make dev-frontend  # :5173
```

2. **Visual check** — Open the app in the browser. Look at every page and component affected by the change. Check layout, styling, content, and responsiveness.

3. **Click through ALL functions and buttons** — Every interactive element on affected pages must be clicked and tested. Forms submitted, modals opened/closed, navigation exercised.

4. **Verify backend is doing its duty** — Check:
   - Network requests are succeeding (no 4xx/5xx in browser DevTools or preview_network)
   - Console has no errors (preview_console_logs)
   - API responses contain correct data (not empty or placeholder)
   - Database state changed as expected (query DB directly if needed)

5. **Check adjacent features** — Verify the change didn't break anything nearby. Test related pages and flows.

### Pass 2: Repeat

Do the entire Pass 1 again. This is not optional. Two full passes catch things the first pass misses.

### Verification Report

| Area                    | Pass 1 | Pass 2 |
|-------------------------|--------|--------|
| Visual layout correct   | ...    | ...    |
| All buttons/forms work  | ...    | ...    |
| API calls succeeding    | ...    | ...    |
| No console errors       | ...    | ...    |
| Backend data correct    | ...    | ...    |
| Adjacent features OK    | ...    | ...    |

If all pass: **FEATURE VERIFIED**

If anything fails: fix it, then run both passes again from the start.

## Phase 3: Commit & Push

After verification passes:

1. Commit with a clear message describing the feature/fix
2. Push to GitHub immediately

```bash
git add <relevant files>
git commit -m "feat: description of what was built"
git push
```

Every verified piece of work must be on the remote before moving to the next task. Do NOT batch commits.

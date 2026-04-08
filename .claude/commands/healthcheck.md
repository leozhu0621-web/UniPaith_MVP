# Health Check

Pre-work environment verification. Run all checks below in order and report a clear PASS/FAIL summary at the end.

## 1. Docker & Postgres

```bash
docker exec unipaith-backend-db-1 pg_isready -U unipaith
```

If Docker is not running, start it:
```bash
cd unipaith-backend && docker compose up -d
```
Wait until `pg_isready` succeeds before continuing.

## 2. Hung DB Connections

```bash
docker exec unipaith-backend-db-1 psql -U unipaith -c "SELECT count(*) AS active_connections FROM pg_stat_activity WHERE state = 'active';"
```

If there are more than 10 active connections, warn and offer to terminate idle ones:
```bash
docker exec unipaith-backend-db-1 psql -U unipaith -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle' AND query_start < now() - interval '10 minutes';"
```

## 3. Backend Lint

```bash
cd unipaith-backend && .venv/bin/ruff check src/ tests/
```

## 4. Frontend Type Check

```bash
cd frontend && npx tsc -b --noEmit
```

## 5. Backend Tests

```bash
cd unipaith-backend && PYTHONPATH=src DATABASE_URL="postgresql+asyncpg://unipaith:unipaith@localhost:5432/unipaith" COGNITO_BYPASS=true AI_MOCK_MODE=true S3_LOCAL_MODE=true .venv/bin/pytest tests/ -v --tb=short
```

## 6. Frontend Tests

```bash
cd frontend && npm test
```

## 7. Report

Print a summary table:

| Check               | Status |
|---------------------|--------|
| Docker/Postgres     | ...    |
| DB Connections      | ...    |
| Backend Lint        | ...    |
| Frontend Types      | ...    |
| Backend Tests (N)   | ...    |
| Frontend Tests (N)  | ...    |

If all checks pass, print: **READY FOR FEATURE WORK**

If any check fails, list the blockers and fix them before reporting again.

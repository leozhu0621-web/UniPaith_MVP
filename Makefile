.PHONY: dev dev-db dev-backend dev-frontend test-backend test-frontend lint format reset-db seed install-backend install-frontend

# ── Local Development ──────────────────────────────────────────────

dev-db:  ## Start PostgreSQL (Docker)
	cd unipaith-backend && docker compose up -d
	@echo "Waiting for PostgreSQL to be ready..."
	@until docker exec unipaith-backend-db-1 pg_isready -U unipaith 2>/dev/null; do sleep 1; done
	@echo "PostgreSQL is ready."

dev-backend: dev-db  ## Start backend (installs deps, runs migrations, starts uvicorn)
	cd unipaith-backend && \
		.venv/bin/alembic upgrade head && \
		.venv/bin/uvicorn unipaith.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:  ## Start frontend dev server
	cd frontend && npm run dev

dev:  ## Start full stack (DB + backend + frontend) — run in separate terminals
	@echo "Run these in separate terminals:"
	@echo "  make dev-backend   # starts DB + API on :8000"
	@echo "  make dev-frontend  # starts Vite on :5173"

# ── Installation ───────────────────────────────────────────────────

install-backend:  ## Install backend dependencies
	cd unipaith-backend && python3.12 -m venv .venv && \
		.venv/bin/pip install -e ".[dev]"

install-frontend:  ## Install frontend dependencies
	cd frontend && npm ci

install: install-backend install-frontend  ## Install all dependencies

# ── Testing ────────────────────────────────────────────────────────

test-backend:  ## Run backend tests
	cd unipaith-backend && \
		DATABASE_URL="postgresql+asyncpg://unipaith:unipaith@localhost:5432/unipaith" \
		COGNITO_BYPASS=true \
		AI_MOCK_MODE=true \
		S3_LOCAL_MODE=true \
		.venv/bin/pytest tests/ -v --tb=short

test-frontend:  ## Run frontend tests
	cd frontend && npm test

test: test-backend test-frontend  ## Run all tests

# ── Code Quality ───────────────────────────────────────────────────

lint:  ## Run linters (backend + frontend)
	cd unipaith-backend && .venv/bin/ruff check src/ tests/
	cd frontend && npm run lint

format:  ## Auto-format code
	cd unipaith-backend && .venv/bin/ruff format src/ tests/
	cd frontend && npm run format

format-check:  ## Check formatting without changing files
	cd unipaith-backend && .venv/bin/ruff format --check src/ tests/
	cd frontend && npm run format:check

# ── Database ───────────────────────────────────────────────────────

reset-db:  ## Drop and recreate all tables + seed data
	cd unipaith-backend && \
		DATABASE_URL="postgresql+asyncpg://unipaith:unipaith@localhost:5432/unipaith" \
		.venv/bin/python -m scripts.reset_dev

seed:  ## Seed development data
	cd unipaith-backend && \
		DATABASE_URL="postgresql+asyncpg://unipaith:unipaith@localhost:5432/unipaith" \
		.venv/bin/python -m scripts.seed_dev_data

migrate:  ## Run pending migrations
	cd unipaith-backend && .venv/bin/alembic upgrade head

migration:  ## Generate a new migration (usage: make migration MSG="add foo table")
	cd unipaith-backend && .venv/bin/alembic revision --autogenerate -m "$(MSG)"

# ── Help ───────────────────────────────────────────────────────────

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help

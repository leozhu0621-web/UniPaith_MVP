# 55 · Backend Production Readiness — Build Spec

> Buildable spec for hardening the existing FastAPI backend (`unipaith-backend/src/unipaith/`) to production-SaaS grade. Grounded in the real package layout (`core/`, `worker/`, `services/`, `ai/`, `crawler/`) and the actual `config.py` settings. Companion to `50` (API), `51` (data), `58` (security).
>
> Status: **draft v2.0** · 2026-05-30 · v2 converts v1 standards into build tasks against the real tree. The substrate `56`–`63` run on.

---

## 1. What already exists (ground truth)

The backend is further along than a greenfield. Real modules to **build on, not replace**:
- `core/` — `rate_limit.py`, `scheduler.py`, `middleware.py`, `security.py`, `s3.py`, `data_safety.py`, `exceptions.py`, `media_urls.py`.
- `worker/` — present (skeleton) for background processing.
- `config.py` — already defines: `db_pool_size`, `db_pool_overflow`, `db_pool_recycle`, `cors_origins`, `rate_limit_per_minute`, `rate_limit_enabled`, `scheduler_*` (7 keys incl. leader election + misfire grace), `engine_loop_*`, `pipeline_*` (crawl rpm/concurrency, Ollama extract URL/model, budget/cost), `log_level`, plus `anthropic/openai/voyage` keys.
- Dep `slowapi` (rate limiting) + `httpx` already in `pyproject.toml`.
- `ai/` has its own `providers/`, `prompt_cache.py`, `cache_invalidation.py`, `state.py`, `evals/`.

So readiness here = **filling gaps** (observability, Redis, queue, circuit breakers) and **formalizing** what's half-built (scheduler, rate limit, pipeline worker).

---

## 2. Observability (the biggest real gap — build it)

- **Structured logging:** adopt `structlog` (or stdlib JSON formatter) in `core/` → one JSON line per request (request_id, user_id, role, route, status, latency_ms) + one per AI call (provider, model, tokens, cost, latency — mirror `ai_turns`). Wire via `core/middleware.py`.
  - Build task: `core/logging.py` + request-id middleware (contextvar) so every log + error carries the id.
- **Metrics:** `prometheus-fastapi-instrumentator` → `/metrics`; export request rate/latency/error by route, DB pool in-use, cache hit rate, queue depth, AI tokens+cost, GPU util (`63`). Scrape to CloudWatch/Grafana.
- **Tracing:** OpenTelemetry FastAPI + SQLAlchemy + httpx instrumentation; sampled; trace request → service → DB/AI.
- **Dashboards + alerts:** golden signals (latency/traffic/errors/saturation) per router; page on SLO breach (§8).

---

## 3. Caching — Redis (NEW; not present today)

- Add Redis (ElastiCache in prod). Build `core/cache.py` (async client + `cached(key, ttl)` helper).
- Cache hot reads: program/school detail, match results, reference data (`60`), feed pages.
- **Key by resource + version** (`profile_version`/`program_version`, `51` §7) so a version bump busts correctly; never serve stale past a bump. Note: `ai/prompt_cache.py` + `ai/cache_invalidation.py` already exist for AI artifacts — reuse their versioning pattern; this adds the read-path cache.
- AI rationale cache per `(profile_version, program_version)` (`45`) — already modeled in `match_rationales` (`51`); Redis fronts it.

---

## 4. Task queue + workers (formalize `worker/` + the existing scheduler)

- **Queue:** adopt **arq** (async-native, Redis-backed) — fits the async stack better than Celery. Define job functions in `worker/`.
- Move to the queue: non-blocking AI calls, the crawler pipeline (`60`; `pipeline_*` config already exists), embeddings/featurization (`63`; `ai/feature_emitter.py` exists), email/SES (`57`), nightly aggregates (yield `35` `services/confidence_outcome_service.py`, attribution `28` `services/attribution_service.py`).
- **Scheduler:** `core/scheduler.py` exists with leader-election + misfire-grace config — use it for crawl cadence (`60` §10), digests (`57`), drift evals (`62`). Don't add a second scheduler.
- **Separate fleets** (bulkhead §6): web (ECS service) vs CPU jobs (arq workers) vs GPU (`63`). Config: distinct ECS task defs.

---

## 5. Rate limiting + idempotency (formalize `core/rate_limit.py`)

- `slowapi` + `core/rate_limit.py` already present + `rate_limit_per_minute`/`rate_limit_enabled` config. Build tasks: per-user **and** per-IP limits; **stricter buckets** on AI + bulk endpoints (`/students/me/matches/refresh`, `/applications/batch/*`, AI runs) → 429 + `Retry-After` (`50` §8).
- **Idempotency:** build `core/idempotency.py` — accept `Idempotency-Key` header on money/decision mutations (fees `39`, decision release `34`, deposit `35`); store key→result in Redis with TTL; replay returns the stored result (`50` §8).

---

## 6. Resilience (NEW — build circuit breakers)

- Wrap every external call (Anthropic, Qwen serving `63`, Ollama extract `60`, SES, S3, Stripe `39`) with timeout + retry(backoff+jitter, capped) + circuit breaker (e.g. `purgatory`/`tenacity` + a breaker). On trip → **graceful degrade**: AI → rule-based (`50` §6; `ai/` agents already have rule-based fallbacks — `tests/test_plan2_integration.py` is the guard); crawler → pause; never a 5xx to the user.
- **Bulkheads:** AI/GPU/crawler workloads on separate workers so they never starve API-serving latency (§4 fleets).

---

## 7. Database (extend the existing async pool)

- Pool already configured (`db_pool_size/overflow/recycle`). Build tasks:
  - **Indexes:** audit every hot filter — FKs, `status`, `stage`, `student_id`, `program_id`, `created_at`; GIN on hot JSONB keys (`programs.application_requirements` etc.); pgvector ANN (HNSW/IVFFlat) on `embeddings`/`student_feature_vectors` (`51`). Add as an Alembic migration.
  - **PgBouncer** (transaction pooling) in front of RDS sized to ECS task count.
  - **Migration safety** (`CLAUDE.md`): Alembic only, expand→contract for breaking changes, never `metadata.create_all()`, `# pragma: allowlist secret` on revision lines, single head (the `test_alembic_has_single_head` guard).
  - **N+1 guards:** eager-load relationships in list endpoints (`selectinload`); a test asserting query count on the heavy lists (pipeline `31`, feed `20`).

---

## 8. Health, deploy, SLOs

- Build `/health` (liveness) + `/ready` (checks DB + Redis + deps) for ECS probes.
- Graceful shutdown: drain in-flight requests, finish/requeue arq jobs.
- Zero-downtime deploy: DB migration runs **before** the new task version serves (entrypoint `alembic upgrade head`); per `CLAUDE.md` deploy checklist (task-def env not overwritten, secrets via Secrets Manager, CloudFront invalidated for FE).
- **SLOs:** API p95 < 400ms (non-AI) / < 2.5s (AI cached); error rate < 0.5%; uptime ≥ 99% (`07` §7). Queue: job p95 within budget; **DLQ** for poison messages + alert.

---

## 9. Build tasks (checklist)

- [ ] `core/logging.py` (structlog JSON) + request-id middleware in `core/middleware.py`.
- [ ] `/metrics` via prometheus instrumentator; OTel tracing on FastAPI+SQLAlchemy+httpx.
- [ ] `core/cache.py` (Redis) + version-keyed read cache; ElastiCache infra (Terraform).
- [ ] arq in `worker/`; move §4 workloads to jobs; wire to `core/scheduler.py`.
- [ ] Per-user+IP + AI/bulk rate buckets in `core/rate_limit.py`; `core/idempotency.py`.
- [ ] Circuit breakers + timeouts on all external calls; verify AI graceful-degrade.
- [ ] Index migration (FKs/filters/JSONB GIN/pgvector ANN); PgBouncer; N+1 query-count tests.
- [ ] `/health` + `/ready`; graceful shutdown; migration-before-serve entrypoint.
- [ ] Golden-signal dashboards + SLO alerts; DLQ + alert.

---

## 10. Acceptance

- [ ] Structured logs + `/metrics` + traces live; dashboards + alerts on golden signals.
- [ ] Redis read cache with version-keyed invalidation; measured hit rate.
- [ ] arq queue + `core/scheduler.py` running §4 workloads on separate fleets.
- [ ] Rate limits (user+IP, AI/bulk buckets) + idempotency on §5 endpoints.
- [ ] Circuit breakers → graceful degrade; AI never 5xx (`tests/test_plan2_integration.py`).
- [ ] No seq-scan on hot paths (EXPLAIN); pooled; single-head migrations.
- [ ] `/health`+`/ready`; SLOs tracked; DLQ alerting.

---

## 11. Open questions

- Queue: arq (recommended, async-native) vs Celery — arq.
- Redis: ElastiCache from day one (multi-task ECS rules out in-process cache).
- The existing `pipeline_extract_ollama_*` config implies an Ollama extraction path predating the `63` Qwen decision — reconcile: `63` standardizes extraction on Qwen (vLLM/Bedrock); confirm whether Ollama stays for local-dev only.

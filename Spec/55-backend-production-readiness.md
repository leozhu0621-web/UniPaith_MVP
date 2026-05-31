# 55 · Backend Production Readiness

> Raises the FastAPI backend to production-SaaS grade: observability, caching, async jobs, rate limiting, idempotency, resilience, DB health. Companion to `50` (API contract), `51` (data model), `58` (security).
>
> Status: **draft v1.0** · 2026-05-30 · Production-parity track. The substrate that `56`–`63` (search, realtime, crawler, ML) run on.

---

## 1. Observability

- **Structured logging** (JSON) with request id, user id, role, route, latency; one log line per request + per AI call.
- **Metrics** (Prometheus/CloudWatch): request rate/latency/error by route, DB pool usage, cache hit rate, queue depth, AI tokens+cost (`ai_turns`), GPU util (`63`).
- **Tracing** (OpenTelemetry): trace a request → service → DB/AI; sample.
- **Dashboards + alerts**: golden signals (latency, traffic, errors, saturation) per surface; page on SLO breach.

## 2. Caching (Redis)

- Cache hot reads: program/school detail, match results, reference data (`60`), feed pages.
- Key by resource + version (`profile_version`/`program_version`) for correct invalidation (`51` §7).
- AI rationale cache per `(profile_version, program_version)` (`45`).
- TTL + explicit bust on write; never serve stale past a version bump.

## 3. Task queue + background jobs

- **Queue** (arq/Celery + Redis or SQS) for: AI calls that needn't block, crawler pipeline (`60`), embeddings/featurization (`63`), email/SES (`57`), nightly aggregates (yield `35`, attribution `28`).
- **Scheduler** (beat/cron) for periodic: crawl cadence (`60` §10), digests (`57`), drift evals (`62`).
- Separate worker fleets (web vs CPU jobs vs GPU `63`) — bulkhead (§6).

## 4. Rate limiting + idempotency

- Per-user + per-IP rate limits; stricter on AI + bulk endpoints → 429 with retry guidance (`50` §8).
- **Idempotency-Key** on money/decision mutations (fees `39`, decision release `34`, deposit `35`) — dedup retries (`50` §8).

## 5. Resilience

- **Circuit breakers / timeouts** on every external call (Anthropic, Qwen serving `63`, SES, S3, Stripe). On trip → graceful degrade (AI → rule-based, `50` §6; never a 5xx to the user).
- Retries with backoff + jitter on transient failures; cap attempts.
- **Bulkheads**: AI/GPU/crawler workloads never starve API-serving latency.

## 6. Database

- **Indexes**: every FK + every hot filter (status, stage, student_id, program_id, created_at); GIN on hot JSONB keys; pgvector ANN index on embeddings.
- **Connection pooling** (PgBouncer or async pool) sized to ECS task count.
- **Migration safety** (CLAUDE.md): Alembic, expand→contract for breaking changes, never `create_all`, `# pragma: allowlist secret` on revision lines.
- N+1 guards (eager-load relationships in list endpoints).

## 7. Health + deploy

- `/health` (liveness) + `/ready` (DB+cache+deps) probes for ECS.
- Graceful shutdown: drain in-flight, finish/requeue jobs.
- Zero-downtime deploy; DB migration runs before new task version serves.
- Per CLAUDE.md deploy checklist: task-def env not overwritten, secrets via Secrets Manager, CloudFront invalidated (FE).

## 8. SLOs

- API p95 < 400ms (non-AI), < 2.5s (AI cached), error rate < 0.5%, uptime ≥ 99% (`07` §7).
- Queue: job p95 within budget; DLQ for poison messages + alert.

## 9. Acceptance

- [ ] Structured logs + metrics + traces live; golden-signal dashboards + alerts.
- [ ] Redis caching with version-keyed invalidation; measured hit rate.
- [ ] Queue + scheduler running the §3 workloads on separate fleets.
- [ ] Rate limits + idempotency on the §4 endpoints.
- [ ] Circuit breakers → graceful degrade; AI never 5xx (`tests/test_plan2_integration.py`).
- [ ] DB indexed (no seq-scan on hot paths), pooled, migration-safe.
- [ ] Health probes + graceful shutdown; SLOs tracked.

## 10. Open questions

- Queue tech: arq (async-native) vs Celery — recommend arq for the async stack.
- Redis vs in-process cache for MVP — Redis from the start (multi-task ECS).

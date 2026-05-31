# 55 · Backend Production Readiness

> What turns the FastAPI backend from "serves requests" into a **production SaaS** at the operational level a marketed app demands: observability, caching, background jobs, rate limiting, idempotency, resilience/graceful-degradation, health probes, and database discipline. Feature docs own business logic; this owns the production substrate that keeps it fast, reliable, and debuggable under load.
>
> Status: **draft v1.0** · 2026-05-30 · Production-parity track. Stack (`CLAUDE.md`): Python 3.12 + FastAPI + SQLAlchemy 2 async + Postgres 16 + pgvector on ECS Fargate. Pairs with `50` (API), `51` (data), `57` (realtime/queues), `58` (security).

---

## 1. Observability — the three pillars

A production app is debuggable in prod without a debugger. Implement all three ([pillars](https://dev.to/thebitforge/building-scalable-saas-products-a-developers-guide-48a7)):

### 1.1 Structured logging
- JSON logs (not free text), one event per line, with a **correlation/request id** propagated through every layer (middleware injects it; AI calls + jobs carry it).
- Standard fields: `timestamp, level, request_id, user_id, role, route, status, latency_ms, msg`.
- Never log PII or secrets (`58`); log ids + masked values.
- Ship to CloudWatch (ECS) → queryable.

### 1.2 Metrics — the golden signals
Per the SRE four + business signals ([source](https://www.sashido.io/en/blog/backend-infrastructure-management-without-on-call-chaos)):
- **Latency** p50/p95/p99 per route (catch degradation before users complain).
- **Traffic** req/s per route.
- **Errors** rate per route + per status class (4xx vs 5xx).
- **Saturation** CPU/mem/connections/queue-depth.
- **Business**: AI cost/tokens per agent (`ai_turns`, `51`), match latency, signup→match funnel, queue lag.
- Emit via OpenTelemetry/StatsD → a dashboard (CloudWatch/Grafana). Alert thresholds in §9.

### 1.3 Tracing + error tracking
- Distributed tracing (OpenTelemetry) across request → service → DB → AI provider, so a slow request shows *where*.
- **Error tracking** (Sentry or equiv): every unhandled exception captured with request context + correlation id; release-tagged. This is table stakes for a marketed app.

---

## 2. Caching (Redis — add to the stack)

Redis is the missing production primitive; it powers cache, rate-limit, idempotency, sessions, and pub/sub for realtime ([source](https://workforcenext.in/blog/nodejs-performance-scaling-production-checklist-2026/)). Provision an ElastiCache Redis in-VPC.

- **Cache-aside** for hot reads: program detail, institution profile, match results, computed analytics. TTL on everything; no unbounded keys.
- **Key convention**: `unipaith:{entity}:{id}:{version}` — version segment makes invalidation a no-op (bump version, old key expires). Aligns with the `profile_version`/`program_version` invalidation already in the schema (`51` §9, `45` §12).
- **Cache the AI rationale** layer already done via `match_rationales` (`51`); Redis fronts it for sub-ms reads.
- **Graceful**: a cache that's down must not take the app down — fall through to DB (`source: cache_miss`).
- Document TTL + invalidation per cached entity (a table in this doc as caching grows).

---

## 3. Background jobs / task queue (add: Celery or Arq + Redis/SQS)

Anything slow, retryable, or fire-and-forget must leave the request path. Today these likely run inline and block — production-grade moves them to a queue ([job patterns](https://www.averagedevs.com/blog/background-jobs-queue-patterns-web-apps)).

**Jobs to enqueue:**
- Email/SES sends (verification, notifications, digests, campaigns `25`).
- AI agent runs that needn't be synchronous (batch rationale, strategy regen, summaries `45`) — though interactive ones stay in-request with the fallback (`50` §6).
- Feature-vector / embedding recompute on profile change (`51` `student_feature_vectors`).
- Document parse/OCR after upload (`44` §5.3).
- Analytics rollups, attribution recompute (`28`), yield snapshots (`35`).
- Notification fan-out (`57`).

**Job discipline** ([reliability](https://medium.com/@ozer.deniz/retry-is-not-a-strategy-rethinking-background-job-reliability-in-enterprise-systems-50e20e127af4)):
- **Idempotent** (safe to retry) — keyed so a re-run doesn't double-send/double-write.
- **Retry with exponential backoff** for transient failures; **dead-letter queue** for permanent ones + alert.
- Observable: queue depth, processing time, error rate metrics (§1.2).
- Visibility timeout > max job time; no lost/duplicated jobs.

---

## 4. Rate limiting (Redis token-bucket)

Protect the app + AI budget + fairness ([token bucket](https://workforcenext.in/blog/nodejs-performance-scaling-production-checklist-2026/)):
- **Per-user + per-IP + per-endpoint-class** limits via Redis `INCR`+`EXPIRE` (token bucket).
- Tighter limits on expensive endpoints: AI runs, bulk campaign/segment, search, auth (brute-force).
- Return **429 + `Retry-After`** (frontend honors it, `50` §3/§8).
- Auth endpoints get progressive backoff / lockout (`58`).

---

## 5. Idempotency (money + decisions + side-effects)

For POST/PATCH that create resources or have side effects ([idempotency](https://dev.to/thebitforge/building-scalable-saas-products-a-developers-guide-48a7)):
- Accept an **`Idempotency-Key` header**; cache `(user_id, key) → response` in Redis 24h; return the cached response on retry (`50` §8).
- Critical: decision release (`34`), batch operations (`/applications/batch/*`), fees/deposits (`39`), enrollment confirm (`35`), application submit (`15`).
- DB-level unique constraints as the backstop (e.g., one application per (student, program)).

---

## 6. Resilience & graceful degradation

The app stays useful when a dependency fails — this is the production mindset.
- **AI provider down** → rule-based fallback, never 5xx (`50` §6, the existing invariant — generalize it: the cache/queue answer the caller even if a tier fails, [source](https://www.sashido.io/en/blog/backend-infrastructure-management-without-on-call-chaos)).
- **Circuit breakers** around external calls (Anthropic/OpenAI, SES, S3): after N failures, open the breaker → serve fallback → periodic half-open retry. Prevents cascade + thundering-herd.
- **Timeouts** on every external call (no unbounded awaits); sensible connection/read timeouts to AI + S3 + DB.
- **Bulkheads**: AI failures don't exhaust the pool that serves profile reads (separate pools/concurrency limits).
- **Provider portability** already specified (`04` §5) — failover Anthropic↔OpenAI↔Bedrock.

---

## 7. Database discipline (Postgres at scale)

107 tables (`51`) means schema discipline matters.
- **Indexing**: index every FK + every column in a WHERE/ORDER BY/JOIN on a hot path. Audit with `pg_stat_statements`; add missing indexes for the slow queries. GIN indexes on hot JSONB keys (program requirements/cost search).
- **N+1 elimination**: async SQLAlchemy with explicit `selectinload`/`joinedload` for relationships rendered in lists (pipeline, feed, match results). N+1 is the #1 silent latency killer.
- **Connection pooling**: tuned pool size for Fargate task count × DB max-connections; use a pooler (pgbouncer / RDS Proxy) so connection storms don't exhaust RDS.
- **Read patterns**: heavy analytics (`28`,`35`) read from a replica or materialized views, not the primary, to protect transactional latency.
- **Migration safety** (`CLAUDE.md`: Alembic, never `create_all`): online migrations — additive first (add column nullable → backfill in a job → enforce), avoid long table locks; expand-contract for renames/drops (e.g., the `match_score` legacy drop, `51` §10).
- **pgvector**: ANN index (HNSW/IVFFlat) on embedding columns for match similarity at scale (`06` §4).

---

## 8. Health, readiness, deploy safety

- **`/health`** (liveness — already exists, `50` §4) + **`/ready`** (readiness — checks DB + Redis + can-serve) so ECS/ALB route only to ready tasks.
- **Graceful shutdown**: drain in-flight requests + finish/requeue jobs on SIGTERM before exit (zero-downtime deploys).
- **Zero-downtime deploys**: rolling ECS update behind ALB; new task must pass `/ready` before old drains.
- **DB migrations in deploy**: run as a pre-deploy step, not at app boot; backward-compatible so old + new app versions coexist during rollout.
- Config via env/Secrets Manager (`CLAUDE.md`); 12-factor — no config in code.

---

## 9. Alerting & SLOs

Define SLOs and alert on burn (matches the `07` §7 performance targets):
- **Availability** ≥ 99.9% (the `07` bar is 99%+; aim higher for API).
- **Latency** alert when p95 > budget for 5m (per critical route).
- **Error rate** alert when 5xx > 1% for 5m.
- **Queue lag** alert when depth/age exceeds threshold.
- **AI cost** alert on daily spend anomaly (`ai_turns` aggregation).
- **DLQ** non-empty → page.
- On-call runbook per alert (link from the alert).

---

## 10. Readiness checklist (gate, complements `52` §5)

- [ ] Structured logs + correlation id end-to-end.
- [ ] Golden-signal metrics dashboard + error tracking (Sentry) live.
- [ ] Tracing across request→DB→AI.
- [ ] Redis: cache-aside on hot reads + graceful fallback.
- [ ] Task queue: email/AI/recompute/fan-out off the request path; retries + DLQ.
- [ ] Rate limiting on expensive + auth endpoints (429 + Retry-After).
- [ ] Idempotency keys on money/decision/batch endpoints.
- [ ] Circuit breakers + timeouts on all external calls.
- [ ] FK/hot-path indexes present; N+1 eliminated on list endpoints; pooler in place.
- [ ] `/ready` probe + graceful shutdown + zero-downtime migration discipline.
- [ ] SLOs + alerts + on-call runbooks.

---

## 11. Open questions

- **Queue tech**: Celery vs Arq (async-native, fits FastAPI better) vs SQS+workers. Recommend **Arq** (async, Redis-backed) to match the async stack — confirm.
- **Redis provisioning**: ElastiCache sizing + whether it doubles as the realtime pub/sub backbone (`57`).
- **Read replica**: when does analytics load justify an RDS read replica / materialized views?
- **Tracing/error vendor**: Sentry + OTel→CloudWatch, or a unified APM (Datadog)? Cost vs depth.
- **Multi-region/DR**: out of MVP, but define RPO/RTO + backup/restore drill before claiming "production."

Sources: [scalable SaaS guide](https://dev.to/thebitforge/building-scalable-saas-products-a-developers-guide-48a7) · [Node prod checklist 2026](https://workforcenext.in/blog/nodejs-performance-scaling-production-checklist-2026/) · [background job patterns](https://www.averagedevs.com/blog/background-jobs-queue-patterns-web-apps) · [job reliability](https://medium.com/@ozer.deniz/retry-is-not-a-strategy-rethinking-background-job-reliability-in-enterprise-systems-50e20e127af4) · [infra without on-call chaos](https://www.sashido.io/en/blog/backend-infrastructure-management-without-on-call-chaos).

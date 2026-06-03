# 73 · Launch Hardening & Scale — Cache, Queue, Idempotency, Surge

> *"Acceptable performance standards include maintaining 99%+ platform uptime"* (`Business Methodology`:829) — and the single most-cited incumbent weakness is the opposite: Common App's *"periodic peak-season outages (most notoriously during November 1 ED deadlines)"* (`Competition Analysis`:917). Surge-fragility is a **winnable** differentiator. But the backend's scale primitives are half-built and **per-replica**: `core/cache.py:130` self-reports `backend="memory"`, `redis_available()` (`core/cache.py:29`) only checks config+import, and **`redis` is not a dependency** (`pyproject.toml`) — so the cross-task bridge `core/realtime.py:6` and `core/cache.py` both promise *"activates automatically once REDIS_URL is set"* (`infra/ecs.tf:260`) is **dead code in prod** (no `REDIS_URL` env, no `aws_elasticache_*` resource). Rate-limit is in-memory and IP-keyed via slowapi `get_remote_address` (`core/rate_limit.py:7,14`) — won't coordinate across ECS tasks, and behind the ALB every request may share a source IP. There is no `/metrics`, no tracing (`core/observability.py` is JSON-logging only), no distributed queue (`worker/__init__.py` is empty; `core/scheduler.py` is in-process APScheduler, `scheduler_enabled` default False), no general idempotency (only two ad-hoc unique constraints: `models/payment.py:55`, `models/workflow.py:39`), and no circuit breakers on LLM/SES/S3. `55` *is the plan for all of this and it is not built.*
>
> This spec is the **execution** of `55`'s still-unbuilt items, plus the deltas the `64` audit found, plus the launch-surge gate. Do not re-spec `55`'s architecture — reference it (`55` §2–§9 map 1:1 to the sections below) and ship the gap-close. This is the **hard gate** on flipping public signup on (`64` §6 "It survives launch").
>
> Build anchor: wire Redis into `core/cache.py` + `core/rate_limit.py` + `core/realtime.py`; build `worker/` (arq) + `core/idempotency.py` + `core/breaker.py` + `core/metrics.py`; add the index migration; cursor-paginate `services/match_service.py:353`. Pairs with `55` (THE plan), `57` (realtime broker already has the Redis seam), `28`/`56` (cached read paths), `65` (cursor paging + ANN index it needs), `63` (worker fleets for GPU serving), `39`/`34`/`35` (idempotent money/decision mutations).
>
> Status: **draft v1.0** · 2026-06-02 · `55` is the plan; this is build-it-now + what `55` missed (surge profile, universal-app fan-out at scale, the dead Redis bridges). Never breaks the AI-fallback invariant (`tests/test_plan2_integration.py`).

---

## 1. What exists vs what to build

| Capability | Real module today | Status |
|---|---|---|
| Read cache (version-keyed, TTL) | `core/cache.py` `VersionedCache` — `backend="memory"` (`:130`) | exists — **back it with Redis** (the soft-dep seam `:29` is built) |
| Cross-task realtime fan-out | `core/realtime.py` in-proc + Redis bridge *seam* (`:6`) | exists, **bridge never fires** (no `redis` dep / `REDIS_URL`) — wire it |
| Rate limit | `core/rate_limit.py` slowapi, in-mem, IP-keyed (`:7,14`) | exists — **distributed (Redis) + per-user + real client-IP (XFF)** |
| Observability | `core/observability.py` JSON logs + `request_id` contextvar | exists — **add `/metrics` (prometheus) + OTel tracing** |
| Background jobs | `core/scheduler.py` APScheduler in-proc; `worker/__init__.py` empty | scheduler exists — **add arq queue + formalize `worker/`** |
| Idempotency | ad-hoc `UniqueConstraint` ×2 (`payment.py:55`, `workflow.py:39`) | **NEW: `core/idempotency.py` + `Idempotency-Key` on money/decision** |
| Circuit breakers | none — raw `httpx`/SDK calls | **NEW: `core/breaker.py` on LLM/embeddings/SES/S3** |
| Indexes | FK indexes on hot cols; **no JSONB GIN / pgvector ANN** | **NEW: index migration** (FK/filter/GIN/ANN) + PgBouncer |
| Pagination | `match_service.py:353` `limit`-only | **NEW: cursor pagination** on match/explore |
| DLQ | `notification_delivery.py:41` in-proc `deque(maxlen=500)` | exists (in-proc) — **durable DLQ via the queue** |
| Health / deploy | `api/health.py` `/health`+`/ready`; entrypoint `alembic upgrade heads` | exists — **harden** (drain on SIGTERM, migrate-lock) |
| Surge survival | none — no load test, no surge autoscale | **NEW: surge profile + load test as the launch gate** |

**The honest frame** (`64` §1.9): health/`/ready`/JSON-logging/PII/realtime are real; *"cache is in-process only … rate-limit is in-memory IP-keyed … no metrics/tracing … no distributed queue. `55` describes the fixes; they are not built."* This spec builds them.

## 2. Redis is the foundation — add the dependency, the infra, the backend (`55` §3)

Everything below needs one shared Redis. The seams are already written; the dependency and infra are not.

- **Dependency + infra.** Add `redis>=5` to `pyproject.toml` (it is absent). Provision `aws_elasticache_replication_group` (Redis 7, single-AZ for v1, multi-AZ at scale) in `infra/`; same VPC + a new SG that the ECS task SG can reach (the `CLAUDE.md` infra rule: new services need correct security groups). Set `REDIS_URL` in the ECS task env (`infra/ecs.tf` — today it is only a *comment* at `:260`, never a real var).
- **Cache backend.** Implement a `RedisCache` behind the existing `VersionedCache` interface so `cached()` / `make_key()` / version-keyed busting (`51` §7) are unchanged; `stats()` must report `backend="redis"` so `/goal/backend` (`55`) stops lying. Keep the in-proc cache as the dev/CI/no-Redis fallback — the soft-dependency posture `core/cache.py` and `core/realtime.py` already share. Front the read paths `55` §3 names: program/school detail, match-result reads (`match_service.py` `list_matches`), reference data (`60`), feed pages (`56`), the `/goal/*` surfaces.
- **Realtime bridge.** With `redis` installed and `REDIS_URL` set, `core/realtime.py`'s `_REDIS_CHANNEL` bridge fires for real — a client on task A receives an event published on task B (the code is written and currently unreachable). This is a *wiring* change, not new code; verify with a two-process test.
- The AI artifact caches (`ai/prompt_cache.py`, `ai/cache_invalidation.py`) keep their own versioning — Redis fronts the *read-path* cache and the rationale cache per `(profile_version, program_version)` (`45`/`65`); do not collapse them.

## 3. Distributed rate limiting + correct client IP (`55` §5)

`core/rate_limit.py` keys on `get_remote_address` (`:14`) into slowapi's **in-memory** store — two failures at once: (a) per-task counters never coordinate across the ECS fleet, so the real limit is `N_tasks × rate_limit_per_minute`; (b) behind the ALB the "remote address" is often the LB's, so all users share one bucket (over-throttling everyone or no one).

- **Distributed store.** Point slowapi at Redis (`storage_uri=settings.redis_url`) so the bucket is fleet-wide; fall back to in-memory when `redis_url` is unset (dev/CI). Config `rate_limit_per_minute`/`rate_limit_enabled` (`config.py:84-85`) stay the knobs.
- **Real client IP.** Derive the key from the **left-most untrusted `X-Forwarded-For`** hop (ALB appends the client IP), not `get_remote_address`; trust only the ALB/CloudFront hop count. Add `ProxyHeadersMiddleware` (or equivalent) so `request.client.host` is correct everywhere, not just rate-limit.
- **Per-user + stricter buckets** (`55` §5, `50` §8). Key authenticated requests by `user_id` (fall back to IP for anon); **tighter buckets** on AI + bulk + surge endpoints — `/students/me/matches/refresh`, `/applications/batch/*`, the AI runs (`45`), and the universal-submit fan-out (§8) — returning `429` + `Retry-After`. A signup-surge bucket protects the registration path specifically (the launch-day hot path).

## 4. Idempotency framework — money & decisions (`55` §5, `64` §6 invariant)

Today idempotency is **two hand-rolled unique constraints** — payments `UniqueConstraint("application_id","kind")` (`payment.py:55`) and notifications `event_id` partial-unique (`workflow.py:39`). Every *other* mutating retry (a double-clicked decision release, a re-fired offer, a deposit reconcile) is unguarded. Build the general framework `55` §5 names:

- **`core/idempotency.py`.** Accept an `Idempotency-Key` header on money/decision mutations; store `key → {status, response_body, status_code}` in Redis with TTL; an in-flight key returns `409 Conflict` (or blocks on a short lock), a completed key **replays the stored response** verbatim, a mismatched body for the same key is a `422` (per Stripe's semantics, since `39` already abstracts Stripe). Keyed per `(user_id, route, key)` so keys can't collide across users.
- **Apply it to the real mutations** the verticals already treat as money/decision: fee checkout + waiver + refund (`39` `payment_service.py`), decision release + offer mint/rescind (`34`), deposit record (`35`), and the universal-submit fan-out (§8 — submitting to N schools must be exactly-once per school). The existing unique constraints stay as the **DB-level backstop**; the framework is the request-level guard so a retry never even reaches the constraint.
- **Invariant:** a replayed mutation must be observably identical and must never double-charge, double-release, or double-notify — the same "never a surprise" contract the payments idempotency note already states (`payment.py:4`).

## 5. Observability — metrics + tracing (`55` §2; logging already done)

`core/observability.py` is the *done* half of `55` §2 — structured JSON access logs + a `request_id` contextvar threaded into every record (`:28,57-67`) and `log_access` golden-signal fields (`:69`). The missing half is **numeric** signals and **distributed** tracing:

- **`/metrics` (prometheus).** Add `prometheus-fastapi-instrumentator` → request rate/latency/error **by route template**, plus app gauges the surge gate needs: DB pool in-use (`db_pool_size`/`overflow`, `config.py`), cache hit-rate (`VersionedCache.stats()`), **queue depth + job latency** (§6), DLQ size (`notification_delivery.py:41`), circuit-breaker state (§7), AI tokens+cost (mirror `ai_turns`), GPU util (`63`). Scrape to CloudWatch/Grafana. Endpoint unauthenticated like `/health` but bound to the internal SG.
- **Tracing (OpenTelemetry).** Instrument FastAPI + SQLAlchemy + httpx + the Anthropic/embedding SDK; sampled; one trace spans request → service → DB / AI / Redis. The `request_id` contextvar becomes the trace correlation id, so a log line and its span join.
- **Golden-signal dashboards + SLO alerts** (latency/traffic/errors/saturation) per router; page on the §9 SLO breach. This is what turns "99% uptime" from an aspiration into something measured weekly (`Business Methodology`:829 names weekly uptime monitoring).

## 6. Task queue + workers — arq, formalize `worker/` (`55` §4)

`worker/__init__.py` is **empty** and `core/scheduler.py` is in-process APScheduler whose job bodies are mostly stubs (`scheduler.py:153-180` "engine being rebuilt") — fine for cadence, wrong for load-bearing async work, and it dies with the web task.

- **arq (Redis-backed, async-native** — `55` §4/§11 already chose it over Celery). Define job functions in `worker/` and run them as a **separate ECS service** (distinct task def — the bulkhead, `55` §4/§6) so AI/crawler/embedding load never starves API latency.
- **Move to the queue** (`55` §4): non-blocking AI calls, the crawler pipeline (`60`, `pipeline_*` config exists), embeddings/featurization (`63`/`65` — the program embedder + featurizer are batch by design), email/SES (`57` `notification_delivery.py`), nightly aggregates (yield `35`, attribution `28` `attribution_service.py` always-backfill-on-read is a prime offload).
- **Keep `core/scheduler.py` as the *cadence* trigger**, not the executor — its jobs (`saved_search_alerts`, `notification_digest`, `crawler_engine_tick`) **enqueue** arq jobs instead of doing the work inline (`scheduler.py:183-237`). Don't add a second scheduler; its leader-election + misfire-grace config (`scheduler_*`) stays the source of "run once across the fleet."
- **Durable DLQ.** arq's retry + a dead-letter set replaces the in-process `deque(maxlen=500)` (`notification_delivery.py:41`, which already flags *"the durable SQS DLQ is the planned replacement"*); poison messages alert (§5/§9). Job p95 within budget; retries with backoff+jitter.

## 7. Circuit breakers on every external call (`55` §6 — NEW)

No external call is wrapped today. A slow Anthropic, SES throttle, or S3 stall propagates as latency or a 5xx — the exact failure mode that takes down a launch.

- **`core/breaker.py`.** Wrap every egress — Anthropic (`ai/providers/anthropic_provider.py`), the embedding provider (`65`), Qwen serving (`63`), SES (`57`), S3 (`core/s3.py`), Stripe (`39`) — with **timeout + retry(backoff+jitter, capped) + circuit breaker** (e.g. `tenacity` for retry + a breaker; `purgatory` is async-native). On open → **graceful degrade**, never a 5xx: AI → rule-based (the `ai/` agents already have rule-based fallbacks; `tests/test_plan2_integration.py` is the guard); crawler → pause (`60`); cache/Redis down → in-proc cache + direct DB read; SES down → enqueue for retry. Breaker state is a `/metrics` gauge (§5).
- **Bulkheads** (§6 fleets): the breaker plus separate worker fleets (§6) means a tripped LLM breaker degrades AI surfaces *only* — API-serving latency is unaffected. This is the structural guarantee behind the fallback invariant under load.

## 8. Surge: deadline fan-out at scale (the launch gate — `64` §6)

Two scale concerns the audit names specifically, both incumbent weaknesses:

- **Deadline surge.** Common App's *"November 1 ED deadline"* outages (`Competition Analysis`:917) are the canonical mode: a thundering herd of submits + payments + notifications in a few hours. Build a **surge profile** — a load-test scenario (k6/Locust) that ramps to the projected ED-night concurrency on the hot paths (signup, match read, **application submit**, fee checkout, notification fan-out) and asserts p95 within SLO (§9) and zero 5xx. Drive an **ECS autoscale policy** (target-tracking on CPU + ALB request-count-per-target + the queue-depth metric §5) sized from the profile; PgBouncer (§ DB) absorbs the connection spike. **The load test passing at the surge profile is the hard gate on public signup** (`64` §6).
- **Universal application fan-out** (`Competition Analysis`:824 — *"routing of completed applications to … institutions' admissions offices and downstream CRMs"*, 10.19M apps/cycle). UniPaith has `applications` (one row per student×program, `models/application.py:46`) but not the surge-scale **apply-once → submit-to-many** rail. At launch scale a single student action can fan out to N schools: each per-school submit must be **idempotent** (§4 — exactly-once per `(application, school)`), **queued** (§6 — the fan-out is async, not a synchronous N-way blocking call), and **back-pressured** (§3 bucket). The student sees one "submitted"; the N downstream routes drain through the queue with per-route retry + DLQ. This is `74`'s CRM/Slate routing at the *transport* layer — `73` owns it surviving the spike, `74` owns the destinations.

## 9. Database, health, SLOs (`55` §7/§8)

- **Index migration** (`55` §7 — the biggest silent gap). Audit hot filters and add as **one Alembic migration** (expand→contract, single head — the `test_alembic_has_single_head` guard, `CLAUDE.md`): composite/covering indexes on hot filter+sort combos (`match_results(student_id, fitness_score desc)` for `list_matches`; `applications(student_id, status)`, `(program_id, status)` — base FK indexes exist `application.py:33,53,59` but not the filter composites); **GIN on hot JSONB** (`programs.application_requirements`, the sparse-feature blobs `65` adds); **pgvector ANN (HNSW)** on `embeddings`/`student_feature_vectors` — the `embeddings` HNSW table exists (`models/matching.py:119`) but `65`'s candidate-gen needs the index live. Verify each with `EXPLAIN` (no seq-scan on hot paths).
- **PgBouncer** (transaction pooling) in front of RDS, sized to ECS task × `db_pool_size` so the surge (§8) doesn't exhaust RDS connections. **N+1 guards:** `selectinload` on list endpoints + a query-count assertion test on the heavy lists (pipeline `31`, feed `20`, matches).
- **Cursor pagination.** `match_service.py:353` `list_matches(..., limit=20)` is `limit`-only — replace with keyset/cursor (`(fitness_score, id)` tuple) on match/explore so deep pages don't `OFFSET`-scan and a growing catalog stays O(page). Mirror on `56` search.
- **Health & deploy** (`55` §8 — mostly done, harden it). `/health`+`/ready` exist (`api/health.py`); `/ready` checks DB — **extend it to ping Redis + report queue reachability** so a Redis outage fails readiness (and the breaker §7 takes over). Migrate-before-serve exists (`docker-entrypoint.sh` runs `alembic upgrade heads` before uvicorn) — harden the **recovery branch** (it purges `alembic_version` + re-stamps on failure, which under concurrent task starts can race): wrap the migrate in an **advisory lock** so only one task migrates per deploy. **Graceful shutdown:** today lifespan only calls `shutdown_scheduler()` (`main.py:251-253`) — add request-drain on SIGTERM + finish/requeue in-flight arq jobs (`55` §8).
- **SLOs** (`Business Methodology`:829 — 99%+ uptime): API p95 < 400ms (non-AI) / < 2.5s (AI cached); error rate < 0.5%; uptime ≥ 99%. Queue job p95 within budget; DLQ alert. These are the §5 dashboard's alert thresholds.

## 10. Build tasks (checklist)

- [ ] Add `redis>=5` to `pyproject.toml`; provision ElastiCache (`infra/`) + SG; set real `REDIS_URL` in `ecs.tf` (today a comment, `:260`).
- [ ] `RedisCache` behind `VersionedCache`; `stats()` reports `backend="redis"`; in-proc fallback kept; verify realtime cross-task bridge fires (`core/realtime.py`).
- [ ] Distributed slowapi store (Redis) + X-Forwarded-For client-IP + `ProxyHeadersMiddleware`; per-user + AI/bulk/signup-surge buckets (`core/rate_limit.py`).
- [ ] `core/idempotency.py` (`Idempotency-Key`, Redis store, replay/409/422); applied to fees `39` / decisions `34` / deposit `35` / universal-submit §8.
- [ ] `/metrics` (prometheus-instrumentator) + OTel tracing (FastAPI+SQLAlchemy+httpx+SDK); golden-signal dashboards + SLO alerts.
- [ ] arq in `worker/` as a separate ECS service; move §6 workloads to jobs; scheduler enqueues instead of executing; durable DLQ replaces the in-proc deque.
- [ ] `core/breaker.py` (timeout+retry+breaker) on Anthropic/embeddings/Qwen/SES/S3/Stripe; verify AI graceful-degrade (`tests/test_plan2_integration.py`).
- [ ] Index migration (FK composites / JSONB GIN / pgvector HNSW), single head; PgBouncer; N+1 query-count tests.
- [ ] Cursor pagination on `match_service.py:353` + `56` search.
- [ ] `/ready` pings Redis + queue; migrate-under-advisory-lock; SIGTERM request-drain + arq requeue.
- [ ] Surge profile load test (k6/Locust) on signup/submit/fee/match; ECS autoscale policy; **gate public signup on it passing** (`64` §6).

## 11. Acceptance

- [ ] Redis is the live cache backend (`stats().backend == "redis"`); cross-task realtime + rate-limit + idempotency all coordinate across ≥2 ECS tasks (proven by a multi-process test). The dead bridges (`core/cache.py:29`, `core/realtime.py:6`) are live.
- [ ] Rate limit is fleet-wide and keyed by **real client IP / user**, not the ALB hop (`core/rate_limit.py` no longer `get_remote_address`-only); AI/bulk/signup buckets return 429+`Retry-After`.
- [ ] `Idempotency-Key` on every money/decision mutation: a replayed request returns the identical stored response and never double-charges/releases/notifies; the §4 routes are covered, the unique constraints remain the backstop.
- [ ] `/metrics` exposes golden signals + pool/cache/queue/breaker/AI-cost gauges; traces span request→DB→AI; SLO alerts fire on breach.
- [ ] arq queue + separate worker fleet running §6 workloads; scheduler enqueues; durable DLQ alerts on poison; `worker/` is no longer an empty package.
- [ ] Circuit breakers on all egress → graceful degrade; **no model path 5xx under a tripped breaker** (`tests/test_plan2_integration.py` green under fault injection).
- [ ] `EXPLAIN` shows no seq-scan on the hot paths; pgvector ANN index live (`65` candidate-gen non-O(N)); cursor pagination on match/explore; single-head migration.
- [ ] `/ready` fails when Redis is down; migrate-before-serve holds an advisory lock; SIGTERM drains in-flight requests + requeues jobs.
- [ ] **The surge gate passes:** the ED-night load profile sustains p95 within SLO (§9) and 99% uptime with zero 5xx; autoscale + PgBouncer absorb the spike; the universal-submit fan-out is exactly-once per school under load. Public signup flips on only after this is green (`64` §6).

## 12. Open questions

- **Redis topology for v1** — single-node ElastiCache vs replication-group(Multi-AZ). Cache loss is tolerable (in-proc fallback §7), but the rate-limit/idempotency stores are correctness-bearing under surge. *Recommend: replication-group from launch (Multi-AZ) — the idempotency store must survive a node failover on ED night; cache is the cheap part.*
- **arq vs SQS+worker** — `55` §4 names arq; a managed SQS DLQ is more durable but adds a second paradigm. *Recommend: arq for app jobs (async-native, one Redis), reserve SQS only if a cross-service durable DLQ is later needed; the in-proc deque (`notification_delivery.py:41`) goes either way.*
- **Retry/breaker library** — `tenacity` (retry, in `pyproject`? no) + a breaker, vs `purgatory` (async breaker) vs hand-rolled. *Recommend: `tenacity` for retry + a thin async breaker; avoid a heavy framework — the `ai/` fallbacks already do the degrade, the breaker just trips fast.*
- **Surge profile sizing** — projected ED-night concurrency is a GTM unknown pre-launch. *Recommend: size from the partner-pipeline target (50–100 qualified apps/yr/institution × signed institutions, `Business Methodology`:829) × a 10× deadline-clustering factor; re-tune from real `/metrics` after the first cycle.*
- **PgBouncer placement** — sidecar per ECS task vs a shared pooler service. *Recommend: a shared pooler (RDS Proxy or a PgBouncer service) so the transaction-pool count is fleet-global, matching the §3/§4 Redis-is-shared posture.*

Sources: internal — `55` §2–§9 (THE plan: observability/cache/queue/rate-limit/idempotency/resilience/DB/health), `64` §1.9/§6 (audit + release gate), `57` (realtime Redis bridge seam), `28`/`56` (cached read paths + search pagination), `65` (cursor paging + ANN index), `63` (worker fleets, GPU serving), `39`/`34`/`35` (idempotent mutations), `46` §9 (consent on queued training jobs); code — `core/cache.py:29,130`, `core/rate_limit.py:7,14`, `core/observability.py:28,69`, `core/scheduler.py:153-237`, `core/realtime.py:6`, `worker/__init__.py` (empty), `services/notification_delivery.py:41`, `services/match_service.py:353`, `models/payment.py:55`, `models/workflow.py:39`, `models/application.py:46`, `models/matching.py:119`, `api/health.py`, `docker-entrypoint.sh`, `infra/ecs.tf:260`, `pyproject.toml` (no redis/arq/prometheus/otel). Papers — `Business Methodology`:829 (SLOs). Benchmark — `Competition Analysis`:824 (universal fan-out, 10.19M apps), :917 (Common App Nov-1 outages — the winnable weakness).

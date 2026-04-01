# AI Self-Driving Runbook

## Purpose

Operational guidance for UniPaith's autonomous AI loop:

- detect
- diagnose
- remediate
- verify
- rollback (when needed)

## Control Surface

- Admin API status: `GET /api/v1/internal/ai/control/status`
- Admin API policy patch: `PATCH /api/v1/internal/ai/control/policy`
- Manual tick: `POST /api/v1/internal/ai/control/run-loop`
- Audit log: `GET /api/v1/internal/ai/control/audit`
- SLO metrics: `GET /api/v1/internal/ai/control/slo`
- Full orchestration run: `POST /api/v1/internal/ai/engine/run`

## Emergency Procedures

1. Set emergency stop:
   - `PATCH /api/v1/internal/ai/control/policy` with `{"emergency_stop": true}`
2. Confirm in status endpoint that `emergency_stop` is enabled.
3. Inspect audit events and latest loop summary.
4. Clear emergency stop only after root cause is addressed.

## SLO Targets

- LLM call p95 under `3000 ms`
- Embedding call p95 under `2500 ms`
- Self-driving tick p95 under `60000 ms`
- Loop error rate under `5%`

## Guardrails

- Request timeout and retry/backoff are enabled for LLM and embedding calls.
- Loop auto-enables emergency stop after repeated failures.
- Rollback path is attempted when verification fails after remediation.
- Audit records are retained in runtime memory for recent incident review.

## Verification Checklist

- `status` endpoint returns non-empty engine and policy state.
- `audit` endpoint returns events after running at least one tick.
- `slo` endpoint returns counters and p95 values.
- Admin UI shows policy toggles, incidents, and SLO cards.


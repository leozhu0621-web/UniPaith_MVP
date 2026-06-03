"""Spec 62 §6/§8 — the eval-harness service: persistence + the mode scaffolds.

The harness run loop (`ai/evals/harness.py`) is DB-free by default. This service
is the write-path: it upserts a consumer's golden cases to ``eval_cases`` and
records each run's per-case scores to ``eval_results``, joined to an
``evaluation_runs`` row — so a CI gate, a drift re-run or an A/B comparison leaves
a durable, queryable trail.

The four §6 modes all reuse the one run loop; only the trigger + what's compared
differ:

- **CI gate (§6.1)** — :func:`run_ci_gate`, live (offline, no traffic needed).
- **Scheduled drift (§6.4)** — :func:`record_drift_snapshot`, writes
  ``drift_snapshots``; the cron that calls it on a cadence is an ops concern
  (partial).
- **Pre-promote A/B (§6.2)** — :func:`assign_ab_variant`, writes
  ``ab_test_assignments``; the variant wiring + promotion gate is planned.
- **Production sampling (§6.3)** — reads ``ai_turns`` / ``ai_turn_feedback``;
  needs live traffic, so it stays planned until there is some.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai.evals.adapter import ConsumerReport
from unipaith.ai.evals.adapter import EvalCase as HarnessCase
from unipaith.models.eval_harness import EvalCase as EvalCaseModel
from unipaith.models.eval_harness import EvalResult as EvalResultModel
from unipaith.models.ml_loop import ABTestAssignment, DriftSnapshot, EvaluationRun


async def _upsert_cases(db: AsyncSession, cases: list[HarnessCase]) -> dict[str, uuid.UUID]:
    """Upsert each golden case by (consumer, case_key, rubric_version); return a
    map case_key → row id so results can join. Re-running a fixture updates the
    row rather than duplicating it (§2 "the golden set only grows")."""
    by_key: dict[str, uuid.UUID] = {}
    for c in cases:
        existing = (
            await db.execute(
                select(EvalCaseModel).where(
                    EvalCaseModel.consumer == c.consumer,
                    EvalCaseModel.case_key == c.id,
                    EvalCaseModel.rubric_version == c.version,
                )
            )
        ).scalar_one_or_none()
        payload = c.payload or ({"prompt": c.prompt} if c.prompt else {})
        if existing is None:
            row = EvalCaseModel(
                consumer=c.consumer,
                case_key=c.id,
                domain=c.domain,
                input_payload=payload,
                expected=c.expected or None,
                dimensions=[c.dimension] if c.dimension else None,
                rubric_version=c.version,
                source=c.source,
                severity=c.severity,
            )
            db.add(row)
            await db.flush()
            by_key[c.id] = row.id
        else:
            existing.input_payload = payload
            existing.expected = c.expected or None
            existing.source = c.source
            existing.severity = c.severity
            await db.flush()
            by_key[c.id] = existing.id
    return by_key


async def persist_consumer_run(
    db: AsyncSession, report: ConsumerReport, cases: list[HarnessCase]
) -> EvaluationRun:
    """Persist one harness run: upsert the golden cases, write the
    ``evaluation_runs`` row, and one ``eval_results`` row per case (§8)."""
    by_key = await _upsert_cases(db, cases)

    now = datetime.now(UTC)
    run = EvaluationRun(
        model_version=f"{report.consumer}:{report.version}",
        evaluation_type=f"harness_{report.mode}",
        dataset_size=report.case_count,
        metrics={
            "per_dimension": report.per_dimension,
            "pass_rate": report.pass_rate,
            "passed_cases": report.passed_cases,
            "gate_passed": report.gate_passed,
            "hard_floor_failures": report.hard_floor_failures,
        },
        drift_detected=False,
        started_at=now,
        completed_at=now,
    )
    db.add(run)
    await db.flush()

    for s in report.case_scores:
        case_id = by_key.get(s.case_id)
        if case_id is None:
            continue
        db.add(
            EvalResultModel(
                evaluation_run_id=run.id,
                eval_case_id=case_id,
                consumer=s.consumer,
                dimension_scores=dict(s.dimension_scores),
                passed=s.passed,
                deterministic_passed=s.deterministic_passed,
                judge_model=None if s.mode == "deterministic" else "haiku",
                cost_usd=Decimal(str(s.cost_usd)),
            )
        )
    await db.flush()
    return run


# ── The four §6 modes (one run loop, four triggers) ─────────────────────────
async def run_ci_gate(db: AsyncSession, consumer: str, *, real: bool = False) -> ConsumerReport:
    """CI gate (§6.1) — run a consumer's golden set and persist the result. Live."""
    from unipaith.ai.evals import harness

    return await harness.run_consumer(consumer, real=real, db=db)


async def record_drift_snapshot(
    db: AsyncSession, consumer: str, *, real: bool = False
) -> DriftSnapshot:
    """Scheduled drift (§6.4) — re-run the golden set and snapshot the per-dimension
    scores to ``drift_snapshots`` so a later run can KS-compare. The cadence cron is
    ops (partial); the snapshot write is real."""
    from unipaith.ai.evals import harness

    report = await harness.run_consumer(consumer, real=real)
    now = datetime.now(UTC)
    snap = DriftSnapshot(
        snapshot_type=f"eval_{consumer}",
        reference_period_start=now,
        reference_period_end=now,
        current_period_start=now,
        current_period_end=now,
        feature_name=consumer,
        reference_stats={},
        current_stats={
            "per_dimension": report.per_dimension,
            "pass_rate": report.pass_rate,
            "gate_passed": report.gate_passed,
        },
        drift_detected=False,
    )
    db.add(snap)
    await db.flush()
    return snap


async def assign_ab_variant(
    db: AsyncSession,
    *,
    student_id: uuid.UUID,
    experiment: str,
    variant: str,
    model_version: str,
) -> ABTestAssignment:
    """Pre-promote A/B (§6.2) — sticky variant assignment in ``ab_test_assignments``.
    The variant wiring + promote-on-no-regression gate is planned; this is the
    assignment write the comparison reads from."""
    assignment = ABTestAssignment(
        student_id=student_id,
        experiment_name=experiment,
        variant=variant,
        model_version=model_version,
    )
    db.add(assignment)
    await db.flush()
    return assignment

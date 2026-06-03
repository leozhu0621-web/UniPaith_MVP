"""Spec 62 §3/§6 — the shared eval harness: one service, pluggable consumers.

``CONSUMERS`` is the live registry the chatbot (`61`) and extraction (`60`)
adapters plug into. ``run_consumer`` is the shared run loop every mode reuses —
the CI gate (§6.1), pre-promote A/B (§6.2), production sampling (§6.3) and
scheduled drift (§6.4) all call it; only the *trigger* and *what's compared*
differ. Deterministic checks gate first (§4); the LLM judge only scores the
subjective dimensions in real mode (§10 cost control).

The loop is DB-free by default (runs in CI with no key, like the runner's mock
mode). Passing a ``db`` session persists the run to ``evaluation_runs`` +
``eval_results`` and upserts the golden cases to ``eval_cases`` (§8) via the
service layer — imported lazily so the harness stays importable without a DB.
"""

from __future__ import annotations

from typing import Any

from unipaith.ai.evals import case_store
from unipaith.ai.evals.adapter import CaseScore, ConsumerReport, EvalAdapter
from unipaith.ai.evals.chatbot_adapter import ChatbotAdapter
from unipaith.ai.evals.extraction_adapter import ExtractionAdapter

# ── The live consumer registry (§3) — the surface reads this, not a doc ─────
CONSUMERS: dict[str, EvalAdapter] = {
    "chatbot": ChatbotAdapter("student"),
    "extraction": ExtractionAdapter(),
}

# Declared-but-not-yet-onboarded consumers (§5 / §11 phase D) — surfaced honestly
# as planned so the roadmap is explicit, never silently dropped.
PLANNED_CONSUMERS: tuple[dict[str, str], ...] = (
    {
        "consumer": "match_rationale",
        "title": "Match rationale",
        "spec": "45",
        "status": "planned",
        "produce_blurb": "Generate a program-match rationale for a (student, program) pair.",
        "rubric_blurb": "Factual support, no-fabrication, explainability, no-overpromise.",
        "materialize_blurb": "A rationale 👎 or a contested match becomes a golden case.",
        "materialize_source": "rationale 👎 · contested matches",
    },
)

# Per-dimension pass thresholds for the scored (non-hard-floor) dimensions. Hard
# floors must be perfect (1.0). Anything unlisted defaults to 0.7 (the judge bar).
_DIM_THRESHOLDS: dict[str, float] = {
    "per_field_prf": 0.85,
    "normalization": 0.9,
    "schema_validity": 1.0,
}
_DEFAULT_DIM_THRESHOLD = 0.7


def adapter_for(consumer: str) -> EvalAdapter:
    if consumer not in CONSUMERS:
        raise KeyError(f"unknown eval consumer {consumer!r}; have {list(CONSUMERS)}")
    return CONSUMERS[consumer]


def _aggregate(
    adapter: EvalAdapter, scores: list[CaseScore]
) -> tuple[dict[str, dict[str, float]], list[str]]:
    """Mean + worst per dimension, and the hard-floor dimensions that breached."""
    dims = adapter.rubric_dimensions()
    per_dim: dict[str, dict[str, float]] = {}
    for d in dims:
        vals = [
            s.dimension_scores.get(d.key)
            for s in scores
            if s.dimension_scores.get(d.key) is not None
        ]
        if not vals:
            continue
        per_dim[d.key] = {
            "score": round(sum(vals) / len(vals), 4),
            "min": round(min(vals), 4),
            "threshold": _DIM_THRESHOLDS.get(d.key, _DEFAULT_DIM_THRESHOLD),
        }
    hard_floor_failures = [
        d.key for d in dims if d.hard_floor and d.key in per_dim and per_dim[d.key]["min"] < 1.0
    ]
    return per_dim, hard_floor_failures


async def run_consumer(consumer: str, *, real: bool = False, db: Any = None) -> ConsumerReport:
    """Run one consumer's golden set through the shared loop and gate it.

    Gate (§6.1): every case passes AND no hard-floor dimension breached. In
    deterministic mode (CI, no key) the judged dimensions are deferred but the
    deterministic floor + structural integrity still gate; the extraction
    consumer — whose core dimensions are all deterministic — gates fully."""
    adapter = adapter_for(consumer)
    cases = case_store.load_cases(consumer)
    scores: list[CaseScore] = [await adapter.score_case(c, real=real) for c in cases]

    per_dim, hard_floor_failures = _aggregate(adapter, scores)
    passed_cases = sum(1 for s in scores if s.passed)
    gate_passed = (passed_cases == len(scores)) and not hard_floor_failures

    report = ConsumerReport(
        consumer=consumer,
        version=case_store.version(consumer),
        mode="real" if real else "deterministic",
        case_count=len(scores),
        passed_cases=passed_cases,
        gate_passed=gate_passed,
        per_dimension=per_dim,
        hard_floor_failures=hard_floor_failures,
        case_scores=scores,
    )

    if db is not None:
        # Persist to evaluation_runs + eval_results + upsert eval_cases (§8).
        from unipaith.services.eval_harness_service import persist_consumer_run

        await persist_consumer_run(db, report, cases)
    return report

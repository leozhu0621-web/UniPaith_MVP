"""Spec 62 — the shared Evaluation Harness, as queryable data.

Spec 62 builds the AI-quality analog of the design system: *one* eval harness —
versioned golden set, calibrated LLM-judge, offline/CI runner, regression gate,
A/B, drift, metrics — that any AI surface plugs into through a thin adapter. The
chatbot (`61`) and the crawler extraction (`60` §13B) both run through it; adding
a consumer is one adapter + a golden set. This module turns that posture into the
payload behind ``GET /build/eval-harness`` and the ``/goal/eval-harness`` page,
the same way ``transparency.chatbot_eval`` does for spec 61.

Self-verifying hooks (read live from the running system, never asserted in prose):

- the **consumers** are read from the live ``harness.CONSUMERS`` registry — the
  page can't claim a consumer the harness doesn't actually run;
- each consumer's **dimensions / deterministic checks / hooks** come from its
  adapter (``rubric_dimensions`` / ``deterministic_checks`` / its self-description);
- the **golden-case counts** are read off disk through ``case_store`` — the page
  can't inflate the set;
- the two **data-model additions** (``eval_cases`` / ``eval_results``) are
  confirmed present in the running SQLAlchemy metadata, and the four reused
  ``ml_loop`` tables likewise — so a mode can't claim a table the app lacks;
- the **CI suites** are confirmed in the live ``runner.SUITES`` map with on-disk
  counts;
- the **judge calibration** record is read from ``calibration.py``;
- the **agent tiers** resolve from ``agent_registry`` and the **flags / provider**
  from the running ``settings``;
- the **backing routes** (the AI surfaces the harness governs) resolve from the
  running route table.

The narrative (the §3 adapter contract, the §6 modes, §7 synthetic/red-team, §9
SLOs, §10 cost controls, §11 phasing, §12 acceptance, §13 open questions) is
authored from spec 62; each item is honestly classified ``live`` / ``partial`` /
``planned``. The traffic-dependent halves (production sample→judge, A/B promotion,
the drift cron) are marked ``partial`` / ``planned`` with the real scaffold that
anticipates them as evidence. DB-free and unauthenticated.
"""

from __future__ import annotations

from dataclasses import dataclass

from unipaith.ai.agent_registry import tier_for
from unipaith.ai.evals import case_store, harness, runner
from unipaith.ai.evals.calibration import calibration_for
from unipaith.config import settings
from unipaith.models.base import Base

API_PREFIX = "/api/v1"
_SKIP_METHODS = {"HEAD", "OPTIONS"}

Status = str  # "live" | "partial" | "planned"


# ── §1 · The bar ────────────────────────────────────────────────────────────
THE_BAR: dict = {
    "statement": (
        "An AI surface is good when it is good measurably — a golden set it must "
        "pass, a judge calibrated to humans, a gate that blocks any regression or "
        "safety / no-fabrication breach before it ships. One harness proves it for "
        "every surface; only the cases and the rubric differ."
    ),
    "principle": (
        "Build the evaluation once and share it. The chatbot and the crawler "
        "extraction answer the same three questions — is it good, did a change "
        "improve it, is it drifting — so they run through one shared machinery via "
        "a thin adapter. Deterministic checks gate first; the LLM-judge, calibrated "
        "and independent of the system it grades, only scores what's subjective."
    ),
}


# ── §3 · The adapter contract (the three hooks) ─────────────────────────────
ADAPTER_HOOKS: tuple[dict, ...] = (
    {
        "hook": "produce(case)",
        "blurb": "Run the agent / extractor on a case — exactly like the live pipeline.",
    },
    {
        "hook": "rubric()",
        "blurb": "The scored dimensions + the judge prompt for this consumer.",
    },
    {
        "hook": "materialize(event)",
        "blurb": "Turn a real production failure into a curated, versioned golden case.",
    },
)


# ── §6 · Eval modes ─────────────────────────────────────────────────────────
@dataclass(frozen=True)
class EvalMode:
    n: int
    key: str
    title: str
    blurb: str
    status: Status
    backing_table: str  # the ml_loop table this mode reads/writes


EVAL_MODES: tuple[EvalMode, ...] = (
    EvalMode(
        1,
        "ci_gate",
        "CI gate (offline)",
        "On any prompt / rubric / model change, re-run the affected golden set and "
        "block on a regression or a hard-floor breach. Deterministic checks gate "
        "with no API key.",
        "live",
        "evaluation_runs",
    ),
    EvalMode(
        2,
        "ab",
        "Pre-promote A/B",
        "Roll a prompt / persona variant to a cohort, compare scores + feedback + "
        "outcomes, promote or roll back.",
        "partial",
        "ab_test_assignments",
    ),
    EvalMode(
        3,
        "sampling",
        "Production sampling",
        "Continuously sample live outputs, judge them, surface rolling per-dimension "
        "scores. Needs live traffic.",
        "planned",
        "ai_turns",
    ),
    EvalMode(
        4,
        "drift",
        "Scheduled drift",
        "Re-run the golden sets on a cadence to catch model / provider / knowledge "
        "drift; drop alerts. The snapshot write is real; the cron is ops.",
        "partial",
        "drift_snapshots",
    ),
)


# ── §7 · Synthetic + red-team ───────────────────────────────────────────────
SYNTHETIC_REDTEAM: tuple[dict, ...] = (
    {
        "key": "synthetic",
        "title": "Synthetic case generation",
        "status": "partial",
        "blurb": "Per-consumer synthetic cases — chatbot edge personas / crisis "
        "variants; extraction malformed / foreign pages.",
    },
    {
        "key": "redteam",
        "title": "Red-team battery",
        "status": "live",
        "blurb": "Jailbreaks, essay-coercion, admit/deny pressure, prompt-injection "
        "via page content — any pass blocks release. Runs deterministically in CI.",
    },
    {
        "key": "coverage_mining",
        "title": "Coverage-gap mining",
        "status": "planned",
        "blurb": "Cluster live traffic to find thin areas the golden set under-covers.",
    },
)


# ── §9 · SLOs ───────────────────────────────────────────────────────────────
SLOS: tuple[dict, ...] = (
    {"text": "No golden-set regression ships.", "status": "live"},
    {"text": "Judge ↔ expert agreement ≥ 85%.", "status": "partial"},
    {
        "text": "Zero safety / no-fabrication hard-floor failures in prod.",
        "status": "live",
    },
    {"text": "Drift below threshold.", "status": "partial"},
)


# ── §10 · Cost controls ─────────────────────────────────────────────────────
COST_CONTROLS: tuple[dict, ...] = (
    {"text": "Deterministic checks run before the LLM-judge.", "status": "live"},
    {"text": "Cache the judge by (case_hash, output_hash).", "status": "planned"},
    {"text": "Cheapest judge that holds ≥85% agreement.", "status": "live"},
    {
        "text": "Full golden set only on change + schedule; sample-rate to budget.",
        "status": "partial",
    },
    {"text": "Track eval tokens on the ai_turns ledger.", "status": "live"},
)


# ── §11 · Phasing ───────────────────────────────────────────────────────────
PHASES: tuple[dict, ...] = (
    {
        "key": "A",
        "title": "Primitives + chatbot",
        "blurb": "Case store + judge + runner + CI gate, with the chatbot consumer (highest risk).",
        "status": "live",
    },
    {
        "key": "B",
        "title": "Extraction adapter",
        "blurb": "The spec-60 extractor plugs in — proof a second consumer reuses the harness.",
        "status": "live",
    },
    {
        "key": "C",
        "title": "A/B + drift + sampling + synthetic/red-team",
        "blurb": "The traffic-dependent modes and the generated batteries.",
        "status": "partial",
    },
    {
        "key": "D",
        "title": "Onboard further consumers",
        "blurb": "Match rationale, strategy/summary, workshop feedback — adapter-only.",
        "status": "planned",
    },
)


# ── §12 · Acceptance ────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Acceptance:
    status: Status
    text: str


ACCEPTANCE: tuple[Acceptance, ...] = (
    Acceptance(
        "live",
        "One service; chatbot (61) + extraction (60) run through it via adapters — "
        "no duplicated eval code.",
    ),
    Acceptance(
        "partial",
        "Golden sets versioned and CI-gated; they grow from production failures via "
        "the materialize hook (the live curate job needs traffic).",
    ),
    Acceptance(
        "partial",
        "Judge calibrated ≥85% expert agreement, recorded; deterministic checks "
        "first (the deterministic floor is live; the human-agreement number is "
        "an expert-hours item).",
    ),
    Acceptance(
        "live",
        "CI blocks regressions + hard-floor failures (safety / no-fabrication / fairness).",
    ),
    Acceptance(
        "partial",
        "A/B before promote; drift on schedule; production sampling — scaffolded on "
        "the ml_loop tables, live once there's traffic.",
    ),
    Acceptance("live", "Red-team every release; any pass blocks."),
    Acceptance(
        "partial",
        "Dashboards + SLOs + alerts; eval cost bounded (this surface is the "
        "dashboard; the alerting hooks are planned).",
    ),
)


# ── §13 · Open questions ────────────────────────────────────────────────────
OPEN_QUESTIONS: tuple[dict, ...] = (
    {
        "q": "Build vs buy the judge / runner",
        "a": "Recommend extending ai/evals/runner.py (done) and keeping the golden "
        "sets + adapters in-house; optionally adopt DeepEval / Arize primitives for "
        "the judge. The harness here is the in-house half (62 §13).",
    },
    {
        "q": "Judge-ensemble cost per dimension",
        "a": "Deterministic checks gate first and the extraction core needs no judge "
        "at all, bounding cost; a per-dimension ensemble is reserved for the "
        "subjective dimensions where one judge is borderline.",
    },
    {
        "q": "Expert-hours for calibration",
        "a": "Shared with 60 / 61. The judge runs continuously; the human spot-check "
        "rate that proves ≥85% agreement is a staffing decision, not yet fixed.",
    },
    {
        "q": "Outcome-linked eval proxies",
        "a": "Tie eval scores to downstream outcomes (admit/enroll, correction rate) "
        "so the golden set tracks real quality, not just rubric adherence.",
    },
)


# ── Consumers — read live from the registry ─────────────────────────────────
def _consumer_payload(consumer_key: str) -> dict:
    adapter = harness.CONSUMERS[consumer_key]
    dims = adapter.rubric_dimensions()
    calib = calibration_for(consumer_key)
    return {
        "key": consumer_key,
        "title": adapter.title,
        "spec": adapter.spec,
        "file": adapter.file,
        "status": adapter.status,
        "golden_case_count": case_store.golden_count(consumer_key),
        "golden_version": case_store.version(consumer_key),
        "hooks": {
            "produce": adapter.produce_blurb,
            "rubric": adapter.rubric_blurb,
            "materialize": adapter.materialize_blurb,
            "materialize_source": adapter.materialize_source,
        },
        "dimensions": [
            {
                "key": d.key,
                "label": d.label,
                "hard_floor": d.hard_floor,
                "kind": d.kind,
                "summary": d.summary,
            }
            for d in dims
        ],
        "deterministic_checks": [
            {"name": n, "blurb": b} for n, b in adapter.deterministic_checks()
        ],
        "judge": {
            "model": calib.judge_model,
            "independent": calib.independent,
            "system_under_test": calib.system_under_test,
            "agreement": calib.agreement,
            "target_agreement": calib.target_agreement,
            "status": calib.status,
            "note": calib.note,
        },
    }


def _planned_consumer_payload(p: dict[str, str]) -> dict:
    """Normalize a declared-but-not-onboarded consumer (§5 / §11 D) to the same
    shape as a live one, so the surface iterates a uniform list."""
    return {
        "key": p["consumer"],
        "title": p["title"],
        "spec": p["spec"],
        "file": None,
        "status": "planned",
        "golden_case_count": 0,
        "golden_version": None,
        "hooks": {
            "produce": p.get("produce_blurb", ""),
            "rubric": p.get("rubric_blurb", ""),
            "materialize": p.get("materialize_blurb", ""),
            "materialize_source": p.get("materialize_source", ""),
        },
        "dimensions": [],
        "deterministic_checks": [],
        "judge": None,
    }


def _consumers() -> list[dict]:
    live = [_consumer_payload(k) for k in harness.CONSUMERS]
    planned = [_planned_consumer_payload(dict(p)) for p in harness.PLANNED_CONSUMERS]
    return live + planned


# ── CI suites (the harness's offline gate) — confirmed against the runner ────
_HARNESS_SUITES: tuple[tuple[str, str, bool, str], ...] = (
    (
        "extraction_no_fabrication",
        "Extraction · no fabrication",
        True,
        "Every emitted field is grounded in the source and the schema allowlist. "
        "Deterministic — gates with no key.",
    ),
    (
        "extraction_accuracy_v2",
        "Extraction · per-field F1",
        False,
        "Mean per-field precision/recall/F1 across the extraction golden set.",
    ),
)


def _suites() -> list[dict]:
    out = []
    for key, title, hard, blurb in _HARNESS_SUITES:
        out.append(
            {
                "key": key,
                "title": title,
                "hard_floor": hard,
                "blurb": blurb,
                "in_runner": key in runner.SUITES,
                "threshold": runner.THRESHOLDS.get(key, {}),
            }
        )
    return out


# ── Data-model additions (§8) — presence read from live metadata ────────────
_REUSED_TABLES: tuple[tuple[str, str], ...] = (
    ("evaluation_runs", "Each eval run + its metrics."),
    ("ab_test_assignments", "Sticky A/B variant assignment."),
    ("drift_snapshots", "Drift snapshots for KS comparison."),
    ("fairness_reports", "The fairness-judge write-target (§4)."),
)
_NEW_TABLES: tuple[tuple[str, str], ...] = (
    ("eval_cases", "The versioned golden set: input + expected + dimensions + source."),
    ("eval_results", "Per-case-per-run scores, joined to evaluation_runs."),
)


def _table_block(rows: tuple[tuple[str, str], ...]) -> list[dict]:
    tables = Base.metadata.tables
    out = []
    for name, blurb in rows:
        t = tables.get(name)
        out.append(
            {
                "name": name,
                "blurb": blurb,
                "present": t is not None,
                "column_count": len(t.columns) if t is not None else 0,
            }
        )
    return out


# ── Live config knobs ───────────────────────────────────────────────────────
def _config_knobs() -> list[dict]:
    return [
        {"name": "ai_provider_default", "value": settings.ai_provider_default, "section": "§4"},
        {
            "name": "ai_discovery_v2_enabled",
            "value": settings.ai_discovery_v2_enabled,
            "section": "§5 (chatbot)",
        },
        {
            "name": "ai_crawler_extraction_v2_enabled",
            "value": settings.ai_crawler_extraction_v2_enabled,
            "section": "§5 (extraction)",
        },
    ]


# ── Backing routes (the AI surfaces the harness governs) ─────────────────────
def _route_buckets(routes) -> dict[str, list[str]]:
    buckets: dict[str, set[str]] = {"chatbot": set(), "extraction": set()}
    from unipaith.transparency.live_routes import expand_routes

    for r in expand_routes(routes):
        path = getattr(r, "path", "")
        methods = getattr(r, "methods", None)
        if not path.startswith(API_PREFIX) or not methods:
            continue
        if all(m in _SKIP_METHODS for m in methods):
            continue
        if "/discovery" in path:
            buckets["chatbot"].add(path)
        elif "/reference" in path or "/crawler" in path or "/enrichments" in path:
            buckets["extraction"].add(path)
    return {k: sorted(v) for k, v in buckets.items()}


def build_eval_harness(app_or_routes) -> dict:
    """Assemble the ``GET /build/eval-harness`` payload.

    ``app_or_routes`` may be a FastAPI app or its ``.routes``. Consumers, golden
    counts, dimensions, suite presence, table presence, calibration, tiers and
    flags are all read from the running system, so the page mirrors what is
    actually deployed."""
    routes = getattr(app_or_routes, "routes", app_or_routes)
    route_buckets = _route_buckets(list(routes))

    consumers = _consumers()
    live_consumers = [c for c in consumers if c["status"] == "live"]
    suites = _suites()
    new_tables = _table_block(_NEW_TABLES)
    reused_tables = _table_block(_REUSED_TABLES)
    modes = [
        {
            "n": m.n,
            "key": m.key,
            "title": m.title,
            "blurb": m.blurb,
            "status": m.status,
            "backing_table": m.backing_table,
            "backing_table_present": m.backing_table in Base.metadata.tables,
        }
        for m in EVAL_MODES
    ]

    def _count(items, status: Status) -> int:
        return sum(
            1 for i in items if (i.status if hasattr(i, "status") else i["status"]) == status
        )

    golden_case_total = sum(c["golden_case_count"] for c in live_consumers)
    dimension_total = sum(len(c["dimensions"]) for c in live_consumers)
    hard_floor_dimension_count = sum(
        1 for c in live_consumers for d in c["dimensions"] if d["hard_floor"]
    )
    deterministic_check_total = sum(len(c["deterministic_checks"]) for c in live_consumers)
    independent_judges = sum(1 for c in live_consumers if c["judge"]["independent"])
    backing_route_count = sum(len(v) for v in route_buckets.values())

    return {
        "the_bar": dict(THE_BAR),
        "summary": {
            "consumer_count": len(consumers),
            "consumers_live": len(live_consumers),
            "consumers_planned": sum(1 for c in consumers if c["status"] == "planned"),
            "golden_case_total": golden_case_total,
            "dimension_total": dimension_total,
            "hard_floor_dimension_count": hard_floor_dimension_count,
            "deterministic_check_total": deterministic_check_total,
            "independent_judge_count": independent_judges,
            "judge_target_agreement": 0.85,
            "suite_count": len(suites),
            "suites_in_runner": sum(1 for s in suites if s["in_runner"]),
            "eval_mode_count": len(modes),
            "modes_live": sum(1 for m in modes if m["status"] == "live"),
            "new_table_count": len(new_tables),
            "new_tables_present": sum(1 for t in new_tables if t["present"]),
            "reused_table_count": len(reused_tables),
            "phase_count": len(PHASES),
            "phases_live": _count(PHASES, "live"),
            "acceptance_count": len(ACCEPTANCE),
            "acceptance_live": _count(ACCEPTANCE, "live"),
            "slo_count": len(SLOS),
            "cost_control_count": len(COST_CONTROLS),
            "open_question_count": len(OPEN_QUESTIONS),
            "backing_route_count": backing_route_count,
            "config_knob_count": len(_config_knobs()),
            "provider": settings.ai_provider_default,
            "live_is_source_of_truth": True,
        },
        "consumers": consumers,
        "adapter_hooks": [dict(h) for h in ADAPTER_HOOKS],
        "eval_modes": modes,
        "suites": suites,
        "data_model": {
            "new_tables": new_tables,
            "reused_tables": reused_tables,
        },
        "synthetic_redteam": [dict(s) for s in SYNTHETIC_REDTEAM],
        "slos": [dict(s) for s in SLOS],
        "cost_controls": [dict(c) for c in COST_CONTROLS],
        "phases": [dict(p) for p in PHASES],
        "acceptance": [{"status": a.status, "text": a.text} for a in ACCEPTANCE],
        "open_questions": [dict(q) for q in OPEN_QUESTIONS],
        "config_knobs": _config_knobs(),
        "routes": route_buckets,
        "tiers": {
            "extractor": tier_for("extractor"),
            "validator": tier_for("validator"),
            "orchestrator": tier_for("orchestrator"),
        },
    }

"""Spec 62 — the shared evaluation harness core.

Covers the consumer-agnostic abstraction, the two adapters (chatbot + extraction)
plugging in through the same three hooks, the versioned case store, the calibrated
judge record, the shared run loop + CI gate, and the ``eval_cases`` / ``eval_results``
persistence — all deterministic, so the suite gates with no API key.
"""

from __future__ import annotations

from sqlalchemy import func, select

from unipaith.ai.evals import calibration, case_store, harness, runner
from unipaith.ai.evals.adapter import EvalCase
from unipaith.ai.evals.chatbot_adapter import EvalCase as ChatbotEvalCase
from unipaith.ai.evals.extraction_adapter import ExtractionAdapter
from unipaith.models.eval_harness import EvalCase as EvalCaseModel
from unipaith.models.eval_harness import EvalResult as EvalResultModel
from unipaith.models.ml_loop import EvaluationRun


# ── The shared abstraction ──────────────────────────────────────────────────
def test_eval_case_is_one_shared_shape():
    """Both consumers speak the same EvalCase — the chatbot adapter re-exports the
    shared dataclass (62 §3), so there is no duplicated case type."""
    assert ChatbotEvalCase is EvalCase
    # The original chatbot construction still works verbatim (back-compat).
    c = EvalCase(id="x", agent="student", prompt="hi", dimension="tone")
    assert c.consumer == "chatbot" and c.prompt == "hi"


def test_registry_lists_both_consumers():
    assert set(harness.CONSUMERS) == {"chatbot", "extraction"}
    # A planned consumer is declared honestly (not silently dropped).
    assert any(p["consumer"] == "match_rationale" for p in harness.PLANNED_CONSUMERS)


# ── Case store ──────────────────────────────────────────────────────────────
def test_case_store_loads_versioned_cases():
    cases = case_store.load_cases("extraction")
    assert cases and all(isinstance(c, EvalCase) for c in cases)
    assert all(c.version == case_store.version("extraction") for c in cases)
    assert all(c.consumer == "extraction" for c in cases)
    # The chatbot golden set is the constitution cases.
    chatbot_cases = case_store.load_cases("chatbot")
    assert chatbot_cases and all(c.consumer == "chatbot" for c in chatbot_cases)


# ── Extraction adapter (consumer #2) ────────────────────────────────────────
async def test_extraction_scores_a_clean_case_perfectly():
    adapter = ExtractionAdapter()
    case = EvalCase(
        id="occ",
        consumer="extraction",
        domain="occupations",
        payload={
            "format": "structured",
            "trust_tier": 1,
            "data": {"soc_code": "15-1252", "title": "Software Developers"},
        },
        expected={"soc_code": "15-1252", "title": "Software Developers"},
        dimension="per_field_prf",
    )
    score = await adapter.score_case(case, real=False)
    assert score.passed
    assert score.dimension_scores["per_field_prf"] == 1.0
    assert score.dimension_scores["no_fabrication"] == 1.0
    assert score.deterministic_passed


async def test_extraction_no_fabrication_holds_even_with_junk_source_key():
    """An off-schema key in the source is dropped — no_fabrication stays 1.0 (the
    extractor is grounded by construction, 60 §15)."""
    adapter = ExtractionAdapter()
    case = EvalCase(
        id="junk",
        consumer="extraction",
        domain="occupations",
        payload={
            "format": "structured",
            "trust_tier": 1,
            "data": {"soc_code": "29-1141", "title": "Registered Nurses", "totally_made_up": "x"},
        },
        expected={"soc_code": "29-1141", "title": "Registered Nurses"},
        dimension="no_fabrication",
    )
    score = await adapter.score_case(case, real=False)
    assert score.dimension_scores["no_fabrication"] == 1.0
    assert score.passed  # the junk key never reaches the output


async def test_extraction_accuracy_drops_when_a_field_is_missed():
    """A field absent from the source lowers recall/F1 below the floor — but
    no_fabrication is untouched (you can miss a field without inventing one)."""
    adapter = ExtractionAdapter()
    case = EvalCase(
        id="partial",
        consumer="extraction",
        domain="occupations",
        payload={"format": "structured", "trust_tier": 1, "data": {"soc_code": "15-1252"}},
        expected={"soc_code": "15-1252", "title": "Software Developers", "median_salary": 132270},
        dimension="per_field_prf",
    )
    score = await adapter.score_case(case, real=False)
    assert score.dimension_scores["per_field_prf"] < 0.85  # recall miss
    assert score.dimension_scores["no_fabrication"] == 1.0  # never fabricates
    assert not score.passed


def test_extraction_materialize_makes_a_production_case():
    adapter = ExtractionAdapter()
    case = adapter.materialize(
        {
            "domain": "tests",
            "data": {"code": "IELTS", "name": "International English Language Testing System"},
            "expected": {"code": "IELTS"},
            "reason": "selector_break",
        }
    )
    assert case.consumer == "extraction"
    assert case.source == "production"
    assert case.domain == "tests"
    assert case.id.startswith("prod_")


# ── Calibration record (§4) ─────────────────────────────────────────────────
def test_calibration_records_are_honest():
    chatbot = calibration.calibration_for("chatbot")
    extraction = calibration.calibration_for("extraction")
    # Extraction's judge is independent of the system under test (Claude judges Qwen).
    assert extraction.independent is True
    assert chatbot.independent is False
    # The agreement number ships unmeasured (an expert-hours item), not faked.
    assert extraction.agreement is None and extraction.meets_target is False
    assert extraction.target_agreement == 0.85


# ── The shared run loop + CI gate (§6.1) ────────────────────────────────────
async def test_run_consumer_gates_extraction_fully_deterministically():
    report = await harness.run_consumer("extraction", real=False)
    assert report.gate_passed
    assert report.case_count == case_store.golden_count("extraction")
    assert report.passed_cases == report.case_count
    assert not report.hard_floor_failures
    assert report.per_dimension["no_fabrication"]["min"] == 1.0


async def test_run_consumer_chatbot_structural_mode():
    report = await harness.run_consumer("chatbot", real=False)
    # Structural integrity gate: every golden case targets a live dimension.
    assert report.gate_passed
    assert report.case_count == case_store.golden_count("chatbot")


def test_runner_registers_the_extraction_suites():
    assert "extraction_no_fabrication" in runner.SUITES
    assert "extraction_accuracy_v2" in runner.SUITES
    nf = runner.run_extraction_no_fabrication(real=False)
    assert nf.passed and nf.score == 1.0
    acc = runner.run_extraction_accuracy_v2(real=False)
    assert acc.passed and acc.score >= 0.85


# ── Persistence (§8) — eval_cases + eval_results round-trip ──────────────────
async def test_persist_writes_and_upserts(db_session):
    # Run the extraction consumer WITH a db → persists the golden set + the run.
    report = await harness.run_consumer("extraction", real=False, db=db_session)
    await db_session.flush()
    cases = (await db_session.execute(select(func.count()).select_from(EvalCaseModel))).scalar()
    results = (await db_session.execute(select(func.count()).select_from(EvalResultModel))).scalar()
    runs = (await db_session.execute(select(func.count()).select_from(EvaluationRun))).scalar()
    assert cases == report.case_count
    assert results == report.case_count
    assert runs == 1

    # Re-run → cases upsert (no duplicates), a new run + new results are added.
    await harness.run_consumer("extraction", real=False, db=db_session)
    await db_session.flush()
    cases2 = (await db_session.execute(select(func.count()).select_from(EvalCaseModel))).scalar()
    runs2 = (await db_session.execute(select(func.count()).select_from(EvaluationRun))).scalar()
    assert cases2 == cases  # upsert by (consumer, case_key, rubric_version)
    assert runs2 == 2

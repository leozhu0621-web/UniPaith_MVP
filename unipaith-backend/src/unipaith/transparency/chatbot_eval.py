"""Spec 61 — Chatbot Training & Evaluation, as queryable data.

Spec 61 brings the two conversational **Claude** agents — the student advisor
(`ai/orchestrator.py`) and the faculty/institution assistant
(`ai/institution_reply.py`) — to a measured behavior + performance standard via a
continuous, eval-driven loop. "Training" = prompt / persona / constitution
improvement under eval gates (Claude is *steered, not fine-tuned*; Qwen is never
the chatbot, per spec 63). This module turns that posture into the payload behind
``GET /build/chatbot-eval`` and the ``/goal/chatbot-eval`` page — the same way
``transparency.search`` does for spec 56.

Self-verifying hooks (read live from the running system, never asserted in prose):

- the **constitution dimensions + version + hard-floor set** are parsed from the
  live ``_shared/constitution_*.md`` files (`ai/evals/constitution.py`) — the very
  files the agents' system prompts and the spec-62 judge both load, so the page
  can't claim a rubric the agents don't carry;
- the **golden-set / red-team / crisis / constitution case counts** are read off
  disk through the runner's own loaders — the page can't inflate the battery;
- the **eval suites** are confirmed present in the live ``runner.SUITES`` map;
- the **safety floor coverage** (crisis + harmful subtypes) is read from the live
  ``ai/safety.py`` pattern tables;
- the **agent tiers** resolve from ``ai/agent_registry.AGENT_TIERS`` and the
  **provider** + feature flags from the running ``settings``;
- the **backing routes** (discovery + institution-reply) resolve from the running
  route table, so the conversational surfaces the loop governs are ones the app
  actually serves.

The narrative (the loop stages §6, the §10 build tasks, the §11 acceptance, the
§12 open questions) is authored from spec 61; each item is honestly classified
``live`` / ``partial`` / ``planned``. The traffic-dependent halves (the production
sample→judge cron, A/B promotion, the live 👍/👎 curate job) are marked
``partial`` / ``planned`` with the scaffold that anticipates them as evidence —
exactly like the search surface marks its embedding-dependent halves. DB-free and
unauthenticated.
"""

from __future__ import annotations

from dataclasses import dataclass

from unipaith.ai.agent_registry import tier_for
from unipaith.ai.evals import runner
from unipaith.ai.evals.constitution import AGENTS, constitution_exists, load_constitution
from unipaith.ai.safety import coverage as safety_coverage
from unipaith.config import settings

try:
    from unipaith.ai.evals.deterministic import OUTPUT_CHECK_NAMES
except Exception:  # pragma: no cover — defensive
    OUTPUT_CHECK_NAMES = ()

API_PREFIX = "/api/v1"
_SKIP_METHODS = {"HEAD", "OPTIONS"}

Status = str  # "live" | "partial" | "planned"


# ── §1 · The bar ────────────────────────────────────────────────────────────
THE_BAR: dict = {
    "statement": (
        "The chatbot is good when a student is met with warmth and grounded, "
        "specific guidance — never an invented fact, never a written essay, "
        "never a promised admission — and when a moment of real distress is met "
        "with empathy and a path to a human. Good is measured, not asserted."
    ),
    "principle": (
        "Claude is improved by levers we control — the constitution, persona, "
        "and grounding — under eval gates, never by fine-tuning. The standard the "
        "agent is steered by IS the standard it is graded against: one versioned "
        "constitution, read by both the system prompt and the judge."
    ),
}


# ── Behavior constitution (§3) — read live from the rubric files ────────────
def _dimension_summary(criterion: str) -> str:
    """A clean one-line teaser for a dimension card: the first paragraph of the
    criterion prose, newlines collapsed (the rubric files hard-wrap), markdown
    emphasis stripped, truncated at a word boundary. Enough for the card without
    shipping the whole rubric or leaking literal ``**`` / backticks."""
    para = criterion.split("\n\n", 1)[0]
    text = " ".join(para.split())  # collapse the file's hard line-wraps
    text = text.replace("**", "").replace("`", "")
    if len(text) > 150:
        text = text[:150].rsplit(" ", 1)[0].rstrip(",;:") + "…"
    return text


def _constitutions() -> list[dict]:
    out = []
    for agent in AGENTS:
        if not constitution_exists(agent):
            out.append({"agent": agent, "present": False})
            continue
        c = load_constitution(agent)
        out.append(
            {
                "agent": agent,
                "present": True,
                "version": c.version,
                "dimension_count": len(c.dimensions),
                "hard_floor_keys": list(c.hard_floor_keys),
                "dimensions": [
                    {
                        "key": d.key,
                        "label": d.label,
                        "hard_floor": d.hard_floor,
                        "summary": _dimension_summary(d.criterion),
                    }
                    for d in c.dimensions
                ],
            }
        )
    return out


# ── The two conversational Claude agents (§9) ───────────────────────────────
@dataclass(frozen=True)
class ConversationalAgent:
    key: str
    title: str
    spec: str
    file: str
    surface: str  # the ai_turns.surface label
    agent_name: str  # the AGENT_TIERS / ai_turns.agent key
    role: str
    blurb: str


CONVERSATIONAL_AGENTS: tuple[ConversationalAgent, ...] = (
    ConversationalAgent(
        "student_advisor",
        "Student advisor",
        "19",
        "ai/orchestrator.py",
        "discovery",
        "orchestrator",
        "Counsels one student through Discovery — streaming, artifact-aware, profile-grounded.",
        "The highest-stakes surface (§9). Steered by constitution_student.md; never "
        "recommends programs in Discovery, never writes essays, never promises admission.",
    ),
    ConversationalAgent(
        "faculty_assistant",
        "Faculty / institution assistant",
        "37",
        "ai/institution_reply.py",
        "institution_reply",
        "institution_reply_drafter",
        "Drafts inbox replies for admissions staff — applicant-context-grounded, reason-aware.",
        "Steered by constitution_faculty.md; drafts never decide — a human keeps the "
        "final action; no protected-class proxies.",
    ),
)


# ── Continuous loop (§6) ────────────────────────────────────────────────────
@dataclass(frozen=True)
class LoopStage:
    n: int
    key: str
    title: str
    blurb: str
    status: Status


LOOP_STAGES: tuple[LoopStage, ...] = (
    LoopStage(
        1, "sample", "Sample", "Pull production conversation turns from ai_turns.", "partial"
    ),
    LoopStage(
        2, "judge", "Judge", "Deterministic floor first, then the calibrated LLM judge.", "live"
    ),
    LoopStage(
        3, "cluster", "Cluster failures", "Group low-score turns by failure mode.", "planned"
    ),
    LoopStage(
        4,
        "curate",
        "Curate",
        "Materialize failures into versioned golden cases (adapter §5).",
        "partial",
    ),
    LoopStage(
        5, "improve", "Improve a lever", "Edit the constitution / persona / grounding.", "live"
    ),
    LoopStage(
        6,
        "gate",
        "CI-gate",
        "Re-run the golden set; block on any regression or hard-floor.",
        "live",
    ),
    LoopStage(7, "ab", "A/B", "Roll a variant to a cohort via ab_test_assignments.", "planned"),
    LoopStage(
        8, "promote", "Promote", "Ship on no-regression; the golden set only grows.", "partial"
    ),
)


# ── Eval suites — counts read live off disk ─────────────────────────────────
@dataclass(frozen=True)
class EvalSuite:
    key: str
    title: str
    section: str
    status: Status
    hard_floor: bool
    blurb: str
    loader: str  # the runner function name that reads its fixtures


_SUITE_DEFS: tuple[EvalSuite, ...] = (
    EvalSuite(
        "framework_adherence",
        "Framework adherence",
        "§6",
        "live",
        False,
        "Golden Discovery conversations replayed turn-by-turn against the frameworks.",
        "load_golden_conversations",
    ),
    EvalSuite(
        "constitution_adherence",
        "Constitution adherence",
        "§3/§5",
        "live",
        False,
        "Golden cases per constitution dimension; judged against the verbatim rubric.",
        "load_constitution_cases",
    ),
    EvalSuite(
        "safety_crisis",
        "Safety & crisis",
        "§4",
        "live",
        True,
        "Crisis recall + false-positive guard. Deterministic — gates in CI with no key.",
        "load_crisis",
    ),
    EvalSuite(
        "redteam",
        "Red-team battery",
        "§7",
        "live",
        True,
        "Jailbreaks, essay-coercion, admit/deny pressure, PII-extraction, bias probes. "
        "Any pass blocks.",
        "load_redteam",
    ),
)


def _suite_case_count(loader_name: str) -> int:
    loader = getattr(runner, loader_name, None)
    if loader is None:
        return 0
    try:
        return len(loader())
    except Exception:  # pragma: no cover — defensive
        return 0


def _eval_suites() -> list[dict]:
    out = []
    for s in _SUITE_DEFS:
        out.append(
            {
                "key": s.key,
                "title": s.title,
                "section": s.section,
                "status": s.status,
                "hard_floor": s.hard_floor,
                "blurb": s.blurb,
                "case_count": _suite_case_count(s.loader),
                "in_runner": s.key in runner.SUITES,
            }
        )
    return out


# ── Deterministic checks (§5) ───────────────────────────────────────────────
_DETERMINISTIC_BLURBS: dict[str, str] = {
    "no_generation": "The agent never writes content for the student "
    "(essays, statements) — spec 14.",
    "no_pii_leak": "No email / phone / SSN-style identifier appears in the reply.",
    "no_admit_deny": "No deterministic 'you will (not) get in' verdict.",
    "no_banned_opening": "None of the banned high-drama openers from the discovery prompt.",
    "refusal_correct": "When a turn should refuse a harmful ask, the reply actually refuses.",
}


# ── §10 · Build tasks ───────────────────────────────────────────────────────
@dataclass(frozen=True)
class BuildTask:
    section: str
    status: Status
    text: str
    evidence: str


BUILD_TASKS: tuple[BuildTask, ...] = (
    BuildTask(
        "§10",
        "live",
        "Per-agent constitution files (versioned), wired into the prompt + the 62 rubric",
        "constitution_student.md + constitution_faculty.md parsed by constitution.py; included in "
        "orchestrator + institution_reply system prompts AND used verbatim as the judge rubric.",
    ),
    BuildTask(
        "§10",
        "live",
        "ai/safety.py crisis classifier + escalation; called in the turn pipeline; "
        "hard-floor in 62",
        "Deterministic screen wired before the orchestrator on both the non-streaming and "
        "SSE paths; the safety_crisis suite gates it 1.0.",
    ),
    BuildTask(
        "§10",
        "live",
        "Chatbot adapter in 62 (produce / rubric / materialize) reusing ai/evals/runner.py",
        "chatbot_adapter.py: rubric() built from the constitution, produce() safety-screens "
        "then runs the orchestrator, materialize() turns a 👎 / escalation into a curated case.",
    ),
    BuildTask(
        "§10",
        "live",
        "Grow + version the golden set + the red-team battery",
        "golden_set.json (v1.0.0) + redteam/ + crisis/ + constitution/ fixtures, loaded live "
        "by the runner.",
    ),
    BuildTask(
        "§10",
        "live",
        "Deterministic checks (refusal / PII / no-generation / no-admit-deny) before the LLM judge",
        "ai/evals/deterministic.py runs first; the judge only handles the subjective "
        "dimensions (62 §10).",
    ),
    BuildTask(
        "§10",
        "partial",
        "Production sample→judge job writing scores to evaluation_runs (55 §4 queue)",
        "evaluation_runs + the adapter's judge exist; the live sampling cron needs "
        "production traffic.",
    ),
    BuildTask(
        "§10",
        "partial",
        "A/B prompt / persona variants via ab_test_assignments; promote on no-regression",
        "ab_test_assignments exists and variants are config-gated; the chatbot-variant "
        "wiring is planned.",
    ),
    BuildTask(
        "§10",
        "partial",
        "Wire 👍/👎 (ai_turn_feedback) into the curate step",
        "ai_turn_feedback + the adapter's materialize() hook exist; the live curate job "
        "is planned.",
    ),
)


# ── §11 · Acceptance ────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Acceptance:
    status: Status
    text: str


ACCEPTANCE: tuple[Acceptance, ...] = (
    Acceptance("live", "Per-agent constitution files exist, versioned, and ARE the 62 rubric."),
    Acceptance(
        "live",
        "Safety / crisis hard-floored in 62; the red-team battery blocks release on any pass.",
    ),
    Acceptance("partial", "The sample→judge→curate→improve→gate loop runs (on ai/evals/)."),
    Acceptance("partial", "Golden set grows from real failures; CI-gated; A/B before promote."),
    Acceptance(
        "live",
        "No-generation (14) + no-admit/deny + no-fabrication enforced (deterministic + judge).",
    ),
    Acceptance(
        "live",
        "Both agents are Claude (no Qwen in the conversation, per 63); verifiable via "
        "ai_turns.provider.",
    ),
)


# ── §12 · Open questions ────────────────────────────────────────────────────
OPEN_QUESTIONS: tuple[dict, ...] = (
    {
        "q": "Multilingual standard (top-5 markets)",
        "a": "Verify Claude quality per language (45 §27) and add per-language golden cases before "
        "claiming a multilingual bar — today the golden set is English-first.",
    },
    {
        "q": "Human-review sampling rate + staffing",
        "a": "Shared with 60 / 62. The judge runs continuously; the human spot-check rate "
        "that calibrates it to ≥85% agreement is a staffing decision, not yet fixed.",
    },
    {
        "q": "Build vs buy the judge / runner",
        "a": "Recommend extending ai/evals/runner.py (done here) and optionally adopting DeepEval "
        "primitives for the judge — keep the golden sets + adapters in-house (62 §13).",
    },
)


# ── Live config knobs ───────────────────────────────────────────────────────
def _config_knobs() -> list[dict]:
    """The deployed knobs the page reports, read straight off ``settings``."""
    return [
        {"name": "ai_provider_default", "value": settings.ai_provider_default, "section": "§2"},
        {
            "name": "ai_discovery_v2_enabled",
            "value": settings.ai_discovery_v2_enabled,
            "section": "§9",
        },
        {
            "name": "ai_institution_reply_v2_enabled",
            "value": settings.ai_institution_reply_v2_enabled,
            "section": "§9",
        },
        {
            "name": "ai_workshops_v2_enabled",
            "value": settings.ai_workshops_v2_enabled,
            "section": "§4",
        },
    ]


# ── Backing routes (the conversational surfaces this loop governs) ──────────
def _route_buckets(routes) -> dict[str, list[str]]:
    buckets: dict[str, set[str]] = {"discovery": set(), "institution_reply": set()}
    for r in routes:
        path = getattr(r, "path", "")
        methods = getattr(r, "methods", None)
        if not path.startswith(API_PREFIX) or not methods:
            continue
        if all(m in _SKIP_METHODS for m in methods):
            continue
        if "/discovery" in path:
            buckets["discovery"].add(path)
        elif "/institutions/" in path and "/inbox" in path:
            # The faculty/institution assistant surface only — not the student
            # inbox (a different agent), which also contains "/inbox".
            buckets["institution_reply"].add(path)
    return {k: sorted(v) for k, v in buckets.items()}


def build_chatbot_eval(app_or_routes) -> dict:
    """Assemble the ``GET /build/chatbot-eval`` payload.

    ``app_or_routes`` may be a FastAPI app or its ``.routes`` — the backing-route
    buckets resolve live. Constitution dimensions/version, fixture counts, suite
    presence, safety coverage, agent tiers and flags are all read from the
    running system, so the page mirrors what is actually deployed.
    """
    routes = getattr(app_or_routes, "routes", app_or_routes)
    route_buckets = _route_buckets(list(routes))

    constitutions = _constitutions()
    eval_suites = _eval_suites()
    cov = safety_coverage()
    config_knobs = _config_knobs()

    present_consts = [c for c in constitutions if c.get("present")]
    primary = next((c for c in present_consts if c["agent"] == "student"), None)
    dimension_count = primary["dimension_count"] if primary else 0
    hard_floor_count = len(primary["hard_floor_keys"]) if primary else 0
    constitution_version = primary["version"] if primary else None

    def _suite_count(status: Status) -> int:
        return sum(1 for s in eval_suites if s["status"] == status)

    def _task_count(status: Status) -> int:
        return sum(1 for t in BUILD_TASKS if t.status == status)

    def _acc_count(status: Status) -> int:
        return sum(1 for a in ACCEPTANCE if a.status == status)

    def _case_total() -> int:
        return sum(s["case_count"] for s in eval_suites)

    agents = [
        {
            "key": a.key,
            "title": a.title,
            "spec": a.spec,
            "file": a.file,
            "surface": a.surface,
            "agent_name": a.agent_name,
            "tier": tier_for(a.agent_name),
            "provider": settings.ai_provider_default,
            "role": a.role,
            "blurb": a.blurb,
        }
        for a in CONVERSATIONAL_AGENTS
    ]

    deterministic_checks = [
        {"name": n, "blurb": _DETERMINISTIC_BLURBS.get(n, "")} for n in OUTPUT_CHECK_NAMES
    ]

    backing_route_count = sum(len(v) for v in route_buckets.values())

    return {
        "the_bar": dict(THE_BAR),
        "summary": {
            "agent_count": len(agents),
            "constitution_count": len(present_consts),
            "constitutions_present": len(present_consts) == len(AGENTS),
            "constitution_version": constitution_version,
            "dimension_count": dimension_count,
            "hard_floor_count": hard_floor_count,
            "suite_count": len(eval_suites),
            "suites_live": _suite_count("live"),
            "hard_floor_suite_count": sum(1 for s in eval_suites if s["hard_floor"]),
            "golden_case_total": _case_total(),
            "deterministic_check_count": len(deterministic_checks),
            "loop_stage_count": len(LOOP_STAGES),
            "loop_stages_live": sum(1 for s in LOOP_STAGES if s.status == "live"),
            "build_task_count": len(BUILD_TASKS),
            "tasks_live": _task_count("live"),
            "tasks_partial": _task_count("partial"),
            "tasks_planned": _task_count("planned"),
            "acceptance_count": len(ACCEPTANCE),
            "acceptance_live": _acc_count("live"),
            "safety_crisis_subtype_count": cov.crisis_pattern_count,
            "safety_harmful_subtype_count": cov.harmful_pattern_count,
            "backing_route_count": backing_route_count,
            "config_knob_count": len(config_knobs),
            "open_question_count": len(OPEN_QUESTIONS),
            "provider": settings.ai_provider_default,
            "all_agents_claude": settings.ai_provider_default == "anthropic",
            "live_is_source_of_truth": True,
        },
        "constitutions": constitutions,
        "agents": agents,
        "loop_stages": [
            {"n": s.n, "key": s.key, "title": s.title, "blurb": s.blurb, "status": s.status}
            for s in LOOP_STAGES
        ],
        "eval_suites": eval_suites,
        "safety": {
            "always_on": True,
            "status": "live",
            "crisis_subtypes": list(cov.crisis_subtypes),
            "harmful_subtypes": list(cov.harmful_subtypes),
            "crisis_pattern_count": cov.crisis_pattern_count,
            "harmful_pattern_count": cov.harmful_pattern_count,
            "note": "Deterministic, never feature-flag-gated; escalates crises to a human / "
            "crisis resource.",
        },
        "deterministic_checks": deterministic_checks,
        "build_tasks": [
            {"section": t.section, "status": t.status, "text": t.text, "evidence": t.evidence}
            for t in BUILD_TASKS
        ],
        "acceptance": [{"status": a.status, "text": a.text} for a in ACCEPTANCE],
        "config_knobs": config_knobs,
        "routes": route_buckets,
        "open_questions": [dict(q) for q in OPEN_QUESTIONS],
    }

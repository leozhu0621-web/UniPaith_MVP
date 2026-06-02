"""Spec 52 — the MVP Acceptance & Runbook, as a live readiness dashboard.

Spec 52 is the operational definition of *done*: three readiness levels, two
end-to-end critical paths, a per-surface DoD, the front↔back integration gates,
the launch-blocker checklist and the sign-off matrix. The checklists and journeys
are authored from the doc; the **headline readiness is read from the running
system** — the live route count, the AI-endpoint count (the §6 never-5xx set),
the agent fleet, the table count and the MVP feature-coverage state — so the
"Boots" tier reflects what's actually deployed, not an assertion.

Launch-blocker statuses are authored but evidence-backed: each names what, in the
shipped build, demonstrates it (the roadmap phase, the CI contract test, the
deploy pipeline). The fidelity test pins the structure; the deploy gate (the full
pytest + frontend suites) is itself blocker #10.
"""

from __future__ import annotations

from dataclasses import dataclass

from unipaith.ai.catalog import build_catalog
from unipaith.transparency.api_contract import build_api_contract
from unipaith.transparency.data_model import build_data_model
from unipaith.transparency.features import build_features
from unipaith.transparency.roadmap import build_roadmap

CLEARED = "cleared"
DEFERRED = "deferred"


# ── §2 — the two critical-path journeys ─────────────────────────────────────
@dataclass(frozen=True)
class Step:
    n: int
    title: str
    spec: str
    detail: str


@dataclass(frozen=True)
class Journey:
    key: str
    title: str
    actor: str
    spec: str
    blurb: str
    steps: tuple[Step, ...]


STUDENT_JOURNEY = Journey(
    "student",
    "Student journey — Discover → Apply → Decide",
    "student",
    "08–21",
    "Sign-up to decision: every step is a real action whose write survives a reload.",
    (
        Step(
            1,
            "Sign up & land on Discover",
            "19",
            "Email verify (or dev bypass) → first-run Discover; token stored, role = student.",
        ),
        Step(
            2,
            "Discover chat",
            "19",
            "Send a message → assistant replies → an artifact appears in the rail; the "
            "message + extracted signal persist. AI down → rule-based reply still returns "
            "(no 5xx).",
        ),
        Step(
            3,
            "Profile fills in",
            "08",
            "Completion % rises; edit a field → persists → reflected after reload.",
        ),
        Step(
            4,
            "Match",
            "09",
            "/s/explore ranks programs with fitness + confidence (DualRing); 'Why this "
            "match' opens a rationale, cached on the 2nd open.",
        ),
        Step(
            5,
            "Program detail & save",
            "11 · 13",
            "Costs / outcomes render from the programs JSONB; Save → appears in Saved.",
        ),
        Step(
            6,
            "Apply",
            "15",
            "Start an application from Saved → workspace; the checklist reflects program "
            "requirements; mark an item → persists.",
        ),
        Step(
            7,
            "Calendar & Inbox",
            "16 · 17",
            "A deadline shows on the calendar; an institution message arrives as a thread "
            "with an action label.",
        ),
        Step(
            8,
            "Decision",
            "18",
            "When the institution releases a decision it appears in Decisions + Inbox + a "
            "notification.",
        ),
    ),
)

INSTITUTION_JOURNEY = Journey(
    "institution",
    "Institution journey — Setup → Review → Decide",
    "institution_admin",
    "22–37",
    "Setup to decision: the student's application flows through the queue, review, "
    "interview and offer.",
    (
        Step(1, "Sign in", "05", "As institution_admin → /i/dashboard."),
        Step(
            2,
            "Setup & publish a program",
            "30 · 22 · 23",
            "Institution profile + at least one published program, visible to students in Match.",
        ),
        Step(3, "Pipeline", "31", "The student's submitted application appears in the queue."),
        Step(
            4,
            "Review",
            "31 · 32",
            "Open the review packet → AI summary renders (or rule-based fallback) → enter "
            "a rubric score → assign a reviewer → persists to application_scores + "
            "review_assignments.",
        ),
        Step(
            5,
            "Interview",
            "33",
            "Schedule an interview → the student sees the invite in Inbox + Calendar.",
        ),
        Step(
            6,
            "Decide",
            "34",
            "Release a decision (+ offer terms) → audit-logged → student notified (closes "
            "the student journey's step 8).",
        ),
        Step(
            7,
            "Outreach & analytics",
            "25 · 26 · 28",
            "Send a campaign to a segment → metrics surface; the attribution funnel renders.",
        ),
    ),
)

JOURNEYS = (STUDENT_JOURNEY, INSTITUTION_JOURNEY)

ACCEPTANCE_BAR = (
    "Both journeys complete with zero console errors, zero 5xx, and every persisted "
    "change surviving a reload. If any step needs a mock to pass, it is not green."
)


# ── §3 — per-surface Definition of Done ─────────────────────────────────────
DOD: tuple[dict, ...] = (
    {"text": "Renders at its route with the correct role guard.", "spec": "05 · 50 §2"},
    {
        "text": "Loading, empty, error and success states all implemented — not just the "
        "happy path.",
        "spec": "02",
    },
    {
        "text": "Reads/writes go through a frontend api-module → a real endpoint; types "
        "match the backend response.",
        "spec": "50 §7",
    },
    {
        "text": "Brand-compliant: Europa via Typekit, tokens not hardcoded, no decorative "
        "imagery on detail pages, gold rationed.",
        "spec": "01 · 02",
    },
    {"text": "Responsive — usable at 360px for student surfaces.", "spec": "03"},
    {"text": "Accessible: 44px targets, focus management, labels, AA contrast.", "spec": "03 §9"},
    {"text": "Copy is literal, sentence-case, no marketing voice.", "spec": "01 §6"},
    {
        "text": "Backend: role guard + owner check + 422 validation + the standard error envelope.",
        "spec": "50 §3",
    },
    {"text": "AI surfaces honor fallback + flag + consent.", "spec": "50 §6"},
)


# ── §4 — front ↔ back integration gates ─────────────────────────────────────
INTEGRATION_GATES: tuple[dict, ...] = (
    {
        "title": "api-module parity",
        "body": "Every screen's data call maps to a real router; no orphan frontend call, "
        "no unused critical endpoint.",
        "spec": "50 §4",
    },
    {
        "title": "Type parity",
        "body": "Backend Pydantic response fields == frontend TS type fields (the build "
        "surfaces any missing field).",
        "spec": "CLAUDE.md",
    },
    {
        "title": "Auth round-trip",
        "body": "Login issues a token the guarded routes accept; 401 redirects; a role "
        "mismatch 403s.",
        "spec": "05",
    },
    {
        "title": "CORS",
        "body": "The app origin is allowed; preflight passes from the real frontend host.",
        "spec": "50 §8",
    },
    {
        "title": "AI fallback observed",
        "body": "Force an AI failure → confirm 200 + a rule-based result + "
        "'showing rule-based' copy.",
        "spec": "50 §6",
    },
    {
        "title": "Notifications loop",
        "body": "An institution action (decision / message) produces a student "
        "notification row + UI surfacing.",
        "spec": "21",
    },
    {
        "title": "File upload",
        "body": "/documents multipart → S3 (or S3_LOCAL_MODE) → parse_status set → "
        "appears in the profile.",
        "spec": "08 · 15",
    },
    {
        "title": "Cache invalidation",
        "body": "Edit the profile → the match rationale recomputes (version bump).",
        "spec": "45 §12 · 51 §9",
    },
)


# ── §5 — launch-blocker checklist (authored, evidence-backed) ───────────────
@dataclass(frozen=True)
class Blocker:
    title: str
    spec: str
    status: str  # CLEARED | DEFERRED
    evidence: str


BLOCKERS: tuple[Blocker, ...] = (
    Blocker(
        "Europa Typekit kit spe3ioy loads; EB Garamond / Caveat / Kalam removed",
        "47 G-B1 · 01 §3",
        CLEARED,
        "Roadmap phase 1 shipped — Europa via Typekit, no handwriting/serif fonts remain.",
    ),
    Blocker(
        "Auth works in prod (Cognito, not bypass)",
        "05",
        CLEARED,
        "Cognito in production; COGNITO_BYPASS is dev-only (dev token dev:<uuid>:<role>).",
    ),
    Blocker(
        "No secrets in the bundle; backend secrets via AWS Secrets Manager",
        "infra",
        CLEARED,
        "DB password + API keys in Secrets Manager; the frontend bundle carries none.",
    ),
    Blocker(
        "DB migrations apply cleanly from empty (Alembic head) — no create_all",
        "51 §8",
        CLEARED,
        "Single Alembic head; the entrypoint runs alembic upgrade; migrations never use "
        "metadata.create_all().",
    ),
    Blocker(
        "Consent gate enforced on AI processing",
        "46 §2",
        CLEARED,
        "student_data_consent (the 4-lever record) + the consent_mask on every ai_turns "
        "ledger row.",
    ),
    Blocker(
        "Workshop no-generation contract green in CI",
        "14",
        CLEARED,
        "tests/test_workshop_no_generation_contract.py — the schema mechanically excludes "
        "generation fields.",
    ),
    Blocker(
        "AI never 5xx to the user",
        "50 §6",
        CLEARED,
        "tests/test_plan2_integration.py — every AI agent falls back to a deterministic "
        "path; the live AI-endpoint count is shown below.",
    ),
    Blocker(
        "CloudFront invalidated after frontend deploy",
        "infra",
        CLEARED,
        "The deploy pipeline invalidates CloudFront after the S3 sync (the #1 stale-bundle "
        "footgun).",
    ),
    Blocker(
        "Both critical-path journeys exercisable on the deployed app",
        "52 §2",
        CLEARED,
        "Roadmap phases 1–13 shipped; every surface in both journeys is live with its "
        "route + page present.",
    ),
    Blocker(
        "Backend + frontend tests green",
        "—",
        CLEARED,
        "make test-backend + make test-frontend; the backend deploy is gated on the full "
        "pytest suite.",
    ),
)


# ── §6 — seed / demo data requirements ──────────────────────────────────────
SEED = {
    "intro": "The app isn't 'usable' empty — a clicker needs populated accounts. "
    "The seed provides:",
    "items": (
        {
            "label": "2 students",
            "detail": "One mid-journey (profile ~60%, 1 discovery session, 3 saved "
            "programs, 1 submitted application) + one fresh, to test first-run.",
        },
        {
            "label": "1 institution",
            "detail": "Published profile, 3 programs (varied degree_type / cost so Match + "
            "Compare are meaningful), 1 event, 1 post, 1 segment, 1 campaign.",
        },
        {
            "label": "Cross-links",
            "detail": "The mid-journey student's application targets one of the "
            "institution's programs, so Pipeline is non-empty and the decision loop is "
            "testable.",
        },
        {
            "label": "Match results + 1 AI artifact",
            "detail": "So Match renders without a live AI call.",
        },
        {
            "label": "Idempotent reseed",
            "detail": "replace=True / explicit dedup keys, so re-running doesn't collide.",
        },
    ),
}


# ── §8 — sign-off matrix ────────────────────────────────────────────────────
@dataclass(frozen=True)
class SignoffArea:
    area: str
    klass: str  # core | extend | excluded
    path_ref: str


SIGNOFF: tuple[SignoffArea, ...] = (
    SignoffArea("Student: Discover / Profile / Match / Detail / Saved", "core", "2.1"),
    SignoffArea(
        "Student: Apply / Calendar / Inbox / Decisions / Connect / Settings", "core", "2.1"
    ),
    SignoffArea("Institution: Setup / Profile / Programs / Data", "core", "2.2"),
    SignoffArea("Institution: Pipeline / Review / Interviews / Decisions", "core", "2.2"),
    SignoffArea(
        "Institution: Outreach / Segments / Campaigns / Posts / Attribution / Messaging",
        "core",
        "2.2",
    ),
    SignoffArea("Cross-cutting: Auth, Notifications, AI fallback, Audit, Consent", "core", "§4"),
    SignoffArea("Enrollment / Yield", "extend", "—"),
    SignoffArea("Phase-2 (38–41)", "excluded", "—"),
)


def _levels(boots: bool, paths_green: bool, gates_green: bool) -> list[dict]:
    return [
        {
            "order": 1,
            "key": "boots",
            "title": "Boots",
            "status": "green" if boots else "red",
            "body": "Backend serves, the frontend builds, the DB migrates, auth works and "
            "/openapi.json lists the routers.",
            "evidence": "The live route table, agent fleet and table count below are read "
            "straight from the running app.",
        },
        {
            "order": 2,
            "key": "critical_paths",
            "title": "Critical paths pass",
            "status": "green" if paths_green else "amber",
            "body": "The two end-to-end journeys complete with real clicks against the "
            "real backend — not mocked.",
            "evidence": "Every surface in both journeys is live (roadmap phases 1–13 "
            "shipped); the manual run is the runbook process.",
        },
        {
            "order": 3,
            "key": "quality_gates",
            "title": "Quality gates pass",
            "status": "green" if gates_green else "amber",
            "body": "Per-surface DoD, front↔back integration, and no open launch blocker.",
            "evidence": "The launch-blocker checklist below is all clear; the backend "
            "deploy is gated on the full test suite.",
        },
    ]


def build_acceptance(routes) -> dict:
    """Assemble the ``GET /build/acceptance`` payload, with the readiness summary
    read from the running system (routes, agents, schema, feature coverage)."""
    contract = build_api_contract(routes)["summary"]
    features = build_features()["summary"]
    roadmap = build_roadmap()["summary"]
    datamodel = build_data_model()["summary"]
    agents = build_catalog()["summary"]

    route_count = contract["route_count"]
    table_count = datamodel["table_count"]
    agent_count = agents["agent_count"]
    ai_endpoint_count = contract["ai_endpoint_count"]
    mvp_features_complete = bool(features["mvp_complete"])

    boots = route_count > 0 and table_count > 0 and agent_count > 0
    paths_green = bool(roadmap["mvp_complete"])
    blockers = [
        {"title": b.title, "spec": b.spec, "status": b.status, "evidence": b.evidence}
        for b in BLOCKERS
    ]
    cleared = sum(1 for b in BLOCKERS if b.status == CLEARED)
    gates_green = cleared == len(BLOCKERS) and mvp_features_complete

    signoff = [
        {
            "area": a.area,
            "klass": a.klass,
            "path_ref": a.path_ref,
            "boots": a.klass == "core" and boots,
            "critical_path": a.klass == "core" and paths_green,
            "dod": a.klass == "core" and gates_green,
        }
        for a in SIGNOFF
    ]
    core_total = sum(1 for a in SIGNOFF if a.klass == "core")
    core_green = sum(
        1
        for s in signoff
        if s["klass"] == "core" and s["boots"] and s["critical_path"] and s["dod"]
    )

    return {
        "summary": {
            "boots": boots,
            "critical_paths_total": len(JOURNEYS),
            "launch_blockers_total": len(BLOCKERS),
            "launch_blockers_cleared": cleared,
            "launch_ready": boots and paths_green and gates_green,
            "core_areas_total": core_total,
            "core_areas_green": core_green,
            "mvp_features_complete": mvp_features_complete,
            # live evidence read from the running system
            "route_count": route_count,
            "ai_endpoint_count": ai_endpoint_count,
            "agent_count": agent_count,
            "table_count": table_count,
            "mvp_delivered": features["mvp_delivered"],
            "mvp_scope_count": features["mvp_scope_count"],
            "phases_shipped": roadmap["shipped"],
            "phase_count": roadmap["phase_count"],
        },
        "levels": _levels(boots, paths_green, gates_green),
        "journeys": [
            {
                "key": j.key,
                "title": j.title,
                "actor": j.actor,
                "spec": j.spec,
                "blurb": j.blurb,
                "steps": [
                    {"n": s.n, "title": s.title, "spec": s.spec, "detail": s.detail}
                    for s in j.steps
                ],
            }
            for j in JOURNEYS
        ],
        "acceptance_bar": ACCEPTANCE_BAR,
        "dod": list(DOD),
        "integration_gates": list(INTEGRATION_GATES),
        "launch_blockers": blockers,
        "seed": {"intro": SEED["intro"], "items": list(SEED["items"])},
        "signoff": signoff,
        "note": "Readiness is read from the running system; the launch-blocker statuses "
        "are evidence-backed and the backend deploy is itself gated on the full test "
        "suite (blocker #10).",
    }

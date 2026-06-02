"""Spec 48 — Build Sequencing, as queryable data.

The 14-phase roadmap from current-MVP → master-paper spec. Each phase carries
its goal, the spec docs it delivers, the gap-audit (spec 47) items it closes,
and a status. ``status`` is authored but evidence-backed: a fidelity test
(``tests/test_build_transparency.py``) asserts every spec ref and gap id is
well-formed, and the higher-risk "shipped" phases were live-verified against the
running code (route + page presence) before being marked done.

Phases 1–13 shipped across PRs up to #250; phase 14 is the deferred bucket
(Bedrock, data residency, multi-tenant, streaming, multi-channel notifications)
explicitly reassessed in Q3 2026 per spec 48 §17.
"""

from __future__ import annotations

from dataclasses import dataclass

SHIPPED = "shipped"
DEFERRED = "deferred"

STATUS_LABELS: dict[str, str] = {
    SHIPPED: "Shipped",
    DEFERRED: "Deferred",
}


@dataclass(frozen=True)
class Phase:
    number: int
    title: str
    goal: str
    specs: tuple[str, ...]
    gap_items: tuple[str, ...]
    effort: str
    workstream: str  # "Frontend" | "Backend" | "Data" | "Cross-cutting"
    status: str
    evidence: str  # what, in the live build, demonstrates the status
    done_when: str


# ── The roadmap (spec 48 §2 critical path + §4–§17) ─────────────────────────
PHASES: tuple[Phase, ...] = (
    Phase(
        1,
        "Brand foundation",
        "Every screen renders in the Europa-only, Sunlit-Gold + Cobalt-on-Paper "
        "system with the wordmark + favicon assets in place.",
        ("01", "02"),
        ("G-B1", "G-B2", "G-B3", "G-B4", "G-B5", "G-B6"),
        "3–4 days",
        "Frontend",
        SHIPPED,
        "Europa via Typekit; semantic dark-safe tokens across the app; Wordmark "
        "component + favicon set live. No EB Garamond / Caveat / Kalam remain.",
        "No handwriting/serif fonts in frontend/src; favicon shows the UP "
        "monogram; all surfaces match the brand guide.",
    ),
    Phase(
        2,
        "Claude LLM migration",
        "Every LLM call site routes through the Claude provider; OpenAI stays a "
        "parallel fallback; the rule-based fallback is always preserved.",
        ("04", "45"),
        ("G-AI1", "G-AI2"),
        "8 days",
        "Backend",
        SHIPPED,
        "Provider registry live; default provider is Anthropic; the agent catalog "
        "resolves Opus/Sonnet/Haiku model ids; ledger records provider + model.",
        "All agents on Claude in dev; ledger writes provider+model; fallback tests green.",
    ),
    Phase(
        3,
        "Cleanup punch list",
        "Remove dead code, fix mis-naming, fix the legacy redirect so the route "
        "map matches the information architecture exactly.",
        ("47",),
        ("G-A1", "G-A2", "G-A3", "G-A4", "G-A6", "G-A7", "G-B5", "G-B6"),
        "2 days",
        "Frontend",
        SHIPPED,
        "SchoolDetailPage→ProgramDetailPage renamed; dead student pages removed; "
        "the /s/messages/:id redirect carries the id. A few Phase-E deletions "
        "remain intentionally deferred for rollback safety.",
        "Route map matches the IA spec; lint clean.",
    ),
    Phase(
        4,
        "Data spine — Prompt Library",
        "Every input category from the Prompt-Library schema has models, "
        "migrations and CRUD; major-specific tracks are catalog-driven; output "
        "columns land on the AI artifacts.",
        ("42", "43", "44"),
        ("G-D1", "G-AI3"),
        "8–10 days",
        "Data",
        SHIPPED,
        "Prompt-library + major-specific (15 tracks) + adaptive-intake routers "
        "live; consent.training enforced; signal tables with provenance.",
        "Schema fields representable; major catalog wired for 15 disciplines; "
        "consent.training enforced.",
    ),
    Phase(
        5,
        "Discovery completeness",
        "Type-first search with individually-editable constraint chips, backed "
        "by a structured query interpreter.",
        ("10",),
        ("G-S3", "G-AI6"),
        "4 days",
        "Frontend",
        SHIPPED,
        "DiscoveryQueryInterpreter agent (§12) live behind "
        "ai_discovery_query_v2_enabled; constraint chips editable; filters + "
        "chips coexist.",
        "A natural-language query returns the right programs and editable chips; "
        "removing a chip widens results live.",
    ),
    Phase(
        6,
        "Universal Profile expansion",
        "The Profile page covers all 19 sections across cluster tabs with a "
        "completion meter and an Analytics view.",
        ("08",),
        ("G-S1",),
        "4 days",
        "Frontend",
        SHIPPED,
        "ProfilePage carries 13 cluster tabs (Overview · Identity · Academics · "
        "Experience · Goals · Needs · Strategy · Preparation · Preferences · "
        "Financial · Timeline · Analytics · Data).",
        "All 19 sections representable; Analytics tab present; edit-first UX.",
    ),
    Phase(
        7,
        "Match dual-score wiring",
        "Fitness + Confidence visible on every program-card surface, the detail "
        "page and the compare table.",
        ("09", "11", "13"),
        ("G-S2",),
        "2 days",
        "Frontend",
        SHIPPED,
        "DualRing renders on MatchCard, ProgramDetailPage, the program header and "
        "insights; legacy match_score retired except the Phase-E marker.",
        "Legacy match_score/match_tier no longer rendered except the deprecation marker.",
    ),
    Phase(
        8,
        "Applications & Workshops polish",
        "The Applications Guardrails tab is fully wired (scan + intent capture); "
        "Workshops legacy code paths retired.",
        ("15", "14"),
        ("G-S4", "G-A5"),
        "3 days",
        "Cross-cutting",
        SHIPPED,
        "guardrail-scan endpoint live; intent + rationale persisted; "
        "feedback-only Workshops contract enforced by a no-generation test.",
        "Guardrail scan wired; intent persisted; legacy workshop pages removed.",
    ),
    Phase(
        9,
        "Saved list persistence",
        "Saved-list priority survives a refresh.",
        ("13",),
        ("G-S5",),
        "0.5 day",
        "Data",
        SHIPPED,
        "priority column on saved lists; PATCH /me/saved/:program_id accepts it; "
        "frontend persists on change.",
        "Priority survives refresh.",
    ),
    Phase(
        10,
        "Institution editors",
        "Replace raw JSON textareas in the program + settings editors with "
        "guided, form-based editors.",
        ("23",),
        ("G-I1",),
        "4 days",
        "Frontend",
        SHIPPED,
        "Guided editors for application requirements, intake rounds, cost and "
        "outcomes; advanced JSON behind a toggle.",
        "Admins edit known shapes via forms, not raw JSON.",
    ),
    Phase(
        11,
        "Fairness signal + auto-halt",
        "Disparate-impact tracked per cohort × week; auto-halt at Δ > 0.20 for 2 "
        "weeks; dashboard visibility + override workflow.",
        ("46",),
        ("G-I5", "G-D4"),
        "5 days",
        "Backend",
        SHIPPED,
        "fairness_signals + programs.matching_halted; deterministic FairnessService; "
        "FairnessPage + dashboard panel; audit-logged override.",
        "Auto-halt fires on a synthetic Δ>0.20 cohort; dashboard shows the trend and halt status.",
    ),
    Phase(
        12,
        "Authenticity risk + AI assistive expansion",
        "Essay anti-AI-pattern flagging, the student inbox reply drafter, and "
        "expanded institution-side AI drafts.",
        ("37", "45"),
        ("G-AI4", "G-AI7"),
        "5 days",
        "Backend",
        SHIPPED,
        "AuthenticityRiskScorer (§18) + InboxReplyDrafter (§13) live; per-"
        "institution AI config governs eight assistive surfaces.",
        "Authenticity scoring raises integrity signals; inbox drafter wired; AI "
        "config governs the surfaces.",
    ),
    Phase(
        13,
        "Peers / Connect Stage 3a",
        "The Connect Peers surface — opt-in, consent- and privacy-gated peer "
        "discovery from followed institutions.",
        ("20",),
        ("G-S7", "G-D3"),
        "5 days",
        "Cross-cutting",
        SHIPPED,
        "connect.py peers routes + PeerService behind connect_peers_enabled; "
        "PostsPage Updates · Events · Peers tabs with PeersTab.",
        "Peers tab live (flag-gated), with opt-in profile sharing per program.",
    ),
    Phase(
        14,
        "Deferred items",
        "Bedrock as a third provider, per-institution data residency, "
        "multi-institution staff users, streaming discovery, multi-channel "
        "notifications, and the bias auto-halt override review workflow.",
        (),
        ("G-C2",),
        "Reassess Q3 2026",
        "Cross-cutting",
        DEFERRED,
        "Explicitly out of MVP scope per spec 48 §17 — reassessed against the Series-A milestones.",
        "Reassessed in Q3 2026 against Series-A milestones.",
    ),
)


def _phase_payload(p: Phase) -> dict:
    return {
        "number": p.number,
        "title": p.title,
        "goal": p.goal,
        "specs": list(p.specs),
        "gap_items": list(p.gap_items),
        "effort": p.effort,
        "workstream": p.workstream,
        "status": p.status,
        "status_label": STATUS_LABELS.get(p.status, p.status),
        "evidence": p.evidence,
        "done_when": p.done_when,
    }


def build_roadmap() -> dict:
    """Assemble the ``GET /build/roadmap`` payload (spec 48)."""
    phases = [_phase_payload(p) for p in PHASES]
    shipped = sum(1 for p in PHASES if p.status == SHIPPED)
    deferred = sum(1 for p in PHASES if p.status == DEFERRED)
    return {
        "summary": {
            "phase_count": len(PHASES),
            "shipped": shipped,
            "deferred": deferred,
            "mvp_complete": all(p.status == SHIPPED for p in PHASES if p.number <= 13),
        },
        "phases": phases,
        "workstreams": ["Frontend", "Backend", "Data", "Cross-cutting"],
    }

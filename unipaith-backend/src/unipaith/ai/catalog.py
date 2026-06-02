"""Spec 45 — AI agent catalog (the transparency surface).

A read-only metadata layer over the *live* registry. It powers the public
``GET /ai/agents`` endpoint and the ``/goal/claude-api`` page, turning spec 45
(per-agent prompts, tiers, consent, JSON-vs-tool-use, cache, streaming,
fallback, validation) into queryable data.

Design invariant — the catalog can never contradict what's actually wired:
- **tier** is resolved live from ``agent_registry.tier_for(name)``.
- **consent** is resolved live from ``consent.AGENT_REQUIRES.get(name)``.
- **enabled** is resolved live from the gating ``settings`` flag.

Only the narrative metadata (title, purpose, group, surface, mode, streaming,
cache breakpoints, fallback contract, prompt file) is authored here. A test
(``tests/test_spec45_agent_catalog.py``) asserts every ``AGENT_TIERS`` agent is
catalogued and every named prompt file exists, so the catalog stays a faithful
mirror of the fleet rather than a doc that rots.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from unipaith.ai.agent_registry import tier_for
from unipaith.ai.client import MODEL_PRICES
from unipaith.ai.consent import AGENT_REQUIRES
from unipaith.config import settings

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


# ── Tier → human label + role + the settings attr holding the model id ──────
# flagship → Opus, workhorse → Sonnet, batch → Haiku, rule_based → no LLM.
TIER_META: dict[str, dict[str, str | None]] = {
    "flagship": {
        "label": "Opus",
        "role": "High-stakes, single-shot reasoning — the heaviest calls.",
        "model_attr": "anthropic_default_flagship",
    },
    "workhorse": {
        "label": "Sonnet",
        "role": "The default tier — chat, drafting, structured generation.",
        "model_attr": "anthropic_default_workhorse",
    },
    "batch": {
        "label": "Haiku",
        "role": "Cheap, high-volume extraction, triage and ranking.",
        "model_attr": "anthropic_default_batch",
    },
    "rule_based": {
        "label": "Rule-based",
        "role": "Deterministic — no LLM call. Labels the audit-ledger row.",
        "model_attr": None,
    },
}

TIER_ORDER = ["flagship", "workhorse", "batch", "rule_based"]

CONSENT_LABELS: dict[str | None, str] = {
    "matching": "Matching consent",
    "outreach": "Outreach consent",
    "analytics": "Analytics consent",
    None: "No student-data gate",
}


def resolve_model(tier: str) -> dict | None:
    """Resolve a tier to the live Claude model id + price (USD / MTok).

    Reuses ``settings.anthropic_default_*`` and ``client.MODEL_PRICES`` so the
    page shows the exact model id production is calling, not a hardcoded label.
    """
    meta = TIER_META.get(tier)
    if not meta or not meta["model_attr"]:
        return None
    model_id = getattr(settings, str(meta["model_attr"]), None)
    if not model_id:
        return None
    price = MODEL_PRICES.get(model_id)
    return {
        "model_id": model_id,
        "label": meta["label"],
        "price": price,  # {"input": x, "output": y} per MTok, or None
    }


@dataclass(frozen=True)
class AgentEntry:
    """Authored, narrative metadata for one agent. Tier + consent + enabled are
    NOT stored here — they're resolved live in ``build_catalog``."""

    name: str
    title: str
    spec_sections: tuple[str, ...]  # spec-45 §; empty = wired by another spec
    surface: str  # "student" | "institution" | "shared"
    group: str
    purpose: str
    mode: str  # "tool_use" | "json" | "deterministic"
    streaming: bool
    cache_persona: str | None  # "5min" | None (system block is 1h for LLM tiers)
    fallback: str
    flag: str | None  # gating settings attr, or None = always on / role-gated
    prompt_file: str | None  # filename under ai/prompts/, or None


# ── The fleet (spec 45 §2–§19 + the rest wired across specs 06–44) ──────────
# Authoring note: keep one entry per AGENT_TIERS key. Surfaces split the page
# into Student / Institution / Shared. spec_sections drives the §coverage test.
CATALOG: tuple[AgentEntry, ...] = (
    # ─────────────── Student · Discovery (Stage 1) ───────────────
    AgentEntry(
        "orchestrator",
        "Discovery Orchestrator",
        ("§2", "§5"),
        "student",
        "Discovery",
        "Decides the single best next question to ask in a discovery session, and "
        "self-elects the hand-off to recommendation once a layer is ~80% complete.",
        "json",
        True,
        "5min",
        "Static next-question pool keyed on (track, layer, missing category).",
        "ai_discovery_v2_enabled",
        "orchestrator_discovery.md",
    ),
    AgentEntry(
        "extractor",
        "Discovery Extractor",
        ("§3",),
        "student",
        "Discovery",
        "Pulls structured Prompt-Library signals out of a student's free-text turn, "
        "each with an honest 0–100 confidence.",
        "tool_use",
        False,
        None,
        "Return no signals — the orchestrator simply re-asks next turn.",
        "ai_discovery_v2_enabled",
        "extractor.md",
    ),
    AgentEntry(
        "validator",
        "Discovery Validator",
        ("§4",),
        "student",
        "Discovery",
        "Fast second pass over extractor output — rejects low-confidence or "
        "enum-violating fields before they're written.",
        "tool_use",
        False,
        None,
        "Accept every field the extractor proposed.",
        "ai_discovery_v2_enabled",
        None,
    ),
    # ─────────────── Student · Match & Strategy ───────────────
    AgentEntry(
        "rationale",
        "Match Rationale",
        ("§6",),
        "student",
        "Match",
        "Writes the plain-language 'why this program' for a (student, program) pair "
        "— every strength linked to a specific profile signal.",
        "json",
        False,
        "5min",
        "Template: matches your stated interest in {top field} + {budget band}.",
        "ai_match_rationale_v2_enabled",
        "rationale.md",
    ),
    AgentEntry(
        "strategy",
        "Strategy Agent",
        ("§10",),
        "student",
        "Strategy",
        "Generates the active broad strategy — career → degree → academic / "
        "financial / geographic paths + a 4-paragraph narrative (forced tool-use).",
        "tool_use",
        False,
        "5min",
        "Preserve the existing active strategy + a 'couldn't regenerate' banner.",
        "ai_strategy_v2_enabled",
        "strategy.md",
    ),
    AgentEntry(
        "strategy_first_time",
        "Strategy Agent · first-run",
        ("§10",),
        "student",
        "Strategy",
        "The first-time strategy generation when profile completeness ≥ 80% — "
        "promoted to Opus for the highest-stakes single shot.",
        "tool_use",
        False,
        "5min",
        "Preserve the existing active strategy + a 'couldn't regenerate' banner.",
        "ai_strategy_v2_enabled",
        "strategy.md",
    ),
    AgentEntry(
        "identity_summary",
        "Identity Summary",
        ("§11",),
        "student",
        "Identity",
        "Synthesizes a 3–5 sentence identity paragraph from the structured "
        "core-values / worldview / self-awareness layer.",
        "tool_use",
        False,
        "5min",
        "Keep the existing real summary; else a 'building your identity' placeholder.",
        "ai_identity_v2_enabled",
        "identity_summary.md",
    ),
    # ─────────────── Student · Workshops (feedback-only) ───────────────
    AgentEntry(
        "workshop_coach",
        "Workshop Coach",
        ("§7", "§8", "§9"),
        "student",
        "Workshops",
        "Feedback-only coach for essay / interview / test — scores a rubric and "
        "flags issues. The schema mechanically excludes any generated answer.",
        "tool_use",
        True,
        "5min",
        "Rubric zeros + a 'couldn't analyze, please retry' note; interview practice "
        "serves the canned question bank.",
        "ai_workshops_v2_enabled",
        "workshop_essay.md",
    ),
    AgentEntry(
        "workshop_judge",
        "Workshop Guardrail Judge",
        (),
        "student",
        "Workshops",
        "The second guardrail layer (§26) — confirms a coach reply carries no "
        "generated essay or model answer before it reaches the student.",
        "tool_use",
        False,
        None,
        "Accept the coach output without the second-pass guardrail check.",
        "ai_workshops_v2_enabled",
        None,
    ),
    # ─────────────── Student · Search / Inbox / Offers ───────────────
    AgentEntry(
        "query_interpreter",
        "Discovery Query Interpreter",
        ("§12",),
        "student",
        "Search",
        "Turns a free-text program search into individually-editable constraint "
        "chips (degree, major, location, budget, format, …).",
        "tool_use",
        False,
        None,
        "Deterministic keyword parser (services/query_parser.py).",
        "ai_discovery_query_v2_enabled",
        "query_interpreter.md",
    ),
    AgentEntry(
        "inbox_reply_drafter",
        "Inbox Reply Drafter",
        ("§13",),
        "student",
        "Inbox",
        "Suggests an editable draft reply to a student inbox thread. Drafts are "
        "never sent automatically — the student edits first.",
        "tool_use",
        False,
        "5min",
        "Empty draft — the student types from scratch (no rule-based draft).",
        "ai_inbox_v2_enabled",
        "inbox_reply.md",
    ),
    AgentEntry(
        "outcome_brief",
        "Offer Brief",
        ("§15",),
        "student",
        "Offers",
        "Converts an offer letter into a plain-language student brief — key terms, "
        "deadlines, next steps, summary.",
        "tool_use",
        False,
        None,
        "Regex key dates + raw text via the rule-based _build_structured_brief.",
        "ai_outcome_brief_v2_enabled",
        "outcome_brief.md",
    ),
    # ─────────────── Student · Connect / Prompt Library / Major tracks ───────
    AgentEntry(
        "connect_ranker",
        "Connect Feed Ranker",
        (),
        "student",
        "Connect",
        "Ranks the Connect feed by relevance when the 'Most relevant' toggle is on.",
        "json",
        False,
        None,
        "Reverse-chronological / deterministic relevance order.",
        "ai_connect_ranker_v2_enabled",
        "connect_ranker.md",
    ),
    AgentEntry(
        "event_recommender",
        "Event Recommender",
        (),
        "student",
        "Connect",
        "Surfaces the events a student is most likely to care about.",
        "json",
        False,
        None,
        "Chronological upcoming events.",
        "ai_connect_ranker_v2_enabled",
        None,
    ),
    AgentEntry(
        "prompt_coach",
        "Prompt Library Coach",
        (),
        "student",
        "Prompt Library",
        "Interview-readiness band, competency coverage, story↔prompt matching and a "
        "practice plan over the student's own responses. Deterministic today; the "
        "tier documents the future LLM swap-in.",
        "deterministic",
        False,
        None,
        "The deterministic STAR / readiness / story-matching engine (always runs).",
        "ai_prompt_library_v2_enabled",
        None,
    ),
    AgentEntry(
        "major_track_coach",
        "Major-Track Coach",
        (),
        "student",
        "Major Tracks",
        "Per-track fit score, readiness band, coverage map and bridge plan across 15 "
        "discipline tracks. Deterministic today; the tier documents the LLM swap-in.",
        "deterministic",
        False,
        None,
        "The deterministic per-track fit / readiness engine (always runs).",
        "ai_major_specific_v2_enabled",
        None,
    ),
    # ─────────────── Shared · Matching pipeline ───────────────
    AgentEntry(
        "feature_emitter",
        "Feature Emitter",
        (),
        "shared",
        "Matching",
        "Distils a discovery session into the structured feature vector the L3 "
        "matcher embeds (the L2→L3 hand-off).",
        "tool_use",
        False,
        None,
        "Skip the refresh — the matcher reuses the last stored vector.",
        None,
        "feature_emitter.md",
    ),
    AgentEntry(
        "embedding",
        "Embedding",
        (),
        "shared",
        "Matching",
        "Produces the dense vector (Voyage) the similarity matcher searches against.",
        "deterministic",
        False,
        None,
        "Reuse the last stored vector.",
        None,
        None,
    ),
    AgentEntry(
        "matcher",
        "L3 ML Matcher",
        (),
        "shared",
        "Matching",
        "The deterministic similarity + historical-yield scorer behind every "
        "fitness / confidence score. Not an LLM — labels its own audit-ledger row.",
        "deterministic",
        False,
        None,
        "N/A — the matcher IS the deterministic scorer.",
        None,
        None,
    ),
    # ─────────────── Institution · Review & Integrity ───────────────
    AgentEntry(
        "review_summarizer",
        "Review Packet Summarizer",
        ("§14",),
        "institution",
        "Review",
        "Opus per-applicant packet summary for reviewers — signal strengths / "
        "weaknesses + rubric-aligned notes. One high-stakes call per applicant.",
        "tool_use",
        False,
        "5min",
        "Template summary from rule-based extraction.",
        None,
        None,
    ),
    AgentEntry(
        "review_synthesis",
        "Review Synthesis",
        (),
        "institution",
        "Review",
        "Reconciles per-criterion × per-reviewer score variance into a synthesis "
        "note (Spec 32 §4).",
        "tool_use",
        False,
        "5min",
        "Show the per-reviewer scores without the AI synthesis.",
        None,
        None,
    ),
    AgentEntry(
        "review_assistant",
        "Review Assistant",
        (),
        "institution",
        "Review",
        "Answers a reviewer's question grounded only in the application packet (Spec 32 §6).",
        "tool_use",
        False,
        "5min",
        "No assistant answer; the reviewer reads the packet directly.",
        None,
        None,
    ),
    AgentEntry(
        "authenticity_risk",
        "Authenticity Risk Scorer",
        ("§18",),
        "institution",
        "Integrity",
        "Flags essays whose patterns match common AI-generated structures — raises "
        "an integrity signal for human review, never an auto-flag.",
        "tool_use",
        False,
        None,
        "{risk_band: low, signals: [], confidence: 0} — better silent than a false flag.",
        None,
        None,
    ),
    # ─────────────── Institution · Campaigns / Segments / Data ───────────────
    AgentEntry(
        "campaign_copy",
        "Campaign Copy Suggester",
        ("§16",),
        "institution",
        "Campaigns",
        "Drafts external campaign subject + body from an audience summary, "
        "objective and institution voice brief.",
        "tool_use",
        False,
        "5min",
        "Objective-keyed template stub.",
        "ai_campaign_copy_v2_enabled",
        "campaign_copy.md",
    ),
    AgentEntry(
        "segment_builder_nl",
        "Segment Builder (NL bridge)",
        ("§17",),
        "institution",
        "Segments",
        "Converts a natural-language audience description into structured "
        "include / exclude rules over the signal dictionary.",
        "tool_use",
        False,
        None,
        "Keyword parser → editable rules.",
        "ai_segment_builder_v2_enabled",
        "segment_builder.md",
    ),
    AgentEntry(
        "document_parse_triage",
        "Document Parse Triage",
        ("§19",),
        "institution",
        "Data",
        "Triages an uploaded transcript / portfolio / dataset to ok / needs-review "
        "/ failed with a suggested action.",
        "tool_use",
        False,
        None,
        "{triage: needs_review, action: request_clarification}.",
        "ai_data_parse_triage_v2_enabled",
        "document_parse_triage.md",
    ),
    # ─────────────── Institution · Messaging & Intelligence ───────────────
    AgentEntry(
        "institution_reply_drafter",
        "Institution Reply Drafter",
        (),
        "institution",
        "Messaging",
        "Drafts a staff reply to an applicant thread with checklist + reason-code "
        "context (respects the applicant's matching consent for profile context).",
        "tool_use",
        False,
        "5min",
        "Null draft — staff types from scratch.",
        "ai_institution_reply_v2_enabled",
        "institution_reply.md",
    ),
    AgentEntry(
        "inbound_intent_classifier",
        "Inbound Intent Classifier",
        (),
        "institution",
        "Messaging",
        "Suggests a reason code + routing hint for a new inbound message "
        "(suggestion-only, never auto-assigns).",
        "tool_use",
        False,
        None,
        "No suggested reason code.",
        "ai_inbound_intent_v2_enabled",
        "inbound_intent.md",
    ),
    AgentEntry(
        "intelligence_digest",
        "Dashboard Intelligence Digest",
        (),
        "institution",
        "Intelligence",
        "Writes the plain-English daily pipeline digest from a pre-aggregated, "
        "non-PII applicant-landscape stat block (migrated GPT-4o → Claude, §11).",
        "tool_use",
        False,
        None,
        "Deterministic rule-based narrator.",
        "ai_intelligence_digest_v2_enabled",
        "intelligence_digest.md",
    ),
    # ─────────────── Institution · Interviews & Yield ───────────────
    AgentEntry(
        "interview_invite_drafter",
        "Interview Invite Drafter",
        (),
        "institution",
        "Interviews",
        "Drafts an interview invite message from interview context.",
        "tool_use",
        False,
        None,
        "No AI invite draft; staff writes manually.",
        "ai_interview_v2_enabled",
        "interview_invite.md",
    ),
    AgentEntry(
        "interview_score_prefill",
        "Interview Score Prefill",
        (),
        "institution",
        "Interviews",
        "Prefills the interview rubric from a transcript for the reviewer to confirm.",
        "tool_use",
        False,
        "5min",
        "No rubric prefill; the reviewer scores manually.",
        "ai_interview_v2_enabled",
        "interview_score_prefill.md",
    ),
    AgentEntry(
        "yield_risk_scorer",
        "Yield Risk Scorer",
        (),
        "institution",
        "Yield",
        "Per-admit confirm-probability for the yield dashboard. A calibrated "
        "deterministic heuristic — disparities surface but never drive selection.",
        "deterministic",
        False,
        None,
        "Deterministic confirm-probability counts.",
        "ai_yield_intelligence_v2_enabled",
        None,
    ),
    AgentEntry(
        "next_best_action_yield",
        "Next-Best-Action (Yield)",
        (),
        "institution",
        "Yield",
        "Refines the dashboard's ranked yield actions.",
        "tool_use",
        False,
        None,
        "Deterministic ranked actions by count.",
        "ai_yield_intelligence_v2_enabled",
        "next_best_action_yield.md",
    ),
    # ─────────────── Institution · International ───────────────
    AgentEntry(
        "credential_normalizer",
        "Credential Normalizer",
        (),
        "institution",
        "International",
        "Refines foreign-GPA normalization onto the 4.0 scale. AI never decides "
        "feasibility — it informs the human reviewer.",
        "tool_use",
        False,
        None,
        "Deterministic grading-scale mapper.",
        "ai_international_v2_enabled",
        "credential_normalizer.md",
    ),
    AgentEntry(
        "country_requirement_advisor",
        "Country Requirement Advisor",
        (),
        "institution",
        "International",
        "Proposes a richer country-requirement pack for a region.",
        "tool_use",
        False,
        None,
        "Platform default country-requirement pack.",
        "ai_international_v2_enabled",
        "country_requirement_advisor.md",
    ),
    # ─────────────── Institution · Recruitment CRM ───────────────
    AgentEntry(
        "prospect_prioritizer",
        "Prospect Prioritizer",
        (),
        "institution",
        "Recruitment",
        "Ranks pre-applicant prospects by apply-likelihood. Prioritization only, never selection.",
        "deterministic",
        False,
        None,
        "Deterministic propensity sort.",
        "ai_recruitment_v2_enabled",
        None,
    ),
    AgentEntry(
        "territory_optimizer",
        "Territory Optimizer",
        (),
        "institution",
        "Recruitment",
        "Suggests high-yield schools / fairs for a recruitment territory.",
        "tool_use",
        False,
        None,
        "Prior-year-yield ranking.",
        "ai_recruitment_v2_enabled",
        "territory_optimizer.md",
    ),
    # ─────────────── Institution · Graduate & PhD ───────────────
    AgentEntry(
        "advisor_matcher",
        "Advisor Matcher",
        (),
        "institution",
        "Graduate",
        "Ranks faculty advisors by research-interest fit for an applicant. Informs "
        "faculty; faculty decide.",
        "tool_use",
        False,
        None,
        "Deterministic advisor-alignment ranking.",
        "ai_graduate_v2_enabled",
        None,
    ),
    AgentEntry(
        "sop_interest_extractor",
        "SoP Interest Extractor",
        (),
        "institution",
        "Graduate",
        "Auto-tags research interests from a statement of purpose.",
        "tool_use",
        False,
        None,
        "No auto-tagged interests; faculty reads the SoP.",
        "ai_graduate_v2_enabled",
        None,
    ),
    AgentEntry(
        "funding_scenario_helper",
        "Funding Scenario Helper",
        (),
        "institution",
        "Graduate",
        "Suggests viable funding mixes and surfaces over-commit warnings (the hard "
        "over-commit block is always on, §9).",
        "tool_use",
        False,
        None,
        "Deterministic over-commit block + funding mix.",
        "ai_graduate_v2_enabled",
        None,
    ),
)


# ── Static narrative blocks (spec 45 §22 / §24 / §26 + 46 principles) ───────
# Kept here so the backend is the single source and the page just renders.

PRINCIPLES: tuple[dict[str, str], ...] = (
    {
        "title": "Humans decide",
        "body": "Every agent informs a person. None of them admit, reject, rank for "
        "selection, or send on their own — matching surfaces evidence, people choose.",
    },
    {
        "title": "Evidence-linked",
        "body": "Generated text references specific signals from the profile or "
        "packet. Agents never invent student facts or program facts.",
    },
    {
        "title": "Consent-gated",
        "body": "The student's consent mask is resolved before every call and "
        "recorded on the audit ledger. A denied lever short-circuits to the "
        "rule-based path.",
    },
    {
        "title": "Always falls back",
        "body": "Provider error, parse error or a guardrail trip degrades to a "
        "deterministic result. A caller never sees a 5xx — 100% fallback coverage.",
    },
)

# Spec 45 §26 — the fallback decision flow.
FALLBACK_FLOW: tuple[dict[str, str], ...] = (
    {
        "trigger": "Provider 5xx / timeout",
        "action": "Fail over to the next configured provider; if that fails too, "
        "use the rule-based fallback. Every attempt is recorded.",
    },
    {
        "trigger": "Provider 4xx (rate limit / bad request)",
        "action": "Retry once, then fall back to the rule-based path.",
    },
    {
        "trigger": "Output fails schema validation",
        "action": "Retry once with a stricter 'respond only in JSON' reminder, then fall back.",
    },
    {
        "trigger": "Guardrail trip (e.g. a workshop tries to generate)",
        "action": "Fall back to the rule-based path immediately — no retry.",
    },
    {
        "trigger": "Consent denied for the agent's lever",
        "action": "Short-circuit before any provider call; record the denied mask.",
    },
)

# Spec 45 §24 — cache breakpoints.
CACHE_STRATEGY: tuple[dict[str, str], ...] = (
    {
        "layer": "System block",
        "ttl": "1 hour",
        "note": "The long, stable instructions — the highest-leverage cache "
        "breakpoint. Cached for every agent.",
    },
    {
        "layer": "Persona block",
        "ttl": "5 minutes",
        "note": "Profile / packet context that's stable within a session but "
        "changes between students. Cached where the persona is heavy.",
    },
    {
        "layer": "Per-turn tail",
        "ttl": "Uncached",
        "note": "The volatile per-call message — always re-read so the answer "
        "reflects the latest state.",
    },
)

# Spec 45 §22 — output validation.
VALIDATION: dict[str, object] = {
    "summary": "Every agent's output is validated by Pydantic v2 before the caller "
    "sees it. Structured agents use forced tool-use so Claude's stricter "
    "type-checking catches malformed output at the call boundary.",
    "steps": [
        "Validate the response against the agent's schema.",
        "On a validation error, log the raw output and retry once with a strict JSON reminder.",
        "If the retry also fails, fall back to the agent's rule-based contract.",
    ],
}


def _enabled(flag: str | None) -> bool:
    """Live enabled state for an agent's gating flag.

    ``None`` flag → always on (role-gated / part of the pipeline). Otherwise read
    the current environment's setting, so the page reflects what's actually live
    (production has these enabled; local defaults are off)."""
    if flag is None:
        return True
    return bool(getattr(settings, flag, False))


def _agent_payload(entry: AgentEntry) -> dict:
    tier = tier_for(entry.name)  # live registry
    consent = AGENT_REQUIRES.get(entry.name)  # live consent map (None if absent)
    model = resolve_model(tier)
    return {
        "name": entry.name,
        "title": entry.title,
        "spec_sections": list(entry.spec_sections),
        "surface": entry.surface,
        "group": entry.group,
        "purpose": entry.purpose,
        "tier": tier,
        "tier_label": TIER_META.get(tier, {}).get("label"),
        "model_id": model["model_id"] if model else None,
        "consent": consent,
        "consent_label": CONSENT_LABELS.get(consent, "No student-data gate"),
        "mode": entry.mode,
        "streaming": entry.streaming,
        "cache": {
            "system": "1h" if tier != "rule_based" else None,
            "persona": entry.cache_persona,
        },
        "fallback": entry.fallback,
        "flag": entry.flag,
        "enabled": _enabled(entry.flag),
        "prompt_file": entry.prompt_file,
    }


def build_catalog() -> dict:
    """Assemble the full ``GET /ai/agents`` payload from the live registry."""
    agents = [_agent_payload(e) for e in CATALOG]

    tier_counts: dict[str, int] = {t: 0 for t in TIER_ORDER}
    for a in agents:
        tier_counts[a["tier"]] = tier_counts.get(a["tier"], 0) + 1

    tiers = []
    for t in TIER_ORDER:
        if tier_counts.get(t, 0) == 0:
            continue
        model = resolve_model(t)
        tiers.append(
            {
                "tier": t,
                "label": TIER_META[t]["label"],
                "role": TIER_META[t]["role"],
                "model_id": model["model_id"] if model else None,
                "price": model["price"] if model else None,
                "agent_count": tier_counts[t],
            }
        )

    llm_agents = sum(c for t, c in tier_counts.items() if t != "rule_based")
    return {
        "summary": {
            "agent_count": len(agents),
            "llm_agent_count": llm_agents,
            "tier_counts": tier_counts,
            "fallback_coverage": "100%",
            "provider": settings.ai_provider_default,
        },
        "tiers": tiers,
        "agents": agents,
        "principles": list(PRINCIPLES),
        "fallback_flow": list(FALLBACK_FLOW),
        "cache_strategy": list(CACHE_STRATEGY),
        "validation": VALIDATION,
    }

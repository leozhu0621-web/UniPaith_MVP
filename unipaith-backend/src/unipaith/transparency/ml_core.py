"""Spec 63 — ML Core & Knowledge Processing, as queryable data.

Backs ``GET /build/ml-core`` and the ``/goal/ml-core`` page. Turns spec 63's hard
model boundary — **Qwen processes, Claude communicates** — into a live,
self-verifying payload, the same way ``transparency.knowledge`` does for spec 60.

Self-verifying hooks (read live from the running app, never asserted in prose):

- the **boundary** (which agents are human-facing vs Qwen-eligible, and that the
  guard passes) is read from ``ai/boundary.py`` — the *same* module
  ``providers/registry`` enforces on every resolution, so the page cannot claim a
  boundary the code doesn't enforce;
- the **pin proof** (human-facing agents that any Qwen route is forced back to
  Claude) is recomputed live via ``enforce_policy`` — it is ``0`` by construction;
- the **provider routing** (default · per-agent overrides · failover order · Qwen
  availability) is read off ``settings`` + the live provider registry;
- the **audit gate** (``ai_turns.provider`` accepts ``'qwen'``) is introspected
  from the running SQLAlchemy model constraint — the same one Alembic builds;
- the **L3 weights** are read live from ``services.matching.DEFAULT_WEIGHTS``;
- the **embedding transport** (provider · model · dim) is read off ``settings``.

The narrative — the §1 rule, the §4 roster, the §5 pipeline, the §11 phasing, the
§14 SLOs, the §16 acceptance, the §17 open questions — is authored from spec 63;
each capability is honestly classified ``live`` / ``partial`` / ``planned``.
DB-free and unauthenticated.
"""

from __future__ import annotations

from dataclasses import dataclass

from unipaith.ai import boundary
from unipaith.config import settings

API_PREFIX = "/api/v1"
_SKIP_METHODS = {"HEAD", "OPTIONS"}
Status = str  # "live" | "partial" | "planned"


# ── §1 · The rule ────────────────────────────────────────────────────────────
THE_RULE: dict = {
    "headline": "Qwen processes. Claude communicates.",
    "statement": (
        "The platform runs on two models with a hard, non-negotiable boundary. "
        "Qwen — open-source, self-hosted, tuned — is the ML backend: it embeds, "
        "extracts, scores and synthesizes the information presented on the "
        "frontend, and never interacts with a human directly. Claude is the "
        "human-facing agent — the advisor chatbot and every advisory surface — "
        "pinned to Claude by policy, not decided per-task by an eval."
    ),
    "seam": (
        "Qwen computes; Claude communicates. A match card = Qwen numbers + Claude "
        "rationale. A program page = Qwen-synthesized facts; ask the chatbot about "
        "it → Claude, grounded by Qwen's RAG."
    ),
    "why_hard": (
        "The conversation is the brand + trust surface, so it stays Claude as a "
        "product decision — independent of whether a tuned Qwen could match it. "
        "The highest-stakes surface carries zero Qwen-migration risk."
    ),
}


# ── §1 · The boundary (two columns) ──────────────────────────────────────────
BOUNDARY_COLUMNS: tuple[dict, ...] = (
    {
        "side": "qwen",
        "title": "Qwen — ML backend (invisible)",
        "role": "processes, scores, ranks, embeds, synthesizes displayed info",
        "human": "none — batch / inline services",
        "why": "open, self-hosted, tuned, cheap at volume, PII in-VPC",
        "where": "GPU / Bedrock worker fleet (55)",
    },
    {
        "side": "claude",
        "title": "Claude — the agent (human-facing)",
        "role": "talks to people; personalized advice",
        "human": "direct — chat, advisory prose",
        "why": "premium reasoning, brand voice (01 §6), trust, safety (61)",
        "where": "Anthropic API / Bedrock via 04",
    },
)


# ── §5 · Knowledge-processing pipeline (raw → presented) ─────────────────────
@dataclass(frozen=True)
class Stage:
    n: int
    name: str
    detail: str


PIPELINE_STAGES: tuple[Stage, ...] = (
    Stage(1, "Extract", "Qwen, schema-strict, grounded (62) — page → structured fields."),
    Stage(2, "Normalize", "Units / SOC / CIP / CEFR / currency / grading scale."),
    Stage(3, "Resolve", "Link facts → canonical knowledge entities."),
    Stage(4, "Embed", "Qwen3-Embedding (Matryoshka → 1536) → pgvector."),
    Stage(5, "Enrich-write", "Confidence-gated; provenance; first-party-wins (60)."),
    Stage(6, "Synthesize", "Qwen → presented facts, sourced, brand-voice (62)."),
    Stage(7, "Serve", "Frontend + RAG index for the Claude advisor + feature vectors for L3."),
)


# ── §2–§13 · Capabilities ────────────────────────────────────────────────────
@dataclass(frozen=True)
class Capability:
    key: str
    title: str
    section: str
    status: Status
    blurb: str
    built: tuple[str, ...]
    planned: tuple[str, ...]


CAPABILITIES: tuple[Capability, ...] = (
    Capability(
        "boundary",
        "Hard model boundary (enforced in code)",
        "§1 · §3 · §16",
        "live",
        "No human-facing output is ever served by Qwen — pinned to Claude, unbreakable by config.",
        (
            "ai/boundary.py — human-facing vs Qwen-eligible classification of every agent",
            "enforce_policy applied on every provider resolution (registry) + failover chain",
            "A human-facing agent routed to qwen in config is forced back to Claude",
            "assert_boundary_intact() guard: no overlap, full coverage, all pins hold",
            "Auditable via ai_turns.provider — a qwen row is never a human-facing surface",
        ),
        (),
    ),
    Capability(
        "transport",
        "Qwen registered as a backend transport",
        "§4 · §10",
        "live",
        "Qwen is a first-class provider in the routing layer (04) — vLLM / Bedrock "
        "OpenAI-compatible.",
        (
            "QwenProvider (ai/providers/qwen_provider.py) implements the AIProvider Protocol",
            "Registered in providers/registry; lazily built; tier → Qwen instruct sizes",
            "ai_turns.provider CHECK widened to accept 'qwen' (cost ledger splits by transport)",
            "MODEL_PRICES carries amortized self-host Qwen rates (no None on the dashboard)",
        ),
        ("Bedrock-managed transport variant (start managed, self-host as volume grows §17)",),
    ),
    Capability(
        "processing_routing",
        "Processing agents routable to Qwen",
        "§2 · §11",
        "partial",
        "The §2 processing agents can be routed to Qwen per-env; default stays Claude "
        "until eval promotes.",
        (
            "extractor / validator / query_interpreter / document_parse_triage / "
            "authenticity_risk / segment_builder_nl flagged Qwen-eligible",
            "Routing via ai_provider_per_agent_json — zero agent-code change",
            "Automatic failover to Anthropic if Qwen is unavailable",
        ),
        (
            "Default route flips to Qwen per-agent only after a 62 A/B win (§11 phased)",
            "Tuned Qwen checkpoints for extraction → normalization → scoring (§9 ROI order)",
        ),
    ),
    Capability(
        "embeddings",
        "Qwen3-Embedding serving + A/B",
        "§8",
        "partial",
        "Qwen3-Embedding (Matryoshka → the live dim) wired as an embedding transport; "
        "Voyage stays default.",
        (
            "embed() embedding-provider seam — qwen branch, Matryoshka-truncated to "
            "embedding_dimension",
            "Falls back to Voyage on any failure (flipping the provider is safe)",
            "No migration / no re-embed — slots into the existing Vector store",
        ),
        (
            "A/B retrieval vs Voyage via 62; promote on win (§8)",
            "Reconcile 1024-d (live Voyage) vs 1536-d (generic tables) per target table",
        ),
    ),
    Capability(
        "extraction",
        "Qwen crawler extraction (60)",
        "§5 · §13",
        "partial",
        "The 60 crawler extractor's Qwen seam is wired — grounded, schema-strict, "
        "deterministic default.",
        (
            "crawler/extractor._extract_llm → Qwen /v1, forced JSON, schema-scoped",
            "Returned fields still pass _enforce_grounding — even a hallucination can't "
            "write ungrounded",
            "Inert until ai_crawler_extraction_v2_enabled AND qwen_enabled (deterministic default)",
        ),
        (
            "Tuned Qwen extractor + 62 extraction-F1 gate before promotion",
            "Two-speed: official API/bulk skips extract; crawl runs the full path (60 §6)",
        ),
    ),
    Capability(
        "l3",
        "L3 ML core — embeddings + classical scoring",
        "§6",
        "partial",
        "Qwen embeddings → pgvector + calibrated classical scoring; every checkpoint "
        "fairness-gated (46).",
        (
            "matching.py: fitness (cosine 0.45 / soft-align 0.35 / needs 0.20) + confidence",
            "Confidence calibrator + learned reranker (cold-start identity, model_registry-backed)",
            "Fairness auto-halt (46 §6) gates promotion before real cohorts",
        ),
        (
            "Qwen embeddings replace Voyage in the cosine stage (behind the embedding flag)",
            "distance-to-training extrapolation term once labeled outcomes accrue",
        ),
    ),
    Capability(
        "synthesis",
        "Display synthesis (factual, eval-gated)",
        "§5 · §7",
        "planned",
        "Qwen drafts the factual content presented on a program / school page — never a "
        "conversation.",
        ("The reference graph + provenance this synthesis presents is built in 60",),
        (
            "Qwen3-Instruct synthesis gated by 62 brand-voice + groundedness before shipping",
            "Falls back to template / Claude per-type if a type can't pass (still not a "
            "conversation)",
        ),
    ),
    Capability(
        "tuning",
        "Tuned checkpoints (LoRA / QLoRA)",
        "§9",
        "planned",
        "Qwen-only tuning, eval+fairness gated, consent-clean data, registered — Claude "
        "is never tuned-in.",
        (
            "model_registry / training_runs / evaluation_runs scaffolding present",
            "consent.training=false data NEVER trains (hard gate, 46 §9)",
        ),
        (
            "LoRA/QLoRA in ROI order: extraction → normalization/classification → scoring",
            "Each checkpoint: no-regression + fairness pass (62/46) + A/B before promote",
        ),
    ),
    Capability(
        "resilience",
        "Graceful degradation",
        "§10 · §16",
        "live",
        "A Qwen outage degrades processing only — Qwen is never on the Claude "
        "conversation's critical path.",
        (
            "Provider failover (qwen → anthropic) on any Qwen error",
            "Crawler extractor + embeddings fall back to deterministic / Voyage",
            "The boundary keeps Qwen off the chat path entirely, so chat is unaffected",
        ),
        (),
    ),
    Capability(
        "sovereignty",
        "PII-heavy processing in-VPC",
        "§12",
        "partial",
        "Self-hosted Qwen processes PII in-VPC; Claude gets only masked, consented, "
        "task-scoped context.",
        (
            "Claude calls are consent-gated + PII-masked today (consent_mask, 58 / 45)",
            "Boundary + masking mean less sensitive data reaches the premium API",
        ),
        ("Self-hosted in-VPC Qwen serving (GPU fleet) is infra — Bedrock-managed first (§17)",),
    ),
)


# ── §11 · Migration phasing (backend-only; no Phase D) ───────────────────────
@dataclass(frozen=True)
class Phase:
    key: str
    title: str
    status: Status
    detail: str


PHASES: tuple[Phase, ...] = (
    Phase(
        "A",
        "Embeddings",
        "partial",
        "Self-host / Bedrock the embedder; A/B retrieval vs Voyage via 62; promote on "
        "win. Seam wired, "
        "flag-gated — the ideal first Qwen move (pure backend, zero human-facing risk).",
    ),
    Phase(
        "B",
        "Crawler extraction (60)",
        "partial",
        "Qwen extractor behind ai_crawler_extraction_v2_enabled + qwen_enabled; "
        "62-gated; deterministic "
        "default holds until it proves out per-env.",
    ),
    Phase(
        "C",
        "Normalization / classification + rerank + display synthesis",
        "planned",
        "Per-task migration as 62 promotes each. No Phase D — the human-facing layer is "
        "permanently "
        "Claude (§1): no step moves the chatbot / advisory reasoning to Qwen.",
    ),
)


# ── §16 · Acceptance ─────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Acceptance:
    status: Status
    text: str


ACCEPTANCE: tuple[Acceptance, ...] = (
    Acceptance(
        "live",
        "Hard boundary enforced: no human-facing output served by Qwen; chatbot + 45 "
        "advisory = Claude "
        "(auditable via ai_turns.provider).",
    ),
    Acceptance(
        "live",
        "04 lists Qwen as a backend transport; human-facing rows pinned to Claude "
        "(not reassignable).",
    ),
    Acceptance(
        "partial",
        "Qwen3-Embedding (Matryoshka → live dim) serving; retrieval A/B via 62; promoted on win.",
    ),
    Acceptance(
        "partial",
        "Processing pipeline (§5) end-to-end on Qwen with provenance (extractor seam "
        "wired, flag-gated).",
    ),
    Acceptance(
        "partial",
        "L3 uses Qwen embeddings + classical scoring; fairness-gated (46) — classical + "
        "gate live today.",
    ),
    Acceptance(
        "planned",
        "Every tuned checkpoint: LoRA/QLoRA, consent-clean data (46), eval + fairness gated (62), "
        "registered.",
    ),
    Acceptance(
        "planned",
        "Display synthesis passes brand-voice + groundedness (62) before shipping.",
    ),
    Acceptance(
        "live",
        "Qwen outage degrades processing gracefully, never breaks the Claude conversation.",
    ),
    Acceptance(
        "partial",
        "PII-heavy processing in-VPC on Qwen; Claude gets only masked / consented "
        "context (masking live).",
    ),
)


# ── §14 · Observability & SLOs ───────────────────────────────────────────────
SLOS: tuple[dict, ...] = (
    {
        "metric": "Tokens + cost by provider",
        "target": "split anthropic / openai / qwen",
        "tracked_via": "ai_turns.provider cost ledger (ix_ai_turns_provider_agent_created)",
    },
    {
        "metric": "Qwen latency p95 (batch / realtime)",
        "target": "per-task throughput targets",
        "tracked_via": "ai_turns.latency_ms filtered to provider=qwen",
    },
    {
        "metric": "Embedding throughput",
        "target": "self-host pays off above ~10–15M/mo",
        "tracked_via": "ai_turns provider=qwen, agent=embedding",
    },
    {
        "metric": "Extraction F1 (62)",
        "target": "no regression vs the deterministic extractor",
        "tracked_via": "62 extraction eval suite, CI-gated",
    },
    {
        "metric": "Display-synthesis voice + groundedness",
        "target": "pass 62 before ship",
        "tracked_via": "62 brand-voice + groundedness judge",
    },
    {
        "metric": "Scoring-checkpoint fairness",
        "target": "pass 46 §6 before real cohorts",
        "tracked_via": "fairness gate on promotion (fairness_check_on_promotion)",
    },
    {
        "metric": "Qwen uptime",
        "target": "outage never degrades the Claude conversation",
        "tracked_via": "failover order + the boundary (Qwen off the chat critical path)",
    },
)


# ── §17 · Open questions ─────────────────────────────────────────────────────
OPEN_QUESTIONS: tuple[dict, ...] = (
    {
        "q": "Bedrock-managed vs self-host (Phase A)",
        "a": "Managed first to defer GPU ops; self-host as volume grows (§10 / §17).",
    },
    {
        "q": "Qwen size per task",
        "a": "7 / 14 / 32B / MoE chosen per task by 62 × cost.",
    },
    {
        "q": "Embedding dimension — 1024 vs 1536",
        "a": "Live store is Voyage 1024-d (student_feature_vectors); the generic embeddings / "
        "knowledge_entities tables are 1536-d. Qwen3-Embedding's Matryoshka emits the configured "
        "dim, so it slots in with no migration — confirmed direction, dim per target table.",
    },
    {
        "q": "Display-synthesis scope",
        "a": "Per-type via 62; default Qwen structured + factual, template / Claude fallback for "
        "types that can't pass.",
    },
    {
        "q": "04 registration",
        "a": "Qwen registered as a provider with a human-faces-Claude policy. This surface is the "
        "live form; 04 is the cross-ref doc (≤30 lines).",
    },
    {
        "q": "Tuning-data pipeline under 46 consent",
        "a": "Permissioned de-identified partner data + curated golden-set failures; "
        "consent.training=false NEVER trains (hard gate).",
    },
    {
        "q": "GPU capacity / autoscale",
        "a": "Idle GPU is the main cost risk; vLLM continuous batching + idle-shutdown "
        "knobs (gpu_*).",
    },
)


# ── Live introspection helpers ───────────────────────────────────────────────
def _route_buckets(routes) -> dict[str, list[str]]:
    """The AI-routing surface backing §16's 'auditable via model_registry'."""
    from unipaith.transparency.live_routes import expand_routes

    bucket: set[str] = set()
    for r in expand_routes(routes):
        path = getattr(r, "path", "")
        methods = getattr(r, "methods", None)
        if not path.startswith(API_PREFIX) or not methods:
            continue
        if all(m in _SKIP_METHODS for m in methods):
            continue
        if path.startswith(f"{API_PREFIX}/ai"):
            bucket.add(path)
    return {"ai": sorted(bucket)}


def _provider_routing() -> dict:
    """Read the live provider-routing config + Qwen availability."""
    import json

    from unipaith.ai.providers.registry import get_provider

    overrides: dict = {}
    raw = (settings.ai_provider_per_agent_json or "").strip()
    if raw:
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                overrides = parsed
        except (ValueError, json.JSONDecodeError):
            overrides = {}
    failover = [n.strip() for n in settings.ai_provider_failover_csv.split(",") if n.strip()]
    try:
        qwen_available = get_provider("qwen").is_available()
    except Exception:  # pragma: no cover — provider build edge
        qwen_available = False
    qwen_routed = sorted(a for a, p in overrides.items() if p == "qwen")
    return {
        "default_provider": settings.ai_provider_default,
        "failover_order": failover,
        "per_agent_override_count": len(overrides),
        "agents_routed_to_qwen": qwen_routed,
        "qwen_registered": True,
        "qwen_enabled": settings.qwen_enabled,
        "qwen_available": qwen_available,
        "qwen_base_url": settings.qwen_base_url,
        "qwen_models": {
            "flagship": settings.qwen_model_flagship,
            "workhorse": settings.qwen_model_workhorse,
            "batch": settings.qwen_model_batch,
            "embedding": settings.qwen_embedding_model,
        },
    }


def _boundary_resolution() -> dict:
    """Recompute the pin live: every human-facing agent routed to Qwen is forced
    back to Claude (leaked == 0 by construction), and Qwen-eligible agents do
    route to Qwen."""
    pinned: list[str] = []
    leaked: list[str] = []
    for a in sorted(boundary.HUMAN_FACING):
        if boundary.enforce_policy(a, "qwen") == boundary.CLAUDE_PROVIDER:
            pinned.append(a)
        else:
            leaked.append(a)
    eligible_routable = sum(
        1 for a in boundary.QWEN_ELIGIBLE if boundary.enforce_policy(a, "qwen") == "qwen"
    )
    return {
        "human_facing_pinned": len(pinned),
        "human_facing_leaked": len(leaked),
        "qwen_eligible_routable": eligible_routable,
        "leaked_agents": leaked,
    }


def _ai_turns_accepts_qwen() -> bool:
    """Introspect the live ai_turns provider CHECK — the audit gate that lets a
    Qwen-served processing call be recorded (and proves the boundary by absence
    on human-facing rows)."""
    from unipaith.models.ai_artifacts import AiTurn

    for c in AiTurn.__table__.constraints:
        if getattr(c, "name", "") == "ck_ai_turns_provider":
            return "qwen" in str(getattr(c, "sqltext", "")).lower()
    return False


def _l3_scoring() -> dict:
    from unipaith.services.matching import DEFAULT_WEIGHTS

    return {
        "weights": dict(DEFAULT_WEIGHTS),
        "weight_sum": round(sum(DEFAULT_WEIGHTS.values()), 4),
        "fairness_gated": settings.fairness_check_on_promotion,
        "fairness_max_disparity": settings.fairness_max_disparity,
    }


def _embeddings() -> dict:
    return {
        "provider": settings.embedding_provider,
        "live_model": settings.embedding_model,
        "live_dimension": settings.embedding_dimension,
        "qwen_model": settings.qwen_embedding_model,
        "matryoshka_target": 1536,
        "qwen_active": settings.embedding_provider == "qwen" and settings.qwen_enabled,
    }


def _config_knobs() -> list[dict]:
    return [
        {"name": "ai_provider_default", "value": settings.ai_provider_default, "section": "§4"},
        {
            "name": "ai_provider_failover_csv",
            "value": settings.ai_provider_failover_csv,
            "section": "§4",
        },
        {"name": "qwen_enabled", "value": settings.qwen_enabled, "section": "§10"},
        {"name": "embedding_provider", "value": settings.embedding_provider, "section": "§8"},
        {"name": "embedding_dimension", "value": settings.embedding_dimension, "section": "§8"},
        {
            "name": "ai_crawler_extraction_v2_enabled",
            "value": settings.ai_crawler_extraction_v2_enabled,
            "section": "§5",
        },
        {"name": "gpu_mode", "value": settings.gpu_mode, "section": "§10"},
        {
            "name": "fairness_check_on_promotion",
            "value": settings.fairness_check_on_promotion,
            "section": "§9 / 46",
        },
    ]


def build_ml_core(app_or_routes) -> dict:
    """Assemble the ``GET /build/ml-core`` payload. ``app_or_routes`` may be a
    FastAPI app or its ``.routes`` — boundary, routing, the audit gate and the L3
    weights all resolve live, so the page mirrors the deployed system."""
    routes = getattr(app_or_routes, "routes", app_or_routes)
    route_buckets = _route_buckets(list(routes))
    bsum = boundary.boundary_summary()
    routing = _provider_routing()
    resolution = _boundary_resolution()
    embeddings = _embeddings()
    l3 = _l3_scoring()
    config_knobs = _config_knobs()
    accepts_qwen = _ai_turns_accepts_qwen()

    roster = [dict(r) for r in boundary.MODEL_ROSTER]
    qwen_roster_rows = sum(1 for r in roster if r["provider"] == "qwen")
    claude_roster_rows = sum(1 for r in roster if r["provider"] == "anthropic")
    # Roster invariant: no human-facing roster row is served by Qwen.
    roster_boundary_ok = all(not (r["faces_human"] and r["provider"] == "qwen") for r in roster)

    def _cap(status: Status) -> int:
        return sum(1 for c in CAPABILITIES if c.status == status)

    def _acc(status: Status) -> int:
        return sum(1 for a in ACCEPTANCE if a.status == status)

    backing_route_count = sum(len(v) for v in route_buckets.values())

    return {
        "the_rule": dict(THE_RULE),
        "summary": {
            "boundary_intact": bsum["intact"],
            "human_facing_count": bsum["human_facing_count"],
            "qwen_eligible_count": bsum["qwen_eligible_count"],
            "qwen_first_batch_count": bsum["qwen_first_batch_count"],
            # The headline safety number — 0 human-facing agents the Qwen backend
            # may serve, recomputed live (not asserted).
            "human_facing_served_by_qwen": resolution["human_facing_leaked"],
            "human_facing_pinned": resolution["human_facing_pinned"],
            "qwen_eligible_routable": resolution["qwen_eligible_routable"],
            "qwen_registered": routing["qwen_registered"],
            "qwen_enabled": routing["qwen_enabled"],
            "qwen_available": routing["qwen_available"],
            "ai_turns_accepts_qwen": accepts_qwen,
            "default_provider": routing["default_provider"],
            "agents_routed_to_qwen_count": len(routing["agents_routed_to_qwen"]),
            "roster_row_count": len(roster),
            "roster_qwen_rows": qwen_roster_rows,
            "roster_claude_rows": claude_roster_rows,
            "roster_boundary_ok": roster_boundary_ok,
            "capability_count": len(CAPABILITIES),
            "capabilities_live": _cap("live"),
            "capabilities_partial": _cap("partial"),
            "capabilities_planned": _cap("planned"),
            "acceptance_count": len(ACCEPTANCE),
            "acceptance_live": _acc("live"),
            "acceptance_partial": _acc("partial"),
            "acceptance_planned": _acc("planned"),
            "pipeline_stage_count": len(PIPELINE_STAGES),
            "phase_count": len(PHASES),
            "slo_count": len(SLOS),
            "embedding_dimension": embeddings["live_dimension"],
            "embedding_provider": embeddings["provider"],
            "l3_weight_sum": l3["weight_sum"],
            "ai_route_count": len(route_buckets["ai"]),
            "backing_route_count": backing_route_count,
            "config_knob_count": len(config_knobs),
            "open_question_count": len(OPEN_QUESTIONS),
            "live_is_source_of_truth": True,
        },
        "boundary_columns": [dict(c) for c in BOUNDARY_COLUMNS],
        "boundary": {
            "human_facing": bsum["human_facing"],
            "qwen_eligible": bsum["qwen_eligible"],
            "qwen_first_batch": bsum["qwen_first_batch"],
            "leaked_agents": resolution["leaked_agents"],
            "ml_backend_providers": bsum["ml_backend_providers"],
            "claude_provider": bsum["claude_provider"],
        },
        "model_roster": roster,
        "provider_routing": routing,
        "pipeline": [{"n": s.n, "name": s.name, "detail": s.detail} for s in PIPELINE_STAGES],
        "embeddings": embeddings,
        "l3_scoring": l3,
        "capabilities": [
            {
                "key": c.key,
                "title": c.title,
                "section": c.section,
                "status": c.status,
                "blurb": c.blurb,
                "built": list(c.built),
                "planned": list(c.planned),
            }
            for c in CAPABILITIES
        ],
        "phases": [
            {"key": p.key, "title": p.title, "status": p.status, "detail": p.detail} for p in PHASES
        ],
        "acceptance": [{"status": a.status, "text": a.text} for a in ACCEPTANCE],
        "slos": [dict(s) for s in SLOS],
        "config_knobs": config_knobs,
        "routes": route_buckets,
        "open_questions": [dict(q) for q in OPEN_QUESTIONS],
    }

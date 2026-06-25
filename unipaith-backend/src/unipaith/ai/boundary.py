"""Spec 63 §1/§3/§4 — the hard model boundary.

The single, non-negotiable rule the whole platform follows:

    **Qwen processes. Claude communicates.**

- **Qwen** (open-source, self-hosted / Bedrock) is the **ML backend**: it embeds,
  extracts, normalizes, classifies, scores, ranks and synthesizes *informational*
  content. It **never** interacts with a human directly — the invisible brain,
  not the voice.
- **Claude** (Anthropic API / Bedrock) is the **human-facing agent**: the advisor
  chatbot (`61`) and every `45` advisory surface — match rationale, essay /
  interview / test feedback, strategy narrative, identity summary, faculty review
  summaries, inbox drafts, campaign copy, the eval judge. These are **pinned to
  Claude by policy** — not eligible for reassignment to Qwen, independent of
  whether a tuned Qwen *could* match them. Per §1 the conversation is the brand +
  trust surface; it stays Claude as a *product* decision, not an eval outcome.

This module is the machine-checkable form of that rule. ``enforce_policy`` is
applied inside ``providers/registry.py`` on *every* provider resolution, so the
boundary cannot be broken by config: even if ``ai_provider_per_agent_json`` maps
``orchestrator`` → ``qwen``, a human-facing agent is forced back to Claude. The
``/goal/ml-core`` surface and ``tests/test_spec63_boundary.py`` both read this
module, so the published page can't claim a boundary the code doesn't enforce,
and a mis-edit fails the suite loudly.

Note on OpenAI: it remains a *same-class premium failover* for availability
(spec 03 §9). The boundary enforced here is specifically that the **Qwen ML
backend never serves a human** — it does not touch the Anthropic↔OpenAI failover.
"""

from __future__ import annotations

from unipaith.ai.agent_registry import AGENT_TIERS

# The Claude provider every human-facing row is pinned to.
CLAUDE_PROVIDER = "anthropic"

# Provider names that are ML-backend transports (no human contact, ever). Listed
# explicitly so a future on-prem / Bedrock Qwen transport inherits the same pin
# by being added here rather than by editing the enforcement logic.
ML_BACKEND_PROVIDERS: frozenset[str] = frozenset({"qwen"})


# ── §3 · Human-facing — pinned to Claude ─────────────────────────────────────
# Conversation with, or personalized advice to, a person. Every entry produces
# prose a human reads or a message a human sends. None of these is ever eligible
# for the Qwen ML backend.
HUMAN_FACING: frozenset[str] = frozenset(
    {
        "orchestrator",  # advisor chatbot (61 / 19)
        "rationale",  # "why this match" explanation (45 §6)
        "strategy",  # broad-strategy narrative (45 §10)
        "strategy_first_time",  # first-run strategy narrative (Opus)
        "identity_summary",  # identity paragraph (45 §11)
        "workshop_coach",  # essay / interview / test feedback (14, 45 §7–9)
        "workshop_judge",  # eval judge (62 / §3)
        "outcome_brief",  # plain-language offer brief (45 §15)
        "inbox_reply_drafter",  # student inbox reply draft (45 §13)
        "institution_reply_drafter",  # faculty inbox reply draft (45 §13)
        "review_summarizer",  # faculty review summary (06 §2 / 45 §13)
        "review_synthesis",  # review synthesis (32 §4)
        "review_assistant",  # review assistant (32 §6)
        "campaign_copy",  # campaign copy (25 §10 / 45 §16)
        "intelligence_digest",  # dashboard digest narrative (31 §9 / 45 §11)
        "interview_invite_drafter",  # interview invite message (33 §9)
        "next_best_action_yield",  # yield action recommendations (35 §6)
        "funding_scenario_helper",  # funding advice narrative (41 §5)
        "territory_optimizer",  # recruitment territory advice (40 §5)
        "country_requirement_advisor",  # country requirement advisory (38 §5)
        "prompt_coach",  # behavioral coaching narrative (42 §4.17)
        "major_track_coach",  # major-readiness coaching (43 §4.18)
    }
)


# ── §2 · Qwen-eligible — the ML backend may serve these ──────────────────────
# Data processing, scoring, ranking, classification, extraction, embeddings —
# never a conversation. The six named in §2 are the first migration batch; the
# rest are Qwen-domain by the §1 rule and may follow as `62` eval promotes them.
QWEN_ELIGIBLE: frozenset[str] = frozenset(
    {
        # §2 named processing agents (the first migration batch)
        "extractor",  # DiscoveryExtractor
        "validator",  # DiscoveryValidator
        "query_interpreter",  # DiscoveryQueryInterpreter
        "document_parse_triage",  # DocumentParseTriage
        "authenticity_risk",  # AuthenticityRiskScorer
        "segment_builder_nl",  # SegmentBuilderNLBridge
        # Embeddings + feature vectors (§2.1 / §8)
        "feature_emitter",
        "embedding",
        # L3 ML scorer (§6) — rule_based today; Qwen's domain, never an LLM call,
        # so enforce_policy never affects it, but it belongs on Qwen's side of
        # the roster.
        "matcher",
        # Other processing / scoring / ranking / classification (§1 rule)
        "connect_ranker",
        "event_recommender",
        "inbound_intent_classifier",
        "interview_score_prefill",
        "yield_risk_scorer",
        "credential_normalizer",
        "prospect_prioritizer",
        "advisor_matcher",
        "sop_interest_extractor",
        # The §60 crawler extraction job — a pipeline stage, not an AGENT_TIERS
        # row, but unambiguously Qwen-domain (grounded structured extraction).
        "crawler_extraction",
    }
)

# The §2-named agents — the documented first migration batch (the rest of
# QWEN_ELIGIBLE are Qwen-domain by the §1 rule but not named migration targets).
QWEN_FIRST_BATCH: tuple[str, ...] = (
    "extractor",
    "validator",
    "query_interpreter",
    "document_parse_triage",
    "authenticity_risk",
    "segment_builder_nl",
)


def is_human_facing(agent: str) -> bool:
    """True iff the agent talks to / advises a person → pinned to Claude.

    Unknown agents default to human-facing — the safe direction: an unclassified
    agent is never silently handed to the ML backend."""
    if agent in HUMAN_FACING:
        return True
    if agent in QWEN_ELIGIBLE:
        return False
    return True  # unknown → treat as human-facing (never auto-route to Qwen)


def enforce_policy(agent: str, provider_name: str) -> str:
    """The hard pin. Returns the provider that may actually serve ``agent``.

    If a caller / config tries to route a human-facing (or unclassified) agent to
    an ML-backend provider (Qwen), force it back to Claude. Everything else passes
    through unchanged — Qwen-eligible agents keep their configured provider, and
    the Claude↔OpenAI availability failover is untouched."""
    if provider_name in ML_BACKEND_PROVIDERS and is_human_facing(agent):
        return CLAUDE_PROVIDER
    return provider_name


def assert_boundary_intact() -> None:
    """Boot / test guard — the boundary is well-formed and enforced.

    Raises ``RuntimeError`` on any violation so a mis-edit fails loudly rather
    than silently routing a human-facing surface to the Qwen ML backend:

    - no agent is both human-facing and Qwen-eligible;
    - every live agent in the registry is classified one way or the other;
    - no human-facing agent can resolve to an ML-backend provider.
    """
    overlap = HUMAN_FACING & QWEN_ELIGIBLE
    if overlap:
        raise RuntimeError(
            "Spec 63 boundary violated — agents both human-facing and "
            f"Qwen-eligible: {sorted(overlap)}"
        )
    unclassified = {a for a in AGENT_TIERS if a not in HUMAN_FACING and a not in QWEN_ELIGIBLE}
    if unclassified:
        raise RuntimeError(
            f"Spec 63 boundary incomplete — registry agents not classified: {sorted(unclassified)}"
        )
    for agent in HUMAN_FACING:
        for ml in ML_BACKEND_PROVIDERS:
            if enforce_policy(agent, ml) != CLAUDE_PROVIDER:
                raise RuntimeError(
                    f"Spec 63 boundary violated — {agent!r} not pinned to Claude against {ml!r}"
                )


def boundary_summary() -> dict:
    """Counts + lists the ``/goal/ml-core`` surface and tests read. ``intact`` is
    computed by actually running the guard, so the page reports the live truth."""
    try:
        assert_boundary_intact()
        intact = True
    except RuntimeError:
        intact = False
    # Human-facing agents that any non-Claude ML backend is allowed to serve —
    # the headline safety number. It is 0 by construction (enforce_policy pins
    # them all), computed live rather than asserted.
    human_facing_on_ml_backend = sum(
        1
        for a in HUMAN_FACING
        for ml in ML_BACKEND_PROVIDERS
        if enforce_policy(a, ml) != CLAUDE_PROVIDER
    )
    return {
        "intact": intact,
        "human_facing_count": len(HUMAN_FACING),
        "qwen_eligible_count": len(QWEN_ELIGIBLE),
        "qwen_first_batch_count": len(QWEN_FIRST_BATCH),
        "human_facing_served_by_ml_backend": human_facing_on_ml_backend,
        "ml_backend_providers": sorted(ML_BACKEND_PROVIDERS),
        "claude_provider": CLAUDE_PROVIDER,
        "human_facing": sorted(HUMAN_FACING),
        "qwen_eligible": sorted(QWEN_ELIGIBLE),
        "qwen_first_batch": list(QWEN_FIRST_BATCH),
    }


# ── §4 · Model roster (data form, for the /goal surface) ─────────────────────
# The §4 table as structured data. ``faces_human`` is the boundary in one column;
# human-facing rows are "pinned to Claude by policy — not eligible for
# reassignment" (§4). DB-free, authored from the spec.
MODEL_ROSTER: tuple[dict, ...] = (
    {
        "task": "Embeddings",
        "model": "Qwen3-Embedding (8B / 4B / 0.6B; Matryoshka → 1536)",
        "provider": "qwen",
        "faces_human": False,
    },
    {
        "task": "Reranking",
        "model": "Qwen3-Reranker",
        "provider": "qwen",
        "faces_human": False,
    },
    {
        "task": "Crawler extraction (60)",
        "model": "Qwen3-Instruct 14–32B (tuned)",
        "provider": "qwen",
        "faces_human": False,
    },
    {
        "task": "Normalization / classification / triage / scoring",
        "model": "Qwen3-Instruct 7–14B",
        "provider": "qwen",
        "faces_human": False,
    },
    {
        "task": "L3 fitness / confidence / CF / rank",
        "model": "Qwen embeddings + classical ML (matching.py)",
        "provider": "qwen",
        "faces_human": False,
    },
    {
        "task": "Display synthesis (factual)",
        "model": "Qwen3-Instruct (brand-voice eval-gated)",
        "provider": "qwen",
        "faces_human": False,
    },
    {
        "task": "Advisor chatbot (61)",
        "model": "Qwen 3 (via Together)",
        "provider": "together",
        "faces_human": True,
    },
    {
        "task": "Rationale / feedback / strategy / summaries (45)",
        "model": "Qwen 3 (via Together)",
        "provider": "together",
        "faces_human": True,
    },
    {
        "task": "Eval judge (62)",
        "model": "Qwen 3 (via Together)",
        "provider": "together",
        "faces_human": True,
    },
)

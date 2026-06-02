"""Spec 45 §20 / spec 06 §2 — agent → model-tier registry.

Single source of truth for which model tier each agent runs at. The
`AIClient` resolves the tier from the `model=` literal passed at the call
site; this registry documents the canonical mapping and is used by tests and
the admin cost dashboard to label spend per agent.

Tiers map to provider Protocol tiers (`ai/providers/base.py`):
  flagship  → Opus  (claude-opus-4-8)
  workhorse → Sonnet
  batch     → Haiku
  rule_based → no LLM (the L3 ML matcher's audit-ledger label)
"""

from __future__ import annotations

AGENT_TIERS: dict[str, str] = {
    # ── Discovery (L2) ──
    "orchestrator": "workhorse",
    "extractor": "batch",
    "validator": "batch",
    # ── Feature/embedding handoff (L2 → L3) ──
    "feature_emitter": "batch",
    "embedding": "batch",
    # ── Match rationale (L2) ──
    "rationale": "workhorse",
    # ── Strategy (L2) ── default workhorse; flagship on first-time gen ≥80% (45 §10)
    "strategy": "workhorse",
    "strategy_first_time": "flagship",
    # ── Identity (L2) ──
    "identity_summary": "batch",
    # ── Inbox reply drafter (L2) — spec 45 §13 ──
    "inbox_reply_drafter": "workhorse",
    # ── Workshops (L2) ──
    "workshop_coach": "workhorse",
    "workshop_judge": "batch",
    # ── Institution review (L2) — spec 06 §2 / spec 32 ──
    "review_summarizer": "flagship",  # DraftSummarizerForReview — Opus
    "authenticity_risk": "batch",  # AuthenticityRiskScorer — Haiku
    "review_synthesis": "workhorse",  # ReviewSynthesisAgent (32 §4) — Sonnet
    "review_assistant": "workhorse",  # ReviewAssistant (32 §6) — Sonnet
    # ── L3 ML scorer (not an LLM; labels the audit-ledger row) ──
    "matcher": "rule_based",
    # ── Discovery type-first program search (spec 10 §3 / 45 §12) ──
    "query_interpreter": "workhorse",
    # ── Connect feed (spec 20 §8) — cheap Haiku ranking, always falls back ──
    "connect_ranker": "batch",
    "event_recommender": "batch",
    # ── Campaign copy (spec 25 §10 / 45 §16) — Sonnet, template fallback ──
    "campaign_copy": "workhorse",
    # ── Data upload parse triage (spec 24 §9 / 45 §19) — Haiku, always falls back ──
    "document_parse_triage": "batch",
    # ── Audience segmentation NL bridge (spec 26 §6 / 45 §17) — Sonnet, keyword fallback ──
    "segment_builder_nl": "workhorse",
    # ── Institution messaging (spec 29 §8 / 45) — Haiku, always falls back ──
    "institution_reply_drafter": "batch",  # InstitutionReplyDrafter — per-thread reply
    "inbound_intent_classifier": "batch",  # InboundIntentClassifier — reason-code suggestion
    # ── Admissions-intake dashboard digest (spec 31 §9 / §11) — Sonnet, falls
    #    back to a rule-based narrator. 45 §11: migrated off GPT-4o to Claude. ──
    "intelligence_digest": "workhorse",
    # ── Interviews (spec 33 §9) — Haiku invite drafter + Sonnet score prefill ──
    "interview_invite_drafter": "batch",  # InterviewInviteDrafter — invite message
    "interview_score_prefill": "workhorse",  # InterviewScorePrefill — rubric prefill
    # ── Enrollment / yield (spec 35 §6) — both fall back to deterministic counts ──
    "yield_risk_scorer": "batch",  # YieldRiskScorer — per-admit confirm-probability (Haiku)
    "next_best_action_yield": "workhorse",  # NextBestActionForYield — ranked actions (Sonnet)
    # ── International admissions (spec 38 §5) — both Haiku, always fall back ──
    "credential_normalizer": "batch",  # CredentialNormalizer — foreign GPA → 4.0 scale
    "country_requirement_advisor": "batch",  # CountryRequirementAdvisor — country pack
    # ── Recruitment CRM (spec 40 §5) — both fall back to deterministic sorting ──
    "prospect_prioritizer": "batch",  # ProspectPrioritizer — apply-likelihood ranking (Haiku)
    # TerritoryOptimizer — high-yield school/fair suggestions (Sonnet).
    "territory_optimizer": "workhorse",
    # ── Graduate & PhD admissions (spec 41 §5) — all deterministic in MVP,
    #    always fall back. AdvisorMatcher embeds research-interest similarity
    #    (Haiku, future embedding cosine); SoPInterestExtractor extends 45
    #    extraction (Haiku); FundingScenarioHelper suggests viable funding mixes
    #    (Sonnet). ──
    "advisor_matcher": "batch",  # AdvisorMatcher — research-fit ranking
    "sop_interest_extractor": "batch",  # SoPInterestExtractor — SoP → interest tags
    "funding_scenario_helper": "workhorse",  # FundingScenarioHelper — over-commit + mixes
}


def tier_for(agent: str) -> str:
    """Canonical tier for an agent name; defaults to workhorse."""
    return AGENT_TIERS.get(agent, "workhorse")


def flagship_agents() -> list[str]:
    """Agents that run on Opus — used by the cost dashboard to spotlight the
    expensive tier (spec 06 §2: review summary is the headline Opus caller)."""
    return [a for a, t in AGENT_TIERS.items() if t == "flagship"]

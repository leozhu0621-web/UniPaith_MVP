# 03 · LLM Migration — OpenAI → Claude (Anthropic)

> Per-agent migration plan: which existing AI call sites move to which Claude model, how prompt caching is structured, what the env/infra changes are, how rule-based fallback is preserved, and how the audit ledger captures provider+model.
>
> Status: **draft v1.0** · 2026-05-29 · Used by every spec that has an AI integration section (10, 11, 12, 13, 15, 16, 17, 19, 1A, 1B, 22, 23, 24, 30, 31, 35, 40, 41, 42).

---

## 1. Why Claude

User directive (2026-05-29): "the LLM agent should be trained based on Claude." This aligns with the model-portability principle from the Master Paper procurement section: *"the AI layer is built to be model-portable: prompts, evaluation harnesses, and routing logic sit behind an internal interface so workloads can shift between providers — OpenAI, Anthropic, or open models served through Amazon Bedrock — as price, latency, and quality change, avoiding single-vendor lock-in on our largest variable cost."*

Why Claude specifically:
1. **Quality on long-context structured tasks.** Discovery transcripts, application packets, and review rationales are long. Sonnet 4.6 and Opus 4.7/4.8 handle 200K-token contexts with strong instruction adherence — better suited than GPT-4o for evidence-linked reasoning we emit to users.
2. **Prompt caching.** Anthropic's 5-minute cache TTL maps cleanly onto our session shape: long system prompt + long persona + short turn-by-turn user message. Cached system+persona dramatically cuts cost on repeat turns.
3. **Tool use + structured output.** Claude's tool-use is well-suited to our forced-tool-use pattern in `StrategyAgent` (already a forced-tool design per CLAUDE.md).
4. **Vendor diversification.** Per competitor analysis: Element451, Salesforce (Einstein Trust Layer), and Studyportals (Sophia on Bedrock) all run multi-provider; matching this is table stakes for procurement conversations with security-conscious institutions.
5. **No-training stance.** Anthropic's API defaults to **no model training on customer data**. The Master Paper's `consent.training` mask (Appendix A output) is enforceable at the provider boundary with no extra contractual work.

---

## 2. Model selection per workload tier

Use the most recent Claude family at all times. As of 2026-05-29:

| Tier | Model ID | Use |
|---|---|---|
| **Flagship** | `claude-opus-4-8` | High-stakes reasoning where quality > cost. Strategy generation, complex multi-source synthesis, the rare premium review pass. |
| **Workhorse** | `claude-sonnet-4-6` | Default for student-facing AI surfaces: discovery dialog, match rationale, workshop feedback, identity summarization, inbox-draft suggestions. |
| **Batch / extraction** | `claude-haiku-4-5-20251001` | High-volume, narrow-scope tasks: signal extraction from discovery messages, profile field normalization, document parse triage, embedding-precursor summaries. |

Decision rule:
- If the request is **user-blocking** and **single-shot**, use Sonnet.
- If the request is **multi-shot extraction over many records** (e.g., normalize 500 uploaded prospect rows), use Haiku.
- If the request is **the single defining moment** of a session (Strategy generation; final review summary at decision time), use Opus.

Never use a model older than 4.5. Re-evaluate the tier mapping each release.

---

## 3. Prompt caching strategy

Anthropic prompt cache TTL is **5 minutes** by default (`ephemeral`), or **1 hour** with `cache_control: {type: "ephemeral", ttl: "1h"}`. The cache breakpoint goes on the LAST cached block; everything before it gets cached.

Structure every multi-turn agent's prompt as:

```
1. System block        ← rarely changes;  cache  TTL: 1h
2. Persona block       ← per-user/session; cache TTL: 5min
3. Conversation tail   ← uncached
```

Examples:

### DiscoveryOrchestrator
```python
messages = [
  # System: assistant role + behavioral guardrails + output schema
  {"role": "system", "content": [
    {"type": "text", "text": SYSTEM_PROMPT},
    {"type": "text", "text": OUTPUT_SCHEMA_DOCS,
     "cache_control": {"type": "ephemeral", "ttl": "1h"}},  # ← cache breakpoint
  ]},
  # Persona: track (profile/goals/needs), layer (basic/personality/identity),
  #          student profile snapshot.
  {"role": "user", "content": [
    {"type": "text", "text": format_persona(session)},
    {"type": "text", "text": format_prior_turns_summary(session),
     "cache_control": {"type": "ephemeral"}},  # 5min — refreshes each new message
  ]},
  # Tail: the user's latest message — uncached
  {"role": "user", "content": latest_message_text},
]
```

### StrategyAgent
- System block cached at 1h: role + output JSON-tool schema + reasoning style + no-generation guardrail.
- Persona block cached at 5min: full profile + active goals + active needs + active strategy snapshot.
- Tail: the trigger ("Generate a new active strategy") — uncached.
- `tool_choice: {type: "tool", name: "emit_strategy"}` forces tool use.

### WorkshopCoach (essay/interview/test)
- System block cached at 1h: role + **schema-enforced no-generation rule** ("Do not produce a rewritten draft. Output only feedback signals.") + rubric definitions.
- Persona block cached at 5min: student profile + target program(s) + prior workshop runs.
- Tail: the artifact (essay text / interview answer / test response) — uncached.

### MatchRationaleAgent
- System block cached at 1h: role + rationale style + confidence-band conventions.
- Persona block cached at 5min: student profile + active strategy.
- Tail: the (program_card, fitness_score, confidence_score) tuple — uncached.
- **Cache key for response store**: `(profile_version, program_version)` per CLAUDE.md.

### DiscoveryExtractor (Haiku)
- System block cached at 1h: extraction prompt + JSON schema for `extracted_signals`.
- Persona block: minimal — just the layer (basic/personality/identity).
- Tail: the message text — uncached.
- Per-message; high volume; Haiku is the right tier.

### IdentitySummaryAgent (Haiku)
- System block cached at 1h: synthesis prompt + 3–5 sentence target + warm-but-direct tone.
- Persona block cached at 5min: structured identity layer (core_values / worldview / self_awareness).
- Tail: trigger phrase — uncached.

---

## 4. Agent-by-agent migration table

| # | Service file (current) | Current model | Target model | Tier | Notes |
|---|---|---|---|---|---|
| 1 | `services/discovery_service.py` (DiscoveryOrchestrator) | `gpt-4o` | `claude-sonnet-4-6` | Workhorse | 3-track journey; long persona; cache aggressively. |
| 2 | `services/discovery_service.py` (DiscoveryExtractor) | `gpt-4o-mini` | `claude-haiku-4-5-20251001` | Batch | One call per message; volume = O(messages). |
| 3 | `services/discovery_service.py` (DiscoveryValidator) | `gpt-4o-mini` | `claude-haiku-4-5-20251001` | Batch | Validates extractor output; cheap second-pass. |
| 4 | `services/discovery_service.py` (DiscoveryJudge) | `gpt-4o` | `claude-sonnet-4-6` | Workhorse | Decides next prompt vs handoff to recommendation. |
| 5 | `services/match_service.py` (RationaleAgent / A5) | `gpt-4o` | `claude-sonnet-4-6` | Workhorse | Per-program rationale + confidence narrative. Response cached by `(profile_v, program_v)`. |
| 6 | `services/workshop_feedback_service.py` (Essay) | `gpt-4o` | `claude-sonnet-4-6` | Workhorse | Feedback-only — guardrail blocks generation in system prompt AND output schema. |
| 7 | `services/workshop_feedback_service.py` (Interview) | `gpt-4o` | `claude-sonnet-4-6` | Workhorse | Practice-question generation IS allowed (the rule-based bank serves canned questions). Scoring a response is feedback-only. |
| 8 | `services/workshop_feedback_service.py` (Test) | `gpt-4o` | `claude-sonnet-4-6` | Workhorse | Guidance, not generation. |
| 9 | `services/strategy_service.py` (StrategyAgent / A6) | `gpt-4o` | `claude-sonnet-4-6` | Workhorse | Forced tool use; emits structured strategy. Use Opus for first-time strategy generation only when profile completeness is ≥ 80%. |
| 10 | `services/identity_service.py` (IdentitySummaryAgent) | `gpt-4o-mini` | `claude-haiku-4-5-20251001` | Batch | Synthesizes 3–5 sentence identity paragraph. On failure, preserve existing real summary. |

New agents to add (covered in `42-ai-agents-claude.md`):

| # | Future agent | Tier | Purpose |
|---|---|---|---|
| 11 | DiscoveryQueryInterpreter | Sonnet | Convert student-typed NL query → constraint chips for Discovery (spec `12`). |
| 12 | InboxReplyDrafter | Sonnet | Suggest a draft reply to admissions-officer threads. Human accepts/edits before send. |
| 13 | DraftSummarizerForReview | Opus | Per-application packet summary for institution reviewers (`31-review-workspace.md`). One Opus call per application; cached per `(profile_v, program_v, intake_id)`. |
| 14 | OutcomeBriefForOfferLetter | Sonnet | Plain-language brief on a decision/offer for students. |
| 15 | CampaignAudienceCopySuggester | Sonnet | Draft external email body/subject for institution Campaigns (`23`). |
| 16 | SegmentBuilderNLBridge | Sonnet | Convert "students who saved Engineering programs in California with budget ≤ $40k" → structured segment rules. |
| 17 | AuthenticityRiskScorer | Haiku | Flag essays with generic/over-optimized AI-generated patterns. Outputs to Appendix A "Authenticity risk flags". |
| 18 | DocumentParseTriage | Haiku | Triage uploaded transcript/portfolio docs to "looks ok / needs human review / parse failed". |

---

## 5. Provider abstraction

The existing codebase has agents wrapped behind feature flags (`ai_discovery_v2_enabled` etc.) and a service-level adapter. The migration adds a **provider** dimension to the existing tier dimension. Suggested location: `unipaith-backend/src/unipaith/services/ai/providers/`.

```python
# providers/base.py
class AIProvider(Protocol):
    name: str   # "openai" | "anthropic" | "bedrock"
    def chat(self, *, model: str, messages: list, tools: list | None,
             cache_control: dict | None) -> ChatResponse: ...

# providers/anthropic.py
class AnthropicProvider:
    def __init__(self, api_key, default_model_tier_map: dict[str, str]): ...
    def chat(self, ...): ...

# providers/__init__.py
def get_provider(name: str) -> AIProvider: ...
```

Routing decision (env-driven, hot-swappable):
```python
# config.py
AI_PROVIDER_DEFAULT: str = "anthropic"          # anthropic | openai | bedrock
AI_PROVIDER_PER_AGENT: dict[str, str] = {       # optional per-agent override
  "discovery_orchestrator": "anthropic",
  "match_rationale": "anthropic",
  # ...
}
```

Each service calls `get_provider(name).chat(...)`. The agent never knows the provider.

---

## 6. Environment variables

Add to `unipaith-backend/.env.example`:
```
ANTHROPIC_API_KEY=                          # required for Claude calls
AI_PROVIDER_DEFAULT=anthropic               # anthropic | openai | bedrock
ANTHROPIC_DEFAULT_FLAGSHIP=claude-opus-4-8
ANTHROPIC_DEFAULT_WORKHORSE=claude-sonnet-4-6
ANTHROPIC_DEFAULT_BATCH=claude-haiku-4-5-20251001
```

Keep `OPENAI_API_KEY` and the `gpt-4o*` model names as a parallel set — they remain valid fallbacks per the model-portability principle.

`AI_MOCK_MODE=true` continues to short-circuit every provider; tests do not call any provider in CI.

### Infra changes (`infra/ecs.tf` env block)
- Add `ANTHROPIC_API_KEY` from a new AWS Secrets Manager entry: `unipaith/production/anthropic`.
- Add `AI_PROVIDER_DEFAULT=anthropic`.
- Add the three default-model env vars (so model upgrades don't require a deploy — just a Secret update + task restart).
- Keep the existing OpenAI secret block in place. Remove only after Claude has soaked ≥ 1 release in prod and feedback signals are healthy.

---

## 7. Rule-based fallback (integration-test invariant)

Per `CLAUDE.md` `test_plan2_integration.py`: **every LLM agent must fall back to a rule-based path on failure (timeout, parse error, guardrail trip). The caller never sees a 5xx.**

The migration MUST preserve this. Behavior per agent:

- **DiscoveryOrchestrator fails** → return the next rule-based prompt from the layer's hardcoded prompt pool; mark turn `model_used: "rule_based"`.
- **DiscoveryExtractor fails** → store the raw message; set `extracted_signals: {}`; flag for retry next turn.
- **MatchRationaleAgent fails** → return the rule-based rationale string (deterministic template using `(top_3_matching_signal_categories)`).
- **WorkshopCoach fails** → return the rule-based rubric scores (zeros + a single "We couldn't analyze this draft in depth. Please retry." note in `structural_issues`). Never surface a 500.
- **StrategyAgent fails** → preserve the existing active strategy; show an inline "couldn't regenerate; showing your current strategy" banner.
- **IdentitySummaryAgent fails** → preserve the existing summary; do not overwrite with a stub.

The fallback path is **rule-based, not "use a different provider."** Provider failover is a separate concern (handled in §9 below).

---

## 8. Audit ledger — model identifier

Per Appendix A output schema: `audit ledger entry bundle (model version + timestamps)`. The migration **must record the provider too**:

```python
class AIAuditEntry(Base):
    id: UUID = primary_key
    agent_name: str           # "match_rationale", "discovery_orchestrator", ...
    provider: str             # "anthropic" | "openai" | "bedrock" | "rule_based"
    model_id: str             # "claude-opus-4-7", "gpt-4o-2024-08-06", "rule_v1"
    request_started_at: datetime
    request_completed_at: datetime
    input_tokens: int | None
    output_tokens: int | None
    cache_read_tokens: int | None    # Anthropic-only
    cache_write_tokens: int | None   # Anthropic-only
    cost_usd_estimated: numeric(10, 6) | None
    consent_mask: JSONB              # {matching, outreach, analytics, training}
    student_id: UUID | None          # nullable for batch jobs
    success: bool
    failure_reason: str | None       # parse_error | timeout | guardrail_trip | provider_5xx | rule_based_fallback
```

Every Claude call writes one row. Cost estimation uses the table in §10.

This ledger is the source for: cost dashboards, compliance audits, fairness/bias reporting (per `43-data-rights-privacy.md`), and per-cohort halt logic (per `43` §6).

---

## 9. Provider failover (separate from rule-based fallback)

When the configured provider 5xx's, the agent attempts ONE failover to the secondary provider before falling back to rule-based. Configuration:

```python
AI_PROVIDER_FAILOVER: list[str] = ["anthropic", "openai"]   # in order
AI_PROVIDER_FAILOVER_TIMEOUT_MS: int = 30000
```

Failover behavior:
- Try `anthropic` first (per `AI_PROVIDER_DEFAULT`).
- On timeout or `5xx`, try `openai` (or `bedrock`).
- If both fail, fall back to rule-based.
- **Each attempt is its own audit ledger row.** The student-visible response notes "showing rule-based result" only on the rule-based final path; failovers between LLM providers are invisible to the user.

---

## 10. Cost model

Per-token costs (USD, as of model-card prices for 4.6/4.7/4.8 family — verify quarterly):

| Model | Input ($/MTok) | Output ($/MTok) | Cache read ($/MTok) | Cache write ($/MTok) |
|---|---|---|---|---|
| `claude-opus-4-8` | 15.00 | 75.00 | 1.50 | 18.75 |
| `claude-sonnet-4-6` | 3.00 | 15.00 | 0.30 | 3.75 |
| `claude-haiku-4-5-20251001` | 0.80 | 4.00 | 0.08 | 1.00 |

(Caching breakpoints reduce input cost 10×; cache write is 1.25× input on first write.)

Estimated annual cost per paying student under typical use (Sonnet-heavy, ~25 discovery turns + ~10 match rationales + ~6 workshop feedback runs + ~3 strategy regenerations + ~50 inbox draft suggestions):
- Input: ~250K tokens (50% cached) → $0.40
- Output: ~80K tokens → $1.20
- **≈ $1.60 per paying student/year on Sonnet** vs. $1.82 budgeted for GPT-4o in the Master Paper financial model.

Institution-side per-applicant cost (one DraftSummarizerForReview on Opus + a few Sonnet workshop reviews):
- ~30K input + 8K output on Opus → $0.60 + $0.60 = $1.20 budget vs. $1.20 Master Paper budget.

The Sonnet-default routing keeps us at or under the Master Paper cost budget. Opus is used sparingly and reserved for the cohort review summary.

---

## 11. Consent enforcement at the call site

Every Claude call resolves the student's `consent_mask` BEFORE making the request:

```python
mask = consent_service.get_mask(student_id)
if not mask.get("matching") and agent.is_matching_related:
    return rule_based_fallback(agent, "consent_matching_denied")
if not mask.get("training"):
    # Anthropic doesn't train on customer data by default, but if we ever
    # used a fine-tuning pathway, this is the gate.
    fine_tune_eligible = False
```

The `consent_mask` itself is recorded in the audit ledger row (§8) so a compliance audit can verify every call respected the active consent state at request time.

### What "training" consent means for Claude calls
- Anthropic's standard commercial API does not train on customer prompts. **Therefore `consent.training=false` does NOT block a Claude call.**
- It DOES block: (a) including the student's data in any retrieval-augmented fine-tuning corpus we maintain, (b) including the student's data in evaluation set exports, (c) using the student's data to retrain rule-based weights.

---

## 12. Cache invalidation rules

Response caches (the `(profile_version, program_version)` cache on MatchRationaleAgent and the analogous caches on other agents) must invalidate when:
- The student's profile version increments (any profile-section edit).
- The program version increments (institution edit on a published program).
- The student's `consent_mask` changes (so an opt-out forces a re-derivation).
- The active model ID changes (model upgrade should force re-evaluation; old rationales remain in the audit ledger but the surfaced rationale is fresh).
- The active prompt version changes (prompt iterations stored in `42-ai-agents-claude.md` and version-tagged in code).

---

## 13. Migration sequencing

The migration order is intentionally **least-risky → highest-stakes**:

1. **Add Anthropic provider + env wiring + ledger schema.** No agent calls Claude yet. Tests cover the provider in isolation.
2. **Port DiscoveryExtractor (Haiku).** Lowest stakes — one record at a time, easy to roll back. Confirms ledger writes and cache stats look right.
3. **Port DiscoveryOrchestrator (Sonnet).** Now the student-facing chat is on Claude. Soak in dev → staging → prod-canary.
4. **Port IdentitySummaryAgent (Haiku) + MatchRationaleAgent (Sonnet).** These are non-blocking renders — failure shows the existing value.
5. **Port WorkshopCoach trio (Sonnet).** Customer-facing feedback; needs the guardrail and the rule-based fallback to be airtight first.
6. **Port StrategyAgent (Sonnet).** Highest user-visible impact — wait until match rationale has soaked.
7. **Add new agents** (§4 future agents) one by one as their feature specs land.

Each step ships behind the existing feature flags. Per-agent flag values flip from "v2 OpenAI" to "v2 Claude" by env, not by code change.

---

## 14. Compliance checklist (per Claude integration)

- [ ] Provider selected via `AI_PROVIDER_DEFAULT` (or per-agent override) — never hardcoded.
- [ ] System block cached at 1h; persona at 5min; tail uncached.
- [ ] `consent_mask` resolved before the call; ledger row records it.
- [ ] Audit ledger row written with `provider`, `model_id`, token counts, success/failure.
- [ ] Rule-based fallback registered and unit-tested.
- [ ] On timeout, agent retries via `AI_PROVIDER_FAILOVER` once before fallback.
- [ ] No model ID is older than the most recent 4.x release (revisit quarterly).
- [ ] Output schema validation runs; on parse failure, agent retries once, then falls back.
- [ ] `AI_MOCK_MODE=true` short-circuits the call before any network IO.
- [ ] Tokens/cost reported to the cost dashboard; per-student running total available for cost-investigation queries.

---

## 15. Open questions / known gaps

- **Bedrock as a third provider.** Studyportals demonstrates the appeal. Adding Bedrock at MVP is yak-shaving; defer until: (a) an institution requests data residency that Anthropic direct can't provide, OR (b) cost difference exceeds 15%.
- **Per-institution model isolation.** If a partner institution demands that THEIR data never touches the multi-tenant cache, we'd need per-tenant cache keys and possibly a per-tenant Claude-on-Bedrock account. Spec'd in `43-data-rights-privacy.md`.
- **Fine-tuning Claude on permissioned partner data.** The "compounding loop" pitch from the Master Paper (more participation → better models). Anthropic supports fine-tuning via Bedrock for some models. Defer until Year 2; not in MVP scope.
- **Latency budget.** Have not measured Claude P95 from us-east-1 vs. OpenAI. Action: add a `/health/ai` probe that pings each provider with a stock prompt every 5 min and emits latency metrics.
- **Streaming.** The current code path is non-streaming for most agents. Discovery chat would feel substantially better streamed (Anthropic supports SSE streaming). Capture as a Phase 2 optimization for DiscoveryOrchestrator.

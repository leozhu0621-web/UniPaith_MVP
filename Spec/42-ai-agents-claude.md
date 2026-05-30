# 42 · AI Agents — Per-Agent Prompts & Behavior

> The full agent inventory: existing + planned, with per-agent system prompts, persona blocks, tool schemas, cache strategy, fallback behavior, and output validation. Depends on `03-llm-claude-migration.md` for the provider abstraction and `40-prompt-library-schema.md` for the signal schema each agent reads/writes.
>
> Status: **draft v1.0** · 2026-05-29.

---

## 1. Common agent contract

Every agent implements:

```python
class Agent(Protocol):
    name: str                             # snake_case, e.g. "discovery_orchestrator"
    model_tier: Literal["flagship", "workhorse", "batch"]
    consent_required: list[str]           # e.g. ["matching"], ["matching", "analytics"]
    output_schema: type[BaseModel]

    def system_prompt(self) -> list[ContentBlock]: ...   # cached 1h
    def persona_prompt(self, ctx: AgentContext) -> list[ContentBlock]: ...  # cached 5min
    def user_prompt(self, ctx: AgentContext) -> str: ...  # uncached
    def tools(self) -> list[ToolDef] | None: ...
    def fallback(self, ctx: AgentContext, reason: str) -> output_schema: ...
    def validate(self, raw_output: dict) -> output_schema: ...   # may raise
```

Calling pattern:
```python
result = provider.chat(
    model=resolve_model(agent.model_tier),
    messages=[
        {"role": "system", "content": agent.system_prompt()},
        {"role": "user", "content": [
            *agent.persona_prompt(ctx),
            {"type": "text", "text": agent.user_prompt(ctx)}
        ]}
    ],
    tools=agent.tools(),
)
output = agent.validate(result.json)
```

On failure: `output = agent.fallback(ctx, reason)`. Audit ledger row written either way per `03` §8.

---

## 2. DiscoveryOrchestrator

**Purpose:** Decide the next question to ask in a Stage-1 discovery session. One call per student turn.

**Tier:** Workhorse (Sonnet).
**Consent:** `["matching"]`.
**Input:** `DiscoverySession + last 10 messages + extracted_signals + active layer`.
**Output:** `{next_prompt: str, suggested_options: list[str] | null, should_handoff: bool, handoff_target: enum | null}`.

**System prompt sketch:**
```
You are UniPaith's discovery coach. You guide a student through one of three
tracks (profile / goals / needs) and one of three layers (basic / personality
/ identity) for the profile track. Your job is to ask the next single best
question — never multiple — that will surface the highest-value missing
signal in this layer.

CONSTRAINTS:
- Conversational, warm, plain. Never list-form. Max 2 sentences.
- Never request the same field twice in a row.
- Never ask for sensitive identity unless layer >= personality AND consent.
- If the layer's completeness >= 80%, set should_handoff=true.
- Output JSON matching the schema.
```

**Persona prompt:** `format(track, layer, profile_snapshot, extracted_signals, last_10_turns)`.

**Tools:** none. JSON-mode output.

**Fallback:** rule-based next-prompt from a static pool keyed on `(track, layer, missing_category)`.

**Done well when:** the next question hits a missing signal category 80% of the time AND the student typically replies with a usable answer (validated by DiscoveryExtractor confidence ≥ 70).

---

## 3. DiscoveryExtractor

**Purpose:** Extract structured signals from a student's natural-language turn.

**Tier:** Batch (Haiku).
**Consent:** `["matching"]`.
**Input:** `message_text + active_layer`.
**Output:** `{extracted_signals: dict[field_name → {value, confidence}]}` matching subset of `40-prompt-library-schema.md` §3 fields.

**System prompt sketch:**
```
You extract structured signals from a student's message. Output ONLY the JSON
object matching the schema — no prose.

Rules:
- Only extract fields explicitly stated or strongly implied.
- Each extracted value has a confidence 0-100 (your honest estimate of how
  certain you are the student said this).
- Never invent. If unsure, omit.
- Use the canonical enum values where applicable.
```

**Tools:** none. JSON-mode.

**Fallback:** return `{}`. Worst case: the orchestrator re-asks next turn.

---

## 4. DiscoveryValidator

**Purpose:** Quick sanity check on extractor output before write.

**Tier:** Batch (Haiku).
**Output:** `{accepted: list[field_name], rejected: list[{field, reason}]}`.

Fast second pass. Rejects fields where confidence < 60 OR value violates enum constraints.

**Fallback:** accept everything from extractor.

---

## 5. DiscoveryJudge

**Purpose:** Decide if the session should end / hand off.

**Tier:** Workhorse (Sonnet).
**Output:** `{action: "continue" | "switch_layer" | "switch_track" | "handoff_to_recommendation", reason: str}`.

Run every 3–5 turns. The orchestrator can also self-elect handoff (see §2), but the judge has the explicit responsibility.

**Fallback:** rule-based — if `completeness ≥ 80` then `switch_layer` or `handoff`.

---

## 6. MatchRationaleAgent (A5)

**Purpose:** Generate plain-language "why this program" rationale for a specific (student, program) pair.

**Tier:** Workhorse (Sonnet).
**Consent:** `["matching"]`.
**Input:** `student_profile + active_strategy + program_card + fitness_score + confidence_score + matching_signals`.
**Output:** `{rationale: str (≤ 80 words), strengths: list[{label, evidence}] (1-4), tradeoffs: list[{label, why}] (0-3)}`.

**System prompt sketch:**
```
You explain why a program was recommended to a student. Plain language.
Evidence-linked: every strength references a specific student signal.

CONSTRAINTS:
- 80 words max for the main rationale.
- Strengths: 1–4 bullets, each referencing a specific profile signal.
- Tradeoffs: 0–3 bullets when the program is strong on one axis but weak on
  another (e.g., "strong outcomes but higher cost").
- Never invent program facts. Use only fields provided in the program_card.
- Never invent student facts. Use only fields in profile/strategy.
```

**Tools:** none.

**Cache key for response store:** `(profile_version, program_version, model_id)` per CLAUDE.md.

**Fallback:** template — "This program matches your stated interest in {top_match_field} and your {budget_band} budget constraint."

---

## 7. WorkshopCoach (Essay variant)

**Purpose:** Feedback-only essay analysis.

**Tier:** Workhorse (Sonnet).
**Consent:** `["matching"]`.
**Input:** `essay_text + prompt + target_program_id + student_profile + rubric_id`.
**Output:** schema-enforced `{rubric_scores: dict, structural_issues: list[{severity, location, issue}], missing_elements: list[{importance, suggestion}]}`.

**THE invariant:** the output schema **mechanically excludes any field that could carry a generated essay or model answer.** Test: `tests/test_workshop_no_generation_contract.py`. See `16-workshops.md`.

**System prompt sketch:**
```
You give feedback on a student's essay draft. You DO NOT rewrite, rephrase,
or produce a model answer.

OUTPUT shape (JSON):
- rubric_scores: dict of rubric criterion → 0-5
- structural_issues: list of {severity: low|med|high, location, issue}
- missing_elements: list of {importance: low|med|high, suggestion}

CONSTRAINTS:
- Never include suggested replacement text > 12 words. If you would, surface
  the issue and leave repair to the student.
- Never produce paragraph-level rewrites.
- Reference the prompt explicitly.
```

**Tools:** none.

**Fallback:** rubric scores of 0; one `structural_issues` entry "We couldn't analyze this draft in depth. Please retry." Never 5xx.

---

## 8. WorkshopCoach (Interview variant)

**Purpose:** Two modes.
1. **Generate practice questions** — allowed (these are coach questions, not student answers).
2. **Score a student's recorded response** — feedback-only.

**Tier:** Workhorse (Sonnet).
**Output (mode 1):** `{questions: list[{question, why, type, difficulty}]}`.
**Output (mode 2):** `{rubric_scores, structural_issues, missing_elements, suggested_questions_to_practice}`.

**Fallback (mode 1):** rule-based question bank (`services/workshop_feedback_service.py` already has this). **Fallback (mode 2):** zeros + retry note.

---

## 9. WorkshopCoach (Test variant)

**Purpose:** Test-prep guidance — feedback on practice attempts, study-plan suggestions.

**Tier:** Workhorse (Sonnet).
**Output:** `{current_band, target_band, gap_analysis: list[{topic, recommendation}], prep_recommendations: list[{action, time_commitment, priority}]}`.

**Fallback:** rule-based band classification + canned recommendations.

---

## 10. StrategyAgent (A6)

**Purpose:** Generate the active broad strategy: career path → degree path → academic / financial / geographic narrative.

**Tier:** Workhorse (Sonnet) by default; Flagship (Opus) for first-time generation when profile completeness ≥ 80%.
**Consent:** `["matching"]`.
**Input:** `full_profile + all_goals + all_needs + prior_strategy_versions`.
**Output (forced tool):** `emit_strategy(career_path: str, degree_path: str, academic_strategy: text, financial_strategy: text, geographic_strategy: text, narrative_paragraphs: list[str] (exactly 4))`.

**System prompt sketch:**
```
You produce a UniPaith broad strategy. Use the emit_strategy tool — never
free-text.

The strategy answers: given this student's profile, goals, needs, and constraints,
what is the broad direction in (a) career path, (b) degree path, (c) academic
strategy, (d) financial strategy, (e) geographic strategy, and (f) a 4-paragraph
narrative the student can read as one cohesive plan?

CONSTRAINTS:
- Reference specific profile signals; never speculate.
- 4 paragraphs total, ≤ 120 words each.
- If signals conflict (e.g., goal=top-tier-research, budget=tight), state the
  tradeoff and recommend a path.
- Never recommend a program by name. That's the Match layer's job.
```

**Tool:** `emit_strategy` with strict JSON schema.

**Fallback:** preserve existing active strategy + show "couldn't regenerate" banner.

---

## 11. IdentitySummaryAgent

**Purpose:** Synthesize a 3–5 sentence identity paragraph from the structured identity layer (core_values / worldview / self_awareness JSONB).

**Tier:** Batch (Haiku).
**Consent:** `["matching"]`.
**Input:** `identity_layer_struct`.
**Output:** `{summary: str (3-5 sentences), tone: enum}`.

**Fallback:** preserve existing real summary if present; else "We're building your identity profile. Add to your core values and worldview to see a summary here."

---

## 12. DiscoveryQueryInterpreter (NEW)

**Purpose:** Convert a natural-language search query to structured constraint chips.

**Tier:** Workhorse (Sonnet).
**Consent:** `["matching"]`.
**Input:** `query_text + student_profile_summary (for context)`.
**Output:** `{constraints: list[{category, value, display, confidence}]}` where category ∈ enum like `degree_level | major | location | budget | format | start_term | duration | selectivity | other`.

**System prompt sketch:**
```
You parse a student's natural-language program search into structured
constraint chips that can each be edited or removed individually.

Output a list of constraints. Each constraint has:
- category (one of: degree_level, major, location, budget, format,
  start_term, duration, selectivity, other)
- value (the canonical value, e.g., "master's", "California", "<=50000")
- display (the short human label, e.g., "Master's", "California", "≤ $50k/yr")
- confidence (0–100, how sure you are this was what the student meant)

CONSTRAINTS:
- Each chip is one fact. Never combine ("MS in CS in California" → 2 chips).
- If ambiguous, output the most likely interpretation with confidence < 70 so
  the user gets prompted to confirm.
- The "other" category is a free-text catch-all for things like "research-heavy"
  — use sparingly.
```

**Tools:** none. JSON-mode.

**Fallback:** keyword extraction via the existing rule-based NLP service.

---

## 13. InboxReplyDrafter (NEW)

**Purpose:** Suggest a draft reply to a student inbox thread.

**Tier:** Workhorse (Sonnet).
**Input:** `thread_messages + application_context + student_profile`.
**Output:** `{draft: str, tone: enum, length: enum, alternate_drafts: list[str] (max 2)}`.

The student edits before sending. Drafts are never sent automatically.

**Fallback:** empty draft. Student types from scratch.

---

## 14. DraftSummarizerForReview (NEW, Opus)

**Purpose:** Per-application packet summary for institution reviewers.

**Tier:** Flagship (Opus). One call per applicant per intake — high-stakes single-shot.
**Consent:** `["matching"]`.
**Input:** `full_application_packet + program_requirements + rubric`.
**Output:** `{summary: text<long>, signal_strengths: list[{signal, evidence}] (3-5), signal_weaknesses: list[{signal, hint}] (0-5), rubric_aligned_notes: dict[rubric_criterion → note]}`.

**Cache key:** `(profile_version, program_version, intake_id)`.

**Fallback:** template-based summary from rule-based extraction.

---

## 15. OutcomeBriefForOfferLetter (NEW)

**Purpose:** Convert an offer letter into plain-language student-readable brief.

**Tier:** Workhorse (Sonnet).
**Input:** `offer_letter_text + student_locale`.
**Output:** `{key_terms: list[{label, value, explanation}], deadlines: list[{label, date, days_remaining}], next_steps: list[{action, by_date}], plain_language_summary: str (4-6 sentences)}`.

**Fallback:** extract key dates via regex; surface raw text.

---

## 16. CampaignAudienceCopySuggester (NEW)

**Purpose:** Draft external email body/subject for institution Campaigns.

**Tier:** Workhorse (Sonnet).
**Input:** `audience_segment_summary + campaign_objective + institution_voice_brief + cta`.
**Output:** `{subject: str, body: text, alternate_subjects: list[str] (max 3), preview_text: str}`.

**Fallback:** template stub keyed on objective.

---

## 17. SegmentBuilderNLBridge (NEW)

**Purpose:** Convert natural-language segment description to structured rules.

**Tier:** Workhorse (Sonnet).
**Input:** `natural_language_segment_description + available_signal_dictionary`.
**Output:** `{rules: list[{field, operator, value}], confidence_overall: int (0-100), ambiguity_notes: list[str]}`.

**Example:** "students who saved Engineering programs in California with budget ≤ $40k" →
```json
{
  "rules": [
    {"field": "saved_programs.major", "operator": "in", "value": ["engineering"]},
    {"field": "saved_programs.location.region", "operator": "==", "value": "California"},
    {"field": "budget_band_annual_total", "operator": "<=", "value": "40-60k"}
  ],
  "confidence_overall": 85
}
```

**Fallback:** keyword parser.

---

## 18. AuthenticityRiskScorer (NEW, Haiku)

**Purpose:** Flag essays whose patterns match common AI-generated structures (per Common App fraud policy and the Master Paper "Authenticity risk flags").

**Tier:** Batch (Haiku).
**Input:** `essay_text + comparison_corpus_summary`.
**Output:** `{risk_band: enum<low|medium|high>, signals: list[enum<generic_opener|overuse_of_em_dashes|over_optimized_thesis|unsupported_specifics|...>], confidence: int}`.

The signal does not auto-flag; an integrity signal is created with the same `confidence`, and the institution's `integrity_signals` workflow surfaces it for human review.

**Fallback:** `{risk_band: "low", signals: [], confidence: 0}`. Better silent than false-positive.

---

## 19. DocumentParseTriage (NEW, Haiku)

**Purpose:** Triage uploaded transcript / portfolio / supplement doc to "looks ok / needs human review / parse failed".

**Tier:** Batch (Haiku).
**Input:** `document_metadata + first_pages_text`.
**Output:** `{triage: enum<ok|needs_review|failed>, reason: str, suggested_action: enum<accept|request_clarification|reject>}`.

**Fallback:** `{triage: "needs_review", reason: "Could not analyze", suggested_action: "request_clarification"}`.

---

## 20. Agent registry / config table

```python
AGENT_REGISTRY = {
    "discovery_orchestrator":      ("workhorse", DiscoveryOrchestrator),
    "discovery_extractor":         ("batch",     DiscoveryExtractor),
    "discovery_validator":         ("batch",     DiscoveryValidator),
    "discovery_judge":             ("workhorse", DiscoveryJudge),
    "discovery_query_interpreter": ("workhorse", DiscoveryQueryInterpreter),
    "match_rationale":             ("workhorse", MatchRationaleAgent),
    "workshop_essay":              ("workhorse", WorkshopEssayCoach),
    "workshop_interview_practice": ("workhorse", WorkshopInterviewCoach),
    "workshop_interview_score":    ("workhorse", WorkshopInterviewCoach),
    "workshop_test":               ("workhorse", WorkshopTestCoach),
    "strategy":                    ("workhorse", StrategyAgent),
    "strategy_first_time":         ("flagship",  StrategyAgent),
    "identity_summary":            ("batch",     IdentitySummaryAgent),
    "inbox_reply_drafter":         ("workhorse", InboxReplyDrafter),
    "review_summarizer":           ("flagship",  DraftSummarizerForReview),
    "offer_brief":                 ("workhorse", OutcomeBriefForOfferLetter),
    "campaign_copy":               ("workhorse", CampaignAudienceCopySuggester),
    "segment_builder_nl":          ("workhorse", SegmentBuilderNLBridge),
    "authenticity_risk":           ("batch",     AuthenticityRiskScorer),
    "doc_parse_triage":            ("batch",     DocumentParseTriage),
}
```

Env override (per `03` §6): `AI_PROVIDER_PER_AGENT={...}` JSON.

---

## 21. Prompt versioning

Each agent's system prompt is version-tagged in code:

```python
class MatchRationaleAgent:
    PROMPT_VERSION = "v3"
    SYSTEM_PROMPT_V3 = "..."
```

Prompt version is written to `ai_artifacts.prompt_version`. Prompt changes trigger cache invalidation (per `03` §12).

A `prompts/` directory stores the historical prompts so behavior diffs across versions can be reproduced.

---

## 22. Output schema validation

Every agent's output is validated by Pydantic v2. On `ValidationError`:
1. Log the raw output to the audit ledger (`failure_reason="parse_error"`).
2. Retry once with a stricter "RESPOND ONLY IN JSON" reminder appended to the user message.
3. If second attempt fails, fall back per agent's fallback contract.

---

## 23. Tool use vs JSON mode

- Use **tool use** when the output IS the action (StrategyAgent emits via `emit_strategy` tool because the agent's behavior is to produce a strategy artifact, not to chat).
- Use **JSON mode** when the output is data the caller consumes (everyone else).

Tool use is preferred when the structure is complex (multiple nested fields) because Claude's tool-use type-checking is stricter than JSON mode.

---

## 24. Cache breakpoints — concrete mapping

| Agent | System block cached (1h)? | Persona block cached (5min)? | Notes |
|---|---|---|---|
| discovery_orchestrator | yes | yes | persona = profile + extracted_signals |
| discovery_extractor | yes | no | persona is tiny — just `active_layer` |
| discovery_validator | yes | no | extractor result is the user msg |
| discovery_judge | yes | yes | persona = session metadata |
| discovery_query_interpreter | yes | no | persona is the profile summary (small) — could cache if frequent |
| match_rationale | yes | yes | persona = profile + active strategy; per (profile_v, program_v) response cache |
| workshop_essay / interview / test | yes | yes | persona = profile + target program |
| strategy | yes | yes | persona = profile + goals + needs |
| identity_summary | yes | yes | persona = identity layer struct |
| inbox_reply_drafter | yes | yes | persona = thread + application |
| review_summarizer | yes | yes | persona = full packet — heavy; Opus benefits most from caching |
| offer_brief | yes | no | each offer is a one-shot |
| campaign_copy | yes | yes | persona = institution voice brief |
| segment_builder_nl | yes | no | signal dictionary in system; user msg is the NL desc |
| authenticity_risk | yes | no | per-essay one-shot |
| doc_parse_triage | yes | no | per-doc one-shot |

---

## 25. Streaming

Default: non-streaming.

Stream when:
- **DiscoveryOrchestrator** — chat feel benefits from streaming. Add SSE to `POST /me/discovery/sessions/:id/messages` in Phase 14.
- **WorkshopEssayCoach** — long structured output; streaming improves perceived latency. Optional.

Never stream:
- StrategyAgent (forced tool use; tool calls are atomic).
- Any agent feeding a structured chart, table, or list rendering.

---

## 26. Fallback decision flow

```
Provider error?
  ├── 5xx or timeout → try AI_PROVIDER_FAILOVER[next]
  │     └── failover succeeds → return result (record both attempts in ledger)
  │     └── failover fails    → rule-based fallback
  └── 4xx (rate limit, bad request) → retry once, then rule-based fallback

Validation error?
  └── retry once with JSON reminder → rule-based fallback

Guardrail trip (e.g., Workshop tries to generate)?
  └── rule-based fallback immediately (no retry)
```

---

## 27. Open questions / known gaps

- **Streaming for `inbox_reply_drafter`** — drafts appearing in real time would feel natural. Defer.
- **Multi-step reasoning agents.** None of the above use multi-step reasoning (ReAct-style). For institution-side `review_summarizer`, an Opus run that retrieves additional context (similar applicants, cohort averages) could improve quality at higher cost. Spec'd separately if needed.
- **Persona reuse across agents.** The profile summary is recomputed per agent call. Suggest a `student_persona_snapshot` cache keyed on `profile_version` that all persona-block builders consume.
- **Per-institution fine-tuning of `review_summarizer`.** Institution-specific rubric vocabulary differs (e.g., "fit" means different things at different schools). Per-tenant prompt overlay would improve quality.
- **Multilingual.** All agents currently English. Add `output_language` parameter; switch system prompts; verify Claude multilingual quality for top 5 markets (Mandarin, Hindi, Spanish, Korean, Arabic).

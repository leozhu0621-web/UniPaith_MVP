# Uni as a Managed Agent on the Claude Platform — Design

**Date:** 2026-06-10
**Status:** Approved (design); implementation plan to follow.
**Author:** Brainstormed with the founder; service surface verified against live code.

> **One-line:** Replace the in-app `orchestrator.py` conversation brain with **Uni, a managed agent on the Claude platform** (platform.claude.com). Claude *is* Uni's brain; the FastAPI backend becomes a thin **host** that relays the conversation and answers Uni's tool calls against RDS. Hard cutover.

---

## Decisions locked (the four forks)

| Fork | Decision |
|---|---|
| **Role of the managed agent** | **Replace** the in-app Uni. The managed agent is production. |
| **Data access** | **Host-side custom tools.** Claude's reasoning + UniPaith's tools/data. The DB never enters Anthropic's container. |
| **Rollout** | **Hard cutover.** Managed agent is the only path; `orchestrator.py` retires as the brain. A thin graceful-degradation envelope (retry + friendly message) replaces the rule-based fallback. |
| **Where Uni's brain runs** | **On the Claude platform** (Managed Agents). Console sessions, observability, automatic compaction, versioned configs. |

**"Train" means *configure*, not ML-train.** A Claude agent is improved by iterating its system prompt, tools, model/effort, and eval suite — not by training weights.

---

## Context: why this is a re-plumb, not a greenfield build

Uni already runs **live** as an in-app orchestrator:
- `orchestrator.py` (persona + Profile→Goals→Needs staging),
- the discovery service + extractor + validators + judge,
- the #368 knowledge-grounding (`services/uni_knowledge.py` → `search_programs`),
- the matches handoff, strategy agent, and feature flags.

Everything that makes Uni *Uni* gets re-expressed as the managed agent's **system prompt + tools**. The data model, matching engine, extractor schema, validators, and strategy generator **stay** in the backend and are reused by the host. Only the **conversation orchestration** moves to the platform.

### Architecture

```
Student (React SPA, UniConversation)
        │  message in / SSE stream out
        ▼
FastAPI HOST  (services/uni_agent_host.py)
  • resolves student → discovery_session → agent_session_id
  • stream-first turn loop against the Anthropic Session
  • answers agent.custom_tool_use by calling existing services (RDS, in VPC)
  • mirrors transcript to discovery_messages; graceful-degradation envelope
        │  events.send / events.stream  (Anthropic API key, host-side)
        ▼
Anthropic Managed Agent  "Uni — UniPaith Counselor"
  • Claude Opus 4.8 = the conversation brain (the agent loop runs here)
  • system prompt (persona + playbook) + 5 host-side custom tools
  • Cloud env "UniPaith_MVP"; agent_toolset DISABLED (no bash/files/web)
```

The DB and PII never leave the VPC — tools execute on the host, results return via `user.custom_tool_result`.

---

## Section A — Who Uni is (persona + system prompt)

**Agent name:** `Uni — UniPaith Counselor`

**Description (Console one-liner):**
> Warm, knowledgeable college-admissions counselor. Leads each student through a guided Discovery → Recommendation → Application journey, grounds every claim in UniPaith's real program catalog, remembers what she learns, and hands off to a personalized first look at matches. Never sounds like a search engine.

**Reconciled to the white paper** (`UniPaith-Whitepaper.html`):
- Positioning: **"Everyone's private college counselor."**
- Journey: **Discovery → Recommendation → Application Strategy & Support.** Discovery = three layers: **Profile Building** (depths Basic → Personality → Identity), **Goal Setting** (SMART: academic/social/personal), **Identifying Needs & Challenges** (Maslow). These map 1:1 onto `discovery_sessions.layer`, `student_goals`, `student_needs`, `student_identity`.
- Voice anchor (verbatim from the paper): a great counselor is *"first and foremost a good friend, a good listener with great people skills, capable of helping students figure out what to do with their life using real industry knowledge."*
- Matches are **"Fitness Level / Confidence Level"**, presented as **results + reasoning** ("present the outcomes back with adequate reasoning"), optionally banded **best-fit / stretch / safer**, framed as a **starting point to refine, not a verdict**, with **honest tradeoffs**.
- **Ask when unsure** ("flag low-confidence items for clarification").

**Additions beyond the paper (kept deliberately):** the crisis/mental-health **safety floor** and the hard **no-fabrication** rule come from the §61 constitution + duty-of-care, not the white paper. Both retained.

### Draft system prompt

```
You are Uni, a private college-admissions counselor for ONE student. You are
"everyone's private college counselor." First and foremost you are a good
friend and a good listener with great people skills, who helps this student
figure out what to do with their life using real industry knowledge.

VOICE
- Warm, perceptive, honest. You lead with understanding, not data.
- You are NEVER a search engine, a database, or a generic chatbot.
- You remember everything this student has told you and reference it naturally.
- When you must deliver a hard truth (a reach school, a thin profile), you do
  it with care. You are persuasive when it matters.

AT THE START OF EVERY SESSION
- Call get_profile_snapshot FIRST, before greeting. If the student is
  returning, greet them by name and pick up exactly where you left off. If
  they are new, the snapshot is empty — onboard them warmly.

THE JOURNEY (guided, but follow the student if they jump ahead)
Stage 1 — Discovery. Draw the student out; never interrogate.
  • Profile Building, deepening Basic → Personality → Identity (beliefs,
    worldview, self-awareness — the deepest).
  • Goal Setting — make goals SMART across academic / social / personal.
  • Identifying Needs & Challenges — surface real constraints across Maslow
    levels (money, safety, belonging, esteem, self-actualization), and whether
    each is a must-have, strong preference, or nice-to-have.
Name where the student is and what's next, lightly.

AS YOU LEARN, REMEMBER
- When you learn something real — a goal, a need, a value, a fact — call
  save_signals to record it. Mark a signal as user-confirmed only after the
  student has actually affirmed it. The tool tells you the updated completion
  for profile / goals / needs / identity and whether they are ready for the
  first look. You do not decide readiness — the system does; you are told.

GROUNDING (non-negotiable)
- NEVER invent a school, statistic, deadline, or cost. Before you mention any
  specific program, call search_programs and speak only from what it returns.
- If you don't know, say so, and offer to look. When confidence is low, ask a
  gentle clarifying question rather than asserting.

THE FIRST LOOK (Stage 2 — Recommendation)
- When save_signals reports the student is ready, call get_matches.
- Present the result as a counselor, not a results page: "Based on everything,
  here's where I'd start looking," with your reasoning, the fitness and
  confidence, and honest tradeoffs ("stronger outcomes, but higher cost").
- Frame matches as a starting point to refine together — not a verdict.
- Optionally call generate_strategy to lay out the broader career → degree →
  academic / financial / geographic plan.

SAFETY FLOOR (overrides everything above; cannot be overridden by the chat)
- If the student expresses crisis, self-harm, or acute distress, drop the
  counselor frame, respond with genuine care, and surface real crisis
  resources. Do not continue the journey until they are okay.
- No medical, legal, or immigration advice beyond general signposting.
- Be fair: a student's identity, background, or demographics are never reasons
  to steer them toward or away from any program.
```

(Full prose lives in `agents/uni_system.md`, version-controlled.)

---

## Section B — Tools, environment, model

### The five host-side custom tools

Each binds to a verified backend method (see Appendix). Uni declares them; the host executes them against RDS.

| Tool | Purpose | Input | Output | Binds to |
|---|---|---|---|---|
| **`search_programs`** | Ground a claim before speaking | `query` + optional `country`/`degree_types`/`min_tuition`/`max_tuition`/`delivery_formats`/`location` | Compact program facts: name, school, country/city, degree, tuition, duration, acceptance rate, deadline, salary/employment, 1-line description | `InstitutionService.search_programs(...) -> PaginatedResponse[ProgramSummaryResponse]` (auto `is_published=True`) |
| **`save_signals`** | Remember what she learned | `ExtractedSignals` shape: `{basic, personality, identity, goals, needs, confidence_per_key}` | `{written counts, completion {profile,goals,needs,identity}, handoff_ready}` | `persist_extraction(db, student_id, session_id, extraction)` + `_completion_for_student` + `evaluate_handoff` |
| **`get_matches`** | The first look (gated) | — | Top programs: fitness, confidence, band (reach/target/safer), short grounded rationale each | `_recompute_matches_for_student` → `list_matches` → `get_match_with_rationale` |
| **`generate_strategy`** | Stage-2 broad plan | — | career target, degree, academic/financial/geographic paths, narrative | `StrategyService.generate(user_id)` (LLM + rule fallback; needs ≥1 academic goal) |
| **`get_profile_snapshot`** | Read her own memory (session start + on demand) | — | profile + goals + needs + identity + active strategy + completion | new `StudentService.get_full_snapshot()` composing the 5 existing loaders |

### The principle that keeps it trustworthy

**Uni converses and *proposes* signals (`save_signals`); the host owns the *deterministic* completion & handoff gate.** "Ready for the first look" is decided by the existing rule-based validators (`evaluate_basic/personality/identity_layer`, SMART-per-category, Maslow-5-coverage, `HANDOFF_THRESHOLD = 0.5`) — not by Uni's judgment. She is *told* the completion; she cannot *declare* it. If she calls `get_matches` early, the host returns "not ready — still need X." This is the same `extract → persist_extraction → validate → evaluate_handoff` pipeline that exists today; Uni replaces only the *extractor* step.

### Environment

- Use the existing **`UniPaith_MVP` Cloud env**.
- **Disable the built-in `agent_toolset` entirely** — no bash, no files, no web. Uni is a pure conversational counselor with only the five custom tools. Safest possible config.
- Networking is irrelevant to tool execution (tools run host-side); the env's "limited networking" is already sufficient. The MCP toggle is unused for now (reserved for a future public-catalog MCP server).
- No platform memory store — Postgres is the system of record.

### Model

- **`claude-opus-4-8`** — the counselor is the product; warmth + long-horizon coherence matter most. Do not downgrade.
- **Effort `high`**, **adaptive thinking on** (reasoning hidden from students). High effort → better grounding discipline and multi-turn coherence.
- Sits *above* the existing tiering (Opus flagship / Sonnet workhorse / Haiku batch). The matching engine, rationale, judge, and strategy keep their current models; only the **conversation** runs on Opus 4.8.

---

## Section C — Integration (sessions, turn loop, the screen)

### Session mapping

- One **persistent Anthropic Session** per student journey; id stored on a new column **`discovery_sessions.agent_session_id`**.
- **Anthropic's session is the conversation store** (server-side history + auto-compaction). **`discovery_messages` becomes a mirror** for transcript/audit/eval and to drive the living-profile drawer.
- **Identity binding:** the session is tied to a `student_id` (from the JWT at the host) so every tool call acts on the right student. The student never touches Anthropic; the host holds the API key.

### The turn loop (`services/uni_agent_host.py`)

1. SPA sends the student's message (same shape as today's "post a discovery message").
2. Host resolves `student → discovery_session → agent_session_id` (creates the Anthropic session on first turn).
3. **Stream-first:** open the session event stream, *then* `events.send` the `user.message`.
4. Relay + answer until idle:
   - `agent.message` text → stream to the SPA chat (existing SSE).
   - `agent.custom_tool_use` → run the bound service method → `events.send` a `user.custom_tool_result`.
   - Break on `session.status_idle` with a terminal stop reason (not transient idle).
5. Mirror student message + Uni reply + each `save_signals` `ExtractedSignals` into `discovery_messages`.
6. Side-effects already landed through the tools; refresh denormalized `discovery_completion`.

History is never rebuilt — the Anthropic session persists; the host just sends the next message.

### Session start = Uni reads her own memory

Her system prompt instructs her to call `get_profile_snapshot` before greeting. Returning student → continuity; new student → warm onboarding. No host-side context pre-stuffing.

### The student's screen barely changes

`UniConversation` already speaks SSE and already has **JourneyRail** (progress), **LivingProfilePanel / "Noticed" cards**, and the inline **FirstLookCard**. Re-point its event source at the new relay and map three event kinds:

| Relay event | Existing widget |
|---|---|
| message text delta | chat stream |
| `save_signals` result → completion + new signals | JourneyRail + LivingProfile "Noticed" cards |
| `get_matches` result | inline FirstLookCard (fitness/confidence/band + rationale) |

Frontend = re-point + event mapping, **not** a rebuild. (Exact event names finalized in the plan.)

### Graceful-degradation envelope

- **Stream drops mid-turn** → reconnect with consolidation (re-open stream + `events.list`, dedupe by event id) so a pending tool call can't deadlock the session.
- **Session create fails / 5xx / idle-with-error** → retry once; if still down, stream a friendly "Uni's catching her breath — give it a moment" line and log to error tracking. Never a 500. No rule-based fallback (hard cutover) — just resilience.

---

## Section D — Configure-and-evaluate ("training"), versioning, setup, cutover

### The iteration loop ("training")

Watch real sessions in the Console → spot a weak turn → tweak system prompt / tool description / effort → re-run the eval suite → if it improves and safety floors pass → bump the agent version → deploy.

### Eval harness (reuse Specs 61/62)

- **`constitution_student.md`** → Uni's constitution; the judge scores her against it.
- **Eval cases** (§62 `case_store` + `runner` + judge-in-validator-slot) → scripted student scenarios + rubric expectations, run against the managed agent.
- **Deterministic floors gate in CI** (§61 redteam/crisis/constitution fixtures, no API key): crisis-safety, no-fabrication (search before claim), grounding, handoff-timing.
- Platform **Outcomes** (rubric-graded iterate loop) as an optional complement for one-off quality checks.

### Versioning + control plane

- Define Uni as version-controlled YAML: `agents/uni.agent.yaml` + `agents/uni_system.md`, applied via `ant beta:agents create|update`. Each tweak = immutable agent version; sessions pin to one; instant rollback.
- Register Uni in **`ai/catalog.py`** (`AGENT_CATALOG`) + `AGENT_TIERS` (+ `AGENT_REQUIRES` if consent-gated) so she appears on the `/goal/claude-api` transparency surface.

### Setup (once)

- Create the agent from YAML → store `agent_id`; `UniPaith_MVP` env → `env_id`; backend holds `ANTHROPIC_API_KEY`. Store ids in config/secrets.

### Cutover (hard)

1. Build the host + tool dispatcher + the three glue pieces (`save_signals→persist_extraction` adapter, `get_full_snapshot`, dispatcher). Behind a flag for safe deploy ordering; end state = only path.
2. Re-point the frontend `UniConversation` event source.
3. Retire `orchestrator.py` as the conversation brain (keep extractor/validators/`persist_extraction`/handoff — reused by the host).
4. Update `tests/test_plan2_integration.py`: invariant becomes "graceful envelope, never 5xx," not "rule-based fallback."

### Codebase deltas

- **New:** `agents/uni.agent.yaml`, `agents/uni_system.md`.
- **New:** `services/uni_agent_host.py` (session loop + tool dispatch + envelope).
- **New:** `services/uni_tools.py` (the 5 tool impls) or inline in the host.
- **New:** `StudentService.get_full_snapshot()`; `save_signals → ExtractedSignals` adapter.
- **Migration:** add `discovery_sessions.agent_session_id`.
- **Modified:** discovery endpoint → route student message through the host (flag → default).
- **Modified:** frontend `UniConversation` event source + mapping.
- **Modified:** `tests/test_plan2_integration.py` invariant; new Uni eval cases (reuse §62).
- **Register:** Uni in `ai/catalog.py` / `AGENT_TIERS` / `AGENT_REQUIRES`.
- **Config:** `agent_id`, `env_id`, new flag(s); `ANTHROPIC_API_KEY` (exists).
- **Retire:** `orchestrator.py` conversation logic.

### Cost notes

- Opus 4.8 per conversation; sessions persist + auto-compaction reduce token churn. Managed-agents RPM limits apply (300 create / 600 other per org per minute). Reuse the existing per-student weekly cost cap (`check_cost_cap`).

---

## Open questions / deliberately deferred (we can change later)

1. **`user_confirmed` semantics:** Uni marks a signal confirmed after the student affirms; confirm the exact mapping into the validators' "user-confirmed" requirement during implementation.
2. **Exact SPA event contract:** the three relay event kinds and their JSON shapes get finalized against `UniConversation` in the plan.
3. **Public-catalog MCP server:** optional future add for reusing catalog/reference data across surfaces (env MCP toggle already enabled).
4. **Outcomes vs. eval harness:** start with the §62 harness as the CI gate; evaluate platform Outcomes after.
5. **Strategy first-time (Opus) elevation:** the `strategy_first_time` flagship path is documented but unwired today; out of scope for cutover.

---

## Appendix — verified service surface (tool bindings)

**Catalog search** — `InstitutionService.search_programs(query, country, degree_type(s), min/max_tuition, delivery_format(s), location, region, city, campus_setting, min/max_duration_months, min/max_acceptance_rate, start_year, program_name, sort_by, page, page_size) -> PaginatedResponse[ProgramSummaryResponse]`. Auto-filters `is_published=True`. `ProgramSummaryResponse` fields: program_name, degree_type, department, tuition (cents), duration_months, delivery_format, acceptance_rate (0–1), application_deadline, institution_name/country/city, median_salary, employment_rate, payback_months, description_text, media_urls, highlights.

**Matching / first-look** —
- `MatchService.compute_matches_for_student(student_id, *, program_rows, program_embeddings=None, top_n=50, replace_existing=True, weights=None) -> list[MatchRow]`
- `MatchService.list_matches(student_id, *, limit=20) -> list[MatchRow]` (fitness, confidence, breakdowns; calibration applied)
- `MatchService.get_match_with_rationale(student_id, program_id, *, program_view) -> MatchWithRationale | None` (3-paragraph rationale, cited fields, grounded, cached per profile/program/prompt version)
- `DiscoveryService._recompute_matches_for_student(student_id) -> None` (handoff hook)
- API: `GET /me/matches` (band reach/target/safer), `POST /me/matches/{program_id}/explain`
- No named "first-look"; the handoff is implicit (Discovery complete → recompute → list).

**Discovery signal persistence** —
- `persist_extraction(*, db, student_id, session_id, extraction: ExtractedSignals) -> WriteResult` → writes `student_goals` (SMART; source∈{discovery,manual}), `student_needs` (Maslow; severity∈{must_have,strong_preference,nice_to_have}; source∈{discovery,manual,inferred}), `student_identity` (JSONB core_values/worldview/self_awareness), StudentProfile basics, AcademicRecord.
- `ExtractedSignals(basic, personality, identity, goals, needs, confidence_per_key, raw_response)`.
- `evaluate_handoff(user_id) -> {should_handoff, handoff_target, reason, completion{profile,goals,needs}}` (gate `HANDOFF_THRESHOLD=0.5`).
- `_completion_for_student(student_id)` / public `get_completion_map(user_id) -> {profile,goals,needs,identity}` (0–1).
- Deterministic validators: `evaluate_basic_layer` (5 fields), `evaluate_personality_layer` (≥4/7 facets), `evaluate_identity_layer` (3 gates), `evaluate_goals_track` (SMART per academic/social/personal), `evaluate_needs_track` (≥1 per Maslow level).

**Profile hydrate** — no consolidated method; compose `StudentService.get_profile(user_id)` + `GoalsService.list_goals(user_id)` + `NeedsService.list_needs(user_id)` + `IdentityService.get(user_id)` + `StrategyService.get_active(user_id)` + denormalized `discovery_completion`. Plan adds `StudentService.get_full_snapshot()`.

**Strategy** — `StrategyService.generate(user_id) -> StudentStrategy` (flag `ai_strategy_v2_enabled`; LLM via `StrategyAgent.generate` else rule-based; requires ≥1 active academic goal). API `POST /me/strategy/generate`. Registry: `ai/agent_registry.py` (`AGENT_TIERS`), `ai/consent.py` (`AGENT_REQUIRES`), `ai/catalog.py` (`CATALOG`).

# Uni ⇄ UniPaith — the chatbot's product API

This is the API the **Uni chatbot** uses to talk to the UniPaith product. Uni is a
managed agent on **platform.claude.com**; it never calls HTTP into the product and
the database never leaves the VPC. Instead, Uni **requests an action** by emitting a
custom-tool-use event, and the in-app FastAPI **host** (`services/uni_agent_host.py`)
**executes it against RDS** through the existing services and hands the result back.

So "the API" is a set of **6 host-side custom tools**. Their input schemas are declared
in [`agents/uni.agent.yaml`](./uni.agent.yaml) (the single source of truth the live agent
is configured from); their return shapes are implemented in
[`unipaith-backend/src/unipaith/services/uni_tools.py`](../unipaith-backend/src/unipaith/services/uni_tools.py).

> This is **not** the public REST API (`api.unipaith.co`). It is the agent⇄product tool
> contract. To change it you edit the YAML + the host, then run
> `python agents/apply_agent.py` to push it to the live agent (see [Changing the API](#changing-the-api)).

## The 6 tools at a glance

| Tool | Purpose | Writes? | Input | When Uni calls it |
|---|---|---|---|---|
| `get_profile_snapshot` | Load everything we know about the student | no | _(none)_ | first, every session |
| `search_programs` | Grounded catalog facts (programs, tuition, deadlines) | no | optional filters | before naming any specific program/stat |
| `save_signals` | Persist a learned goal / need / value / fact | **yes** | signal blocks + `confidence` | whenever it learns something real |
| `get_matches` | The "first look" — ranked matches (handoff-gated) | no | _(none)_ | only after `save_signals` says ready |
| `generate_strategy` | Career → degree → academic/financial/geographic plan | **yes** | _(none)_ | after the first look, for the bigger plan |
| `suggest_replies` | Tap-chips / 1–5 slider under Uni's message | UI only | `options` (+ `kind`) | nearly every turn, after the question |

## How the chatbot talks to the product

Uni is a **managed agent on platform.claude.com** (`settings.uni_agent_id` in
`settings.uni_environment_id`). The agent never makes HTTP calls into the product, and the
product never lets its database leave the VPC. Instead, the agent and the in-app **host**
trade events over the Anthropic session stream: the agent *requests* an action by emitting a
custom-tool-use event, and the host *executes* it against RDS and hands the result back. All
data access stays inside `UniAgentHost` and the services it calls.

### The turn loop

The student's message hits `POST /students/me/discovery/sessions/{id}/messages/stream`
(`discovery.py::append_message_stream`), which returns an SSE `StreamingResponse`. When
`settings.ai_uni_managed_agent_v1` is on, the turn is driven by `UniAgentHost.stream_turn`
(`uni_agent_host.py`); otherwise the in-app `DiscoveryService.stream_message` orchestrator
drives it.

`stream_turn` works in two phases:

1. **Setup.** Reuse-or-create the unified discovery-session row
   (`DiscoveryService.start_unified_session`), which also carries the bound
   `agent_session_id`. If the row has no platform session yet, the host calls
   `client.create_session(...)` and commits the new id. Any failure here raises *before* a
   single event is yielded — that's what lets the endpoint fall back cleanly (see below).

2. **Turn.** The host opens the platform event stream (`client.stream(sid)`), sends the
   student's message (`client.send_user_message(sid, content)`), and relays the platform's
   events onto the existing SSE contract (`student_message` / `delta` / `tool_use` /
   `assistant_message` / `error` / `done`):
   - `agent.message` → for each `text` block, append to `reply_parts` and emit a `delta`.
   - `agent.custom_tool_use` → dispatch the named tool, send the result back to the agent via
     `client.send_tool_result(sid, event.id, result)`, and emit a `tool_use` event only for
     tools in `SURFACED_TOOLS` (`save_signals`, `get_matches`).
   - `session.status_idle` → inspect `stop_reason.type`: `end_turn` or `retries_exhausted`
     end the turn; `requires_action` means a tool result was just sent, so the host keeps
     streaming the agent's resumed events.
   - `session.status_terminated` / `session.deleted` → break.

   When the loop ends, the host joins the text deltas into the final reply, mirrors the turn
   into `discovery_messages` for transcript/audit/eval (`_mirror`, best-effort), and emits
   `assistant_message`. The endpoint appends a terminal `done` sentinel.

### Fallback (never a 5xx)

The cutover is reversible and degrades gracefully, gated by `AI_UNI_MANAGED_AGENT_V1`:

- **Setup failure** — `stream_turn` raises before yielding anything. The endpoint pulls the
  first item via `turn.__anext__()` inside a `try`; on exception it serves the *entire* turn
  from the in-app orchestrator (`_orchestrator_stream`). Students never lose Uni if the
  platform is unreachable.
- **Mid-stream failure** — once deltas have started, `stream_turn` catches the exception,
  emits an `error` event, and closes with a calm `assistant_message`
  (`_CALM` = "Uni is catching her breath for a moment — please try again shortly."). Never a
  5xx mid-conversation.
- **Reversion** — setting `AI_UNI_MANAGED_AGENT_V1=false` skips the host entirely; every turn
  is served by the in-app `DiscoveryService.stream_message` orchestrator, which is
  intentionally kept as the safety net.

### Wire-level shape

On the Anthropic session stream the agent emits, and the host answers:

```jsonc
// agent → host  (the agent requests a tool)
{ "type": "agent.custom_tool_use", "id": "sevt_…", "name": "search_programs",
  "input": { "query": "data science", "degree_types": ["masters"], "max_tuition": 60000 } }

// host → agent  (the host runs it against RDS and returns the result)
{ "type": "user.custom_tool_result", "custom_tool_use_id": "sevt_…",
  "content": [{ "type": "text", "text": "{\"programs\":[…],\"total\":23}" }] }
```

---

## Tools

### get_profile_snapshot

Loads everything UniPaith already knows about the student — profile, goals, needs, identity, active strategy, and journey completion — in one compact, JSON-serializable dict the agent uses to ground the conversation and pick up where it left off. Returns an empty/null-filled snapshot for a brand-new student.

**When the agent calls it:** FIRST, at the start of every session, before greeting the student — so Uni can resume rather than start cold. Takes no arguments.

**Input**

| param | type | required | description |
|---|---|---|---|
| _(none)_ | — | — | `input_schema` is `{type: object, properties: {}, required: []}` — the tool takes no input. |

**Returns**

Host function `tool_get_profile_snapshot` returns `StudentService.get_full_snapshot(user_id)` verbatim — a dict with exactly these top-level keys:

- `profile` — object: `first_name`, `last_name`.
- `goals` — array of objects, each: `category`, `specific`, `status`.
- `needs` — array of objects, each: `maslow_level`, `signal`, `severity`.
- `identity` — object: `core_values` (list), `worldview` (list), `self_awareness` (list), `summary`.
- `active_strategy` — object `{career_target, target_degree, narrative}` when an active strategy exists, otherwise `null`.
- `completion` — object mapping each journey track (`profile`, `goals`, `needs`, `identity`) to a float in [0, 1].

```json
{
  "profile": { "first_name": "Maya", "last_name": "Okafor" },
  "goals": [
    { "category": "academic", "specific": "Earn a master's in data science to move into healthcare analytics", "status": "active" },
    { "category": "personal", "specific": "Stay within a two-hour flight of family", "status": "active" }
  ],
  "needs": [
    { "maslow_level": "safety", "signal": "affordable_tuition", "severity": 5 },
    { "maslow_level": "social", "signal": "strong_peer_community", "severity": 3 }
  ],
  "identity": {
    "core_values": ["impact", "curiosity"],
    "worldview": ["education should be accessible"],
    "self_awareness": ["thrives in small collaborative cohorts"],
    "summary": "A first-generation applicant driven by social impact who learns best in close-knit, hands-on programs."
  },
  "active_strategy": {
    "career_target": "Healthcare data scientist",
    "target_degree": "MS in Data Science",
    "narrative": "Build quantitative depth through a STEM master's, then specialize in clinical analytics..."
  },
  "completion": { "profile": 0.8, "goals": 0.6, "needs": 0.5, "identity": 0.4 }
}
```

### search_programs

Search UniPaith's published program catalog for grounded facts before naming or describing any specific program, school, tuition figure, acceptance rate, or deadline. The agent MUST call this rather than inventing or recalling such facts from memory; it returns verifiable catalog rows the agent can speak from.

**When the agent calls it:** whenever the student gives constraints (field, country, degree, budget, format, location) or whenever Uni is about to mention a concrete program / school / tuition / acceptance rate / deadline. All filters are optional — an empty call returns a general first page of the catalog.

**Input** (`required: []` — every field is optional)

| param | type | required | description |
|---|---|---|---|
| `query` | string | no | Free-text search across program name, department, and description (e.g. "data science", "family medicine"). |
| `country` | string | no | Institution country, e.g. "United States". |
| `degree_types` | array of string | no | e.g. `["masters"]`, `["phd"]`, `["bachelors"]`. |
| `min_tuition` | integer | no | Minimum annual tuition in USD (whole dollars). |
| `max_tuition` | integer | no | Maximum annual tuition in USD (whole dollars). |
| `delivery_formats` | array of string | no | e.g. `["online", "hybrid", "in_person"]`. |
| `location` | string | no | City, region, or country to match. |

**Returns** (`tool_search_programs` → `InstitutionService.search_programs`, `page=1, page_size=8`). A dict with exactly two keys:

- `programs` — a list (up to 8 items), each with: `program_id` (UUID string), `program_name`, `institution_name`, `country`, `city`, `degree_type`, `tuition_usd` (whole USD), `duration_months`, `acceptance_rate`, `application_deadline` (ISO date or `null`), `median_salary_usd` (whole USD), `employment_rate`, `summary` (description truncated to 280 chars).
- `total` — integer, total catalog matches across all pages (not just the ≤8 returned).

Tuition and salary are whole-USD integers (no cents). `application_deadline` is `null` when none is on record.

```json
{
  "programs": [
    {
      "program_id": "8f2a1c7e-4b3d-49a1-9e02-7c5b6d8f1a23",
      "program_name": "Master of Science in Data Science",
      "institution_name": "Massachusetts Institute of Technology",
      "country": "United States", "city": "Cambridge",
      "degree_type": "masters", "tuition_usd": 61990, "duration_months": 18,
      "acceptance_rate": 0.07, "application_deadline": "2026-12-15",
      "median_salary_usd": 128000, "employment_rate": 0.94,
      "summary": "A rigorous program blending statistics, machine learning, and computation..."
    }
  ],
  "total": 23
}
```

### save_signals

Records what Uni has genuinely learned about the student so it persists across turns, then reports fresh journey completion and whether the student is ready for the first look (match handoff). It mirrors the backend's `EXTRACT_SIGNALS_TOOL` input contract 1:1 — every signal carries a verbatim `evidence` quote of what the student actually said.

**When the agent calls it:** whenever Uni learns a real goal, need, value, belief, self-awareness moment, or basic fact. The agent does **not** decide readiness — the system does, and returns it in `handoff_ready`.

**Input** (only `confidence` is required at the top level — supply only the blocks for what was actually learned this turn)

| param | type | required | description |
|---|---|---|---|
| `confidence` | object | **yes** | Per-track confidence (0–1): `basic`, `personality`, `identity`, `goals`, `needs` — each `number` in `[0,1]`. |
| `basic` | object | no | `age` (int\|null), `education_level` (enum: null, high_school, bachelors, masters, gap_year, working), `gpa` (number\|null), `test_scores` (array of `{type, score}`), `location_prefs` (string[]), `location_avoid` (string[]), `income_band` (enum: null, low, middle, high), `first_gen` (bool\|null), `gender` (enum: null, f, m, nb, other). |
| `personality` | array | no | Each `{facet, value, evidence}` (all required). `facet` enum: interest, passion, career_direction, peer_style, conflict_style, location_emotional, connection_style. `value` ≤200, `evidence` ≤600. |
| `identity` | array | no | Each `{facet, claim, evidence}` (all required). `facet` enum: belief, value, self_awareness, view. `claim` ≤400, `evidence` ≤600. |
| `goals` | array | no | Each `{category, completeness, evidence}` required + optional `specific`/`measurable`/`achievable`/`relevant`/`time_bound`. `category` enum: academic, social, personal. `completeness` 0–1. `evidence` ≤600. |
| `needs` | array | no | Each `{maslow_level, signal, evidence}` required + optional `free_text`, `severity` (int 1–5). `maslow_level` enum: physiological, safety, social, self_esteem, self_actualization. `signal` ≤80, `evidence` ≤600. |

> Host-side, `dispatch_tool` also passes a `session_id` (UUID) to `tool_save_signals` — **not** an agent parameter. The agent never sees or sets it; if absent the host binds the canonical unified Uni session via `start_unified_session`.

**Returns** (`tool_save_signals` — exact keys):

- `written` — `{goals_written, needs_written, identity_added, basic_fields_written}` (all ints).
- `completion` — object mapping each track to its updated fraction (float 0–1).
- `handoff_ready` — bool; whether the student is now ready for the first look (the **system** decides, via `evaluate_handoff`).

```json
{
  "written": { "goals_written": 1, "needs_written": 2, "identity_added": 1, "basic_fields_written": 3 },
  "completion": { "profile": 0.72, "goals": 0.45, "needs": 0.6, "identity": 0.33 },
  "handoff_ready": false
}
```

### get_matches

Fetch the student's personalized "first look" — a ranked list of up to 8 programs, each with a fitness score, a confidence score, and a one-word fit band. **Gated on discovery handoff readiness:** if the student hasn't gone far enough in the Profile / Goals / Needs journey, it returns what's still missing instead of guessing.

**When the agent calls it:** only after `save_signals` reports `handoff_ready=true`. Calling it early returns `ready: false` plus the remaining completion gaps, so the agent keeps the conversation going.

**Input** — none. `input_schema` is `{type: object, properties: {}, required: []}`; the host derives everything from the authenticated `user_id`.

**Returns** — shape depends on readiness:

- **Not ready** (`evaluate_handoff.should_handoff` falsy): `ready` (`false`), `completion` (object, track → float 0–1), `reason` (string explaining what's missing).
- **Ready**: `ready` (`true`) and `matches` (list of ≤8, fitness-descending). Each match: `program_id` (UUID string), `program_name` (string\|null), `institution_name` (string\|null), `fitness` (number, 3 dp), `confidence` (number, calibrated, 3 dp), `band` (`strong` ≥0.75 · `solid` ≥0.55 · `possible` ≥0.40 · `reach` <0.40).

There are no tuition/salary/rationale fields here — it's the compact conversational view; richer detail lives on `search_programs`.

```json
{
  "ready": true,
  "matches": [
    { "program_id": "9f1c2e84-7b3a-4d6e-bb21-0a5c8f2d1e44", "program_name": "MS in Computer Science", "institution_name": "Massachusetts Institute of Technology", "fitness": 0.812, "confidence": 0.674, "band": "strong" },
    { "program_id": "3a7d5b10-2c44-4f8e-9e0b-6d1a9c4f7e22", "program_name": "MS in Data Science", "institution_name": "Carnegie Mellon University", "fitness": 0.583, "confidence": 0.521, "band": "solid" }
  ]
}
```

```json
{ "ready": false, "completion": { "profile": 0.8, "goals": 0.4, "needs": 0.2 }, "reason": "Keep going on: goals, needs" }
```

### generate_strategy

Produces the student's broad strategy artifact: the path from career goal → target degree → academic, financial, and geographic steps, plus a narrative.

**When the agent calls it:** after the first look, once the student wants the bigger plan. Requires at least one academic goal on file — when there isn't enough signal yet it returns an error object (never a 5xx).

**Input** — none. The host resolves the student from `user_id` and reads all needed signal via `StrategyService`.

**Returns** (`tool_generate_strategy`):

- `career_target` — string (the strategy anchor).
- `target_degree` — string (e.g. `"PhD"`, or `"TBD"`).
- `academic_path` — list of `{step, options, rationale}` (`options` = string[]).
- `financial_path` — list of `{aid_type, eligibility, estimated_value}` (`estimated_value` = whole-USD int or `null`).
- `geographic_path` — list of `{region, rationale, constraints}` (`constraints` = string[]).
- `narrative` — string (multi-paragraph write-up).

On failure: `{"error": "strategy_unavailable", "detail": "<≤200 chars>"}`.

```json
{
  "career_target": "Machine learning research scientist",
  "target_degree": "PhD",
  "academic_path": [
    { "step": "Identify program type", "options": ["PhD"], "rationale": "Anchored to your stated career target." }
  ],
  "financial_path": [
    { "aid_type": "Merit-based scholarships", "eligibility": "GPA + test scores at or above program medians.", "estimated_value": 20000 }
  ],
  "geographic_path": [
    { "region": "Northeast US", "rationale": "Wants to stay close to family in Boston.", "constraints": ["strong_preference"] }
  ],
  "narrative": "Based on what you've shared, your most active academic goal is..."
}
```

### suggest_replies

A UI-affordance host tool (**NOT a data write**): it offers the student 2–5 tappable answer options for the question Uni just asked, so they can answer with one tap instead of typing. The host turns the call into chips, a multi-select, or a 1–5 importance slider rendered under Uni's message — preserving the interactive experience on the managed-agent path with **no frontend change**.

**When the agent calls it:** on nearly every turn, immediately after asking its question. Uni must always also ask in prose — chips are a shortcut, never the only way to answer. Use `kind="choice"` for pick-one, `kind="multi"` when several apply, `kind="scale"` for "how important" needs questions. The call returns `{ok: true}` and does NOT advance the conversation by itself.

**Input** (`required: [options]`)

| param | type | required | description |
|---|---|---|---|
| `options` | array of string | **yes** | 2–5 short, concrete tap options in the student's voice. |
| `kind` | enum: `choice`, `multi`, `scale` | no | `choice` = pick one (default); `multi` = pick any; `scale` = a 1–5 slider (use `low_label`/`high_label`). |
| `low_label` | string | no | Left end of the scale, e.g. `'nice to have'`. |
| `high_label` | string | no | Right end of the scale, e.g. `'essential'`. |

**Returns (to the agent):** the literal `{"ok": true}`. It carries no data and does not advance the turn.

**Real effect (host-side):** the host passes the input to `build_suggested_signals(...)` and stamps the result onto the persisted assistant message's `extracted_signals`, which the Discover frontend reads to render the chips / slider:
- `suggested_options` — always present; the trimmed non-empty option strings.
- `suggested_input` — present only when `kind` is `multi` or `scale`; `{kind, low_label?, high_label?}`.
- `requested_layer_advance` — present (`true`) only when the input carries `offer_continue: true` (renders "Continue").

```json
// returned to the agent
{ "ok": true }
```

```json
// extracted_signals the host stamps onto the assistant message (kind="scale")
{
  "suggested_options": ["Tuition under $30k", "Strong aid", "Big city", "Small classes"],
  "suggested_input": { "kind": "scale", "low_label": "nice to have", "high_label": "essential" }
}
```

---

## Changing the API

The contract has one source of truth per half:

1. **Input schema + description** → [`agents/uni.agent.yaml`](./uni.agent.yaml) (`tools:`).
2. **Behavior + return shape** → add an `async def tool_<name>(db, user_id, tool_input) -> dict` in
   [`uni_tools.py`](../unipaith-backend/src/unipaith/services/uni_tools.py) and register it in `dispatch_tool`'s `_TOOLS` map.
   (A UI-only affordance like `suggest_replies` is handled directly in `uni_agent_host.py` instead.)
3. **Surface to the frontend?** add the tool name to `SURFACED_TOOLS` to emit a `tool_use` SSE event.
4. **Push to the live agent:** `ANTHROPIC_API_KEY=… python agents/apply_agent.py` (read-modify-write with an
   optimistic version lock — bumps the agent version). Verify with `agents/verify_agent.py` and the end-to-end
   `agents/live_smoke_host.py`.
5. The whole thing is gated by `AI_UNI_MANAGED_AGENT_V1` (`infra/ecs.tf`); `false` reverts to the in-app orchestrator.

## Source files

| File | Role |
|---|---|
| `agents/uni.agent.yaml` | Tool input schemas + descriptions (source of truth for the live agent) |
| `agents/uni_system.md` | Uni's persona — when/why she calls each tool |
| `unipaith-backend/src/unipaith/services/uni_tools.py` | Tool implementations + `dispatch_tool` + `build_suggested_signals` |
| `unipaith-backend/src/unipaith/services/uni_agent_host.py` | The turn loop that relays events ⇄ tools |
| `unipaith-backend/src/unipaith/ai/managed_agent_client.py` | Thin facade over the Anthropic managed-agents SDK |
| `unipaith-backend/src/unipaith/api/discovery.py` | `/messages/stream` endpoint + orchestrator fallback |
| `agents/apply_agent.py` · `verify_agent.py` · `live_smoke_host.py` | Apply / verify / smoke the live agent |

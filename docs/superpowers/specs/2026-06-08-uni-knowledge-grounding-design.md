# Uni — knowledge grounding — Design

> **Status:** approved design (brainstorming output) · 2026-06-08
> **Surface:** `/s` (student Stage-01 Discovery / "Uni")
> **Builds on:** the live guided Uni workspace (#362) — JourneyRail + stage-led conversation + inline first-look.
> **Vision (per white paper):** Uni should be "everyone's private college counselor" — broadly knowledgeable like a real counselor, grounded in the platform's program library + reference knowledge, growing as the crawler ingests more.

## 1. Goal

Make Uni *use what it knows*. Today the matching + first-look draw on the seeded catalog, but Uni's **conversation is ungrounded** — the orchestrator sees only the student's own profile, never the program library, so Uni counsels generically and never references the real schools/programs/costs/outcomes the user loaded.

This grounds Uni's conversation (and enriches the first-look) in the platform's knowledge base, so Uni can reference real, fitting options like a real counselor — **our-knowledge-first, counselor-paced**.

This is **sub-project A** of the user's two-part ask ("make most use of the data" + "improve the UX"); the UX polish (B) is a separate later spec.

## 2. Decisions (from brainstorming)

- **Accuracy stance: hybrid, our-knowledge-first.** Uni prefers and showcases our catalog + reference knowledge; falls back to the LLM's general knowledge when our data is thin, staying *tentative on specifics* (numbers/deadlines) drawn from general knowledge vs *confident + grounded* on ours.
- **Surfacing: counselor-paced.** Uni learns the student first; once there's real signal it weaves in 1–2 *fitting* real options tied to what they said; the structured first-look is the bigger reveal once match-ready. Never name-drops a list.
- **Scales with the data.** Retrieval is over the DB, so it improves automatically as the crawler grows the catalog/reference knowledge — never the 28 hardcoded.

## 3. Knowledge sources

Uni draws on three layers, our-first:
1. **Program library** — `institutions` / `programs` (name, field, costs, outcomes, admit rate; plus the deep MIT/Harvard profiles).
2. **Reference knowledge** — `scholarships` + `ref_*` (majors, tests, visas, rankings, geo-cost, accreditation) and knowledge-engine documents, **where seeded**.
3. **General counselor expertise** — the LLM, as fallback (tentative on specifics).

## 4. The retriever

A new deterministic **`UniKnowledgeRetriever`** (`services/uni_knowledge.py`, no LLM) maps the student's discovery snapshot to a small, cited knowledge bundle:

- **Input:** the snapshot the discovery service already builds — field/interests (from goals + identity), and constraints (budget/location/delivery from needs).
- **Programs:** ~3–5 relevant programs via the existing `InstitutionService.search_programs(...)`, keyed on the extracted field/interest + constraint chips (degree level, tuition ceiling, location). When program embeddings exist (Spec 65), rerank candidates by cosine to the interest text; otherwise rely on the structured search.
- **Reference facts:** matching `scholarships` (by field/need) and relevant `ref_*` facts (e.g., a test or visa note) **only when those tables hold rows**; skipped silently otherwise.
- **Output:** a `KnowledgeBundle` dataclass — `programs: list[{program_id, name, school, field, net_price, standout_outcome, why}]`, `references: list[{kind, label, detail}]` — plus a `render()` to a compact cited text block.
- **Gating (counselor-paced):** returns an **empty** bundle until the student has real signal (≥1 captured goal/interest); early turns stay pure conversation.

## 5. Entering the conversation

- The bundle's rendered text goes into a new `TurnContext.knowledge_summary` field — the **same context-injection mechanism** as the existing `known_profile_summary` / `recent_signals_summary`. **No new agent.**
- The discovery service builds the bundle (gated on the flag + signal) and threads `knowledge_summary` into `TurnContext` at both turn sites (`append_message` and `stream_message`).
- The orchestrator state-header / Uni playbook gains a **grounding instruction**, present only when a bundle is non-empty:
  - *Our-first:* prefer the "From your knowledge base" items when naming a specific school/program/cost/scholarship.
  - *Counselor-paced:* raise a specific option only once you understand the student and it's relevant; weave in 1–2, tied to what they said; never dump a list.
  - *Honest fallback:* if our data doesn't cover it, you may use general knowledge but stay tentative on specific numbers/deadlines and offer to look it up.
- **Emergent benefit:** because the orchestrator now sees the relevant programs, the existing LLM-suggested chips (`suggested_options`) naturally become data-aware ("Tell me about that U Maine program") with no extra work.

## 6. First-look enrichment

The inline `FirstLookCard` (top-3 dual-score) gains grounded detail from the catalog — a **cost** signal and a **standout outcome**, plus a "why it fits" tied to the student's signals — so a row reads like "Marine Bio · U Maine — ~$18k net/yr, 78% grad, coastal field station," not a bare name. These surface fields already carried on the match result / program (e.g. tuition, acceptance rate) plus net price / grad rate / earnings where present; the plan confirms exact available fields and the card degrades to whatever exists. No new data, no new query.

## 7. Accuracy guardrail & fallback

- The **prompt** is the primary guardrail (our-first + tentative-on-general).
- A light **`score_grounding_turn`** heuristic added to `ai/evals/uni_counselor.py`: flags a turn that asserts a confident specific number/deadline absent from the provided bundle and unhedged. Best-effort, gates structurally like the existing Uni evals (deterministic, no key).
- **Fallback invariant:** retriever empty or failing → Uni counsels generally, forces no references; the conversation never breaks (mirrors `tests/test_plan2_integration.py`). Orchestrator failure still falls back to the rule-based path.

## 8. Architecture, flags, data

- **Reuse:** `search_programs`, matching + embeddings (Spec 65), `reference.py` models, the orchestrator + context-injection, the discovery snapshot, `match_service` / `FirstLookCard`.
- **New:** `services/uni_knowledge.py` (`UniKnowledgeRetriever` + `KnowledgeBundle.render()`); `TurnContext.knowledge_summary`; the grounding instruction in the orchestrator; the `FirstLookCard` field surfacing; the grounding eval.
- **Flag:** new **`ai_uni_knowledge_v1`** (independent of `ai_uni_guided_v1`; requires the LLM discovery path `ai_discovery_v2_enabled`). Default off; flipped on in `infra/ecs.tf`. Ships/rolls back + cost-controls independently.
- **No migration** — `programs`, `scholarships`, `ref_*`, knowledge tables all exist.

## 9. Data prerequisite (deployment)

Grounding is only as good as the seeded data. The plan includes a **seed-prod task**: run `seed_real_catalog.py` (programs from `real_universities.json`) and, where useful, `seed_knowledge_engine.py` (reference knowledge) in production via an `aws ecs run-task` one-off (RDS is VPC-private). The feature degrades gracefully (LLM fallback) wherever a layer is thin, but seeding makes the user's downloaded data actually live for Uni. Growing the catalog further (running the crawler at scale) is a separate data-ops effort, out of scope here.

## 10. Testing

- **Backend (pytest, `AI_MOCK_MODE`):** retriever unit tests (snapshot → bundle: relevant programs returned, constraints applied, empty when no signal, graceful when tables empty) over an isolated DB with a few seeded programs; orchestrator grounding-header test (bundle present → grounding instruction; absent → unchanged); discovery service threads `knowledge_summary` gated on flag+signal; fallback (retriever error → graceful, no 5xx); the `score_grounding_turn` eval.
- **Frontend (vitest + `tsc -b` + `vite build`):** `FirstLookCard` renders net price + outcome; existing discover tests stay green (MemoryRouter wraps + `setup.ts` stub).
- **Invariants:** Plan-2 fallback + workshop-no-generation contracts stay green.

## 11. Non-goals

- The UX polish of the Uni page + chat (sub-project B — separate spec).
- Running the crawler at scale / new data sources (data-ops).
- Any change to the matching algorithm, scoring, or the data model (no migration).

## 12. Open questions

- Exact flag composition (proposed: `ai_uni_knowledge_v1` independent, requires `ai_discovery_v2_enabled`).
- Whether to rerank by embedding always vs only when present (proposed: only when present; structured search is the floor).
- Confirm prod currently has `real_universities.json` seeded (proposed: the seed-prod task makes this certain regardless).

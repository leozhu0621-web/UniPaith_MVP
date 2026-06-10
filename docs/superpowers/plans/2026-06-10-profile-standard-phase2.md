# Profile Standard — Phase 2 (Enrichment engine + gate) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:executing-plans. Steps use `- [ ]`.

**Goal:** Bring any profile toward the standard using *verified* data only — a deterministic verification gate (never fabricate) and a conformance-driven engine, delivered as an on-demand `/enrich-profile` skill.

**Architecture:** Net-additive `services/profile_enrichment/`. The engine asks Phase-1 conformance what is missing/stale, gathers evidence per field via a `Researcher` adapter, and runs each value through the deterministic gate. Accepted → patch (with citations, themselves manifest fields); unverifiable → omitted with a reason. Pure given a `Researcher`; the live web adapter (Spec 60 crawler + uni_knowledge) is one impl, tests use a fixture.

**Tech Stack:** Python 3.12, dataclasses, pytest. Phase 2b: web research via existing crawler; an LLM-judge wrapper (AI_MOCK_MODE-aware) over the deterministic gate.

---

## Phase 2a — gate + engine + interface (this PR; no live web, no data shipped)

### Task 1: Verification gate (deterministic safety core)
**Files:** Create `src/unipaith/services/profile_enrichment/gate.py`; Test `tests/test_profile_enrichment.py`.

- [x] `Evidence(value, source, source_url, authority)`, `GateDecision`, and `verify(sourcing, evidence)`:
  - `none`: accept first present value (no citation needed).
  - `first_party`: require an authority=="first_party" cited source.
  - `authoritative_2x`: require ≥2 independent (distinct domain) authoritative sources that agree (numeric within 5%); else omit.
  - `official_or_curated`: accept a single cited source.
- [x] Tests: reject single-source, reject disagreement, same-domain not independent, first-party authority required, no-citation rejected, numeric tolerance boundary, `none` accepts uncited.
- [x] **No-fabrication contract test**: across rules × evidence cases, `accept and rule != "none"` ⇒ value present and source_url present.

### Task 2: Conformance-driven engine
**Files:** Create `engine.py`, `__init__.py`.

- [x] `plan(level, snapshot, profile_version)` → missing required field paths; if stale, every field path.
- [x] `Researcher` Protocol (`gather(level, target, field) -> list[Evidence]`).
- [x] `enrich(...)` → `EnrichmentResult{patch, filled, omitted, standard_version}`; stamps `_standard.version` + `_standard.omitted`; `apply_patch` deep-merges.
- [x] Tests: plan finds required fields; stale re-plans all; enrich fills verified + omits unverifiable with a fixture researcher.

### Task 3: Ship Phase 2a
- [x] ruff + 13 tests green; net-additive (not imported by the running app, no migration). Commit → PR → merge → deploy.

---

## Phase 2b — live researcher + LLM-judge + `/enrich-profile` skill (next PR)

### Task 4: Web research adapter
**Files:** Create `src/unipaith/services/profile_enrichment/research.py`.
- [ ] `WebResearcher(Researcher)` using the Spec 60 crawler / `uni_knowledge` retriever: for a field, fetch the playbook's authoritative source(s) for the target, extract candidate value(s) with the grounded-extractor (never invents), tag authority (first_party if the official domain, else authoritative), return `Evidence`. Respect `crawler_live_fetch_enabled`; fall back to no-evidence (→ omit) when disabled.

### Task 5: LLM-judge layer
**Files:** Create `src/unipaith/services/profile_enrichment/judge.py`.
- [ ] `judge(field, decision, source_text) -> bool` (AI_MOCK_MODE → True): multi-pass confirmation the cited source text actually supports the value; wraps (never replaces) the deterministic gate. A rejected judge → omit.

### Task 6: Migration emit + `/enrich-profile` skill
**Files:** Create `src/unipaith/services/profile_enrichment/emit.py`; a `.claude` skill/workflow doc.
- [ ] `emit_migration(target, result)` writes an idempotent Alembic data migration that deep-merges the verified patch into the profile's JSONB via the shared base (Phase 1.5 base refactor) or directly onto the columns, stamped to `STANDARD_VERSION`; validated on a scratch DB.
- [ ] `/enrich-profile <target>` skill: run engine → judge → emit → show diff/report → ship via the standard pipeline (build→tests→scratch-validate→commit→PR→merge→deploy→verify).
- [ ] First real run: **Harvard** (+ a school + program) to standard — proof on a non-reference profile, verified fields only.

---

## Self-Review
**Spec coverage:** §7 engine → Tasks 2,4,6; §8 gate → Tasks 1,5; §9 delivery skill → Task 6. Phase 2a (Tasks 1–3) is the deterministic, shippable core; Phase 2b (Tasks 4–6) wires live web research + judge + the skill and is where real data first ships (Harvard). **Note:** the shared-base refactor (spec §4) is a prerequisite for the migration-emit in Task 6 — sequence it as "Phase 1.5" before Phase 2b, or have `emit_migration` write columns directly in the interim.

**Placeholder scan:** Tasks 1–3 are complete with code in the implementation; Tasks 4–6 describe concrete adapters with named inputs/outputs (no vague "handle errors").

**Type consistency:** `Researcher.gather`, `Evidence`, `GateDecision`, `EnrichmentResult` names match between `gate.py`, `engine.py`, and the tests.

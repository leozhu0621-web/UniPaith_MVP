# Profile Standard & Self-Growing Enrichment — Design

**Status:** approved design (brainstorming complete) — pending implementation plan

**Goal:** Make MIT (institution) → Sloan (school) → Master of Business Analytics (program) the single canonical standard for all three profile levels, build a self-growing enrichment routine that raises every profile to that standard, and make the standard *versioned* so changing the blueprint re-conforms the whole fleet automatically — with zero per-profile hand-editing and zero fabricated data.

**Architecture (one sentence):** One versioned `Standard` drives both the shared render and an enrichment engine; the engine researches and *verifies* real data before writing it; a conformance check loops stale profiles back to the engine, so editing the Standard once converges the entire fleet.

**Tech stack:** Python 3.12 / FastAPI / SQLAlchemy 2 (async) / Alembic (backend) · React 19 / TS / Vite (frontend, already-global render) · existing Spec 60 crawler + `uni_knowledge` retriever for research · `/schedule` cron for the background agent.

---

## 1. Decisions (locked during brainstorming)

| Decision | Choice |
|---|---|
| What propagates when the blueprint changes | **The whole blueprint** — layout, the set of sections/fields (IA), and the sourcing/wording rules. |
| How the routine runs | **Both** — an on-demand `/enrich-profile` skill *and* a scheduled background agent. |
| Ship autonomy | **Fully autonomous ship behind an exhaustive verification gate.** Verify everything (multi-pass, extra tokens fine); unverifiable facts are **omitted, never guessed**; no human staging queue required. |
| Re-conform on standard change | **Versioned standard, auto re-enrich the whole fleet.** Bump `STANDARD_VERSION` → every profile flagged stale → routine re-enriches to the new version. |
| Architecture | **Approach A** (versioned manifest + component render + conformance check), with the option to adopt declarative widgets *incrementally* for brand-new section types later. |
| Reference instance | **MIT / Sloan / MBAn ONLY.** Harvard and all other profiles are *fleet members that must conform* — never sources of the standard. |

## 2. Current state (what we build on)

- Each institution is a bespoke ~80–96 KB Python module (`unipaith-backend/src/unipaith/data/mit_profile.py`, `harvard_profile.py`) sharing the **same implicit shape** by hand-copy: identical top-level constants (`RANKING_DATA`, `SCHOOL_OUTCOMES`, `SCHOOLS`, `PROGRAMS`, `_OUTCOMES_*`, `_REQ_*`, `_TRACKS_*`, …) and the same `apply(session)` mapping into JSONB columns (`institutions.ranking_data`/`school_outcomes`, `schools.about_detail`, `programs.outcomes_data`/`cost_data`/`application_requirements`/`tracks`).
- Render is **already global**: every institution/school/program renders through the same `InstitutionDetail` / `SchoolSubunitPage` / `ProgramDetailPage`. A layout change is one component edit applied to every profile.
- Data ships via idempotent Alembic data migrations calling `<profile>.apply(session)` (flush-not-commit), validated on a scratch DB.
- **Gap:** the shared shape is a *convention you hand-copy*, with nothing enforcing it and nothing that fills a new section when you add one. There is no version, no conformance check, no enrichment engine.

## 3. The Standard (single source of truth)

A new backend package `unipaith-backend/src/unipaith/profile_standard/`:

### 3.1 `manifest.py`
- `STANDARD_VERSION: int = 1` — the one knob that, when bumped, re-conforms the fleet.
- `LEVELS = {"institution", "school", "program"}`.
- For each level, an **ordered** list of `Section`:
  - `Section(id, title, order, required, widget, fields=[Field(...)])`
  - `Field(key, label, type, sourcing, required)` where:
    - `type` ∈ {text, number, currency, percent, list[str], list[citation], distribution, chips, …}
    - `sourcing` = a reference into the playbook (which authoritative sources, citation requirement)
    - `widget` = a render hint (`stat-grid`, `chip-list`, `distribution-bar`, `citation-block`, `funnel`, `timeline`, …) — used by the render-parity test now and by optional declarative widgets later.
- The manifest is **extracted only from the MIT trio**: it enumerates exactly the sections the MIT/Sloan/MBAn pages render today (e.g. program-level: *Basic info · Admissions (requirements · timeline) · Costs & Aid · Outcomes (Employment & Placement, Salary Distribution — each with source + conditions) · Events & Updates · Insights*; institution-level: *report card · rankings · distinction · admissions funnel · outcomes/cost · campus resources · quick facts · sourced citation*; school-level: *About (facts & leadership · notable faculty · research centers · source) · Events & Updates · Programs*).
- Exported to `manifest.json` (generated artifact) so the frontend can read the same source of truth.

### 3.2 `playbook.md`
Per-field, human-readable rules the enrichment engine follows:
- **Authoritative sources** per field (e.g. employment figures → the institution's official career-office employment report; rankings → the named ranking body; tuition → the registrar/bursar page). First-party-never-overwritten authority precedence (reuse Spec 60's model).
- **Citation format** — every sourced field carries `{source, source_url}` (and `conditions`/methodology where applicable, as the MBAn outcomes already do).
- **Wording/tone** — editorial, content-rich, program-specific, never generic marketing (mirrors `CLAUDE.md` UI/Design preferences).
- **No-fabrication policy** — omit if unverifiable; never estimate a citable fact.

### 3.3 Versioning semantics
- A profile stores the `standard_version` it last satisfied (see §5).
- **`stale` is version-only:** `profile is stale ⇔ profile.standard_version < STANDARD_VERSION`. Missing required sections/fields are a **separate** conformance signal (`missing required`), not folded into `stale` — this keeps `check().stale` and the §9 ranking axes (`{stale, missing required, fact-age}`) orthogonal. A profile can be missing-required without being stale (it satisfied the current version but a field is gone/unverifiable) and stale without being missing-required (the blueprint moved on).
- **Omitted ≠ missing:** a required field recorded in `_standard.omitted` **at the current `standard_version`** counts as conformance-satisfied (honestly-empty), not missing — so the gate's no-fabrication omissions (§5–§8) don't re-queue endless enrichment for unverifiable required fields (e.g. a profile that legitimately lacks a citable source). A bump to `STANDARD_VERSION` clears this exemption (the omission is re-attempted once against the new standard); the refresh cadence (§9) may also periodically re-check omitted fields.
- Bumping `STANDARD_VERSION` makes the whole fleet stale by definition → drives §7 re-conform.

## 4. Shared base (`profile_base.py`)

- Extract the duplicated `apply()` JSONB-mapping out of `mit_profile`/`harvard_profile` into one `profile_base.apply(profile_data, session)` that maps **manifest-shaped data** → the JSONB columns.
- Each institution becomes **data + base**: `mit_profile` keeps only its DATA constants (the reference values) and delegates mapping to the base. Harvard is migrated the same way as a regular (initially incomplete) member.
- This is the change that lets the engine *grow new profiles* (write data) without hand-authoring a 90 KB module.
- **Safety:** the refactor is behavior-preserving — a test asserts `base.apply(mit_data)` produces byte-identical JSONB to today's `mit_profile.apply()` for the legacy-mapped payloads, before the old code is deleted (golden-output test on a scratch DB). The additive `_standard` metadata key (§5) is excluded from this comparison since legacy `mit_profile.apply()` never emitted it; the golden test compares everything *except* `_standard`.

## 5. Data model change

- Add a `standard_version` stamp per profile. Lowest-risk option: a `_standard` key inside the existing JSONB blobs (`{"version": N, "enriched_at": ..., "omitted": [...]}`) — **no migration of table schema**, written by `base.apply`. (Alternative: a dedicated nullable `smallint` column per level; decide in the plan. Default to the JSONB `_standard` key to avoid schema churn.)
- `omitted` records fields the verification gate could not confirm, so the conformance report can show coverage honestly.

## 6. Conformance & render parity

- `profile_standard/conformance.py` → `check(level, data) -> {missing_sections, missing_fields, stale, omitted}`.
- **Backend parity test:** the MIT/Sloan/MBAn reference data is **100% conformant** to the manifest (the gold trio defines the bar — if it fails, the manifest or the data is wrong).
- **Frontend parity test:** every manifest section has a render block in the detail pages and vice-versa (reuse the existing parity-test pattern — Spec 54 used `import.meta.glob`; here a generated `manifest.json` is the cross-check). This is what guarantees "add a section once → it renders on every profile."

## 7. Enrichment engine (`services/profile_enrichment/`)

Input: `(target, level, manifest, current_data)`. For each missing or stale field:
1. **Research** — web search/fetch the playbook's authoritative sources. Reuse Spec 60's `services/crawler` pipeline + `services/uni_knowledge.py` retriever (grounded-extractor-never-invents).
2. **Verify (the gate, §8)** — extract, cross-check, confidence-score.
3. **Conform** — write the value in the manifest's shape with `{source, source_url}` (+ `conditions` where the field type calls for it); OR **omit** and append to `_standard.omitted`.
4. **Emit** — an idempotent Alembic data migration calling `base.apply(updated_data, session)`, stamped to `STANDARD_VERSION`, validated on a scratch DB (the pattern already shipped for `mit_profile`).

Output: a migration + a human-readable diff/report (filled, refreshed, omitted-with-reason).

## 8. Verification gate (no-fabrication core)

A distinct, independently-tested module — the reason autonomous shipping is safe.

A field **ships only if all hold:**
- ≥ 2 **independent authoritative** sources agree (per the playbook's source list), OR one designated first-party source for first-party-only facts (e.g. the school's own employment report);
- the value carries a **citation** (`source` + resolvable `source_url`);
- numeric values **cross-check** within tolerance across sources;
- an **LLM-judge** pass (multi-pass; "double-check everything, extra tokens fine") finds no contradiction with the cited source text.

Otherwise the field is **omitted, never guessed.** Deterministic checks gate first (cheap, no key); the judge is the second layer. Reuses Spec 60 authority-precedence + grounded-extraction patterns and the Plan-2 fallback invariant (an agent failure never fabricates — it omits).

## 9. Delivery

- **`/enrich-profile <target>` skill** — runs the engine for one target in a session, prints the diff/report, and ships via the standard pipeline (build → tests → migration scratch-validate → commit → PR → merge → deploy → verify live). Fully autonomous per the standing rule, verified fields only.
- **Scheduled cloud agent** (`/schedule` cron) — wakes on a cadence, ranks the fleet by `{stale, missing required, fact-age}`, picks the top N within a token budget, runs the engine, ships verified updates, logs filled/omitted. Bounded per run.

## 10. Propagation model (the payoff)

Changing the blueprint, end to end:
1. Edit the manifest (add a section / change a field's sourcing) and bump `STANDARD_VERSION`.
2. Adjust the **one** shared render block (global — every profile shows it; new sections degrade gracefully when empty).
3. Conformance now flags **every** profile stale.
4. The routine (next scheduled pass + `/enrich-profile --all`) re-enriches each profile to the new version, verified-ship, backfilling the new section fleet-wide.
5. Fleet converges. **No profile was hand-edited.**

## 11. Phases (each independently shippable)

**Phase 1 — Standard foundation (keystone).** `profile_standard/` (manifest + playbook + version) extracted from the MIT trio; `profile_base.py` with golden-output safety test; MIT trio certified 100% conformant; Harvard migrated onto the base as a detectable-gaps member; conformance check + backend/frontend parity tests. *No enrichment yet.*

**Phase 2 — Enrichment engine + verification gate + `/enrich-profile` skill.** The engine, the gate (with its own unit + no-fabrication contract tests), and the on-demand skill. First real run: bring **Harvard** (+ one school + one program) up to the MIT standard — the machine's proof on a non-reference profile.

**Phase 3 — Scheduled agent + fleet re-conform.** The cron agent (ranking, bounded runs, logging); version-bump → all-stale → convergence; `/enrich-profile --all`; refresh cadence for stale facts; new-institution growth from a base shell; a conformance/enrichment report (optionally a `/goal` transparency surface later).

## 12. Testing

- Phase 1: manifest ↔ MIT-reference conformance · render ↔ manifest parity · `base.apply` golden-output (byte-identical to legacy, excluding the additive `_standard` key) + idempotency · migration scratch-DB validation.
- Phase 2: verification-gate units (reject single-source · reject source-disagreement · require citation · omit-unverifiable) · engine produces conformant + cited output for a fixture · **no-fabrication contract test** (gate can never emit an uncited field) · Harvard run leaves only verifiable fields.
- Phase 3: scheduler picks-stalest · version-bump-marks-all-stale · bounded-per-run · refresh-detects-newer-report.

## 13. Risks & mitigations

- **Refactoring MIT/Harvard onto a base could change live data.** → Golden-output test asserts byte-identical JSONB before deleting legacy code; ship behind a scratch-DB-validated migration.
- **A wrong source ships a wrong fact.** → ≥2-source agreement + citation + judge; omit on doubt; refresh cadence re-checks; `omitted` list keeps coverage honest.
- **Flattening the editorial design.** → Approach A keeps bespoke render; declarative widgets are opt-in for *new* section types only.
- **Background agent cost / runaway.** → bounded per run (N targets, token budget), logged; "extra tokens fine" applies to verification depth, not unbounded fan-out.
- **Manifest ↔ render drift.** → the parity test fails CI if a section lacks a render block or vice-versa.

## 14. Out of scope (now) / future

- A generic declarative-widget renderer (Approach B) — adopted incrementally per new section type, not a big-bang rewrite.
- A public `/goal` transparency surface for fleet conformance (nice-to-have in Phase 3+).
- Non-US institutions' source playbooks (the playbook is extensible per field; seed with US-authoritative sources first).

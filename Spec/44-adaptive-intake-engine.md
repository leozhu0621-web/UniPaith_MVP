# 44 · Adaptive Intake Engine

> The pipeline that turns student inputs (chat answers, form fills, uploads, links, platform activity) into normalized Prompt Library signals with provenance, confidence, and version history. Progressive completion thresholds, not exhaustive intake.
>
> Status: **draft v1.0** · 2026-05-29 · Depends on `42-prompt-library-schema.md` (signal schema) and `45-ai-agents-claude.md` (DiscoveryExtractor, DiscoveryValidator agents).

---

## 1. Purpose

The student NEVER fills a 200-field form. The engine populates the Prompt Library through multiple intake channels in the moment when each piece of information is most natural to provide:

1. **Conversational** (Discovery chat) — natural language.
2. **Structured** (form fields when precision is required).
3. **Document upload** (transcripts, portfolio, resume).
4. **External links** (LinkedIn, GitHub, personal site).
5. **Institution-provided** (program requirements, prerequisite catalogs).
6. **System-derived** (platform activity, derived flags).

Every channel feeds the same set of canonical Prompt Library fields. The engine reconciles, deduplicates, validates, and versions.

---

## 2. Layered storage model

Per Master Paper Business Methodology, four layers:

```
┌──────────────────────────────────────────────────────────────────┐
│ Engagement layer        ← behavioral telemetry (views/saves/...) │
├──────────────────────────────────────────────────────────────────┤
│ Derived signals layer   ← computed gates (readiness/completeness)│
├──────────────────────────────────────────────────────────────────┤
│ Normalized signals layer ← Prompt Library schema (canonical)     │
├──────────────────────────────────────────────────────────────────┤
│ Raw inputs layer        ← original answers/files/links/timestamps│
└──────────────────────────────────────────────────────────────────┘
```

- **Raw inputs** are immutable; updates create a new raw input. Lets us replay normalization if extractor improves.
- **Normalized signals** are the values used by every downstream service (match, application, workshop, etc.).
- **Derived signals** are computed from normalized; recomputed on any normalized change.
- **Engagement signals** never affect derived gating (e.g., a high apply_propensity_score does not unlock anything; it's a recommendation hint).

Storage map per `42` §8.

---

## 3. Per-signal pipeline

Every input value passes through:

```
[Source channel] → [Normalize] → [Validate] → [Persist with provenance + confidence + version]
                                     ↓
                                     fails → flag for clarification (visible to student)
```

### 3.1 Normalize
- Free text → enum value (e.g., "I want a master's degree" → `target_degree_level=master`). Done by `DiscoveryExtractor` per `45` §3.
- Free text → number/range (e.g., "around 40 grand a year" → `budget_band_annual_total=40-60k`).
- Free text → date (e.g., "starting in fall 2027" → `target_start_term_season=fall, target_start_term_year=2027`).
- Document → fields (e.g., transcript PDF → `student_courses[]`). OCR + LLM extraction.
- Link → fields (e.g., LinkedIn → `work[]`, `current_institution_name`, `education_context`). API or scrape (license-permitted).

### 3.2 Validate
- Type check (string vs int).
- Required-field check (per category).
- Enum membership.
- Range check (0–100 for percent; 1900–today for graduation_year).
- Cross-field consistency (e.g., `expected_graduation_date > date_of_birth + 16 years`).

Done by `DiscoveryValidator` (LLM second-pass) AND a schema-validation step. The schema check is authoritative; LLM check is advisory and feeds confidence.

### 3.3 Persist
- Write a new row to `raw_inputs` for the value.
- Upsert the normalized signal row with version++.
- Compute provenance chain (append event).
- Set confidence per the rules in `42-prompt-library-schema.md` §5.

### 3.4 Cross-module fanout
- Fire `event:signal_changed(student_id, signal_name, version)`.
- Subscribers:
  - **Match service** invalidates per-program `match_results` cache.
  - **Discovery service** updates `next_questions_to_ask_user`.
  - **Application service** re-evaluates `apply_ready_per_program` for each open application.
  - **Workshops** re-evaluates feedback signals if an open draft references this field.
  - **Audit ledger** writes a row.

---

## 4. Progressive completion thresholds

Per `42-prompt-library-schema.md` §6 — the engine enforces two gates:

### 4.1 Match-ready (Stage 1 → Stage 2)

Engine computes `match_ready=true` when:
- `core` field coverage ≥ the required subset (per `42` §6.1).
- `overall_profile_completeness_pct ≥ 35`.

While `match_ready=false`, Discover prompts continue (`DiscoveryOrchestrator` returns the next-best question keyed on missing categories). Discover's UI shows "X more questions until your first matches."

When `match_ready` flips true:
- Discover surfaces a Generate-strategy CTA.
- Match page (Explore) enables — but the strategy widget at top shows "Generate your first strategy" until run.

### 4.2 Apply-ready (Stage 2 → Stage 3, per program)

Engine computes `apply_ready_per_program[program_id]=true` when:
- All `core` fields above.
- All program-specific required fields per program's `requirements_checklist`.
- Visa fields per `visa_required_flag`.
- Portfolio per `has_portfolio_requirement_flag`.
- Recommenders sufficient for program's `recommendations_required`.
- Major-specific track signals per program's discipline.

UI in `/s/applications/:appId` shows the checklist with `apply_ready` boolean; "Mark as ready to submit" gate enables when all pass.

---

## 5. Intake channels — implementation surface

### 5.1 Discovery chat (the primary intake channel)

Each user turn:
1. Persist the message to `discovery_messages`.
2. Run `DiscoveryExtractor` (Haiku) → structured `extracted_signals`.
3. Run `DiscoveryValidator` → keep/reject.
4. Persist accepted signals via §3.
5. Run `DiscoveryOrchestrator` → next prompt.
6. Run `DiscoveryJudge` (every 3–5 turns) → continue / switch_layer / switch_track / handoff.
7. Stream the next prompt back to the student.

### 5.2 Profile section forms

Each form field is bound 1:1 to a Prompt Library field. On save:
1. Validate client-side (zod schema).
2. POST the change.
3. Server runs §3 pipeline (Normalize step is mostly identity; Validate runs schema check).
4. Per-section provenance: `source="student-typed"`, confidence=95.

### 5.3 Document upload

For each uploaded transcript / portfolio / resume / writing sample:
1. Upload to S3 via signed URL.
2. Run `DocumentParseTriage` (Haiku) → ok / needs_review / failed.
3. If ok: run domain-specific extractor (transcript → `student_courses[]`; resume → `work[]` + skills).
4. Each extracted field carries `source="student-uploaded"`, confidence per parse quality.
5. Surface extractions to the student for confirmation BEFORE persisting normalized values. Student confirms → confidence bumped to 95 + `source="student-confirmed"`.
6. If parse fails: surface "We couldn't read this. Try uploading a clearer copy or fill in the fields manually."

### 5.4 External link

For LinkedIn / GitHub / personal site:
1. Validate URL (`external_link_validation_status`).
2. Where API access exists (e.g., GitHub for repo metadata): fetch directly.
3. Where not (LinkedIn): require the student to verify they own the link by signing in via OAuth (Phase 2) or by uploading a screenshot (MVP fallback).
4. Extracted fields: `source="student-link"`, confidence 75.

### 5.5 Institution-provided (program requirement templates)

When an institution publishes a program:
1. Their `requirement_checklist` becomes the template for per-application apply-ready check.
2. Conditional fields (visa, portfolio, major-specific) follow flags.
3. `source="institution-supplied"`, confidence 95.

### 5.6 System-derived (platform activity)

Per `42` §3.16 engagement signals.
- Telemetry capture in frontend → server.
- Aggregated nightly (or in real-time for hot fields like `apply_propensity_score`).
- `source="system-derived"`, confidence 90.

---

## 6. Confidence + clarification loop

When a normalized signal has confidence < 60:
1. It's persisted with that confidence.
2. The `next_questions_to_ask_user` derived signal (per `42` §4.11) gets a corresponding entry: "Just to confirm — did you mean X?"
3. Discover surfaces the question on the student's next visit.
4. Student confirms → confidence → 95.
5. Student corrects → new value persisted with confidence 95.

This is the mechanism that keeps the platform from acting on hallucinated extractions.

---

## 7. Reconciliation rules

When multiple sources disagree:

| Conflict | Winner | Rationale |
|---|---|---|
| `student-typed` vs `system-extracted` | student-typed | Student authority. |
| `student-confirmed` vs `student-uploaded` | student-confirmed | Latest authority. |
| `third-party-verified` vs `student-typed` | third-party-verified | E.g., official transcript beats self-report. |
| `institution-supplied` vs `student-typed` (e.g., test score) | institution-supplied | Wins for this institution's app; student notified. |
| Two `student-typed` updates | latest | But provenance_chain retains the history. |

---

## 8. Engagement layer specifics

Engagement is captured at the event level (not per-page), batched, and aggregated nightly.

**Event types:** `view_program`, `save_program`, `unsave_program`, `add_to_compare`, `remove_from_compare`, `apply_started`, `apply_submitted`, `essay_drafted`, `interview_rsvp`, `interview_attended`, `event_rsvp`, `event_attended`, `message_sent_to_school`, `inquiry_submitted`.

Aggregation produces the §3.16 fields (`programs_saved_count`, `apply_propensity_score`, etc.).

Privacy: per `46` §2, engagement is gated on `consent.analytics` for cross-cohort aggregates; the student's own dashboard sees their own data unconditionally.

---

## 9. Cross-module consistency invariants

The engine maintains these invariants at all times:

1. **Single source of truth.** Per signal, exactly one canonical value visible to consumers. (Raw inputs may differ; normalized is canonical.)
2. **Provenance always knowable.** Every signal value has a traceable source chain back to a raw input.
3. **Version monotonic.** `version++` on every write; no decreasing.
4. **Confidence reflects current value.** When a low-confidence value is replaced by student-confirmed, the new confidence is the higher one — not a blend.
5. **Consent respected in flight.** Any agent reading signals checks `consent` per `46`.
6. **Audit always written.** Every change writes a `signal_change_event` row, separate from the `ai_audit_ledger`.

---

## 10. APIs (engine-facing)

```
POST /me/intake/messages                 → ingest a discovery-chat turn
POST /me/intake/form-save                → save a form-bound signal change
POST /me/intake/document-upload          → start an upload + parse pipeline
POST /me/intake/external-link            → ingest a link and run extraction
GET  /me/intake/clarifications           → list low-confidence values needing student confirmation
POST /me/intake/clarifications/:id/confirm → confirm or correct a value
GET  /me/intake/completeness             → completeness map per category
GET  /me/intake/match-ready              → boolean + reasons for false
GET  /me/intake/apply-ready/:program_id  → boolean + per-requirement detail
```

Each ingestion endpoint is consent-gated (`matching` for most; `outreach`/`analytics` only when applicable).

---

## 11. Tests

- Per-intake-channel: ingest → verify normalized field + provenance + confidence + version.
- Conflict resolution per §7.
- Match-ready and apply-ready gating per §4.
- Consent enforcement: `matching=false` → no LLM call.
- Clarification loop: low-confidence input → clarification visible in `/me/intake/clarifications`.
- Cross-module fanout: signal change invalidates downstream caches (match_results, derived flags).

---

## 12. Open questions / known gaps

- **Replay normalization on extractor upgrade.** When `DiscoveryExtractor` is improved, do we re-run on all historical raw inputs? Yes for confidence-50 or lower rows; skip the rest (cost concerns).
- **LinkedIn deep-extraction.** Currently no API access for non-employer accounts. MVP path: student-typed shortcuts seeded from their LinkedIn URL (just URL stored). Phase 2: OAuth-based extraction.
- **Transcript parsing accuracy across grading systems.** US, UK, IB, A-level, Gaokao differ. Initial parse: confidence ≤ 60 → always surface for confirmation. Improvement: train discipline-specific parsers per system.
- **Engagement signal latency.** Real-time updates would feel better for `apply_propensity_score`; nightly is fine for the others. Recommend: real-time for the 3-4 high-value engagement signals; nightly for the rest.
- **Bulk import for institution-supplied signals.** `24-data-upload.md` covers institution-side bulk import; the engine consumes those rows via the same §3 pipeline (treats them as `institution-supplied` source).

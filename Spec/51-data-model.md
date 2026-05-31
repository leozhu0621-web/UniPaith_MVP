# 51 · Data Model — Consolidated Table Map

> One map of the persisted schema so a builder doesn't reconstruct it from `42`/`43`/`44` or the model files. **Verified against the live SQLAlchemy models** (`unipaith-backend/src/unipaith/models/`, **107 tables across 23 model files**, as of 2026-05-30). `42`/`43` own *signal semantics*; this doc owns *physical schema as built*.
>
> Status: **draft v1.0** · 2026-05-30 · Build-integration doc. Source of truth = model code + Alembic migrations (`alembic/versions/`). Postgres 16 + pgvector. Most tables have `id` (UUID PK, `UUIDPrimaryKeyMixin`) + `created_at`/`updated_at` (`TimestampMixin`) — omitted below to cut noise.
>
> **Reality check:** the schema is FAR larger than the MVP feature set — 107 tables including a full ML-loop + knowledge-crawler subsystem. The student profile is already decomposed into real per-domain tables (not JSONB blobs). Much that other specs call "future" is **already built** — see §7.

---

## 1. How to read

- **Table** = `__tablename__`. FKs shown `→ table`. JSONB columns are common (flagged where notable).
- "Spec" links the feature doc owning the semantics.
- Genuinely-absent tables (spec'd but not in the model layer) are in §8 — that list is SHORT; assume a table exists unless listed there.

---

## 2. Student identity & profile (model file `student.py` + `goals/needs/identity/strategy`)

The profile is **fully relational**, not a JSONB dump. Core + per-domain tables:

| Table | Spec | Notes |
|---|---|---|
| `users` | `05` | unified identity (students + institution staff); `user.py` |
| `student_profiles` | `08` | the hub; FK target for almost every student table |
| `student_preferences` | `08` | institution/program preferences |
| `academic_records` | `08`,`42` | per-school academic history (**real table**) |
| `student_courses` | `42` | per-course rows (**real table**) |
| `test_scores` | `08`,`42` | standardized tests (**real table**) |
| `activities` | `42` | activities/leadership (**real table**) |
| `student_competitions` | `42` | (**real table**) |
| `student_research` | `42` | (**real table**) |
| `student_work_experiences` | `42` | (**real table**) |
| `student_portfolio_items` | `42` | (**real table**) |
| `student_languages` | `42` | (**real table**) |
| `student_online_presence` | `42` | links (LinkedIn/GitHub/site) |
| `student_visa_info` | `42` §3.3 | international (**real table**) |
| `student_accommodations` | `42` §3.2 | accessibility/accommodations |
| `student_scheduling` | `42` | availability |
| `student_major_readiness` | `43` | per-discipline readiness (**= the "major-specific" tables**) |
| `recommendation_requests` | `08` | recommenders |
| `student_data_consent` | `46` §2 | **consent IS built** — the 4-lever consent record |
| `student_goals` | `08` | SMART; `source` (discovery\|manual), `source_session_id`, `confidence` |
| `student_needs` | `08` | Maslow-keyed; `severity` |
| `student_identity` | `08`,`19` | core_values/worldview/self_awareness + `identity_summary` |
| `student_strategies` | `09` | versioned; one-active-per-student |
| `onboarding_progress` | `05` §11 | first-run state |

---

## 3. Discovery, matching, AI artifacts (`discovery.py`, `matching.py`, `ai_artifacts.py`, `confidence_outcome.py`)

| Table | Spec | Notes |
|---|---|---|
| `discovery_sessions` | `19` | `track`(profile\|goals\|needs), `layer`(basic\|personality\|identity), `completion_pct`, `exit_signal` |
| `discovery_messages` | `19`,`44` | append-only; `extracted_signals` JSONB (Plan-2 extractor) |
| `match_results` | `09` | `match_score` (legacy) — **dual fitness/confidence lives in the matching/scoring layer**; confirm columns before reading |
| `match_rationales` | `09`,`45` | `rationale_text`, `cited_student_fields`, `cited_program_fields`, `(profile_version,program_version,prompt_version)` cache key |
| `student_feature_vectors` | `45`,`06` | `embedding`, `sparse_features`, `applicant_summary` — L2→L3 handoff |
| `ai_turns` | `45` §8 | **the AI audit/cost ledger**: agent, surface, model, provider, tokens, cost_usd, latency, success, `consent_mask` — provenance spine |
| `ai_turn_feedback` | `37` | thumbs-up/down per AI turn |
| `confidence_outcome_pairs` | `09` | predicted confidence vs actual outcome (calibration) |
| `embeddings`, `model_registry`, `prediction_logs`, `raw_ingested_data`, `data_sources`, `institution_features`, `student_features`, `offer_comparisons` | `06`,`45` | the ML/matching substrate (`matching.py`) |

---

## 4. Application lifecycle (`application.py`)

| Table | Spec | Notes |
|---|---|---|
| `applications` | `15`,`18` | `status`, `match_score`, `completeness_status`, `missing_items`, `decision`, `decision_by/at/notes` |
| `application_checklists` | `15` | `items` JSONB, `completion_percentage`, `auto_generated_at` |
| `application_submissions` | `15` | submitted docs + package URL + confirmation number |
| `review_assignments` | `32` | reviewer ↔ application, due date, status |
| `rubrics` | `32` | per institution/program; `criteria` JSONB |
| `application_scores` | `32` | **(this is the "review" row)** criterion_scores, total_weighted_score, `scored_by_type` (human/AI) |
| `ai_packet_summaries` | `32`,`37` | AI review summary: strengths/concerns/criterion_assessments/recommended_score |
| `interviews` | `33` | proposed/confirmed times, type, status |
| `interview_scores` | `33` | criterion_scores + recommendation |
| `offer_letters` | `34` | offer_type, tuition/scholarship/assistantship, `financial_package_total`, conditions, `student_response` |
| `enrollment_records` | `35` | **enrollment IS built** — enrolled_at, enrollment_status, start_term |
| `integrity_signals` | `32` §7 | fraud/anomaly per application |
| `historical_outcomes` | `06` | per-program prior outcomes (matching training signal) |

---

## 5. Institution & engagement (`institution.py`, `engagement.py`)

| Table | Spec | Notes |
|---|---|---|
| `institutions` | `22` | rich profile JSONB (campus, outcomes, policies, international_info, social) |
| `schools` | `12` | sub-institution (e.g. "School of Engineering") |
| `programs` | `11`,`23` | `application_requirements`, `cost_data`, `outcomes_data`, `intake_rounds`, `tracks` (all JSONB) — read by EXACT key (CLAUDE.md) |
| `intake_rounds` | `23` | per-round windows + capacity + enrolled_count |
| `program_checklist_items` | `23` | per-program requirement items |
| `target_segments` | `26` | `criteria` JSONB |
| `campaigns` | `25` | + `campaign_recipients`, `campaign_links` (trackable, `short_code` → `/t/{short_code}`), `campaign_actions` |
| `events` | `20`,`27` | + `event_rsvps` |
| `institution_posts` | `27` | posts/updates; `pinned`, `tagged_program_ids`, `is_template` |
| `promotions` | `27` | spotlight/featured; impression/click counts |
| `inquiries` | `31` | inbound prospect/applicant inquiries; `assigned_to`, `campaign_id` |
| `communication_templates` | `25`,`29` | reusable subject/body + variables |
| `institution_datasets` | `24` | uploaded data; `column_mapping`, `validation_errors`, `usage_scope` |
| `reviewers` | `32` | institution staff reviewers; workload |
| `employer_feedback`, `student_program_reviews` | `11` | Insights (employer + student reviews) |
| `crm_records` | `26` | touchpoints |
| `saved_lists` + `saved_list_items` | `13` | saved programs |
| `student_calendar` | `16` | calendar entries (deadline/interview/work-block) |
| `student_engagement_signals` | `44` §8 | telemetry |
| `student_essays`, `student_resumes` | `14` | workshop drafts (feedback-only; see §6) |
| `conversations` + `messages` | `17`,`29` | **messaging uses `conversations`, not "threads"**; `conversation_sessions` tracks the LLM intake dialog |

---

## 6. Notifications, audit, workshops, ML-loop, knowledge

| Table(s) | Spec | Notes |
|---|---|---|
| `notifications`, `notification_preferences`, `touchpoints` | `21` | `workflow.py` |
| `admissions_audit_log`, `admin_audit_events` | `36` | append-only audit (two scopes) |
| `workshop_feedback_runs` | `14` | **feedback-only — mechanically excludes any generation field** (CI: `test_workshop_no_generation_contract.py`); rubric_scores/structural_issues/missing_elements/suggested_questions |
| `ml_loop.py`: `training_runs`, `evaluation_runs`, `drift_snapshots`, `fairness_reports`, `outcome_records`, `ab_test_assignments` | `46`,`06` | **fairness IS built** (`fairness_reports`); the full learning loop |
| `knowledge.py`: `knowledge_documents`, `knowledge_links`, `crawl_frontier`, `advisor_personas`, `person_insights`, `interaction_signals`, `engine_directives`, `engine_loop_snapshot` | — | knowledge/crawler subsystem (beyond MVP feature docs; exists in code) |
| `pipeline.py`: `pipeline_configs`, `pipeline_stage_snapshots` | `31` | admissions pipeline config |

---

## 7. What's ALREADY built that other specs imply is future

Correcting the common assumption — these exist in the model layer **now**:
- **Consent** → `student_data_consent` (not "implicit").
- **Enrollment/yield** → `enrollment_records` (the `35` data spine exists; UI/flow may not).
- **Fairness** → `fairness_reports` + the whole `ml_loop` (the `46` §6 harness has tables).
- **Profile sub-domains** → `academic_records`, `student_courses`, `test_scores`, `activities`, `student_work_experiences`, `student_languages`, `student_research`, `student_competitions`, `student_portfolio_items`, `student_visa_info` — all real tables, not JSONB.
- **Major-specific** → `student_major_readiness`.
- **Insights** → `employer_feedback`, `student_program_reviews`.

So building those features = wiring services/UI to **existing** tables, not creating schema.

---

## 8. Genuinely NOT built (spec'd, absent from `models/`) — the real build tasks

Short list — assume a table exists unless it's here:
| Planned | Spec | Note |
|---|---|---|
| `student_follows` | `20` §2 | Connect feed needs it — **not present** |
| `payments` | `39` | Phase-2 fees/deposit gateway — **not present** (note: `offer_letters` + `enrollment_records` exist, but no payment-transaction table) |
| Behavioral layer: `student_behavioral_responses`, `student_stories`, `student_decision_style`, `student_working_style`, `student_skills`, `student_friction_signals` | `42` §3.19–3.26 | story-bank / decision-psych — **not present** (future scope) |

> Migration discipline: `make migration MSG="…"`, import in `models/__init__.py`, **update the response schema in the same change** (CLAUDE.md). Never `metadata.create_all()` in a migration.

---

## 9. Conventions (as built)

- UUID PKs (`UUIDPrimaryKeyMixin`); `created_at`/`updated_at` (`TimestampMixin`).
- JSONB for evolving blobs (profile sections live as real tables, but program requirements/cost/outcomes are JSONB on `programs`); query by exact key; GIN-index hot keys.
- Versioning columns (`profile_version`, `program_version`, strategy `version`) drive cache invalidation (`45` §12); bump on write.
- pgvector (`embeddings`, `student_feature_vectors.embedding`) for match similarity (L3, `06` §4).
- Audit + ML-outcome + financial rows: append-only / never hard-deleted; student PII soft-delete + grace (`46`).

---

## 10. Open questions

- **`match_results` dual-score columns.** The table has legacy `match_score`; confirm where `fitness_score`/`confidence_score` physically live (separate columns vs the matching/scoring service output) before the frontend reads them — `09`/CLAUDE.md Phase E.
- **`users` vs `student_profiles` id space.** `users.py` defines a unified `users` table; most student FKs target `student_profiles.id`. Document the mapping (Cognito sub → users → student_profiles) so notification/audit `*_user_id` columns are unambiguous.
- **JSONB on `programs`.** Requirements/cost/outcomes are JSONB while student data is relational — fine, but the frontend reads program JSONB by exact key; keep `23` schemas authoritative.
- **Knowledge/crawler subsystem scope.** `knowledge.py` (8 tables) exists but isn't in any MVP feature doc — confirm it's in-scope or dormant, so the build doesn't wire dead tables.

# Student Data Standard

Companion to `docs/INSTITUTION_DATA_STANDARD.md`. The bar for what UniPaith collects from every student, derived from the appendix Prompt Library in `Platform_business_plan.docx`. The dev student `student@unipaith.co` (Leo) is the reference example — every field listed here is populated on that account after `scripts/fill_dev_student_profile.py` runs.

## Source hierarchy (same rule as the institution doc)

1. **Student self-report** — primary. Entered via the onboarding + profile UI.
2. **Evidence file** — transcript upload, score report, portfolio file, resume. Used to verify / enrich the self-reported values.
3. **Third-party derived** — Scorecard-normalized GPA, Niche percentile, LinkedIn skill tags. Always annotated via `reviewer_context` / `external_source`-style attribution.

"No mocks or placeholders" — if a value is truly unknown, leave it null and surface an honest empty state. Never invent a score or rank.

## Required INPUT fields (from appendix + Package A schema)

Bar is one "publishable" tier per student: the onboarding `completion_percentage` ≥ 80% (enforced by the matching engine at `matching_service.py:88`).

### 1. Identity & contact (`student_profiles`)

| Field | Source | Notes |
|---|---|---|
| `first_name`, `last_name` | Self-report | — |
| `preferred_name` | Self-report | What the student wants to be called |
| `name_in_native_script` | Self-report | Non-Latin-script name for international admissions |
| `preferred_pronouns` | Self-report | Free text, common forms validated loosely |
| `date_of_birth`, `place_of_birth` | Self-report | — |
| `gender_identity`, `legal_sex` | Self-report | Separate columns; legal_sex only required where program mandates |
| `nationality`, `passport_issuing_country`, `country_of_residence` | Self-report | Can all differ (dual citizen example) |
| `addresses` (JSONB) | Self-report | `{current, permanent, mailing, billing}` each `{line1, line2, city, state, postal_code, country}` |
| `emergency_contact` (JSONB) | Self-report | `{name, email, phone, relationship}` |
| `guardian` (JSONB) | Self-report, required only for minors | `{name, email, phone, relationship, custody_status}` |
| `secondary_email`, `secondary_phone` | Self-report | — |
| `preferred_contact_channel`, `preferred_platform_language`, `preferred_writing_language` | Self-report | — |
| `marital_status` | Self-report | For visa/financial-aid downstream |
| `residency_status_for_tuition`, `domicile_state`, `duration_of_residency_months` | Self-report + derivation | US-specific fields for in-state classification |
| `email_verified`, `phone_verified`, `id_verification_status` | System (verification flow) | Flags set after the verification step |

### 2. Academics (`academic_records` + `student_courses`)

| Field | Source | Notes |
|---|---|---|
| `institution_name`, `degree_type`, `field_of_study` | Self-report + transcript | — |
| `gpa`, `gpa_scale`, `weighted_gpa_flag` | Transcript | — |
| `normalized_gpa` | Derived | 4.0-scale; NULL until transcript parser runs |
| `start_date`, `end_date`, `is_current`, `leave_of_absence_flag`, `withdrawal_incomplete_flag` | Transcript | Plus `disruption_details` freeform when applicable |
| `honors`, `thesis_title` | Self-report | — |
| `country`, `transcript_language` | Self-report + doc | — |
| `credential_evaluation_status`, `credential_evaluation_report_url` | WES/ECE upload | — |
| `rigor_indicator_count` (summary) + `school_reported_rigor` (JSONB breakdown) | Transcript | JSONB: `{ap_count, ib_count, honors_count, college_count}` |
| `attendance_rate` | Transcript | Decimal 0-1 |
| `class_rank`, `class_rank_denominator`, `percentile_rank` | Counselor letter / school report | — |
| `grading_scale_type`, `term_system_type` | Transcript | `4.0 / 100 / letter / custom`, `semester / trimester / quarter / year` |
| `transcript_upload_url`, `translation_provided_flag` | S3 upload | — |
| `transcript_parse_status` | System | `not_parsed / parsing / parsed / failed` |

### 3. Standardized tests (`test_scores`)

| Field | Source | Notes |
|---|---|---|
| `test_type`, `total_score`, `section_scores`, `test_date` | Self-report + official upload | — |
| `is_official`, `is_verified` | Self-report + system | `is_official` = student claims official; `is_verified` = system compared hash with provider |
| `percentile` | Test provider / lookup table | 0–100 |
| `test_attempt_number`, `superscore_preference` | Self-report | — |
| `score_expiration_date` | Derived | 2yr TOEFL/IELTS, 5yr SAT/GRE |
| `test_waiver_flag`, `test_waiver_basis` | Self-report | — |
| `official_score_report_url` | S3 upload | — |
| `score_normalization_status` | System | `unmapped / mapped` |

### 4. Activities, work, research, portfolio, competitions, languages

Existing tables cover these (`activities`, `student_work_experiences`, `student_research`, `student_portfolio_items`, `student_competitions`, `student_languages`). Package A did not extend column sets on these because they already carry most appendix fields; further expansion is a follow-on package.

### 5. Preferences & intent (`student_preferences`)

| Field | Notes |
|---|---|
| `preferred_countries`, `preferred_regions`, `preferred_city_size`, `preferred_climate` | — |
| `budget_min`, `budget_max`, `funding_requirement` | — |
| `program_size_preference`, `career_goals`, `dealbreakers`, `goals_text` | `career_goals` is an array, `goals_text` is the long-form narrative |
| `career_goal_short_term` | NEW — appendix calls out short + long form |
| 7 × 0-10 scales: `weight_cost`, `weight_location`, `weight_outcomes`, `weight_ranking`, `weight_flexibility`, `weight_support`, `weight_time_to_degree` | Feed the matching preference-vector |
| `application_intensity` (`few_deep / many_broad / balanced`) | — |
| `preferred_learning_style` (`lecture / project / research / mixed`) | — |
| `preferred_program_style` (`theory / applied / mixed`) | — |
| `research_interest_level`, `thesis_interest` | — |
| `return_home_intent` (international students) | — |
| `risk_tolerance`, `stretch_target_safety_mix` | Drives school-list composition |
| `target_degree_level`, `target_start_term` | — |
| `values_priorities` (JSONB) | Free-shape keyed preferences beyond the 7 weights |

### 6. Visa / international (`student_visa_info`)

Covered: `current_immigration_status`, `visa_required`, `target_study_country`, `passport_expiration_date`, `sponsorship_source`, `financial_proof_available/_amount_band`, `post_study_work_interest`, `prior_visa_refusals`, `travel_constraints`, `work_authorization_needed`, **plus Package A additions**: `current_location_city`, `current_location_country`, `dependents_accompanying`, `intended_start_term`, `visa_type_current`, `country_of_citizenship` (distinct from nationality for dual citizens).

### 7. Compliance & consent (`student_data_consent`)

Covered: `consent_matching`, `consent_outreach`, `consent_research`, `data_retention_preference`, `deletion_requested`, **plus Package A additions**: `first_generation_status` + `first_generation_definition`, `ferpa_release`, `honor_code_ack`, `background_check_required`, `code_of_conduct_ack`, `criminal_history_disclosed`, `disciplinary_history_disclosed`, `immunization_compliance`, `health_insurance_waiver_intent`, `military_status`, `veteran_status`, `prior_academic_dismissal_flag`, `directory_info_release`, `third_party_sharing_consent`, `marketing_channel_consent` (JSONB per-channel), `consent_revocation_timestamps` (JSONB array).

### 8. Major-specific readiness (`student_major_readiness`) — NEW

One row per `(student_id, track)`. `track` is one of `cs / engineering / business / health / arts / humanities`. `readiness_data` is a JSONB blob with the appendix per-track self-rating fields (CS has ~73, Engineering ~44, Business ~48, Health ~30, Arts ~52, Humanities ~50).

**CS track reference fields** (see NYU example in `scripts/fill_dev_student_profile.py:ensure_cs_major_readiness`):
- Programming: `primary_programming_language`, `programming_languages_list`, `tool_ide_list`, `tool_cloud_list`, `tool_db_list`, `tool_version_control_level`.
- CS fundamentals self-ratings 1-5: algorithms, data structures, OS, networks, databases, discrete math, concurrency, security, software engineering.
- Math readiness 1-5: calculus, linear algebra, probability, statistics.
- ML readiness 1-5: classification/regression, deep learning, model evaluation, NLP, time series.
- Data skills 1-5: EDA, SQL, feature engineering, visualization.
- SWE workflow: CI/CD, code review, testing, system design exposure, MLOps exposure + tools.
- Focus area: `data_vs_ai_vs_cyber_vs_swe`, `specialization_interests`.
- Evidence: `github_profile_link`, `open_source_contributions_flag`, `research_experience_flag`, `work_experience_tech_flag`, `work_experience_months_tech`.

Each track section in the appendix is its own mini-schema; copy the pattern when adding a new track.

### 9. Recommendations (`recommendation_requests`)

Existing table — `recommender_name`, `recommender_email`, `recommender_title`, `recommender_institution`, `recommender_relationship`, `status`, `requested_at`, `due_date`, `notes`, `target_program_id`. Minimum bar: at least **3 recommenders** (teacher / counselor / supervisor pattern).

### 10. Platform analytics (`student_platform_events`) — NEW

Broad analytics events — not program-scoped (program-scoped engagement still goes to `student_engagement_signals`). Schema: `event_type`, `event_metadata` (JSONB), `session_id`, `device_type`, `url_path`, `referral_source`, `utm_campaign`, `ip_country`, `occurred_at`.

Event-type vocabulary (minimum set):
- Session: `login`, `logout`, `session_start`, `session_heartbeat`
- Discovery: `search`, `program_view`, `school_view`, `compare`, `filter_applied`
- Funnel: `cta_save`, `cta_apply`, `cta_ask_counselor`, `cta_message`
- Editing: `profile_edit`, `essay_draft_saved`, `document_uploaded`
- Drop-off: `form_abandoned`, `tab_closed`

Each row feeds the OUTPUT-side engagement signals (apply propensity, churn risk, drop-off diagnosis, next-best-action, segment label).

## Completeness score

Extended from the existing `onboarding_progress.completion_percentage`. When scaling, use these weights:

- account + basic_profile: 25%
- academics (≥1 record with rigor + transcript): 15%
- test_scores (≥1 verified): 10%
- activities + research + work (≥2 total): 10%
- online_presence (≥1): 5%
- languages (≥1): 5%
- visa_info (for international): 5%
- data_consent (all 5 core flags set): 5%
- preferences (all 7 weights set + career goals): 10%
- major_readiness (≥1 track populated): 5%
- recommendations (≥3 requests): 5%

Threshold: ≥80% = **publishable** (Match Analysis unlocks).

## OUTPUT features (derived — Package B scope, not this doc)

The appendix lists ~280 OUTPUT features (contactability, data-quality, academic readiness bands, resume readiness, career-alignment, feasibility band, preference vector, churn risk, apply propensity, etc.). These are computed from the INPUT fields above. Package B wires the inference pipeline to produce and persist them. Until Package B lands, the UI shows null / honest empty states for derived signals.

## NYU example (reference fill)

The dev student `student@unipaith.co` is the end-to-end example of this standard. Run:

```bash
cd /Users/leozhu/Desktop/工作/Platform/UniPaith_MVP
unipaith-backend/.venv/bin/python scripts/fill_dev_student_profile.py
```

The script is idempotent: every step GETs first and either creates, updates, or skips. Re-running it against a scratch account produces a fully-populated reference student matching this standard.

## Scaling procedure (for the next scaling session)

1. Pick a pilot student cohort (e.g., 20 real high-school seniors or a test user set).
2. For each, walk through the onboarding UI and collect the INPUT fields listed above. Anything auto-derivable (GPA normalization, transcript parse, score percentile lookup) runs in Package B's pipeline post-ingest.
3. For the major-specific section, prompt per-track — most students fill one track initially; they can add more.
4. Log `student_platform_events` from day one so Package B has signal data.
5. Validate each student profile against the completeness score; ≥80% unlocks matching.
6. Spot-check 10% of the cohort against this doc to confirm no appendix fields were skipped.

The NYU example proves the full loop works: complete student profile → matches computed on 61 NYU programs → Match Analysis tab renders with tier + score + reasoning.

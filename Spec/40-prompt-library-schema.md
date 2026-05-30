# 40 · Prompt Library — Canonical Signal Schema

> The enumerated catalog of every signal the platform captures, derives, and consumes. The Master Paper calls this Appendix A and the Business Methodology treats it as the operational schema. This doc is the single source of truth for field names, data types, taxonomies, provenance, and where each signal flows.
>
> Status: **draft v1.0** · 2026-05-29 · Sources: Master Paper Appendix A (lines 2929–5185 of `/tmp/master_paper.txt`), Business Methodology §3 (Prompt Library & Adaptive Intake Engine, lines 1231+).
>
> **Used by:** every spec that touches student data (`10`, `11`, `12`, `13`, `15`, `16`, `17`, `1A`, `1B`, `22`, `30`, `31`, `35`, `41`, `42`, `43`).

---

## 1. What this is

The Prompt Library is the **schema contract** for every fact UniPaith knows about a student. Two parallel hierarchies:
- **INPUT FEATURES** — what students provide, the platform captures, or the institution supplies. ~250 fields across 13 cross-cutting categories + ~120 fields across major-specific subsections.
- **OUTPUT FEATURES** — what the inference layer derives. ~150 fields organized 1:1 against the input categories plus a final "behavioral questions & prompts" category.

Both hierarchies use the same category headings so any input has a clear output home, and the inference layer's responsibilities are visible at a glance.

> **Important defect note**: the Master Paper source contains two near-duplicate sections (Activities/Leadership/Competitions/Research is a near-duplicate of Work/Internships/Service; Recommendations is verbatim duplicate of Portfolio). This spec resolves both — Activities is its own structured-entry list; Recommendations gets its own field list per §3.7.
>
> **Two complementary sources** — this schema is the union of two files, neither complete alone:
> 1. **`Misc./Prompt Library.docx`** — the deepest INPUT enumeration (~900 fields), including the rich behavioral-prompt / story-bank / decision-psychology / working-style / per-major blocks reproduced in §3.19–§3.26. **Untyped** (no Categorical/Numeric/Text tags); classification carried via inline suffixes (`(policy-gated)`, `(derived)`, `(implicit)`, `(if applicable)`).
> 2. **Master Paper Appendix A** — the **typed** I/O catalog (every field tagged Categorical/Numeric/Text) AND the entire OUTPUT half (§4). Drops the behavioral/story-bank input depth.
>
> For a build-ready schema you need both: §3.1–§3.18 + §3.19–§3.26 (inputs) and §4 (outputs). The standalone file's classification suffix conventions:
> - `(policy-gated)` — sensitive-data class (criminal/disciplinary/immigration-violation/probation/government-ID); collection + visibility gated by policy.
> - `(derived)` — computed from other fields (e.g., `age`, `gpa_trend_metric`).
> - `(implicit)` — behavioral telemetry, not user-entered (the whole engagement section).
> - `(if applicable)` / `(where relevant)` / `(some programs)` — conditional class.
> - `reuse allowed flag (core vs school-specific)` — the one explicit core-vs-school-specific dichotomy; scoped to behavioral prompts.

---

## 2. Field convention

Each field row in the catalogs below uses this format:

```
field_name — Data type | Allowed values / format | Source(s) | Conditional / Core / Major-specific | Sensitivity
```

- **Data type:** `string` · `int` · `float` · `bool` · `date` · `datetime` · `enum<X|Y|Z>` · `array<T>` · `json<schema>` · `text<long>`.
- **Source(s):** comma-separated from: `student-typed` · `student-uploaded` · `student-link` · `student-derived` · `institution-supplied` · `system-derived` · `system-extracted` · `third-party-verified`.
- **Classification:**
  - `core` = collected for every student.
  - `conditional` = collected only when a gating flag is true (e.g., visa fields only if `international=true`).
  - `program-specific` = required by certain programs (e.g., portfolio for art programs).
  - `major-specific` = relevant only to students targeting a particular discipline.
- **Sensitivity:** `public` · `pii` · `pii-sensitive` (FERPA-gated) · `policy-gated` (criminal, disciplinary, etc.) · `health-pii` (HIPAA-adjacent).

All fields carry the universal record metadata (per §6):
- `value`, `value_normalized`, `source`, `confidence`, `created_at`, `updated_at`, `version`, `raw_input_ref`.

---

## 3. INPUT FEATURES

### 3.1 Identity, contact, account
**Universe:** every student. **Classification:** core. **Sensitivity:** pii / pii-sensitive.

| Field | Type | Notes |
|---|---|---|
| `legal_name` | string | Passport. |
| `preferred_name` | string | Display name. |
| `name_in_native_script` | string | E.g., Han characters. |
| `previous_legal_names` | array<string> | Name change history. |
| `alternate_spellings` | array<string> | |
| `preferred_pronouns` | enum<she/her, he/him, they/them, custom> | |
| `gender_identity` | enum (extensible) | |
| `legal_sex_at_birth` | enum<F, M, X, prefer_not_to_say> | Only if required by program. |
| `date_of_birth` | date | Derives `age`. |
| `age` (derived) | int | system-derived. |
| `place_of_birth` | json<{city, country}> | |
| `country_of_birth` | enum (ISO 3166) | |
| `nationality` | enum (ISO 3166) | |
| `citizenship_primary` | enum (ISO 3166) | |
| `citizenship_secondary` | enum (ISO 3166) | Dual-citizenship flag derived. |
| `passport_issuing_country` | enum (ISO 3166) | |
| `national_id_non_us` | string | pii-sensitive. |
| `government_id_last_4` | string | policy-gated. |
| `photo_id_presence_flag` | bool | |
| `marital_status` | enum<single, partnered, married, divorced, widowed> | |
| `custody_legal_guardian_status` | enum<self, parent, guardian> | Conditional on minor. |
| `primary_email` | string | |
| `secondary_email` | string | |
| `primary_phone_number` | string | |
| `secondary_phone_number` | string | |
| `preferred_contact_channel` | enum<email, sms, in_app, phone> | |
| `whatsapp_handle` | string | |
| `wechat_id` | string | |
| `linkedin_profile_link` | string | |
| `personal_website_link` | string | |
| `mailing_address` | json<address> | |
| `permanent_address` | json<address> | |
| `billing_address` | json<address> | |
| `current_address` | json<address> | line1, line2, city, region, country, postal_code, country_of_residence, time_zone |
| `domicile_state_us` | enum (US state) | Conditional on US. |
| `duration_of_residency_in_domicile` | int (months) | |
| `residency_status_for_tuition_classification` | enum<in_state, out_of_state, international> | |
| `emergency_contact_full_name` | string | |
| `emergency_contact_relationship` | enum<parent, guardian, sibling, spouse, friend, other> | |
| `emergency_contact_email` | string | |
| `emergency_contact_phone` | string | |
| `guardian_parent_full_name` | string | Conditional on minor. |
| `guardian_parent_email` | string | |
| `guardian_parent_phone` | string | |
| `guardian_parent_relationship` | enum<parent, guardian, foster_parent, other> | |
| `preferred_platform_writing_language` | enum (ISO 639-1) | |
| `communication_preferences_email_frequency` | enum<all, weekly_digest, important_only, none> | |
| `communication_preferences_sms_whatsapp_optin` | bool | |
| `accessibility_dyslexia_friendly_mode` | bool | |
| `accessibility_font_size` | enum<small, medium, large, x_large> | |
| `accessibility_other_accommodations_mode` | text<long> | |

### 3.2 Eligibility, compliance, consent
**Universe:** every student. **Classification:** core. **Sensitivity:** pii-sensitive / policy-gated.

| Field | Type | Notes |
|---|---|---|
| `adult_minor_status` | enum<adult, minor> | system-derived from DOB. |
| `first_generation_status` | bool | |
| `first_generation_definition_selected` | enum<def_v1, def_v2, ...> | Tracks WHICH definition the student selected. |
| `veteran_status` | bool | |
| `military_status` | enum<none, active_duty, reservist, veteran, dependent> | |
| `disability_accommodations_needed` | bool | |
| `disability_category` | array<enum> | |
| `disability_documentation_status` | enum<none, in_progress, available, verified> | |
| `disability_accommodations_details` | text<long> | |
| `health_insurance_waiver_intent_us` | bool | Conditional on US. |
| `health_insurance_waiver_proof_required_flag` | bool | |
| `immunization_compliance_status` | enum<unknown, compliant, partial, non_compliant> | |
| `criminal_history_disclosure_status` | enum<none_disclosed, disclosed, withheld> | **policy-gated.** |
| `disciplinary_history_disclosure_status` | enum<none_disclosed, disclosed, withheld> | **policy-gated.** |
| `prior_academic_dismissal_suspension_disclosure_status` | enum<none_disclosed, disclosed> | **policy-gated.** |
| `honor_code_acknowledgement_flag` | bool | |
| `code_of_conduct_acknowledgement_flag` | bool | |
| `background_check_required_flag` | bool | |
| `directory_information_release_preference_us` | enum<release, withhold> | **FERPA.** |
| `ferpa_release_preference_us` | enum<release, withhold> | **FERPA.** |
| `consent_status_minor_consent_workflow_needed_flag` | bool | |
| `consent_use_for_matching` | bool | DEFAULT true. |
| `consent_use_for_outreach_marketing` | bool | DEFAULT false. |
| `consent_use_for_research_analytics` | bool | DEFAULT false. |
| `consent_use_for_model_training` | bool | DEFAULT false. **The 4th lever.** Enforced per `03-llm-claude-migration.md` §11. |
| `consent_timestamps` | array<datetime> | Per change. |
| `consent_version_id` | string | E.g., "consent_v1.2_2026-05". |
| `consent_revocation_timestamps` | array<datetime> | |
| `marketing_channel_specific_consent` | json<{email: bool, sms: bool, calls: bool}> | |
| `third_party_data_sharing_consent` | bool | |
| `data_deletion_request_status` | enum<none, requested, in_progress, completed> | GDPR-style. |
| `data_retention_preference` | enum<standard, minimum, extended> | |

### 3.3 Visa & immigration (international)
**Universe:** students with `nationality` ≠ target study country. **Classification:** conditional. **Sensitivity:** pii-sensitive.

| Field | Type | Notes |
|---|---|---|
| `target_study_country` | enum (ISO 3166) | |
| `visa_required_for_target_country_flag` | bool | system-derived from nationality × target. |
| `current_immigration_status` | enum (per country) | |
| `current_visa_type` | enum | |
| `passport_expiration_date` | date | |
| `prior_visa_refusals_denials_flag` | bool | |
| `prior_visa_refusals_denials_details` | text<long> | |
| `intended_start_term` | enum<fall_2026, spring_2027, ...> | |
| `marital_status_for_visa` | enum<single, married, partnered> | |
| `dependents_accompanying_flag` | bool | |
| `financial_proof_available_flag` | bool | |
| `financial_proof_amount_band` | enum<lt_20k, 20-50k, 50-100k, gt_100k> (USD-equivalent) | |
| `sponsorship_source_type` | enum<self, family, scholarship, employer, government> | |
| `work_authorization_need_during_study` | bool | |
| `post_study_work_interest` | enum<OPT, PGWP, none, other> | |
| `travel_constraints` | text<long> | |
| `current_location_city` | string | |
| `current_location_country` | enum (ISO 3166) | |

### 3.4 Current education context
**Universe:** every student. **Classification:** core.

| Field | Type | Notes |
|---|---|---|
| `current_institution_name` | string | |
| `institution_country` | enum (ISO 3166) | |
| `institution_city` | string | |
| `institution_type` | enum<high_school, community_college, college, university, other> | |
| `curriculum_system` | enum<IB, A_level, AP, Gaokao, other_national> | |
| `language_of_instruction` | enum (ISO 639-1) | |
| `current_academic_year_level` | enum<grade_9, grade_10, grade_11, grade_12, freshman, sophomore, junior, senior, masters_y1, ...> | |
| `program_major_current` | string | |
| `enrollment_status` | enum<full_time, part_time, on_leave, withdrawn> | |
| `expected_graduation_date` | date | |
| `transfer_applicant_flag` | bool | |
| `gap_year_status_planned_gap_flag` | bool | |
| `education_interruptions_explanation` | text<long> | |
| `school_counselor_available_flag` | bool | |
| `school_counselor_contact` | json<{name, email, phone}> | |

### 3.5 Academic record
**Universe:** every student. **Classification:** core. **Sensitivity:** pii-sensitive (some fields).

**Top-level summary fields:**

| Field | Type | Notes |
|---|---|---|
| `gpa_reported` | float | |
| `gpa_scale_max` | enum<4.0, 5.0, 10.0, 100, custom> | |
| `weighted_gpa_flag` | bool | |
| `class_rank_numeric` | int | |
| `class_rank_denominator` | int | class size |
| `percentile_rank` | float | system-derived. |
| `school_reported_rigor_indicators_ap_count` | int | |
| `school_reported_rigor_indicators_ib_count` | int | |
| `school_reported_rigor_indicators_honors_count` | int | |
| `academic_honors` | array<string> | |
| `attendance_rate` | float (0-1) | |

**Per-course repeatable entries** (table `student_courses`):

| Field | Type | Notes |
|---|---|---|
| `course_code` | string | |
| `course_name` | string | |
| `course_subject_area` | enum (broad subject taxonomy) | |
| `course_level` | enum<regular, honors, AP, IB, college, dual_enrollment> | |
| `course_start_date` | date | |
| `course_end_date` | date | |
| `term_label` | string | |
| `term_semester_system_type` | enum<semester, quarter, trimester, year> | |
| `credits_units` | float | |
| `grade_format` | enum<letter, percent, pass_fail, narrative> | |
| `grade_value_as_reported` | string | Raw. |
| `pass_fail_outcome` | enum<pass, fail, n/a> | |
| `withdrawal_incomplete_flag` | bool | |
| `repeated_course_flag` | bool | |

**Transcript metadata:**

| Field | Type | Notes |
|---|---|---|
| `transcript_uploads` | array<file_ref> | |
| `transcript_language` | enum (ISO 639-1) | |
| `translation_provided_flag` | bool | |
| `credential_evaluation_provided_flag` | bool | |
| `credential_evaluation_report_link` | string | |
| `grading_scale_type` | enum<4.0, 100, letter, custom> | |
| `leave_of_absence_flag` | bool | |
| `leave_disruption_dates` | array<{start: date, end: date}> | |
| `disruption_explanation` | text<long> | |
| `disciplinary_academic_record_flag` | bool | **policy-gated.** |
| `disciplinary_academic_record_details` | text<long> | **policy-gated.** |

### 3.6 Standardized tests
**Universe:** every student (each test repeatable). **Classification:** core. **Sensitivity:** pii.

| Field | Type | Notes |
|---|---|---|
| `test_type` | enum<SAT, ACT, TOEFL, IELTS, DET, GRE, GMAT, AP, IB, MCAT, LSAT, ...> | |
| `test_date` | date | |
| `test_attempt_number` | int | |
| `section_name` | enum (per test) | |
| `section_score` | int | |
| `writing_essay_score` | int | |
| `subscore_name` | string | |
| `subscore_value` | int | |
| `percentile` | float | |
| `superscore_preference_availability_flag` | bool | |
| `score_expiration_date` | date | |
| `official_score_report_uploaded` | file_ref | |
| `official_score_verified_flag` | bool | third-party-verified. |
| `registration_candidate_id` | string | **policy-gated.** |
| `test_waiver_requested_flag` | bool | |
| `test_waiver_basis` | text<long> | |

### 3.7 Recommendations *(distinct from Portfolio — Master Paper duplication corrected)*
**Universe:** students with at least one application. **Classification:** core.

**Recommenders table** (repeatable):

| Field | Type | Notes |
|---|---|---|
| `recommender_full_name` | string | |
| `recommender_email` | string | |
| `recommender_phone` | string | |
| `recommender_title` | string | |
| `recommender_organization` | string | |
| `recommender_relationship` | enum<teacher, professor, advisor, supervisor, mentor, coach, counselor, other> | |
| `recommender_years_known` | int | |
| `waiver_consent` | bool | Student waives right to see the letter. |
| `requested_at` | datetime | |
| `due_date` | date | |
| `submission_status` | enum<not_requested, requested, in_progress, submitted, declined> | |
| `submission_date` | datetime | |
| `letter_upload` | file_ref | If institution accepts uploads. |
| `recommendation_platform` | enum<UniPaith, Common_App, Naviance, direct_email, school_portal> | |

### 3.8 Work, internships, service
**Universe:** every student. **Classification:** core. Repeatable entries (table `student_work`).

| Field | Type | Notes |
|---|---|---|
| `has_work_experience` | bool | top-level flag |
| `current_employment_status` | enum<student, employed, unemployed, on_leave> | |
| `employment_type` | enum<internship, part_time, full_time, volunteer, fellowship> | |
| `organization_name` | string | |
| `organization_city` | string | |
| `organization_country` | enum (ISO 3166) | |
| `role_title` | string | |
| `start_date` | date | |
| `end_date` | date | |
| `currently_in_role` | bool | |
| `hours_per_week` | int | |
| `hours_total` | int | derived |
| `compensation_type` | enum<paid, unpaid, stipend> | |
| `description` | text<long> | |
| `impact_scale_metrics` | text<long> | |
| `responsibilities` | text<long> | |
| `key_achievements_impact_metrics` | text<long> | |
| `skills_tools_used` | array<string> | |
| `team_size` | int | |
| `people_led_count_or_band` | int | |
| `budget_managed` | float | |
| `supervisor_name` | string | |
| `supervisor_title` | string | |
| `supervisor_email` | string | |
| `supervisor_phone` | string | |
| `permission_to_contact_supervisor_flag` | bool | |
| `employment_verification_document` | file_ref | |
| `preferred_industry` | enum (taxonomy) | |
| `preferred_function` | enum | |
| `resume_cv_upload` | file_ref | top-level on student, not per-entry |

### 3.9 Activities, leadership, competitions, research *(distinct from Work — Master Paper duplication resolved)*
**Universe:** every student. **Classification:** core. Repeatable entries (table `student_activities`).

| Field | Type | Notes |
|---|---|---|
| `activity_name` | string | |
| `primary_activity_category` | enum<club, sport, music, arts, community, leadership, academic, religious, political, hobby, other> | |
| `role_position` | enum<member, officer, lead, founder, other> + `role_title` string | |
| `leadership_level` | enum<member, lead, officer, founder> | |
| `leadership_title` | string | |
| `start_date` | date | |
| `end_date` | date | |
| `currently_active` | bool | |
| `hours_per_week` | int | |
| `weeks_per_year` | int | |
| `scope` | enum<school, regional, national, global> | |
| `description_impact` | text<long> | |
| `awards_related_to_activity` | text<long> | |
| `reference_coach_advisor_contact` | json<{name, email, phone, title}> | |

**Competitions sub-list** (table `student_competitions`):

| Field | Type | Notes |
|---|---|---|
| `competition_name` | string | |
| `level` | enum<school, district, state, national, international> | |
| `year_date` | date | |
| `role` | enum<participant, team_lead, organizer> | |
| `result_placement` | string | |
| `link_proof` | string | |
| `domain` | enum<math, CS, science, business, debate, art, music, sports, other> | |

**Research sub-list** (table `student_research`):

| Field | Type | Notes |
|---|---|---|
| `research_topic_title` | string | |
| `field_discipline` | enum (taxonomy) | |
| `institution_lab` | string | |
| `advisor_pi_name` | string | |
| `start_date` | date | |
| `end_date` | date | |
| `role` | enum<assistant, independent, lead> | |
| `outputs` | array<enum<paper, poster, code, dataset, presentation>> | |
| `publication_link_doi` | string | |
| `conference_presentation_details` | text<long> | |
| `methods_tools` | text<long> | |
| `abstract_summary` | text<long> | |
| `outcomes_impact` | text<long> | |

### 3.10 Portfolio & creative work
**Universe:** students targeting arts/design/architecture/media OR with portfolio_required programs. **Classification:** program-specific.

| Field | Type | Notes |
|---|---|---|
| `has_portfolio_requirement_flag` | bool | system-derived from target programs. |
| `portfolio_type` | enum<art, design, music, writing, film, architecture, dance, theater, photography, code> | |
| `portfolio_link_primary` | string | |
| `additional_portfolio_links` | array<string> | |
| `portfolio_upload` | array<file_ref> | |
| `portfolio_pieces_count` | int | |
| `portfolio_rubric_criteria` | text<long> | Per program. |
| `portfolio_submission_deadline` | date | Per program. |

**Per-piece repeatable** (table `student_portfolio_pieces`):

| Field | Type | Notes |
|---|---|---|
| `title` | string | |
| `type` | enum<image, video, pdf, audio, code, text> | |
| `description` | text<long> | |
| `tags_keywords` | array<string> | |
| `media_technique` | string | |
| `creation_date` | date | |
| `size_duration` | json | bytes or seconds |
| `role_solo_team` | enum<solo, team> | |
| `collaborators` | text<long> | |
| `external_link` | string | |

**Performing arts subset** (when `portfolio_type` ∈ {music, dance, theater}):

| Field | Type | Notes |
|---|---|---|
| `audition_required_flag` | bool | |
| `audition_instrument_voice_type` | string | |
| `audition_repertoire_list` | text<long> | |
| `audition_recording_link_upload` | string | |

### 3.11 Languages
**Universe:** every student. **Classification:** core. Repeatable entries (table `student_languages`).

| Field | Type | Notes |
|---|---|---|
| `language` | enum (ISO 639-1) | |
| `proficiency_level` | enum<A1, A2, B1, B2, C1, C2> (CEFR) or `enum<novice, intermediate, advanced, superior>` (ACTFL) | |
| `proof_type` | enum<self_report, test_certificate> | |
| `proof_document` | file_ref | If certificate. |
| `last_used_date` | date | |
| `frequency_of_use` | enum<daily, weekly, monthly, rarely> | |
| `can_demonstrate_flag` | bool | |

### 3.12 Intent, goals, priorities, tradeoffs
**Universe:** every student. **Classification:** core.

| Field | Type | Notes |
|---|---|---|
| `motivation_for_study` | text<long> | |
| `career_goal_long_term` | text<long> | |
| `career_goal_short_term` | text<long> | |
| `target_industry_list` | array<string> | |
| `target_job_role_list` | array<string> | |
| `target_degree_level` | enum<certificate, associate, bachelor, master, doctorate, professional> | |
| `target_major_field_primary` | enum (CIP-based taxonomy) | |
| `target_major_field_secondary` | enum | |
| `target_start_term_season` | enum<fall, spring, summer> | |
| `target_start_term_year` | int | |
| `thesis_interest` | enum<yes, no, maybe> | |
| `research_interest_level` | enum<none, low, medium, high> | |
| `internship_co_op_priority` | enum<critical, important, nice_to_have, none> | |
| `preferred_learning_style` | enum<lecture, project, research, mixed> | |
| `preferred_program_style` | enum<theory, applied, mixed> | |
| `application_intensity_preference` | enum<few_deep, balanced, many_broad> | |
| `stretch_target_safety_mix_preference` | json<{reach: int, target: int, safer: int}> | E.g., {2,4,2}. |
| `transfer_intent` | enum<yes, no, unsure> | |
| `return_home_intent` | enum<yes, no, undecided> | |
| `post_graduation_location_preference` | text<long> | |
| `risk_tolerance` | enum<conservative, balanced, aggressive> | |
| **Preference weights (0–10)** | int each | |
| `weight_cost_importance` | int | |
| `weight_flexibility_online_importance` | int | |
| `weight_location_importance` | int | |
| `weight_outcomes_placement_importance` | int | |
| `weight_ranking_selectivity_importance` | int | |
| `weight_support_services_importance` | int | |
| `weight_time_to_degree_importance` | int | |
| `dealbreakers_list` | text<long> | |
| `non_negotiables_list` | text<long> | |
| `tradeoff_notes` | text<long> | |

### 3.13 Constraints & feasibility
**Universe:** every student. **Classification:** core.

| Field | Type | Notes |
|---|---|---|
| `budget_band_annual_total` | enum<lt_20k, 20-40k, 40-60k, 60-80k, gt_80k> | |
| `max_affordable_tuition` | float | annual |
| `max_affordable_total_cost_of_attendance` | float | annual |
| `needs_financial_aid_flag` | bool | |
| `scholarship_required_flag` | bool | |
| `employer_sponsorship_available_flag` | bool | |
| `geography_constraint_country_list` | array<enum (ISO 3166)> | |
| `geography_constraint_state_province_list` | array<string> | |
| `geography_constraint_city_metro_list` | array<string> | |
| `distance_to_home_preference` | enum<local, regional, any> | |
| `willingness_to_relocate` | enum<yes, no, conditional> | |
| `preferred_modality` | enum<in_person, online, hybrid> | |
| `program_length_limit_months` | int | |
| `must_start_by_date` | date | |
| `earliest_start_date` | date | |
| `hours_available_for_work_while_studying` | int | per week |
| `time_availability_per_week_for_study` | int | per week |
| `housing_constraints_flag` | bool | |
| `housing_constraints_details` | text<long> | |
| `family_caregiver_constraints_flag` | bool | |
| `family_caregiver_constraints_details` | text<long> | |
| `military_deployment_constraint` | text<long> | |
| `disability_access_constraints_affecting_campus_choice` | text<long> | |

### 3.14 Institution / program preferences
**Universe:** every student. **Classification:** core.

| Field | Type | Notes |
|---|---|---|
| `institution_size_preference` | enum<small, medium, large, very_large, any> | |
| `institution_type_preference` | enum<public, private, community, vocational, any> | |
| `setting_preference` | enum<urban, suburban, rural> | |
| `class_size_preference` | enum<small_seminar, medium, large_lecture> | |
| `religious_affiliation_preference` | enum<none, prefer, required, avoid> + `religion` enum | |
| `application_platform_preference` | enum<Common_App, Coalition, Direct, any> | |
| `admission_round_preference` | enum<ED, EA, RD, rolling> | |
| `program_format_preference` | enum<cohort, self_paced, mixed> | |
| `internship_requirement_preference` | enum<required, preferred, optional> | |
| `delivery_flexibility_required_flag` | bool | |
| `bridge_pathway_programs_acceptable` | bool | |
| `campus_culture_preference` | text<long> | |
| `grading_policy_preference` | text<long> | |
| `schedule_preference` | enum<day, evening, weekend, any> | |
| `support_services_needed` | array<enum<tutoring, career, disability, advising, counseling, financial_literacy>> | |
| `target_institution_list` | array<institution_id> | |
| `target_program_list` | array<program_id> | |
| **Importance ratings (0–10)** | int each | |
| `importance_credit_transfer_acceptance` | int | |
| `importance_diversity_inclusion` | int | |
| `importance_faculty_interaction` | int | |
| `importance_research_opportunities` | int | |

### 3.15 Readiness & planning state
**Universe:** every student. **Classification:** core. **Source:** system-derived + student-typed (notes).

| Field | Type | Notes |
|---|---|---|
| `application_stage` | enum<discovering, planning, prepping, submitting, post_submit> | |
| `target_application_cycle` | string | e.g., "2026-2027" |
| `application_round_preference_per_school` | json<{school_id: round}> | |
| `overall_profile_completeness_pct` | int (0-100) | system-derived. |
| `last_updated_timestamp_profile` | datetime | |
| **Checklist flags** | bool each | |
| `checklist_profile_basics_complete` | bool | |
| `checklist_academics_complete` | bool | |
| `checklist_activities_complete` | bool | |
| `checklist_tests_complete` | bool | |
| `checklist_recommendations_initiated` | bool | |
| `checklist_school_list_finalized` | bool | |
| `checklist_essays_started` | bool | |
| `checklist_essays_finalized` | bool | |
| `checklist_application_submitted` | bool | per app |
| `draft_status_personal_statement` | enum<none, draft, revised, final> | |
| `draft_status_resume` | enum<none, draft, revised, final> | |
| `draft_status_supplements` | enum<none, draft, revised, final> | per program |
| `number_of_drafts_uploaded` | int | |
| `planned_weekly_time_budget_hours` | int | |
| `preferred_support_mode` | enum<self, mentor, counselor, parent> | |
| `counselor_mentor_assigned_flag` | bool | |
| `reminder_preferences` | enum<daily, weekly, custom> | |
| `deadline_calendar_imported_synced_flag` | bool | |
| `student_notes_reflections` | text<long> | |
| `advisor_notes` | text<long> | |

### 3.16 Platform-native engagement signals
**Universe:** every authenticated session. **Classification:** core. **Source:** system-derived (telemetry).

| Field | Type | Notes |
|---|---|---|
| `account_created_timestamp` | datetime | |
| `last_login_timestamp` | datetime | |
| `session_count_7d` / `_30d` / `_90d` | int | rolling. |
| `average_session_duration` | int (seconds) | |
| `page_views_count_7d` / `_30d` / `_90d` | int | |
| `programs_saved_count` | int | |
| `programs_viewed_count` | int | |
| `compare_actions_count` | int | |
| `message_count_student_school` | int | |
| `message_topics_tags` | array<string> | |
| `upload_events_count_documents_essays` | int | |
| `time_on_program_page_avg_seconds` / `total_seconds` | int | |
| `cta_interactions` | array<enum<apply, start_checklist, message>> | |
| `checklist_interaction_events` | array<enum> | |
| `reminder_interactions` | array<enum<opened, snoozed, dismissed>> | |
| `click_through_events` | text (event-type log) | |
| `search_queries_raw` | text<long> | sensitive — opt-in. |
| `search_filters_used` | json | |
| `scroll_depth_band` | enum<0-25, 25-50, 50-75, 75-100> | per page-load |
| `drop_off_step` | string | last incomplete step id |
| `device_type` | enum<desktop, mobile, tablet> | |
| `os_browser` | string | |
| `ip_country` | enum (ISO 3166) | |
| `referral_source` | enum<organic, paid, partner> | |
| `campaign_id_utm_parameters` | string | |
| `a_b_test_assignment_bucket` | enum | |

### 3.17 Risk, integrity, verification
**Universe:** every student. **Classification:** core. **Source:** system-derived + third-party-verified.

| Field | Type | Notes |
|---|---|---|
| `email_verified` | bool | |
| `phone_verified` | bool | |
| `id_verification_status` | enum<none, pending, verified, failed> | |
| `transcript_verification_status` | enum<none, pending, verified, failed> | |
| `test_score_verification_status` | enum<none, pending, verified, failed> | |
| `recommendation_verification_status` | enum<none, pending, verified, failed> | |
| `document_metadata_captured` | json<{hash, file_size, type}> | per file |
| `document_upload_timestamp` | datetime | |
| `external_link_validation_status` | enum<unchecked, valid, invalid, suspicious> | per link |
| `duplicate_account_suspected_flag` | bool | |
| `duplicate_identifiers_observed` | array<string> | |
| `mismatch_details` | text<long> | |
| `report_submitted_flag` | bool | |
| `login_risk_events` | array<enum<new_device, suspicious_ip, multiple_failures>> | |
| `policy_acknowledgements_completed` | array<audit_ref> | |
| `integrity_disclosure_details` | text<long> | |
| `integrity_disclosure_completed_flag` | bool | |
| `audit_log_event_stream` | array<{event_type, timestamp}> | |

### 3.18 Major-specific tracks

Each track is a JSONB subdocument on `student_major_specific_signals.{track_key}`. Only populated when `target_major_field_primary` matches.

**Available tracks (track_key):**
- `cs_data_ai` — Computer Science, Data Science, AI.
- `engineering` — ME / EE / Civil / Aerospace / ChemE.
- `business` — Finance / Marketing / Analytics / Operations.
- `health` — Pre-med / Nursing / Public Health.
- `arts_design` — Art / Design / Architecture / Media.
- `performing_arts` — Music / Theater / Dance.
- `humanities_social_sciences` — Humanities / Social Sciences.
- `law_policy` — Law / Policy / International Relations.
- `education_counseling` — Education / Teaching / Counseling / Social Work.
- `journalism_communications` — Journalism / Communications / Media.
- `math_physics_chemistry_sciences` — Pure Sciences.
- `comp_engineering_robotics` — Computer Engineering / Embedded / Robotics.
- `environmental_sustainability` — Environmental / Sustainability / Energy.
- `language_linguistics` — Language Majors / Linguistics / Translation.
- `entrepreneurship_product` — Entrepreneurship / Product / Innovation.

Full per-track field catalog is reproduced in **Appendix 40A: Major-Specific Field Catalog** (to be split into its own doc on next iteration). For now, see Master Paper Appendix A lines 3905–4617 — that subagent output is preserved at `/tmp/master_paper.txt` for any engineer needing the verbatim list.

A representative sample (CS / Data / AI track):

| Field | Type |
|---|---|
| `coding_assessment_score` | int |
| `cs_fundamentals_self_rating_algorithms` | int (1-5) |
| `cs_fundamentals_self_rating_dsa` | int (1-5) |
| `cs_fundamentals_self_rating_databases` | int (1-5) |
| `cs_fundamentals_self_rating_compilers` | int (1-5) |
| `cs_fundamentals_self_rating_os` | int (1-5) |
| `cs_fundamentals_self_rating_concurrency` | int (1-5) |
| `cs_fundamentals_self_rating_security_basics` | int (1-5) |
| `data_skill_self_rating_sql` | int (1-5) |
| `data_skill_self_rating_viz` | int (1-5) |
| `data_skill_self_rating_ab_testing` | int (1-5) |
| `ml_readiness_classification_regression` | int (1-5) |
| `ml_readiness_deep_learning` | int (1-5) |
| `ml_readiness_nlp` | int (1-5) |
| `ml_readiness_recsys` | int (1-5) |
| `ml_readiness_time_series` | int (1-5) |
| `competitive_programming_best_rank_level` | enum<n/a, regional, national, ICPC_world_finalist> |
| `leetcode_practice_frequency` | enum<none, occasional, weekly, daily> |
| `github_link` | string |
| `kaggle_link` | string |
| `open_source_contributions` | bool |
| `hackathon_list` | array<string> |
| `track_choice` | enum<data, AI, cyber, SWE> |

(Engineering, business, health, etc. follow analogous patterns — see Master Paper.)

---

### 3.19 Behavioral prompt library

The standalone Prompt Library defines a structured behavioral-prompt system — distinct from Workshops (`16`). Workshops give feedback on a draft; this layer is the **catalog of prompts** + the student's **responses** as reusable profile signals. Stored in `student_behavioral_prompts` + `student_behavioral_responses`.

**Per-prompt metadata** (table `behavioral_prompts` — platform-defined catalog):

| Field | Type | Notes |
|---|---|---|
| `prompt_id` | string | Stable id. |
| `title` | string | E.g., "Tell me about a time you led without authority." |
| `intent_tag` | enum<leadership, conflict, failure, impact, ethics, learning, motivation, fit, vision> | |
| `target_channel` | enum<interview, essay, short_answer, video> | |
| `time_limit_seconds` | int | For interview/video variants (e.g., 30s / 2min / 5min). |
| `word_limit` | int | For essay/short-answer. |
| `format_required` | enum<STAR, CAR, freeform> | |
| `evidence_required_flag` | bool | |
| `allowed_attachments_flag` | bool | |
| `language_option` | enum (ISO 639-1) | |
| `confidentiality_scope` | enum<private, shareable, recommender_facing> | |
| `reuse_allowed_flag` | enum<core, school_specific> | The core-vs-school-specific dichotomy. |

**Per-response** (table `student_behavioral_responses`):

| Field | Type | Notes |
|---|---|---|
| `prompt_id` | string (fk) | |
| `draft_status` | enum<none, draft, revised, final> | |
| `last_edited` | datetime | |
| `version_count` | int | |
| `confidence_self_rating` | int (1-5) | Student's own confidence. |
| `authenticity_confidence_flag` | bool | System: looks authentic. |
| `needs_feedback_flag` | bool | |
| `reviewer_feedback_received_flag` | bool | |
| `star_situation_present` | bool | STAR completeness flags. |
| `star_task_present` | bool | |
| `star_action_present` | bool | |
| `star_result_present` | bool | |
| `star_reflection_present` | bool | |
| `impact_metric_present` | bool | |
| `impact_metric_type` | enum<count, percent, dollar, time, scale> | |
| `impact_metric_value_band` | enum | |

~70 canonical prompt titles exist (tell-me-about-yourself at 30s/2min/5min, proudest accomplishment, biggest failure, conflict with teammate/authority, leadership without title, ethical dilemma, why-this-field/program/now, 5–10yr vision, cross-cultural teamwork, etc.). Full list: `Misc./Prompt Library.docx`.

### 3.20 Story bank

Reusable narrative units the student can map to prompts/essays. Table `student_stories`.

| Field | Type | Notes |
|---|---|---|
| `story_id` | string | |
| `title` | string | |
| `primary_competency` | enum<leadership, teamwork, impact, resilience, creativity, analytical, communication, initiative> | |
| `secondary_competency` | enum | |
| `competency_tags` | array<string> | |
| `context_tags` | array<string> | school / work / personal / research / community |
| `role_type` | enum<leader, contributor, founder, observer> | |
| `stakeholder_type` | enum<peers, authority, clients, public, self> | |
| `conflict_type` | enum<interpersonal, resource, ethical, technical, time, none> | |
| `difficulty_tier` | int (1-5) | |
| `recency` | date | |
| `duration` | string | |
| `scale_tier` | int (1-5) | reach of the impact |
| `evidence_link` | string | |
| `referenceable_contact_flag` | bool | someone can vouch |

### 3.21 Decision style & preference mechanics

How the student decides — feeds Match presentation (e.g., a "many options" student gets a longer shortlist; a "single recommendation" student gets a top pick). Scalar fields on `student_profiles` / `student_decision_style`.

| Field | Type |
|---|---|
| `decision_making_mode` | enum<fast_iterative, slow_analytical> |
| `option_preference` | enum<many_options, single_recommendation> |
| `regret_tolerance` | enum<low, medium, high> |
| `ambiguity_tolerance` | enum<low, medium, high> |
| `preference_stability_frequency` | enum<stable, occasionally_shifts, volatile> |
| `social_influence_reliance` | enum<low, medium, high> |
| `trusted_information_sources_ranking` | array<enum<counselor, family, peers, rankings, official, AI, social>> |
| `dealbreakers_list` | text<long> |
| `nice_to_have_list` | text<long> |

### 3.22 Working style & learning success signals

Predicts program-environment fit. Table `student_working_style`.

| Field | Type |
|---|---|
| `autonomy_preference` | enum<high, balanced, structured> |
| `collaboration_intensity` | enum<solo, small_team, large_team> |
| `structure_preference` | enum<rigid, flexible, self_directed> |
| `feedback_cadence_preference` | enum<frequent, periodic, minimal> |
| `mentorship_style_preference` | enum<hands_on, hands_off, peer> |
| `conflict_approach` | enum<direct, diplomatic, avoidant> |
| `risk_appetite` | enum<conservative, balanced, aggressive> |
| `deep_work_vs_multitask` | enum<deep_work, multitask, mixed> |
| `learning_modality` | enum<visual, auditory, reading, kinesthetic, mixed> |
| `study_hours_per_week` | int |
| `consistency_pattern` | enum<steady, burst, deadline_driven> |
| `procrastination_risk` | enum<low, medium, high> |
| `productivity_time_window` | enum<morning, afternoon, evening, night> |
| `academic_stamina` | enum<low, medium, high> |

### 3.23 Skill matrix

Cross-cutting skill inventory (distinct from major-specific tracks). Repeatable entries (table `student_skills`):

| Field | Type |
|---|---|
| `skill_name` | string |
| `proficiency_level` | enum<novice, intermediate, advanced, expert> |
| `years_used` | float |
| `last_used_date` | date |
| `frequency_of_use` | enum<daily, weekly, monthly, rarely> |
| `evidence_type` | enum<self_report, certificate, work_sample, test, endorsement> |
| `evidence_link` | string |
| `can_demonstrate_flag` | bool |

### 3.24 Career realism & recruiting readiness

| Field | Type |
|---|---|
| `target_role_specificity` | enum<vague, directional, specific> |
| `salary_expectation_band` | enum |
| `salary_realism_flag` | bool (system: expectation vs market) |
| `geographic_flexibility_for_jobs` | enum<local_only, regional, national, global> |
| `recruiting_timeline_awareness` | enum<unaware, aware, prepared> |
| `interview_practice_frequency` | enum<none, occasional, regular> |
| `network_strength` | enum<none, emerging, established> |
| `industry_exposure_level` | enum<none, coursework, internship, full_time> |

### 3.25 Narrative building blocks, relationship graph, communication ops

- **Narrative building blocks** — `throughline_theme`, `origin_story`, `turning_points[]`, `core_motivation`, `values_in_action[]` (free-text + tags) — feed essay/identity coherence.
- **Relationship graph** — recommenders, mentors, peers, and their `relationship_strength`, `contact_recency`, `can_vouch_flag`, `referenceable_for` tags. Distinct from §3.7 recommenders (which is application-mechanical); this is the broader network.
- **Communication operations** — `preferred_response_time`, `channel_responsiveness` per channel, `last_responsive_at`, `nudge_fatigue_band` — feed nudge scheduling without over-messaging.

### 3.26 Consistency / ops-friction predictors

System-derived flags that predict where a student will stall. Table `student_friction_signals` (mostly `system-derived`):

| Field | Type |
|---|---|
| `cross_field_consistency_score` | float (0-100) |
| `deadline_adherence_history` | enum<reliable, mixed, slips> |
| `form_abandonment_rate` | float |
| `re_engagement_latency_days` | float |
| `document_upload_friction_flag` | bool |
| `predicted_stall_step` | string |

---

## 4. OUTPUT FEATURES

Inference layer responsibilities. Each output is computed by one or more of the agents in `42-ai-agents-claude.md`. Each is stored with provider+model+timestamp+confidence per `03` §8.

### 4.1 Identity, contact, account (outputs)
- `account_lifecycle_stage` enum<new, active, stale, reactivated>
- `contactability_score` 0-100
- `data_quality_score` 0-100
- `duplicate_account_risk_flag` bool + `duplicate_account_risk_score` 0-100
- `field_conflict_flags` array<enum<dob_mismatch, name_mismatch, address_mismatch>>
- `guardian_workflow_required_flag` bool
- `identity_verification_status` enum<unverified, partially, fully>
- `missing_critical_fields_list` array<field_name>
- `preferred_outreach_channel_recommendation` enum<email, sms, in_app>
- `preferred_outreach_frequency_recommendation` enum<all, weekly, important_only>
- `residency_tuition_classification_suggestion` enum
- `timezone_normalized_deadline_calendar` array<{deadline, normalized_tz}>
- `verification_failure_reason_code` enum

### 4.2 Eligibility, compliance, consent (outputs)
- `accommodation_routing_recommendation` enum
- `block_reason_category` enum<consent, missing_doc, policy>
- `compliance_status` enum<pass, pending, blocked>
- `consent_audit_record` text (version + timestamp summary)
- `consent_usage_mask` json<{matching: bool, outreach: bool, analytics: bool, training: bool}>
- `disclosure_review_flag` bool
- `documentation_required_list` array<doc_type>
- `missing_required_steps_checklist` array
- `risk_escalation_required_flag` bool

### 4.3 Visa & immigration (outputs)
- `visa_required_flag` bool (derived)
- `visa_feasibility_band` enum<high, medium, low>
- `visa_timeline_risk_score` 0-100
- `visa_readiness_checklist` array
- `missing_visa_documents_list` array
- `program_visa_eligibility_filter_flag` enum<eligible, ineligible, unknown>
- `escalation_advisor_review_needed` bool
- `funding_sufficiency_band` enum<insufficient, marginal, sufficient, excess>
- `suggested_earliest_feasible_start_term` enum

### 4.4 Current education context (outputs)
- `school_context_confidence_score` 0-100
- `credential_evaluation_required_flag` bool
- `transcript_translation_required_flag` bool
- `grading_scale_normalization_status` enum<mapped, unmapped, partial>
- `transfer_pathway_detected_flag` bool
- `transfer_credit_review_needed_flag` bool
- `academic_interruption_impact_note` text
- `context_notes_for_reviewers` text
- `missing_context_items_list` array

### 4.5 Academic record (outputs)
- `normalized_gpa` float
- `gpa_band` enum<top_10pct, top_25pct, top_50pct, bottom_50pct>
- `academic_readiness_score` 0-100 per program family
- `academic_readiness_band` enum<low, medium, high>
- `academic_rigor_index` 0-100
- `class_rank_percentile` float
- `grade_trend_slope` float (positive = improving)
- `course_to_prerequisite_mapping_confidence` 0-100
- `prerequisite_gaps_list` array<{requirement, missing}>
- `prerequisite_satisfaction_matrix` json
- `transcript_parse_status` enum<parsed, partial, failed>
- `risk_flags_withdrawals_repeats_incompletes_anomaly` array
- `missing_transcript_elements_list` array
- `reviewer_academic_summary_rubric_aligned` text<long>
- `contextual_explanation_prompts_needed_flag` bool
- `fastest_fix_path_plan_for_gaps` text

### 4.6 Standardized tests (outputs)
- `score_normalization_status` enum
- `percentile_band` enum
- `test_validity_flag` bool
- `test_policy_compatibility` enum<required, optional, waived>
- `superscore_computed_values` json<{test, score}>
- `superscore_eligible_flag` bool
- `meets_typical_range_band_per_target_program_group` enum<below, at, above>
- `submit_vs_withhold_recommendation` enum
- `missing_invalid_score_report_flag` bool
- `test_readiness_plan` text<long>

### 4.7 Work, internships, service (outputs)
- `experience_duration_total_months` int
- `experience_intensity_score` 0-100
- `seniority_band` enum<entry, mid, senior>
- `skill_tags_inferred` array
- `industry_function_tags_inferred` array
- `impact_metric_presence_score` 0-100
- `verification_needed_flag` bool
- `supervisor_contact_risk_flag` bool
- `resume_gaps_list` array<{period, hint}>
- `resume_gaps_readiness_score` 0-100
- `fit_contribution_highlights` text (evidence-linked)

### 4.8 Portfolio (outputs)
- `portfolio_completeness_score` 0-100
- `portfolio_readiness_band` enum<low, medium, high>
- `portfolio_compliance_status` enum<compliant, non_compliant, unknown>
- `portfolio_requirement_detected_flag_per_program` json
- `portfolio_to_program_compatibility_flag` bool
- `missing_portfolio_items_list` array
- `artifact_tagging_summary` array<{medium, style, theme}>
- `escalation_human_review_needed` bool
- `research_output_credibility_flag` bool
- `reviewer_extracurricular_summary_portfolio_digest` text

### 4.9 Recommendations (outputs)
- `recommendation_completion_probability` 0-100
- `recommendation_requirement_satisfied_flag` bool
- `missing_recommender_type_flags` array
- `delay_risk_band` enum
- `recommended_nudge_schedule` json<{who, when, channel}>
- `invalid_recommender_contact_flag` bool
- `waiver_consistency_flag` bool
- `reviewer_recommendation_packet_status_summary` text

### 4.10 Activities, leadership, competitions, research (outputs)
- `activity_profile_completeness_score` 0-100
- `leadership_band` enum<emerging, established, distinguished>
- `leadership_intensity_score` 0-100
- `achievement_tier_weights` json<{tier, weight}>
- `competency_coverage_map` json<{leadership, teamwork, impact, technical, communication}>
- `artifact_tagging_summary` array
- `missing_evidence_flags` array
- `best_fit_story_bank_suggestions` text
- `differentiators_list` array (evidence-linked)
- `escalation_flag` bool

### 4.11 Intent, goals, priorities, tradeoffs (outputs)
- `goal_embedding_intent_signature` vector (internal)
- `goal_tags` array (standardized taxonomy)
- `preference_vector` json (normalized weights)
- `career_alignment_score` 0-100
- `conflicts_detected` array<{a, b, hint}>
- `next_questions_to_ask_user` array<text>
- `risk_tolerance_band` enum
- `tradeoff_profile` enum<cost_first, outcomes_first, fit_first, location_first, balanced>
- `suggested_school_list_composition` json<{stretch, target, safety}>
- `program_style_fit` enum
- `why_this_program_talking_points` array<text> (evidence-linked)

### 4.12 Constraints & feasibility (outputs)
- `feasibility_band` enum<low, medium, high>
- `feasibility_score` 0-100
- `affordability_band` enum
- `aid_scholarship_likelihood_band` enum
- `hard_constraint_satisfaction_flag_per_program` json
- `constraint_violation_reasons` array<text>
- `recommended_constraint_relaxations` array<text>
- `feasibility_first_shortlist` array<program_id>
- `earliest_feasible_start_term` enum
- `latest_feasible_submission_timeline` array<{program_id, date}>
- `net_cost_scenario_range` json<{min, expected, max}>

### 4.13 Institution / program preferences (outputs)
- `preference_program_similarity_score_per_program` 0-100
- `preference_match_band` enum<low, medium, high>
- `school_type_fit_band` enum
- `support_services_fit_flag` bool
- `preference_mismatch_warnings` array<text>
- `recommended_alternatives` array<program_id>
- `personalized_ranking_adjustment` float
- `compare_page_highlights` array<{program_id, highlight}>

### 4.14 Readiness & planning state (outputs)
- `overall_readiness_score` 0-100
- `readiness_band` enum<low, medium, high>
- `application_submission_forecast` enum<on_time, at_risk, late>
- `deadline_risk_band` enum + `deadline_risk_score` 0-100
- `draft_quality_triage` enum<needs_work, ok, strong>
- `draft_revision_priority_list` array
- `missing_critical_items_list` array (blockers)
- `recommended_next_actions` array (ordered checklist)
- `recommended_work_plan` text (hours/week allocation)
- `personalized_timeline_plan` text
- `advisor_intervention_needed_flag` bool

### 4.15 Platform-native engagement (outputs)
- `apply_propensity_score` 0-100
- `churn_risk_band` enum + `churn_risk_score` 0-100
- `completion_propensity_score` 0-100
- `intent_strength_score` 0-100 (recency-decayed)
- `engagement_trend` enum<rising, flat, declining>
- `next_best_action_recommendation` enum
- `personalized_nudge_message_template` text (internal)
- `re_ranking_personalization_weight` float
- `segment_label` enum
- `drop_off_diagnosis` text

### 4.16 Risk, integrity, verification (outputs)
- `anomaly_score` 0-100
- `anomaly_category_tags` array<enum<identity, docs, scores, activity>>
- `document_authenticity_confidence_band` enum<low, medium, high>
- `duplicate_identity_likelihood_score` 0-100
- `fraud_risk_flag` bool **policy-gated.**
- `trust_band` enum + `trust_score` 0-100
- `verification_next_steps` array (ordered)
- `clarification_requests_list` array<text>
- `audit_ledger_entry_bundle` json<{provider, model_id, model_version, timestamps, consent_mask}>

### 4.17 Behavioral questions & prompts (outputs)
*(No input counterpart — inference layer takes entire profile + essays as input.)*

- `interview_question_set_personalization` array<text>
- `interview_readiness_band` enum
- `suggested_practice_plan` text
- `prompt_routing` enum (which prompt to answer next)
- `story_prompt_matching_table` json<{prompt, best_story_id}>
- `revision_priority_list` array (highest-ROI edits)
- `draft_feedback_signals` json (clarity / structure / specificity)
- `inconsistency_flags` array<text> (cross-essay/profile contradictions)
- `competency_coverage_gaps` array<enum>
- `word_count_compliance_status` enum<under, met, over>
- `authenticity_risk_flags` array<enum<generic, over_optimized, AI_pattern>>

### 4.18 Major-specific outputs (per track)

Sample (CS/Data/AI track):
- `coding_readiness_band` enum
- `major_track_fit_score_per_target_track` json<{track, score}>
- `project_strength_score` 0-100
- `project_coverage_map` json<{area, depth}>
- `prerequisite_gaps_plus_satisfaction` json
- `research_readiness_band` enum
- `skill_gap_severity` enum
- `specialization_match_tags` array<enum<NLP, CV, Systems, RecSys, ...>>
- `suggested_artifacts_to_add` array<text>
- `suggested_bridge_plan` text
- `track_recommendation` enum<CS, Data, AI, Cyber, SWE>
- `best_projects_to_showcase_list_by_program_type` json

(Similar shapes for Engineering, Business, Health, Arts/Design/Architecture/Media, Performing Arts, Law/Policy/Humanities/SocSci/Education — see source. Each track defines its own readiness bands, fit scores, and suggested-artifact lists.)

---

## 5. Provenance, confidence, versioning (universal record metadata)

Every signal, input or output, carries:

```ts
type SignalRecord<T> = {
  value: T;                                  // current value
  value_normalized: T | null;                // normalized for matching (e.g., "3.8" → 3.8)
  source: 'student-typed' | 'student-uploaded' | 'student-link' | 'student-derived'
        | 'institution-supplied' | 'system-derived' | 'system-extracted'
        | 'third-party-verified';
  confidence: number;                        // 0–100
  created_at: datetime;
  updated_at: datetime;
  version: number;                           // incremented on each write
  raw_input_ref: string | null;              // pointer to raw input (file ref, message id)
  provenance_chain: array<{event, timestamp, actor}>;
}
```

Confidence rules:
- **`student-typed`** structured field → confidence 95.
- **`student-typed`** free-text → confidence 70.
- **`student-uploaded`** doc with successful parse → confidence 80.
- **`student-uploaded`** doc with partial parse → confidence 40 + `escalation_human_review_needed=true`.
- **`student-link`** (LinkedIn, GitHub) post-validation → confidence 75.
- **`system-derived`** from rules → confidence 90.
- **`system-extracted`** from LLM with self-reported confidence → that value, capped at 85.
- **`third-party-verified`** → confidence 99.
- **`institution-supplied`** → confidence 95.

Low-confidence (< 60) values flag the `clarification_requests_list` to ask the student to confirm.

---

## 6. Progressive completion thresholds

Per Master Paper:

### 6.1 Match-ready minimum (Stage 1 → Stage 2 gate)

The minimum signal coverage required to generate an initial shortlist. Collecting beyond this is OK; less than this means Discovery keeps prompting.

Required:
- Identity: `legal_name`, `primary_email`, `nationality`, `current_address.country_of_residence`.
- Education: `current_academic_year_level`, `expected_graduation_date`, `gpa_reported` OR equivalent.
- Intent: `target_degree_level`, `target_major_field_primary`, `target_start_term_season + year`.
- Constraints: `budget_band_annual_total`, `preferred_modality`, at least one geography signal (country list OR `willingness_to_relocate=conditional` + a preference list).
- Priorities: at least 3 of 7 preference weights set.
- Gating flags: `visa_required_for_target_country_flag` (derived), `has_portfolio_requirement_flag` (derived).

`overall_profile_completeness_pct` increments by category as fields populate. Match-ready threshold ≈ 35%.

### 6.2 Apply-ready completion (Stage 2 → Stage 3 gate, per program)

When a student promotes a program to "I'm applying," the platform pulls the program's `requirements_checklist` and gates against it:

Required:
- All `core` fields above.
- Recommenders sufficient for the program's `recommendations_required` count.
- Test scores per the program's policy (`test_policy_compatibility` ≠ blocking).
- Essays / supplements per the program's `requirement_checklist`.
- Portfolio per `has_portfolio_requirement_flag` if true.
- Visa fields per `visa_required_flag` if true.
- Major-specific track signals per the program's discipline.

Apply-ready returns `ready_to_submit=true` per program when all program-specific checks pass. The UI's "Mark as ready to submit" gate is enabled at that point.

---

## 7. Cross-module consistency

Single source of truth per signal. Updates propagate:

```
student_typed change
   ↓
Profile section save → student_profile field update + version++
   ↓
event:profile_changed
   ↓
   ├→ Match service invalidates per-program match_results cache
   ├→ Discovery service updates `next_questions_to_ask_user`
   ├→ Application service re-evaluates `apply_ready_per_program`
   ├→ Workshops service re-evaluates `feedback_signals` for any open draft
   └→ AI audit ledger records the change with version + actor
```

Conflict resolution:
- If `student-typed` and `system-extracted` disagree on a field: student-typed wins; system-extracted preserved in `provenance_chain` for context.
- If `institution-supplied` and `student-typed` disagree (e.g., institution-supplied test score vs student-typed): institution-supplied wins; student is notified.

---

## 8. Storage layout (backend)

Recommended SQLAlchemy table layout. Existing tables are extended where they exist; new tables for the major-specific tracks and the per-piece repeatables.

| Table | Source for fields | Status |
|---|---|---|
| `student_profiles` | §3.1, §3.13 (constraints), §3.14 (preferences scalar), §3.15 (readiness scalar) | exists; extend |
| `student_identity` | §3.1 identity-deep fields | exists |
| `student_consent` | §3.2 | NEW |
| `student_visa` | §3.3 | NEW |
| `student_education_context` | §3.4 | exists as part of profile; extract |
| `student_courses` | §3.5 per-course | NEW |
| `student_transcripts` | §3.5 transcript metadata | NEW |
| `student_test_scores` | §3.6 | exists |
| `student_recommenders` | §3.7 | exists |
| `student_work` | §3.8 | NEW |
| `student_activities` | §3.9 | NEW |
| `student_competitions` | §3.9 sub | NEW |
| `student_research` | §3.9 sub | NEW |
| `student_portfolio` | §3.10 top-level | NEW |
| `student_portfolio_pieces` | §3.10 per-piece | NEW |
| `student_languages` | §3.11 | NEW |
| `student_goals` | §3.12 (goal-shaped) | exists |
| `student_intent` | §3.12 scalar | extend `student_profiles` |
| `student_needs` | §3.13 | exists |
| `student_engagement_events` | §3.16 | NEW (telemetry) |
| `student_integrity_signals` | §3.17 inputs | NEW |
| `student_major_specific_signals` | §3.18 — JSONB per track | NEW |
| `behavioral_prompts` | §3.19 prompt catalog (platform-defined) | NEW |
| `student_behavioral_responses` | §3.19 per-response | NEW |
| `student_stories` | §3.20 story bank | NEW |
| `student_decision_style` | §3.21 | NEW |
| `student_working_style` | §3.22 | NEW |
| `student_skills` | §3.23 skill matrix | NEW |
| `student_career_readiness` | §3.24 | NEW |
| `student_narrative` / `student_relationship_graph` / `student_comms_ops` | §3.25 | NEW |
| `student_friction_signals` | §3.26 (system-derived) | NEW |
| `ai_artifacts` | §4 outputs — JSONB per category | exists; extend per `03` §8 |
| `consent_audit` | §4.2 audit record | NEW |
| `fairness_signals` | §43 fairness tracking | NEW |

---

## 9. Open questions / known gaps

- **CIP code adoption.** The taxonomy for `target_major_field_primary` should align with CIP (Classification of Instructional Programs) for cross-program compatibility. Confirm version (CIP 2020 latest).
- **Geography taxonomy.** ISO 3166-1 country codes universal; for sub-regions, US uses USPS state codes, international uses ISO 3166-2. Define one schema across all geo fields.
- **Major-specific catalog full reproduction.** Move §3.18 to its own doc `40A-prompt-library-major-specific.md` for editability.
- **Privacy/PII labels.** Each field marked `pii-sensitive` or stricter needs an explicit retention rule. Cross-reference with `43-data-rights-privacy.md`.
- **Versioning across rebuilds.** When a field is removed or its enum extended, how do existing values reconcile? Suggest a migration playbook doc.
- **CSV import column maps.** For `22-data-upload.md`, the institution-side bulk import must declare column → Prompt Library field. A reverse lookup table per data source type would help.

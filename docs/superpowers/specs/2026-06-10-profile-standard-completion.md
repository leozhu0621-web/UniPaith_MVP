# The Profile Standard, figured out — completion spec (STANDARD_VERSION 2)

**Status:** ready to execute (audited against the gold MIT/Sloan/MBAn render + data, 2026-06-10)

**Why:** Phase 1's manifest was a thin first pass. A 4-agent audit of the actual render pages vs. the MIT reference data found the manifest is an **incomplete and partly-incorrect** mirror of what the gold pages render. The MIT data is conformant by definition, so every gap means the **manifest** must be corrected, not the data. Until this lands, conformance "lies" (notably two phantom paths) and the mass-enrichment plan has nothing trustworthy to key off.

This spec is the precise, prioritized set of manifest edits that make the standard the complete, correct, dotted-path mirror of the gold instance — then `STANDARD_VERSION` bumps to 2, which is the lever that re-conforms the fleet.

## Correctness fixes (do first — without these, conformance is wrong)

1. **Program phantom paths.** `insights.faculty` declared `faculty.lead` → real column is `faculty_contacts.lead`. `insights.reviews` declared `reviews.summary` → real column is `external_reviews.summary`. As written they resolve to non-existent columns (passed Phase-1 tests only because both were optional).
2. **School path mismatch.** Manifest declares `description`; the served/typed field is `description_text`.
3. **Institution `admissions_funnel` mis-pointed.** It lists `test_scores` + `demographics`, but the funnel renders from `school_outcomes.flagship.{applicants,admits,admissions_cycle,enrollment_total}`; `demographics` renders in a separate **Diversity** card. Re-point the section and split Diversity out.
4. **Over-declared, not rendered.** Program `costs.cost_source` (`cost_data.source`) and `admissions.evaluation` are declared but have no render slot for MBAn → drop (or add a render slot).
5. **Render-only, non-enrichable class.** Program `match_results.*` (DualRing, "Your realistic shot") render as content but are per-student, not facts. Mark a `render_only`/non-enrichment class so conformance & enrichment never chase them.

## Institution — add the under-modeled sections (paths verified in the audit)

- **Cost & aid** (entirely missing): `school_outcomes.financial_aid.{pell_grant_rate, federal_loan_rate, tuition_free_rate, no_loan_debt_rate, median_scholarship, median_debt_completers, cost_of_attendance}`; `school_outcomes.avg_net_price` in report-card.
- **Admissions funnel** (re-pointed): `school_outcomes.flagship.{applicants, admits, admissions_cycle, enrollment_total}` + `school_outcomes.test_scores.{sat_reading_25_75, sat_math_25_75, act_25_75}` + `retention_rate_first_year`.
- **Diversity** (new): `school_outcomes.demographics.{asian, white, hispanic, black, women}`.
- **Recognition** (missing): `school_outcomes.flagship.{nobel_laureates, macarthur_fellows, national_medal_science, national_medal_tech}` (+ `us_presidents`, `pulitzer_prizes` optional).
- **Scale / By the numbers** (missing): `school_outcomes.scale.{faculty_count, student_faculty_ratio, research_centers, endowment_usd, campus_acres, undergrad_majors}`.
- **Outcomes** (missing): `school_outcomes.{employed_or_continuing_ed, top_employer_industries, median_earnings_10yr}`, `completion_rate_4yr_150pct`.
- **Location & campus basics**: `school_outcomes.location.{lat, lng}`, `school_outcomes.campus_basics.{location, academic_calendar}`.
- **Identity / web-presence** (top-level columns): `website_url, contact_email, contact_phone, social_links, campus_setting, founded_year, type, campus_description` (+ `support_services`, `policies`, `international_info` optional).
- **Disambiguate** hero socials: the hero reads `Institution.social_links` while `apply()` writes `content_sources.social` — declare the canonical one.

## School — add cross-level + missing surfaces

- **Quick-facts strip (cross-level dependency — make explicit):** Acceptance / Grad-rate / Students / Setting render from the **parent institution** (`institution.school_outcomes.admit_rate`, `.graduation_rate_6yr`, `institution.student_body_size`, `institution.campus_setting`). Declare a `inherited` field class: **a school can never be gold unless its parent institution is enriched first** (ordering constraint for the mass plan).
- **Programs surface**: `program_count`, program names, degree-level mix.
- **`about_detail.named_for`** (rendered Sloan field, undeclared). Decide `about_detail.scale` (declared/rendered nowhere → drop).
- **Single-instance risk:** only MIT Sloan has `about_detail`/`content_sources`; the other 5 MIT schools are NULL. The school certification baseline rests on Sloan alone — keep school certification keyed to Sloan.

## Program — add the distinctive sections + flesh out leaves

- **Tracks / curriculum** (whole section, missing — the most editorially distinctive gold content): `tracks.{concentrations[], curriculum[].term, curriculum[].courses[], note, learning_format}` (MBAn's 4-term Analytics Capstone).
- **Program-level feeds** (whole section, missing): `content_sources.{social, news_rss, events_feed}`.
- **Basics**: add `department`, `highlights[]`, `who_its_for`.
- **Class profile** (only `cohort_size` declared; add 9): `class_profile.{international_pct, countries, women_pct, stem_pct, median_gpa, median_gre_quant, median_gmat, avg_work_experience_months, source, source_url}`.
- **Outcomes** (add 10): `outcomes_data.{mean_salary, median_signing_bonus, employment_timeframe, class_size, knowledge_rate, internship_conversion_rate, top_employers, scope, scope_note, source_url}`.
- **Admissions** (add): `application_requirements.{recommendations, test_policy, international.{english,visa,opt,sources}, prerequisites, source_url, application_fee}`.
- **Costs** (add): `cost_data.{breakdown[], note, source_url, year, fees, international_premium, net_price_by_income}`; `ranking_data.{debt_percentiles, price_calculator_url, avg_net_price, total_cost_attendance, median_debt, pell_grant_rate}`.
- **Faculty / reviews**: the corrected `faculty_contacts.{lead[].{name,title,url}, note, directory_url}` and `external_reviews.{summary, themes[].{label,sentiment,detail}, sources[].{label,url}, disclaimer}`.

## Required vs optional, and the version bump

- Sections/fields the gold pages render as primary content → `required`. Defensive-optional leaves (e.g. `us_presidents`, `support_services`) → `required=False`. Per-student render-only (`match_results`) → excluded from conformance/enrichment.
- After the edits: regenerate `frontend/src/generated/profile-manifest.json`, extend the render-parity anchor map for the new required sections, update the certification tests to build **full** MIT snapshots (reading the real `flagship`/`scale`/`financial_aid`/`tracks`/`class_profile`/`faculty_contacts`/`external_reviews` structures) and re-assert 100% conformance, then **bump `STANDARD_VERSION` to 2**.
- The bump marks the whole fleet stale; the engine's `plan()` then re-plans only the newly-added/changed fields (a diff, not a full re-crawl). This is the propagation lever.

## Acceptance
- Manifest mirrors the gold render (no rendered required section undeclared; no declared field unrendered; no phantom path).
- MIT/Sloan/MBAn certify 100% conformant against the **expanded** manifest (full snapshots).
- Render-parity passes for every new required section.
- `STANDARD_VERSION == 2`.

# Institution Data Standard

The bar for every institution in UniPaith's DB. NYU is the reference example — every field listed here is populated on NYU (institution id `6dd6d3ad-2e6a-4209-ae2b-1f928bc2429e`).

## Source hierarchy

Every field that holds content (not derived) must carry a `[Source: X]` annotation in the text, or a `source` key in the JSONB. Priority order:

1. **School office** — university's own official bulletin, admissions office, catalog. Always primary.
2. **Authoritative second-hand** — College Scorecard (US Dept of Ed / IPEDS), accreditor registries, US News public rankings.
3. **Website scrape** — school homepage, meta tags, OG images. Use only when the above don't cover the field.
4. **Generic inference** — e.g., default Common App requirements. Must be annotated `[Source: inferred from common-app-member list]`.

## Honest empty-state rule

If the data for a field is truly unknown after sources 1–3 have been checked:
- Store `null` / omit the key — do NOT invent a value.
- Do NOT silently fall back to institution-wide values (no `prog.tuition or inst.tuition_in_state` chains).
- UI must show an annotated empty state: `"Data not yet available — sources checked: Scorecard, NYU Bulletin"`.

One documented exception: institution-wide `ranking_data` IS exposed on the program detail page under its own `ranking_data` block, so students see institution context without confusing it with program data. Program-level fields (tuition, acceptance_rate, median_salary, employment_rate) stay `null` when unknown.

## Required Institution fields

| Field | Source used for NYU | Notes |
|-------|--------------------|-------|
| `name` | Official | — |
| `type` | Scorecard `ownership_type` (`private_nonprofit` → `"university"`) | — |
| `country`, `region`, `city` | Scorecard address | — |
| `description_text` | Curated summary + `[Source: College Scorecard, IPEDS 193900]` | ≥200 chars |
| `campus_description` | NYU official website + `[Source: nyu.edu]` | ≥200 chars |
| `campus_setting` | Inferred (`urban`) | One of `urban` / `suburban` / `rural` |
| `student_body_size` | Scorecard `student_size` | Integer |
| `logo_url` | Downloaded to S3 from school favicon/bulletin | Must be S3, not external URL |
| `website_url` | Official | — |
| `contact_email` | Admissions office | — |
| `media_gallery` | ≥3 images downloaded to S3 | List of S3 URLs |
| `ranking_data` | **All 43 keys** from `scripts/rebuild_nyu_v2.py:127-222` | See next section |
| `social_links` | Official school social accounts | **Currently NULL on NYU — gap** |
| `policies` | Admissions / transfer / code-of-conduct links | **Currently NULL on NYU — gap** |
| `support_services` | Disability services, counseling, first-gen programs | **Currently NULL on NYU — gap** |
| `international_info` | Visa info, language requirements, international services | **Currently NULL on NYU — gap** |
| `school_outcomes` | Aggregate placement / grad-school yield / alumni network metrics | **Currently NULL on NYU — gap** |
| `is_verified` | `true` when a real admin has claimed it | Scorecard-seeded records stay `false` |

### `ranking_data` required keys (43 total)

Grouped as they appear in `rebuild_nyu_v2.py`:

- **Identity**: `us_news_2025`, `source`, `scorecard_id`, `accreditor`, `address`, `ownership_type`, `lat`, `lon`, `price_calculator_url`
- **Admissions**: `acceptance_rate`, `sat_avg`, `sat_reading_25_75`, `sat_math_25_75`, `act_25_75`
- **Costs**: `tuition_in_state`, `tuition_out_of_state`, `total_cost_attendance`, `room_board`, `books_supply`, `avg_net_price`, `net_price_by_income`
- **Financial aid**: `pell_grant_rate`, `federal_loan_rate`, `students_with_any_loan`, `median_debt`, `median_debt_monthly`, `debt_percentiles`
- **Student body**: `student_size`, `grad_students`, `retention_rate`
- **Demographics**: `gender`, `race_ethnicity`, `first_generation`
- **Faculty**: `faculty_salary_avg_monthly`, `ft_faculty_rate`, `instructional_expenditure_per_fte`
- **Graduation**: `graduation_rate`, `graduation_rate_4yr`, `graduation_rate_by_race`, `transfer_rate`
- **Earnings (institution)**: `earnings_6yr_median`, `earnings_10yr_median`
- **Endowment**: `endowment`

## Required Program fields

| Field | Source for NYU | Notes |
|-------|---------------|-------|
| `program_name` | NYU Bulletin | — |
| `degree_type` | Inferred from bulletin (currently all `bachelors` on NYU — **gap**, NYU has masters/PhD) | One of `bachelors` / `masters` / `phd` / `certificate` / `diploma` |
| `department` | Bulletin (e.g., `Stern School of Business`) | — |
| `description_text` | Bulletin scrape + `[Source: https://bulletins.nyu.edu/...]` | ≥200 chars |
| `outcomes_data` | Scorecard earnings-by-CIP | dict with `earnings_1yr_median` OR `earnings_4yr_median` required when Scorecard covers the CIP |
| `media_urls` | ≥1 image (school-specific or campus fallback) | List of S3 URLs |
| `application_requirements` | NYU admissions office | List of 8 items (Common App, essay, etc.) |
| `intake_rounds` | NYU admissions calendar | dict with `fall_YYYY.early_decision_1 / early_decision_2 / regular_decision` |
| `cost_data` | Scorecard + NYU fees | dict with `tuition_annual`, `fees`, `total_cost_attendance`, `source` |
| `highlights` | Per-school facts from bulletin | ≥3 bullet items |
| `tracks` | Bulletin concentrations (where applicable) | dict with `concentrations` list |
| `campus_setting` | Inherited from institution on enrich | OK to be same as institution |
| `is_published` | `true` after seeding | — |
| `tuition` | Leave `null` unless program-specific tuition known | Institution tuition is in `ranking_data`, accessed separately |
| `acceptance_rate` | Leave `null` unless program-specific known | Same — institution-wide is in `ranking_data` |
| `requirements` | Structured admissions requirements dict | **Currently NULL on NYU — gap** |
| `faculty_contacts` | Department chair + admissions contact | **Currently NULL on NYU — gap** |
| `who_its_for` | 1-paragraph fit summary for students | **Currently NULL on NYU — gap** |

## Per-tab minimum checklist (student SchoolDetailPage)

The 7 tabs at `frontend/src/pages/student/SchoolDetailPage.tsx:241-248`. For each, list fields that MUST render; tab fails audit if any are missing (empty-state OK when data genuinely unknown and annotated).

1. **Overview** — `description_text`, `campus_description`, `media_gallery` (carousel ≥3), `ranking_data.{student_size, graduation_rate, sat_avg, acceptance_rate, us_news_2025}`.
2. **Requirements** — `application_requirements` (Application Checklist ≥5 items), `requirements` dict (or honest empty-state).
3. **Costs & Aid** — `ranking_data.{total_cost_attendance, tuition_in_state, avg_net_price, pell_grant_rate, median_debt}`. Program tab also shows `cost_data.fees`, `cost_data.estimated_living_cost`. NEVER shows "$0 tuition" — if unknown, show "Contact school".
4. **Outcomes** — program-level `outcomes_data.{earnings_1yr_median, earnings_4yr_median}` renders Earnings Progression. Honest empty-state when not covered by Scorecard. Do NOT silently substitute institution `earnings_10yr_median`.
5. **Reviews** — `student_program_reviews` + averages. Empty-state OK when no reviews.
6. **Employer Insights** — `employer_feedback` + averages. Empty-state OK when none.
7. **Match Analysis** — requires logged-in student; calls `/students/me/matches/{program_id}`. Must not crash on a fresh account.

## Known current gaps on NYU (baseline before audit)

These were observed on prod (2026-04-16 status):

| Severity | Gap | Field / Location |
|---|---|---|
| P0 | Detail endpoint falls back `acceptance_rate` to institution | `unipaith-backend/src/unipaith/api/programs.py:115-116` — violates no-fallback rule for program detail view |
| P0 | `institutions.social_links / policies / support_services / international_info / school_outcomes` all NULL on NYU | Institution record |
| P1 | All NYU programs `degree_type = "bachelors"` — rebuild script hard-codes, but NYU has masters/PhD | `scripts/rebuild_nyu_v2.py:241-244` |
| P1 | All NYU programs: `faculty_contacts`, `requirements` dict, `who_its_for` NULL | Program records |
| P1 | `search_programs` keeps `median_salary` fallback to institution `earnings_10yr_median`; `employment_rate` falls back to `graduation_rate` — uniform 82509 / 0.8757 across programs without Scorecard coverage | `unipaith-backend/src/unipaith/services/institution_service.py:1884-1893` |

These gaps will be tracked and fixed in Steps 5/6 of the audit plan.

## Completeness score (future scaling reference)

When the scaling work starts, use this scoring formula (deferred to a future session):

```
score = Σ (filled_required_fields × tab_weight) / Σ (total_required_fields × tab_weight)
tab_weight: Overview = 2.0, Requirements/Costs/Outcomes = 1.0, Reviews/Employers/Match = 0.5
```

Thresholds:
- **Publishable** ≥ 80%
- **Partial** 50–79%
- **Unclaimed** < 50%

NYU target: ≥95% after this session's fixes land.

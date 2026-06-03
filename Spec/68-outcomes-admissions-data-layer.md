# 68 · Outcomes & Admissions-History Data Layer — Typed, Not JSONB

> The papers make outcomes the table-stakes that separate a product from a demo: every Featured filter and the whole Outcomes detail section are specced over *"Salary distribution ranges when available · Starting salary bands · Employment/Underemployment rate · Employer concentration level, feedback score, hire rate · Internship to offer conversion rate · Payback period bands when defined · Graduate placement geography distribution · Top hiring employers by count and recency"* (`Business Methodology`:121-128) — each *"shown with clear labels and time windows"* (`Business Methodology`:178-181). None of that has a typed home.
>
> The code gap: `Program.outcomes_data` and `Program.cost_data` are **untyped JSONB blobs** (`models/institution.py:211,216`). The Featured filter/sort path reaches *into* them by string key — `Program.outcomes_data["median_salary"].as_integer()`, `["employment_rate"].as_float()`, `["payback_months"]` (`institution_service.py:2175-2210`) — and the read helpers are so defensive they handle the blob *deserializing as a string* (`institution_service.py:100-118`, `_outcomes_int`). There is no schema: no enum of metric names, no time window, no provenance, no nullability contract. The salary/employer/payback/placement data the papers promise binds to nothing, so the filters narrow on keys that may never exist and the detail section renders whatever ad-hoc shape a seed happened to write. The "historical partner data" `66`/`67` need is worse — `HistoricalOutcome` (`models/application.py:25`) is seeded with **~14 fabricated round-number rows** (gpa 3.8/3.7/3.0, gre 330/325/300, hand-looped over 6 programs × 2 years, `scripts/seed_dev_data.py:477-489`).
>
> What is already good and must not be rebuilt: the **review schema**. `StudentProgramReview` (7 rubric dims, `models/institution.py:1017`) and `EmployerFeedback` (6 dims, `:1063`) exist, and `api/programs.py:213-219` already does `func.avg()` dimension roll-ups. The missing piece is only the **theme-summarization** the papers put at the top of Insights — *"what students consistently say, what employers consistently say, and common tradeoffs"* (`Business Methodology`:191) — not the tables.
>
> Build anchor: replace the JSONB blobs with typed `program_outcomes` / `program_admissions_history` (+ school-level peers) carrying the `ProvenanceMixin` envelope (`models/crawler.py:63`), build `review_theme_summaries` over the existing review tables, and a service that all consumers (`65` embed, `67` labels, `70` net-price, Featured filters, `11`/`12` detail) read instead of digging into JSONB. Pairs with `65` (matching embeds outcomes), `67` (trains on admit history), `70` (net-price reads cost), `60` (crawled/reference sourcing + first-party-wins), `62` (eval-gates the theme synthesis), `46` §6 (no protected attrs in admit history), `11`/`12` (detail surfaces).
>
> Status: **draft v1.0** · 2026-06-02 · turns the untyped outcomes/cost blobs and the fabricated admit rows into a typed, windowed, provenance-carrying data layer with review-theme synthesis. Rule-based path stays the fallback (`tests/test_plan2_integration.py`).

---

## 1. What exists vs what to build

| Capability | Real module today | Status |
|---|---|---|
| Program outcomes storage | `Program.outcomes_data` JSONB (`institution.py:211`) | **NEW (build): typed `program_outcomes`** |
| Program cost storage | `Program.cost_data` JSONB (`institution.py:216`) | exists — **extend: typed `program_costs` (keep blob as `70` migrates)** |
| Featured filter/sort over outcomes | JSONB key dig (`institution_service.py:2175-2210`) | exists — **rebind to typed columns** |
| Defensive JSONB coercion | `_outcomes_int/_float` (`institution_service.py:98-135`) | exists — **delete once typed** |
| Admissions history | `HistoricalOutcome`, ~14 seeded rows (`application.py:25`, `seed_dev_data.py:477`) | **NEW (build): typed `program_admissions_history` + school peer** |
| School-vs-program separation | none (papers mandate, `Business Methodology`:220) | **NEW (build): `school_outcomes` / `school_admissions_history`** |
| Review dimension roll-ups | `func.avg()` (`api/programs.py:213-219`) | exists — keep |
| Review **theme** synthesis | none (`Business Methodology`:191) | **NEW (build): `review_theme_summaries` + synth agent** |
| Provenance + time window | none on outcomes/cost | **NEW (build): `ProvenanceMixin` + window on every fact** |
| `data_completeness` for `65`/Confidence | not derivable from a blob | **NEW (build): computed from typed coverage** |

## 2. Typed program outcomes — replace the blob

New table **`program_outcomes`** (one row per `(program_id, metric, reference_window)`; long-and-typed beats wide-and-sparse because the papers concede most metrics are *"when available"* / *"when defined"* and a sparse wide row wastes a column-per-rare-field). Carries `ProvenanceMixin` (`models/crawler.py:63`: `source`, `source_url`, `confidence`, `source_count`, `fetched_at`, `status`) so every number knows where it came from.

- **`metric`** — a closed enum, not free JSON keys. The exact `Business Methodology`:121-128 vocabulary: `salary_median`, `salary_band` (p25/p50/p75 → `value_json`), `starting_salary_band`, `employment_rate`, `underemployment_rate`, `hire_rate`, `internship_to_offer_rate`, `payback_period_months` (band → `value_json`), `employer_concentration` (HHI/top-N share). One canonical name; Featured filters bind to it, not to a string a seed invented.
- **Value shape** — `value_numeric Numeric` for scalars (median, rate), `value_json JSONB` for distributions/bands/geography (a band is `{p25,p50,p75,currency}`; placement geography is `[{region, share}]`). Typed *envelope*, structured *payload* — the opposite of today's typed-nothing.
- **Time window (required).** `reference_period` (`String`, e.g. `2024`, `2023-2024`, `class_of_2025`) + `cohort_n int | None`. The papers demand *"clear labels and time windows"* (`:181`); a salary with no window is unshippable. UNIQUE on `(program_id, metric, reference_period, source)` so the same metric across years/sources coexists; latest-window resolution in the service (§7).
- **Nullable "when available"** is the default posture — absence is first-class, never zero-filled. A program with no employer data has *no row*, not an `employer_concentration=0`. Migration: Alembic, expand→contract, single head (never `metadata.create_all()`); `Program.outcomes_data` stays dual-readable until all consumers cut over, then drop in a later contract.

**Top hiring employers** (`:128`) get their own child **`program_top_employers`** (`program_id`, `employer_name`, `hire_count`, `most_recent_hire_year`, `industry`, provenance) — it is a *list by count and recency*, not a scalar, so it does not belong in the metric table.

## 3. Typed admissions-history — replace the fabricated rows

The current `HistoricalOutcome` is a per-applicant row good for nothing aggregate; the papers and `67` need **aggregate admit statistics**. New table **`program_admissions_history`** (one row per `(program_id, cycle_year)`): `applicants int`, `admits int`, `enrolled int`, `admit_rate Numeric`, `yield_rate Numeric` (derived, stored for query speed), `class_profile JSONB` (typed sub-shape: `{gpa_p25, gpa_p50, gpa_p75, test_p50, intl_share, ...}`), `selectivity_band String`, `ProvenanceMixin`. Trends are a query over `cycle_year`, not a stored field.

- This is the **corpus `67` trains on** and **`66`/`70` read for feasibility/probability** (`65` §4's feasibility term, `70`'s admit-probability bands). It must be real or honestly empty — never `random.uniform` (`64` §1).
- **Bias-avoidance (`46` §6):** `class_profile` carries **academic** aggregates only. No protected or proxy attribute (race, name-origin, ZIP-as-proxy) enters admissions-history, because `67` reads it as a training feature. A boot/CI assertion rejects any non-allowlisted `class_profile` key.
- **Retire `HistoricalOutcome`:** keep the per-applicant table only if a real partner feed populates it under `67`'s consent tier; otherwise migrate its (sparse) signal into the aggregate and stop seeding fabricated rows. **Zero `random.uniform` / hand-coded rows in any prod path** (`64` §6 release gate).

## 4. School-level vs program-level — the papers mandate the split

*"Clear separation between school-level aggregates and program-specific outcomes"* (`Business Methodology`:220, restated on the School Detail page spec). Two peer tables, same shape, different grain:

- **`school_outcomes`** / **`school_admissions_history`** — keyed by `institution_id`, same `metric` enum / same `cycle_year` columns + `ProvenanceMixin`. A school employment-rate is a *different fact* from a program one, with its own source (IPEDS school-level vs a program's own reporting) and its own window — never silently averaged up from programs.
- The detail surfaces read them separately: `12` (School Detail) shows school aggregates + a *"Clear separation"* boundary; `11` (Program Detail) shows program outcomes; neither fabricates the other grain. The service (§7) exposes `get_school_outcomes` and `get_program_outcomes` as distinct calls so the two can never be conflated in a join.

## 5. Review theme-summarization — synth, don't re-table

The review *tables* exist; the *dimension averages* exist (`api/programs.py:213-219`). Build only the top-of-Insights theme block (`Business Methodology`:191):

- **New table `review_theme_summaries`** — `(target_type ∈ {program, school}, target_id, audience ∈ {student, employer})`, `themes JSONB` (`[{label, sentiment, supporting_review_ids, n}]` for *what they consistently say*), `tradeoffs JSONB` (*common tradeoffs*), `dimension_rollup JSONB` (snapshot of the existing `func.avg()` so the card is one read), `n_reviews`, `model_version`, `generated_at`, `ProvenanceMixin`. Recompute on review-count delta past a threshold (mirror the rationale cache-key pattern).
- **Theme synth agent** — Qwen *display-synthesis* (`63` §2.5: this is presenting scattered facts, not conversing → Qwen, not Claude), behind **`ai_review_themes_v2_enabled`** (net-new flag; convention `ai_<domain>_v2_enabled`, `config.py:252-318`). **Source-grounded:** every theme cites the `StudentProgramReview` / `EmployerFeedback` rows it summarizes (`supporting_review_ids`); no theme without ≥N backing reviews; no invented sentiment. **Eval-gated (`62`):** groundedness + no-fabrication check before any summary ships; **rule-based fallback** = top dimensions by avg + most-common `reviewer_context` tags + a templated tradeoff from the lowest-rated dimension (never 5xx, `tests/test_plan2_integration.py`).
- Employer themes filter by `industry` (`Business Methodology`:194); student themes by `reviewer_context` (degree level / cohort year). The filters read the same table, sliced.

## 6. Who reads it — wire the consumers off the typed layer

The whole point is that downstream stops digging into JSONB:

- **`65` matching** — the program embedding doc includes a normalized **outcomes summary** (median salary, employment, top employers) from `program_outcomes`; **`data_completeness`** (fraction of the `metric` enum + admit-history populated for this program) replaces the cold-start `0.5` and feeds Confidence (`65` §3/§5). Real coverage, not a constant.
- **`67` learning loop** — `program_admissions_history` is the labeled corpus for outcome models + calibration; consent/training gates apply (`46` §9) — licensed/public reference data trains freely, partner-reported only on `consent.training=true`.
- **`70` financial fit** — net-price reads typed `program_costs` (today `net_price_service.py:100,179,419` reads the `cost_data` blob); `70` owns the cost typing and the admit-probability model that reads `program_admissions_history`. `68` provides the *table*; `70` provides the *estimator*.
- **Featured filters/sorts** — `institution_service.py:2175-2210` rebinds from `outcomes_data["..."].as_integer()` to typed columns; the `_outcomes_int/_float` coercion helpers (`:98-135`) delete. Filters now narrow on a *guaranteed* schema with `nulls_last` honesty for missing windows.
- **`11`/`12` detail** — Outcomes section + Featured cards read the service; provenance + window render beside each number (`63` §7 invariant: provisional + sourced + confidence + first-party-wins).

## 7. Sourcing & resolution — where real data comes from

Per metric, three lanes, **first-party-wins** (`60` §7/§8 authority precedence, never overwrite a first-party value with a crawled one):

- **Institution-reported** (partner DPAs) → `source="reported"`, highest authority. The institution's own placement/admit numbers.
- **Crawled public-non-personal** (`60`) → `source="crawled"`, lands in `reference.py`'s graph first (`Scholarship`/`RefGeoCost`/`RefOccupation` already carry `ProvenanceMixin`), gated behind `ai_crawler_extraction_v2_enabled` / `crawler_live_fetch_enabled` (`config.py:447,563`), grounded-extractor-never-invents.
- **Licensed** — **IPEDS** (admit rates, yield, enrollment, school-level outcomes) + **U.S. College Scorecard** (program-level earnings, employment, debt/payback) → `source="licensed"`, bulk-loaded, skips extraction (`63` §5 two-speed). These seed U.S. outcomes; partner-reported overlays where richer (`64` §7 recommendation).
- **Resolution service** — `OutcomesService.resolve(program, metric)` picks the value by authority precedence then recency-within-authority, exposes `source`+`reference_period`+`confidence` on every read, and computes `data_completeness`. One service; no consumer re-implements precedence.

## 8. Build tasks (checklist)

- [ ] Migration: `program_outcomes` (`metric` enum, `value_numeric`/`value_json`, `reference_period`, `cohort_n`, `ProvenanceMixin`) + `program_top_employers`; expand→contract, single head.
- [ ] Migration: `program_admissions_history` (`cycle_year`, applicants/admits/enrolled, admit/yield rate, academic-only `class_profile`, selectivity band, provenance).
- [ ] Migration: `school_outcomes` + `school_admissions_history` (institution-grain peers); detail surfaces read them separately from program grain.
- [ ] Migration: `review_theme_summaries`; theme-synth agent (Qwen display-synth) behind `ai_review_themes_v2_enabled`, source-grounded, eval-gated (`62`), rule-based fallback.
- [ ] `OutcomesService`: typed CRUD + `resolve()` authority precedence (first-party-wins, `60`) + `data_completeness` computation.
- [ ] Rebind Featured filters/sorts (`institution_service.py:2175-2210`) to typed columns; delete `_outcomes_int/_float` (`:98-135`); keep `outcomes_data` dual-readable until all consumers cut over, then drop.
- [ ] Wire `65` (outcomes summary in program embed + `data_completeness`), `70` (typed costs + admit history), `11`/`12` (provenance+window render).
- [ ] Retire fabricated `HistoricalOutcome` seed (`seed_dev_data.py:477`); IPEDS/Scorecard bulk loader for U.S. seed; partner-reported overlay path.
- [ ] CI assertion: `class_profile` keys are academic-allowlisted only (`46` §6); no protected/proxy attribute in admit history.
- [ ] Fallback: theme synth / any model path unavailable → rule-based summary; never 5xx (`tests/test_plan2_integration.py`).

## 9. Acceptance

- [ ] `Program.outcomes_data` is no longer read by any prod consumer; Featured filters/sorts bind to `program_outcomes` typed columns; `_outcomes_int/_float` deleted.
- [ ] Every outcomes/admit fact carries a `reference_period` (time window) + provenance; a metric with no window cannot be written or rendered.
- [ ] Missing data is absent (no row), never zero-filled; the detail Outcomes section renders only populated, windowed, sourced metrics.
- [ ] School-level and program-level outcomes are stored and read as distinct grains; no surface averages programs up into a school figure silently (`Business Methodology`:220).
- [ ] Zero `random.uniform` / hand-coded rows in any prod admissions-history path; the corpus is real (licensed/reported) or honestly empty (`64` §6).
- [ ] Review theme summaries cite the reviews they summarize; disabling `ai_review_themes_v2_enabled` returns the rule-based dimension+tag summary (clean fallback, tested).
- [ ] `65` reads `data_completeness` from real coverage (not `0.5`); admit history flows to `67` only under its consent/training gate (`46` §9).
- [ ] No `class_profile` field carries a protected/proxy attribute; the CI guard fails if one is added (`46` §6).

## 10. Open questions

- **Outcomes value shape — long-typed rows vs wide nullable columns.** *Recommend long `(metric, window)` rows: most metrics are "when available", a wide table is mostly NULLs and needs a migration per new metric; the enum gives type-safety without column churn.*
- **U.S.-first sourcing vs international parity.** IPEDS/Scorecard are U.S.-only; international programs have no equivalent licensed feed. *Recommend seed U.S. via licensed, international via partner-reported + crawled (`60`), and surface `data_completeness` honestly so the matcher down-weights thin programs rather than guessing.*
- **Does `68` own `program_costs` typing or does `70`?** Both touch cost. *Recommend `68` defines the typed table (so it's available to Featured filters now); `70` owns the net-price/EFC estimator that reads it — table here, model there.*
- **Theme-synth model — Qwen display-synth vs Claude.** Per `63` §1 this is presenting, not conversing → Qwen. *Recommend Qwen behind the flag with the Claude eval-judge (`62`) scoring groundedness; rule-based until it passes per-environment.*
- **Recompute cadence for theme summaries.** *Recommend on review-count delta past a threshold + a nightly floor, version-keyed like the rationale cache, so the card is one read and never stale-by-months.*

Sources: internal — `65` §3/§4 (embeds outcomes, `data_completeness`, feasibility), `67` (trains on admit history), `70` (net-price/admit-probability), `60` §4/§7/§8 (provenance, first-party-wins, sourcing), `62` (eval-gate), `46` §6/§9 (fairness/consent), `11`/`12` (detail surfaces), `63` §2.5/§5 (Qwen display-synthesis); code — `models/institution.py:211,216,1017,1063`, `models/application.py:25`, `models/crawler.py:63` (`ProvenanceMixin`), `models/reference.py:43` (`Scholarship`/`Ref*` provenance pattern), `services/institution_service.py:98-135,2175-2210`, `api/programs.py:213-219`, `services/net_price_service.py:100,179,419`, `scripts/seed_dev_data.py:477-489`, `config.py:252-318,447,563`. Papers — `Business Methodology.docx`:121-128, 178-181, 184-194, 220. Benchmark #2 — `Feature_List_V1.txt` L47/L53 ("Outcome Data — Placement rates, median salaries, licensure pass rates"; "Historical Admit Data") — the table-stakes that separate "finished" from "demo".

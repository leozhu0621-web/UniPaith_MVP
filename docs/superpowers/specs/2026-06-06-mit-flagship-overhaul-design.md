# MIT Institution Page — Flagship Overhaul (Data + Presentation)

- **Date:** 2026-06-06
- **Status:** Approved design → implementation plan next
- **Surface:** `app.unipaith.co/s/institutions/{id}` (student + public institution detail page)
- **Reference institution:** Massachusetts Institute of Technology (`e885756a-dbf3-4140-879d-fa873dc07973`)
- **Goal:** Make the MIT page the **gold-standard template** — complete, accurate, real-sourced data + a few presentation fixes — that every other institution page is measured against.

---

## 1. Context

The layout is fine; the **details** are thin or incomplete. The page already renders Niche-level depth (stat cards, rankings, distinction, test scores, financial aid, demographics, campus map) **if the data exists** — so most of this work is *data completeness*, not redesign.

Key finding from reading the renderer (`frontend/src/pages/student/institution/InstitutionDetail.tsx`) and the live API (`GET /api/v1/institutions/{id}`): **production's MIT data is real and College-Scorecard-sourced** (acceptance 4.55%, net price $20,111, median earnings $143,372, 6-yr completion 96.41%, Nobel 106, MacArthur 85, Class of 2029 funnel 29,281→1,334). The stale dev seed (`seed_dev_data.py`) holds *older* values ($124,200 earnings, no net price) — production is the source of truth, the dev seed is behind.

So this is **fill gaps + surface existing data + cite it + complete schools/programs + small UI cuts** — not "replace fabricated data."

### Gap analysis (traced to code + live API)

| # | Gap | Root cause | Fix type |
|---|-----|-----------|----------|
| 1 | Header shows redundant `acceptance` + `students` chips | Hero pushes them — `InstitutionDetail.tsx:245, 247–248` | Frontend |
| 2 | Rankings only renders **#1 QS** | Renderer (`:555–560`) only shows `ranking_data` entries shaped `{rank, year}`. Prod has *only* `qs_world_university_rankings` in that shape; Times Higher Ed & US News are absent | Data |
| 3 | Two conflicting "students" numbers (4,535 vs 11,816) | Quick facts "Students" = `student_body_size` (≈ undergrad); Distinction "Total enrollment" = `flagship.enrollment_total` (≈ total) | Frontend (relabel) |
| 4 | One-sentence intro | `description_text` is thin | Data |
| 5 | Empty depth sections | Overview already renders `school_outcomes.test_scores / financial_aid / demographics / location` **if present** — MIT's prod data doesn't populate them, so the cards silently don't appear (`:535–544, 634–659+`) | Data |
| 6 | Schools (7) / Programs (22) incomplete & off | Don't match MIT's real **6 academic units** or real program catalog | Data |
| 7 | No visible source line | Page is built for sourcing (`trimSource`, accreditor line) but shows no citation | Both |

---

## 2. Goals / Non-goals

**Goals**
- Fix the 7 gaps above with **real, cited** data and minimal, surgical frontend edits.
- Establish a documented **institution-profile data contract** (validated shape + provenance) so MIT is a reusable template.
- Ship the enriched MIT data to **production** via an idempotent, git-tracked script. No schema migration.

**Non-goals**
- No layout redesign (user: "the basic layout is fine").
- No Events/Updates content work.
- No general crawler build (Spec 60 knowledge engine exists; out of scope here).
- No DB schema migration — data lives in existing JSONB (`ranking_data`, `school_outcomes`) + the `schools` / `programs` tables.

---

## 3. Current data → UI contract (as discovered)

The Overview tab reads (all keys confirmed against the live MIT API):

- **Hero stats** (`:240–248`): `ranking_data.qs_world_university_rankings.{rank,year}`, `school_outcomes.admit_rate`, `founded_year`, `school_outcomes.flagship.enrollment_total ?? student_body_size`.
- **Stat cards** (`:550–554`): `school_outcomes.admit_rate`, `.avg_net_price`, `.median_earnings_10yr`, `.completion_rate_4yr_150pct` (each with a `ranking_data` fallback).
- **Rankings** (`:555–560, 582–595`): every `ranking_data[k]` that is an object with a numeric `.rank`; label via `rankingLabel(k)`.
- **Distinction** (`:561–565, 597–611`): `school_outcomes.flagship.{nobel_laureates, macarthur_fellows, enrollment_total, admissions_cycle, applicants, admits}`.
- **Intro** (`:612–616`): `trimSource(description_text)` (strips a trailing source marker for display).
- **Quick facts** (`:618–632`): `ranking_data.ownership_type`, `campus_setting`, size band of `student_body_size`, `founded_year`, `student_body_size` (labeled "Students"), school/program counts, `ranking_data.accreditor`.
- **Depth (conditional)** (`:634–659+`): `school_outcomes.location.{lat,lng}` (map), `.test_scores.{sat_reading_25_75, sat_math_25_75, act_25_75}`, `.financial_aid`, `.demographics`, `.retention_rate_first_year`.

Schools and Programs come from separate queries (`schoolsQ`, `programsQ`) → the `schools` and `programs` tables.

---

## 4. Design

### 4.1 Presentation (frontend — surgical)

1. **Header** (`:243–248`) — remove the `acceptance` push (`:245`) and the `students` push (`:247–248`). Result: `#1 QS World 2025 · 1861 founded`.
2. **Quick facts** (`:625`) — relabel `"Students"` → `"Undergraduates"` (the value `student_body_size = 4,535` is the undergrad count; total stays in Distinction as "Total enrollment").
3. **Rankings** — no renderer change needed; lighting up THE/US News is a *data* change (4.3). Verify `rankingLabel()` maps the new keys to clean labels ("Times Higher Ed", "US News") — add mappings if missing.
4. **Sources footer** — new small `<SourcesFooter>` card at the bottom of Overview that renders `school_outcomes.sources` (array of `{label, source, year, url}`). Text-only, muted, links open in new tab. This satisfies the "sourced citation" design standard.

> All other Overview cards already exist and will populate automatically once the data (4.3) is present.

### 4.2 Data contract + provenance (the "template")

Add a documented Pydantic contract (no migration — it validates the JSONB shape on write, it is **not** a DB column):

- `InstitutionProfileContract` — documents/validates the expected shapes of `ranking_data` and `school_outcomes`, including the nested `flagship`, `test_scores`, `financial_aid`, `demographics`, `location`, and `sources` blocks.
- **Provenance convention:** `school_outcomes.sources: [{label, source, year, url}]` — one entry per data group (e.g., College Scorecard 2024, QS 2025, MIT Facts 2025, Common Data Set 2024–25). Rendered by the Sources footer.
- The existing TS `Institution` type already covers `ranking_data`/`school_outcomes` as `Record<string, any>`; add a typed `InstitutionProfile` helper type for the validated shape (documentation-grade; no runtime break).

This is what makes the page a template: any institution populated to this contract gets the same depth.

### 4.3 Data content (real, sourced)

**Headline stats** — keep production's existing real values (College Scorecard); verify source + year and attach to `sources`. Re-sync the dev seed to match so dev ≈ prod.

**Rankings** — add to `ranking_data` as rank-objects so all three render:
- `qs_world_university_rankings: {rank: 1, year: 2025}` (already present)
- `times_higher_education: {rank: <verify>, year: 2025}`
- `us_news_national: {rank: <verify>, year: 2025}`
- Exact THE / US News ranks verified at build against timeshighereducation.com and usnews.com (do not guess).

**Intro** — replace the one-liner with a 3–4 paragraph editorial overview grounded in real MIT facts (founding/mission, scale & research, distinctive culture, outcomes). Carries its source via the `trimSource` convention.

**Light up empty sections** — populate from Common Data Set / College Scorecard (verified + cited at build):
- `location: {lat: 42.3601, lng: -71.0942}` (campus map)
- `test_scores: {sat_reading_25_75, sat_math_25_75, act_25_75}`
- `financial_aid: {...}` and `demographics: {...}`

**Distinction** — keep existing (Nobel/MacArthur/enrollment/funnel); optionally add 1–2 more real flagship facts (e.g., research expenditure, startups founded by alumni) if cleanly sourced.

**Schools — MIT's real 6 academic units** (replace the current 7):
1. School of Engineering
2. School of Science
3. School of Humanities, Arts, and Social Sciences (SHASS)
4. MIT Sloan School of Management
5. School of Architecture and Planning
6. MIT Stephen A. Schwarzman College of Computing

Each with an accurate one-paragraph description + sort order.

**Programs — real catalog organized by school** (≈30–40 flagship/representative degrees; **not** exhaustive). Curation targets (per-program degree type, duration, cost/funding, acceptance, requirements verified + cited at build):
- *Engineering:* EECS (6), Mechanical (2), Aero/Astro (16), Chemical (10), Materials Science (3), Biological (20), Civil & Environmental (1), Nuclear Science (22)
- *Science:* Physics (8), Mathematics (18), Biology (7), Chemistry (5), Brain & Cognitive Sciences (9), EAPS (12)
- *SHASS:* Economics (14), Linguistics & Philosophy (24), Political Science (17), Comparative Media Studies/Writing (21)
- *Sloan:* MBA, Master of Finance, Master of Business Analytics, Sloan Fellows MBA, PhD in Management, Management (15, undergrad)
- *Architecture & Planning:* Architecture (4), Urban Studies & Planning (11), Media Arts & Sciences (Media Lab), Real Estate Development
- *Schwarzman College of Computing:* Computer Science & Engineering (6-3), AI & Decision Making (6-4), Computational Science & Engineering, PhD in Computer Science

### 4.4 Delivery to production

- Author an **idempotent, git-tracked enrichment script** (e.g., `scripts/enrich_institution_mit.py`) that upserts MIT's canonical profile (`ranking_data`, `school_outcomes` incl. `sources`, `description_text`) and replaces its `schools` + `programs` rows by stable dedup keys (`replace=True` / explicit keys per the data rules — no collisions).
- **Open item to confirm first:** trace how production was enriched beyond the dev seed (existing prod-seed/enrichment path vs. manual) — extend that path if it exists; otherwise this new script is the path. Run against the prod DB, then verify live.
- Keep the **dev seed in sync** so local dev mirrors prod.

---

## 5. Testing

- **Backend:** a contract test that validates the seeded MIT profile against `InstitutionProfileContract` (shape + required `sources`); a test asserting the enrichment script is idempotent (run twice → same row counts, no dup schools/programs).
- **Frontend:** vitest assertions that the hero no longer renders `acceptance`/`students` chips, Quick facts label reads "Undergraduates", and `<SourcesFooter>` renders given a `sources` array.
- **Manual/preview:** load the MIT page, confirm three rankings render, depth cards appear, schools = 6, programs catalog is complete, sources footer shows.

---

## 6. Sources (to cite on-page + in spec)

- U.S. Dept. of Education **College Scorecard** (net price, earnings, completion, test scores, demographics, aid)
- **QS** World University Rankings 2025
- **Times Higher Education** World University Rankings 2025
- **U.S. News** Best National Universities
- **MIT Facts** (mit.edu/about) — Nobel/MacArthur, enrollment, schools
- **MIT Common Data Set** 2024–25 (admissions funnel, test ranges)

All numeric figures verified against these at build; none invented.

---

## 7. Rollout

Per the standing "ship every time" rule: implement → `tsc 0 · build 0 · tests green` → commit → merge to `main` → auto-deploy → **verify live** on app.unipaith.co + api.unipaith.co, in the same unit of work. MIT page is the acceptance check.

# Discover hub — four feature ideas (from the 2026-06-14 review)

**Date:** 2026-06-14
**Status:** Approved (user: "1 to 4 are good, build them all")
**Source:** the multi-agent Discover review (`project_discover_review`). Ideas #1–#4 of 5; #5 (peer cohort chip) deferred.
**Benchmarks:** Niche (list-building, outcomes), Handshake (saved-jobs compare, deadline tracker), LinkedIn (saved-items comparison).

Each feature is shipped as its OWN increment (spec → build → test → ship → verify) so it lands verified, not as one mega-PR. Build order is small→large: **#1 → #2 → #4 → #3**. All data contracts below were verified against the live code (never fabricate).

---

## Feature 1 — Application-list balance meter

**What:** a compact "Your list balance" strip telling the student whether their *saved* list is balanced across reach/target/safer, with a neutral nudge when it's lopsided (Niche "build a balanced list").

**Data (verified):** `listSaved()` → `SavedProgram[]`, each with `band_label?: 'reach'|'target'|'safer'|null` (joined from the match row). Count bands across saved programs; `null` band = "not yet scored" (excluded from the balance, surfaced as a quiet aside if any).

**Logic (pure, deterministic, frontend-only):**
- counts `{ reach, target, safer, unscored }` from saved programs.
- nudge rule (neutral copy, NO gold): `safer === 0 && total >= 3` → "Consider adding a safer school."; `reach === 0 && total >= 3` → "Room for an ambitious reach."; else balanced → "A balanced spread."
- hide entirely when `total === 0` (nothing saved) — the empty Saved page already guides.

**Placement:** the Saved room (`SavedListPage`) — it IS the saved list. A `ListBalanceMeter` strip directly under the page header (above the saved grid). Reads the `listSaved` query the page already runs (no new fetch).

**Files:** create `pages/student/saved/ListBalanceMeter.tsx` + `pages/student/saved/listBalance.ts` (pure `computeBalance`); render in `SavedListPage.tsx`. Test `listBalance` (pure) + a render test.

---

## Feature 2 — Outcome-first discovery

**What:** make ROI data *navigable*, not just decorative — a "Best outcomes" sort + outcome-themed browse tiles (Niche "after graduation" / LinkedIn "where graduates work").

**Data (verified):** backend `InstitutionService.search_programs` ALREADY orders by `sort_by="salary_desc"` and `"employment_desc"` (institution_service.py:2240-2257) and filters `min_median_salary` / `min_employment_rate` (search.py:85-86). The only gap is enum wiring.

**Backend (tiny):**
- `schemas/search.py::SortOption` — add `salary_desc = "salary_desc"` and `employment_desc = "employment_desc"`.
- `services/search_service.py::_SORT_MAP` — add both → their string keys.
- (filters already pass through `_FILTER_KEYS`.)

**Frontend:**
- `types/search.ts::SortOption` — add `'salary_desc' | 'employment_desc'`.
- `SortMenu.tsx` — add options: "Best outcomes (salary)" → `salary_desc`, "Best job placement" → `employment_desc`.
- Outcome tiles (frontend-only, set existing filters): extend `GenreTiles` (or add an `OutcomeTiles` strip shown alongside the genre tiles when search is idle) with 3 tiles that write filters into the URL via the existing filter mechanism:
  - "High earning potential" → `min_median_salary` (a sensible floor, e.g. 60000) + `sort=salary_desc`
  - "Strong job placement" → `min_employment_rate: 0.8` + `sort=employment_desc`
  - "Low tuition, high salary" → `max_tuition` (e.g. 20000) + `min_median_salary: 60000`
  - tiles only surface programs that have real outcome data (the filters guarantee it — no fabrication).

**Files:** backend `schemas/search.py`, `services/search_service.py` (+ test `test_search.py`); frontend `types/search.ts`, `SortMenu.tsx`, `GenreTiles.tsx`/new `OutcomeTiles.tsx`, wired in `DiscoverySearch.tsx`. Tests: backend sort param accepted + orders; frontend tile→filter mapping pure test.

---

## Feature 4 — Application-season timeline

**What:** promote the cramped 3-row deadline radar into a horizontal "Application season" overview — saved/applied program deadlines grouped by month with a per-month density cue, plus a batch "remind me this month" (Handshake deadline tracker).

**Data (verified):** `getConnectFeed('recent', undefined, { kinds: 'deadline' })` → items `{ program_id, program_name, institution_name, deadline, days_until }`. `createReminder()` already exists (used by the rail). Group by `deadline` month; density = count per month; urgency thresholds reuse the rail's (≤7 error, ≤30 warning).

**Placement:** the Calendar room (`CalendarPage`) — it's the time surface. An `ApplicationSeason` strip above the calendar grid (collapses to nothing when there are no upcoming deadlines). Keeps it independent of ExplorePage.

**Logic (frontend-only):** group deadline items into the next ~6 months; render each month as a column/segment with its count + the soonest item; "Remind me for all in <month>" fires `createReminder` per item in that month (best-effort, toast on done).

**Files:** create `pages/student/calendar/ApplicationSeason.tsx` + a pure `groupByMonth` helper; render in `CalendarPage.tsx`. Tests: `groupByMonth` pure test + a render test.

---

## Feature 3 — Saved Compare board (Shortlist matrix)

**What:** turn the saved pile into a decision surface — a persistent, sortable side-by-side matrix of ALL saved programs (distinct from the existing transient 4-item `CompareTray`). Flags "too many reaches" by band count (Handshake/LinkedIn saved-items comparison).

**Data (verified):** `listSaved()` → `SavedProgram[]` carries `program_name, institution_name, degree_type, band_label, tuition, acceptance_rate, duration_months, application_deadline` (fitness/confidence are band-only per AI-Structure §14 — use band, not raw numbers). Salary/employment are NOT on the saved row → omit those columns (no fabrication).

**Placement:** the Saved room — a "Compare" view toggle on `SavedListPage` (alongside the existing list/grid), OR a dedicated `?view=compare` section. A sortable table: columns = Program · School · Band · Acceptance · Tuition · Duration · Deadline. Click a column header to sort; a band-count summary line ("4 reach · 2 target · 1 safer") reuses Feature 1's `computeBalance` and flags too-many-reaches.

**Logic (frontend-only):** sortable table over the `listSaved` data; sort comparators per column (nulls last); reuse `computeBalance`. Row click → program detail. Empty → reuse the page's empty state.

**Files:** create `pages/student/saved/CompareBoard.tsx` (+ reuse `listBalance.ts`); a view toggle in `SavedListPage.tsx`. Tests: sort comparator pure tests + a render test (renders saved rows, sorts on header click).

**Note:** #3 and #1 both live in `SavedListPage` and share `listBalance.ts` — build #1 first, then #3 reuses it. They ship as separate increments but the second rebases on the first.

---

## Cross-cutting

- **Brand:** neutral/cobalt; gold stays reserved (no gold in any of these). Density per the app-shell rule. Card/table styling reuses the unified shell + density primitives.
- **Motion:** `stagger-list` on new lists; respect reduced-motion.
- **No new tables, no migrations.** Only #2 adds two enum values + map entries (additive, backward-compatible).
- **Testing:** each feature's pure logic is unit-tested; each component gets a render test; full `vitest` + `tsc -p tsconfig.app.json` + `npm run build` green before each merge; backend #2 adds a `test_search.py` case. Ship + verify-live each.

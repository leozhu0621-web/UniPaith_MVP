# MIT Overview Presentation Redesign — Implementation Plan (Round 2)

> **For agentic workers:** execute task-by-task with TDD + frequent commits. Frontend-only; all data exists. Steps use `- [ ]`.

**Goal:** Recompose `OverviewTab` in `InstitutionDetail.tsx` into a Niche-style narrative using small reusable visual primitives, dedupe, and surface unused data.

**Architecture:** Add 5 presentational primitives near the existing in-file helpers (`RankingBadge`, `AdmissionsFunnel`, `DiversityBar`, `StatBar`, `ChipList`), then rebuild `OverviewTab`'s JSX to the new section order. No data/schema/API change. No file split (concurrent branches share this file). Semantic tokens only (dark-safe); gold = the single #1-ranking peak.

**Tech Stack:** React 19 + TS + Tailwind + lucide-react + vitest/testing-library.

---

## Task 0 — Ground the build (read existing code)
- [ ] Read `InstitutionDetail.test.tsx` to learn the render wrapper + how the institution query is mocked (round-1 tests live here).
- [ ] Read the `Fact` component + `Card` import + the lucide icon import block + helpers `ownershipLabel` / `SETTING_LABELS` / `sizeBandLabel` in `InstitutionDetail.tsx`.
- [ ] Confirm available lucide icons for a ribbon/medallion (`Award`, `Trophy`, `Medal`); pick one already imported or add to the import.

## Task 1 — Visual primitives + unit tests
**Files:** Modify `InstitutionDetail.tsx` (add primitives near other helpers); Test `InstitutionDetail.test.tsx`.

- [ ] **1.1 Write failing tests** for the primitives (render in isolation):
  - `RankingBadge` with `peak` renders the rank and applies the peak (gold) treatment (assert a marker class/testid); without `peak`, no gold.
  - `AdmissionsFunnel` renders applicants, admits, and the rate.
  - `DiversityBar` renders one labeled segment per `{label,pct}`.
  - `StatBar` renders label + percent text; bar width ∝ pct.
  - `ChipList` renders one chip per item.
- [ ] **1.2 Run tests → fail** (`npx vitest run src/pages/student/institution/InstitutionDetail.test.tsx`). Expected: components undefined.
- [ ] **1.3 Implement the 5 primitives.** Semantic tokens only. `RankingBadge` peak → gold ring/fill (`ring-[--gold]` equivalent token used elsewhere for earned beats — grep the codebase for the existing gold token rather than inventing one); non-peak → `text-secondary`/muted. `DiversityBar` palette = `secondary` at descending opacity + `muted` for the remainder; include a legend; ARIA label per segment. Each primitive accepts a typed props object; returns null on empty input.
- [ ] **1.4 Run tests → pass.**
- [ ] **1.5 Commit** `feat(institution): visual primitives for the Overview redesign`.

## Task 2 — Recompose OverviewTab
**Files:** Modify `InstitutionDetail.tsx` (`OverviewTab`); Test `InstitutionDetail.test.tsx`.

- [ ] **2.1 Write failing tests** (mock institution query with MIT-shaped `ranking_data` + `school_outcomes`):
  - Rankings render as 3 badges; the QS #1 badge carries the peak treatment.
  - Admissions section shows the funnel (29,281 / 1,334 / 4.5%) and **acceptance rate does not appear as a separate bare `Fact`** (dedupe — it's a key card + the funnel).
  - Outcomes section shows top-industry chips (Technology, Finance, Consulting, Research) and median earnings.
  - Cost & Aid leads with net price ($20K) and shows Pell/loan bars + median debt.
  - Student body shows the `DiversityBar` + Women + the size split (Undergraduate / Graduate / Total).
  - Recognition shows Nobel + MacArthur with the context subtitle; Total enrollment is no longer inside it.
  - Quick facts shows Carnegie classification + ownership; founded appears once.
- [ ] **2.2 Run → fail.**
- [ ] **2.3 Implement** the new section order + wire each section to its primitive. Compute `grad = enrollment_total - student_body_size` (guard nulls). Remove the duplicate acceptance `Fact` from Admissions; move the funnel in; move Total enrollment to Student body; rename "First destination"→"After MIT", "Financial aid"→"Cost & Aid"; enrich Quick facts (Carnegie, ownership) and drop the vague size band. Keep Location + Sources as-is.
- [ ] **2.4 Run → pass; run the full institution test file → green** (no regressions).
- [ ] **2.5 Commit** `feat(institution): Niche-style Overview narrative + dedupe`.

## Task 3 — Verify + ship + show live
- [ ] **3.1** `cd frontend && npx tsc --noEmit ; echo EXIT=$?` → 0.
- [ ] **3.2** `npx vitest run src/pages/student/institution/InstitutionDetail.test.tsx ; echo EXIT=$?` → pass.
- [ ] **3.3** `npm run build ; echo EXIT=$?` → 0.
- [ ] **3.4 Preview** locally (uvicorn + vite against dev DB w/ MIT enriched) and screenshot the new Overview for a visual gut-check before shipping.
- [ ] **3.5 Ship:** `git fetch origin && git rebase origin/main` (reconcile any concurrent `InstitutionDetail.tsx` edits — keep-both; if a concurrent session redesigned these sections, merge thoughtfully). Re-run 3.1–3.3. Push, open PR, squash-merge to `main`.
- [ ] **3.6 Verify live:** frontend deploy success; grep the live bundle for new markers (e.g., "After MIT", "MacArthur"); load `app.unipaith.co` MIT page and **screenshot the result for the user**. Invalidate CloudFront if stale.
- [ ] **3.7** Confirm clean tree + main at new commit + deploy green.

## Self-review
- Spec sections 1–6 all covered: rankings→T1/T2, distinction-split→T2, quick-facts dedupe/enrich→T2, outcomes/cost/student-body→T1 primitives+T2 wiring. ✓
- No placeholders: primitive behavior + test assertions are concrete; the one "grep for the existing gold token" is a deliberate "match the codebase, don't invent" instruction. ✓
- Types consistent: primitive names + props identical across Task 1 (def) and Task 2 (use). ✓

# 13 · Program Detail Page (Student-Facing)

> The editorial deep-dive a student lands on after picking a program. Fit, affordability, requirements, outcomes, **Insights** (student/alumni reviews + employer feedback) in a consistent format across institutions. **No decorative imagery, no marketing gradients — program-specific and editorial.**
>
> Status: **draft v1.0** · 2026-05-29 · Route: `/s/programs/:programId` (also at `/s/schools/:programId` alias — see `90` G-A1 to remove).

---

## 1. Purpose

After Discovery/Match, the student needs to decide if a program is worth applying to. This page presents standardized comparable fields + insights that aggregate the human signal the cards can't carry.

**Critical brand rule** (per user memory + CLAUDE.md):
- No decorative images.
- No gradients.
- No color accents specific to "marketing" feel.
- Aesthetic is editorial and program-specific, not generic.

The current `SchoolDetailPage.tsx` file is mis-named — it's actually the program detail page. Rename per `90` G-A1.

---

## 2. Visual layout

```
┌────────────────────────────────────────────────────────────────────────────┐
│  [Wordmark]   Discover · Match · Apply · Connect              [avatar]      │
├────────────────────────────────────────────────────────────────────────────┤
│  Match · Search · Computer Science MS  ·  ◾  University of Foo               │← breadcrumb
│                                                                              │
│  ╔════════════════════════════════════════════════════════════════════════╗ │
│  ║                                                                         ║ │
│  ║  PROGRAM                                                                ║ │← eyebrow
│  ║  Computer Science, M.S.                                                 ║ │← H1
│  ║  University of Foo · New York, NY                                       ║ │← H3 muted
│  ║                                                                         ║ │
│  ║  [DualRing 82/74]    Master's · In-person · 2 years · $48k/yr           ║ │← fact strip
│  ║                                                                         ║ │
│  ║  [Save to my list] [Add to compare] [Start application →]               ║ │← actions
│  ╚════════════════════════════════════════════════════════════════════════╝ │
│                                                                              │
│  TABS:  Overview · Admissions · Costs & Aid · Outcomes · Insights · Reviews  │
│                                                                              │
│  TAB CONTENT (per tab)                                                       │
└────────────────────────────────────────────────────────────────────────────┘
```

No hero banner with rotating photos. No campus images. The header is text-driven.

---

## 3. Tabs

### 3.1 Overview
Program description, academic focus, tracks/concentrations, learning format expectations, typical completion timeline. Sourced from `programs.description`, `programs.tracks_concentrations[]`, `programs.who_its_for`. Plain markdown rendering.

### 3.2 Admissions
- Requirements summary (materials, prerequisites, tests policy). Sourced from `programs.application_requirements`.
- Deadline and intake windows. Per `programs.intake_rounds[]`.
- Selectivity and access.
- Plain-language guidance on what the program typically values.

### 3.3 Costs & Aid
- Tuition + fee structure.
- Estimated total cost bands.
- Funding + aid signals.
- Cost fields shown in a consistent schema (`programs.cost_data`) — so cross-program compare works.

#### 3.3a Net Price Estimator (MVP-extend, `92` §2)
A personalized **net price** — not the sticker price — for *this* student at *this* program. Sourced from the OUTPUT schema `40` §4.12 (`net_cost_scenario_range`, `affordability_band`, `aid_scholarship_likelihood_band`).

- Inputs: the program's `cost_data` (COA components) + the student's financial signals (`40` §3.13 budget, `needs_financial_aid_flag`) + scholarship likelihood.
- Output: **estimated net price range** (`{min, expected, max}`) = COA − estimated aid/scholarship, with a one-line "what drives this."
- **Gap analysis:** net price vs the student's `max_affordable_total_cost_of_attendance` → affordable / stretch / out-of-reach, with the shortfall amount.
- Optional: import a result from a school's official Net Price Calculator (paste/upload) to reconcile against the estimate (`92` Net Price Estimator feature).
- **Honesty guardrail:** always a range with "estimate, not a quote" framing; never implies an aid commitment. Recompute on profile/program version change.
- Display: in the Costs & Aid tab as a highlighted block; the headline net-price range also appears in the sidebar (§4) and feeds the compare table (`12`/`15`).

### 3.4 Outcomes
- Employment + placement summary.
- Salary bands + distributions.
- Internship + co-op pipeline.
- Employer + industry placement.
- All outcomes labeled with clear time windows.

### 3.5 Insights (the differentiator)
**The single most important tab.** Two panels:

**Student / alumni reviews:**
- Overall rating + per-dimension ratings: teaching quality, workload, career support, internship access, community & culture, perceived ROI.
- Reviewer context tags: current student, recent graduate, alumni, degree level, cohort year.
- Guided prompts: "Who thrives here?" / "Who should avoid it?" / "Best resources?" / "Biggest tradeoffs?"

**Professional / employer feedback:**
- Aggregated sentiment indicators on job readiness + skill alignment.
- Dimension-based feedback categories: technical fundamentals, practical skills, communication, teamwork, reliability.
- Hiring behavior: repeat-hiring patterns + internship-to-offer conversion indicators.
- Summary themes: "what students consistently say" / "what employers consistently say" / "common tradeoffs."

Filters inside Insights:
- Filter reviews by reviewer type, degree level, cohort year range, rating dimension.
- Filter employer feedback by industry.

### 3.6 Reviews (alias / extension of Insights)
Some current code splits Insights into Reviews + Employer Feedback. The spec considers them one tab (Insights). Migration: collapse to one tab; legacy `?tab=reviews` redirects to `?tab=insights`.

---

## 4. Sidebar

```
RELATED
- Similar programs (3 cards)
- Other programs at this school (link)
- Back to Discovery with these attributes pre-applied
```

Generated by similarity search on (subject + degree + location vector). No promotional content.

---

## 5. Data shape

```ts
type ProgramDetail = {
  id: string;
  name: string;
  school_id: string;
  school_name: string;
  location: Location;
  degree_type: DegreeType;
  delivery_format: DeliveryFormat;
  duration_months: number | null;
  description: string;            // markdown
  tracks_concentrations: string[];
  who_its_for: string | null;
  application_requirements: ApplicationRequirements;
  intake_rounds: IntakeRound[];
  cost_data: CostData;
  outcomes_data: OutcomesData;
  insights: {
    student_reviews: Review[];
    employer_feedback: EmployerFeedback[];
    summary_themes: SummaryThemes;
  };
};

// match-context overlays when student is logged in
type ProgramDetailWithMatch = ProgramDetail & {
  fitness_score: number | null;
  confidence_score: number | null;
  rationale: AIRationale | null;
};
```

Endpoints:
- `GET /programs/:id` — public.
- `GET /me/programs/:id` — authenticated, includes match overlays.
- `GET /programs/:id/insights?filter=...` — reviews + employer feedback (paginated).

---

## 6. States

- **Loading:** skeleton for header + 6 tab placeholders.
- **Empty insights:** "Reviews aren't available for this program yet." (no fabrication).
- **Match not computed (student not logged in):** hide DualRing; show single "Sign in to see your match" CTA in fact strip.
- **Program archived:** "This program is no longer accepting applications" banner; actions disabled.

---

## 7. AI integration

- `MatchRationaleAgent` (`42` §6) — Why-this-match popover from the DualRing.
- (Future) `InsightsSummarizer` agent — distills review themes; defer to Phase 2.

---

## 8. Brand compliance

- Header is text-only — no hero image.
- DualRing in the fact strip is the sole accent.
- Action button order: Save (tertiary) → Add to Compare (tertiary) → Start application (secondary cobalt).
- Tabs underline in `--accent`.
- Insight panels: no charts with marketing color schemes; use `--secondary` for primary series only.

---

## 9. Gaps (from `90`)

- G-A1 (major): file is named `SchoolDetailPage.tsx` — rename to `ProgramDetailPage.tsx`.
- G-S2 (major): DualRing not wired; current code reads legacy `match_score`.
- Hero banner with auto-rotating images per audit — violates "no decorative images" — must be removed.
- "Reviews" tab and "Employer Feedback" merged into Insights per spec.

---

## 10. Tests

- Route /s/programs/:id renders correctly.
- DualRing displays for authenticated student with computed match; hidden for public visitors.
- Insights filter by reviewer type / industry persists in URL.
- Save / Add to Compare / Start application actions trigger correctly.
- "Similar programs" suggestions return ≥ 3 results in seeded test data.

---

## 11. Copy

- "Save to my list" / "Saved" (toggle).
- "Add to compare" / "Open compare".
- "Start application →".
- "Reviews aren't available for this program yet."
- "Sign in to see your match."

---

## 12. Open questions

- **Verified-reviewer policy.** How do we authenticate that a "current student" review is from an actual current student? Recommend: email-domain verification at submission time.
- **Employer-feedback source.** Seed from public sources (Glassdoor, LinkedIn alumni statistics)? Or build a partner pipeline? MVP: scrape-summarized aggregates with provenance shown.
- **Comparable cost fields across countries.** Need a normalization layer for currency + inclusion (is housing in this tuition figure?). Defer; flag in `cost_data` schema for institution to declare.

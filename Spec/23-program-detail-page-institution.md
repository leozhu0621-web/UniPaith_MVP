# 23 · Program Detail Page Editor (Institution-Facing)

> The institution-facing program editor + the public program page contract. Where institutions publish program overview, deadlines, requirements, costs, outcomes, media — and where the canonical `ProgramCard` schema (used everywhere students see programs) is filled.
>
> Status: **draft v1.0** · 2026-05-29 · Routes: `/i/programs/:id/edit`, `/i/programs/new`. Public output renders at `/s/programs/:programId` (`11`) and `/program/:programId`.

---

## 1. Purpose

Institutions need a guided editor that produces a complete, schema-valid program detail. Current editor uses raw JSON textareas for the complex blobs (G-I1) — spec replaces with form-based editors.

---

## 2. Editor structure

Sections (vertical scroll, each a card):

1. **Identity** — name, school (sub-institution), department, degree type, delivery format, duration (months).
2. **Overview & structure** — description (markdown), tracks/concentrations, who-it's-for, learning format expectations.
3. **Requirements** — application materials, prerequisites, test policy. (Cross-link to `RequirementsChecklistPage`.)
4. **Deadlines & rounds** — intake rounds with open/deadline/decision dates. (Cross-link to `IntakeRoundsPage`.)
5. **Costs** — tuition + fee structure, estimated total cost bands, funding/aid signals.
6. **Outcomes** — placement summaries, salary bands, common roles, internship pipeline.
7. **Media** — program logo (text-only per brand), optional gallery if institution chooses.
8. **Promotion settings** — categories the program participates in for promoted placements.

Each section: form-based; under an "Advanced" toggle, an optional raw-JSON editor for power users.

---

## 3. Schemas per section

```ts
type ProgramApplicationRequirements = {
  materials: Array<RequirementItem>;
  prerequisites: Array<{ name: string; required: boolean; allowed_substitutes: string[] }>;
  test_policy: {
    required: TestType[]; optional: TestType[]; waived_rules: string;
    stance: 'required' | 'recommended' | 'test_optional' | 'test_blind';   // MVP-extend, 49 §3
    superscore_enabled: boolean;
    accepted_tests: TestType[];
    typical_ranges: Array<{ test: TestType; low: number; high: number }>;
  };
  recommendations: { required_count: number; types: Array<'academic' | 'professional' | 'other'> };
};
// Test-score management (MVP-extend, `49` §3): `test_policy.stance` drives the student's
// `test_policy_compatibility` (`42` §4.6) + apply-ready gate (`42` §6.2). `superscore_enabled`
// → platform computes the superscore across attempts (`42` §4.6). Test-optional cohort
// outcome-analysis for the committee lives in `32` §7A.3. Direct score import + verification
// record status in MVP; provider integration is Phase-2 (`49`).

type IntakeRound = {
  id: string;
  name: string;                     // "Fall 2027 Round 1"
  term: { season: string; year: number };
  open_date: ISO8601;
  deadline: ISO8601;
  decision_date: ISO8601 | null;
  start_date: ISO8601 | null;
  capacity: number | null;
};

type ProgramCostData = {
  tuition_amount: number;
  tuition_currency: string;
  tuition_period: 'per_year' | 'per_credit' | 'total_program';
  fees: Array<{ name: string; amount: number; required: boolean }>;
  estimated_total_cost_band: { min: number; max: number; currency: string };
  funding_signals: { ta_funded: boolean; ra_funded: boolean; merit_scholarship_available: boolean; need_based_available: boolean };
};

type ProgramOutcomesData = {
  placement_rate_pct: number | null;
  median_starting_salary: number | null;
  salary_distribution_bands: Array<{ band_label: string; percent: number }>;
  common_roles: string[];
  top_employers: string[];
  internship_to_offer_pct: number | null;
  time_to_placement_months: number | null;
  outcome_reporting_window: string;
};
```

---

## 4. Publish flow

- Save draft → `status='draft'`.
- Publish → schema-validates against `ProgramCard` + requirements; on success `status='published'`.
- Unpublish → `status='draft'` (existing applications retain their snapshotted requirements).

---

## 5. Data shape

```ts
type Program = {
  id: string;
  institution_id: string;
  school_id: string | null;        // sub-institution
  name: string;
  department: string | null;
  degree_type: DegreeType;
  delivery_format: DeliveryFormat;
  duration_months: number | null;
  tuition_amount: number | null;
  acceptance_rate_pct: number | null;
  description: string;             // markdown
  tracks_concentrations: string[];
  who_its_for: string | null;
  application_requirements: ProgramApplicationRequirements;
  intake_rounds: IntakeRound[];
  cost_data: ProgramCostData;
  outcomes_data: ProgramOutcomesData;
  media_urls: string[];
  highlights: string[];
  faculty_contacts: Array<{ name: string; email: string; role: string }>;
  status: 'draft' | 'published';
  version: number;                 // for cache invalidation
};
```

Endpoints:
- `GET /i/programs/:id`.
- `POST /i/programs` — create.
- `PATCH /i/programs/:id` — update.
- `POST /i/programs/:id/publish`.
- `POST /i/programs/:id/unpublish`.
- `DELETE /i/programs/:id`.

---

## 6. States

- **Loading** — skeleton.
- **Validation error on publish** — modal lists missing required fields; clicking each scrolls to the section.
- **Concurrent edit** — optimistic lock via `version` field; conflict → "Someone else edited this. Reload?"

---

## 7. AI integration

None for MVP. Future: `ProgramDescriptionAssistant` — drafts an updated description from the structured fields when the institution updates curriculum.

---

## 8. Brand compliance

- Form sections collapsible.
- Publish button cobalt; Unpublish in tertiary.
- "Advanced (raw JSON)" toggle small text + warning style.

---

## 9. Gaps (from `47`)

- G-I1 (major): replace raw JSON textareas with guided forms.

---

## 10. Tests

- Create → publish flow.
- Schema validation rejects required-missing.
- Version increment on save.
- Public page reflects published version; draft never appears publicly.

---

## 11. Copy

- "Publish program" (CTA).
- "Save draft".
- "This program is missing required fields. Resolve to publish."
- "Someone else edited this. Reload to see their changes?"

---

## 12. Open questions

- **Per-school inheritance.** Some fields (test policy, accreditation) defaulting from the school level. Implement as inherited-default UX with per-program override.
- **Localization.** Multi-language descriptions for international student audiences. Defer.
- **Versioning vs snapshots.** Submitted applications snapshot the requirements at submit time; the editor shows "X applications use the current version; Y use prior versions" so the institution understands the blast radius.

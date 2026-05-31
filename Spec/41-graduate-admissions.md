# 41 · Graduate & PhD Admissions

> The graduate-specific admissions layer: faculty-advisor matching, research-interest alignment, funding-package building (TA / RA / fellowship), and department-level review. Graduate admissions is faculty-driven and funding-centric in ways undergraduate isn't — this doc adds that depth on top of the shared pipeline (`31`, `32`, `34`).
>
> Status: **draft v1.0 · Phase-2** · 2026-05-29 · Routes: `/i/admissions?tab=graduate`, department portal `/i/departments/:deptId`, per-applicant `/i/pipeline/:studentId?tab=advisor-match`. Scope: program-type-specific depth, beyond the launch beachhead (`07` §3); sequenced after MVP.

---

## 1. Purpose

Graduate admissions differs structurally from undergrad:
- **Faculty decide**, not (only) a central office — departments run their own review.
- **Funding is the offer** — a TA/RA/fellowship package often matters more than admission itself.
- **Research fit** is the core signal — advisor↔applicant alignment, not just GPA/scores.

This module layers those onto the shared admissions pipeline without forking it.

---

## 2. Sub-modules

### 2.1 Faculty-advisor matching
- Applicants state research interests + target advisors (`42` §3.12 intent + a grad-specific extension).
- Faculty profiles: research areas, current openings, funding availability, accepting-students flag.
- **Match surface**: for each applicant, ranked advisor-fit (research-interest similarity via embeddings — uses the same vector infra as program matching, `06` §4). Faculty see applicants who fit them; applicants see advisors who fit them.
- Mutual-interest flags (applicant named advisor AND advisor flagged interest) surface to the department.

### 2.2 Research-interest alignment
- Structured research-interest taxonomy + free-text statement of purpose parsed (`45` extraction) into interest tags.
- Alignment score per (applicant, advisor) and (applicant, lab/department).
- Feeds the review packet (`32`) as a grad-specific signal — context, not auto-decision (`46`).

### 2.3 Funding-package builder
- Build an offer combining: TA (teaching assistantship), RA (research assistantship), fellowship, tuition waiver, stipend.
- Per-source budget tracking (department/grant/fellowship pools) so packages don't over-commit funds.
- Package becomes part of the offer (`34` offer terms extended); student sees it in their offer view (`18`) + explainer.
- Multi-year package modeling (year-1 fellowship → year-2+ RA, etc.).

### 2.4 Department review portal
- Departments run their own review workspace (a scoped `32`): their applicants, their rubric, their committee.
- Department recommends → central office confirms/releases (`34`) — two-stage, role-gated.
- Department dashboards: applicant pool, funding committed vs budget, yield.

---

## 3. Flow

```
Applicant (research interests + target advisors, funding need)
   → Advisor matching surfaces fit (both directions)
   → Department review (scoped 31) with research-alignment signal
   → Faculty/committee recommend + propose funding package
   → Central office confirms → offer released (33) with funding package
   → Student sees admission + funding (1A) → confirms (33b)
```

---

## 4. Data shape

```ts
type FacultyProfile = {
  id: string; name: string; department_id: string;
  research_areas: string[]; accepting_students: boolean;
  openings: number; funding_available: boolean;
};

type AdvisorMatch = {
  application_id: string; advisor_id: string;
  alignment_score: number;            // 0-100, research-interest similarity
  applicant_named_advisor: boolean; advisor_flagged_interest: boolean;
  mutual: boolean;
};

type FundingPackage = {
  application_id: string;
  components: Array<{ kind: 'TA'|'RA'|'fellowship'|'tuition_waiver'|'stipend'; amount: number; source_pool_id: string; years: number[] }>;
  total_value: number; currency: string;
  multi_year: boolean;
};
```
Endpoints: `GET /i/graduate/advisor-matches?application_id=…`, `GET/PATCH /i/faculty/:id`, `POST /i/applications/:id/funding-package`, `GET /i/departments/:id/review`, `GET /i/departments/:id/funding-budget`.

---

## 5. AI integration

| Agent | Trigger | Output |
|---|---|---|
| `AdvisorMatcher` | Application received | Ranked advisor-fit from research-interest embeddings |
| `SoPInterestExtractor` (extends `45`) | Statement of purpose uploaded | Research-interest tags + alignment summary |
| `FundingScenarioHelper` | Building a package | Flags over-commit vs pool budget; suggests viable mixes |

Fall back to manual. Matching informs humans; faculty decide.

---

## 6. States

- **Undergrad program:** module hidden (program `degree_type` gates it).
- **No advisor named:** match surface still ranks by research fit.
- **Funding pool exhausted:** package builder blocks over-commit + warns.
- **Department recommended, central pending:** two-stage badge.

---

## 7. Brand compliance

- Funding package presented to the student as a clear, hopeful package (the one place grad applicants feel the offer's weight — restrained gold permitted on the student's funded-offer moment, `18`/`02` §15).
- Institution side operational; no gold.

---

## 8. Gaps / dependencies

- Extends `32` (scoped review), `34` (offer terms + funding), `35` (yield), `42` §3.12 (intent), `06` §4 (vector infra), `45` (extraction).
- Requires program `degree_type` to gate grad-only features.
- Faculty as a new user sub-role (lighter than `institution_admin`) — extends `05` role model; Phase-2 auth work.

---

## 9. Tests

- Advisor match ranks by research-interest similarity; mutual-interest flagged.
- Funding package cannot exceed source pool budget.
- Department review is scoped to that department's applicants + rubric.
- Two-stage release: department recommend → central confirm → offer (`34`).
- Grad features hidden for undergrad programs.

---

## 10. Copy

- "Advisors who fit your research" (student) / "Applicants who fit your work" (faculty).
- "Mutual interest ✓".
- "Build funding package" / "Exceeds fellowship pool budget."
- "Recommended by department — awaiting central confirmation."

---

## 11. Open questions

- **Faculty sub-role** scope + permissions — read applicants in their dept, score, recommend, propose funding; not release.
- **Funding pool accounting** integration with institution finance — start self-contained, integrate later.
- **Rotations / lab matching** (sciences) vs direct-admit (humanities) — support both advising models.

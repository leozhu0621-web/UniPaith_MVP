# 15 · Applications — Per-Application Workspace

> Stage 3 — Apply. The student's execution hub. Each saved target becomes an application project with status, program-adaptive checklist, documents, essays, interviews, guardrails, decisions, offer. List + portfolio dashboard at `/s/manage`; per-application detail at `/s/applications/:appId`.
>
> Status: **draft v1.0** · 2026-05-29 · Routes: `/s/manage?tab=applications`, `/s/applications/:appId`.

---

## 1. Purpose

Convert saved targets into actionable application projects. Each application:
- Has a clear status, deadlines, next actions.
- Has a **program-adaptive checklist** — institution defines what's required; UniPaith displays it consistently.
- Tracks materials, essays, interviews, recommendations, scheduling.
- Has a "Ready to submit" gate — enabled only when all required items pass.
- Continues through decisions and offers.

---

## 2. Portfolio dashboard (`/s/manage?tab=applications`)

```
APPLICATIONS
Your portfolio

Counts
  Not started 3 · In progress 8 · Ready to submit 1 · Submitted 4
  · Under review 2 · Decided 1

Next actions
  ★ Submit CS MS — Foo (ready now, deadline in 4 days)
  ★ Confirm recommender for U of Bar (due in 7 days)
  ★ Schedule interview for Y School (slots offered)

[Filter: All ▾]  [Sort: Deadline ▾]

APPLICATIONS LIST

┌─────────────────────────────────────────────────────────────────────┐
│ Computer Science MS · University of Foo                              │
│ Status: In progress (78%) · Deadline: Jan 15                         │
│ Next: Submit essay supplement                                        │
│ [Open application →]                                                 │
└─────────────────────────────────────────────────────────────────────┘
... rows
```

Filters: status, deadline window, priority, institution.
Sort: deadline (default), readiness %, priority.

---

## 3. Per-application workspace (`/s/applications/:appId`)

```
Match · CS MS · University of Foo

[ Draft  ─  Submitted  ─  Under Review  ─  Interview  ─  Decision ]
   ●

[Checklist 78%] [Documents] [Essays] [Recommenders] [Interviews] [Guardrails] [Offer]

SIDEBAR (left)                  MAIN (right)
  Checklist                       (tab content)
  ●─ Personal complete
  ●─ Academics complete
  ◯─ Essay (you)
  ◯─ Recommender 2 (Dr Lee)
  ◯─ Interview prep

  [Check readiness]               [Submit application] (disabled until 100%)
  [Submit application]
```

---

## 4. Status timeline

5 stages per application:
1. **Draft** — student building materials.
2. **Submitted** — student submitted; institution received.
3. **Under review** — institution actively reviewing.
4. **Interview** — interview scheduled (if applicable).
5. **Decision made** — accepted / rejected / waitlisted.

Visual: horizontal progress bar with stage labels; current stage highlighted.

---

## 5. Program-adaptive checklist

The single most important spec element. The institution publishes a `requirement_checklist` per program (per `23-program-detail-page-institution.md`). UniPaith renders it consistently:

For each item:
- Type: form / essay / short answer / resume / portfolio / writing sample / recommendation / transcript / document upload / test / fee / interview / assessment.
- Required / optional / N/A.
- Format expected (upload type, word limit, link submission, count of recommenders).
- Owner: student / recommender / institution / system.
- Status: not started / in progress / complete / blocked.

The system flags mismatches early:
- Missing required items.
- Wrong document type.
- Insufficient recommender count.
- Incomplete interview step.

**"Ready to submit" gate enables only when all required items pass.** Per the Adaptive Intake Engine apply-ready check (`44-adaptive-intake-engine.md` §4.2).

---

## 6. Sub-tabs in the workspace

### 6.1 Documents
Drag-drop S3 upload (already wired). Per file: type, name, replace, delete, verification status.

### 6.2 Essays
Per-application essay list. CRUD. Each essay → "Get feedback" routes to Workshops (`14`) program-specific mode.

### 6.3 Recommenders
List of recommenders required for this program. Per recommender: status (requested / in_progress / submitted / overdue), nudge action, replace action.

### 6.4 Interviews
Per-application interview list (filtered from the global interviews). Type, status, scheduled time, prep checklist.

### 6.5 Guardrails (CURRENTLY UNWIRED — `47` G-S4)
- "Why are you applying?" intent picker (`career_fit` / `back_up` / `dream` / `cultural_fit` / `family_input` / `other`).
- Rationale capture (≥ 80 chars when intent is `back_up` or `other`).
- Low-fit warning when fitness ≤ 30.
- Scan endpoint returns `{fit_band, recommended_action, blockers}`.

### 6.6 Offer (after decision)
Accept / decline. Deadlines visible. Offer terms summary via `OutcomeBriefForOfferLetter` agent (`45` §15).

---

## 7. External vs internal submission

**Internal** — student submits through UniPaith. Platform enforces program-specific requirements during completeness check + final review.

**External** — student tracks the application in UniPaith but submits on the institution's own portal. Per-checklist items can be marked complete by the student; confirmation evidence (screenshot, email) can be attached.

Per-application `submission_mode` field.

---

## 8. Guardrails against mass / random applications

- Priority must be set (Reach / Target / Safer) per saved list (`13`).
- Rationale notes required when total saved exceeds a threshold (default: 12).
- Warning on extremely low-fit applications (fitness ≤ 30) to redirect effort.
- Optional intent capture per application.

---

## 9. Data shape

```ts
type Application = {
  id: string;
  student_id: string;
  program_id: string;
  program: ProgramCard;
  status: 'draft' | 'submitted' | 'under_review' | 'interview' | 'decided';
  decision: 'pending' | 'accepted' | 'rejected' | 'waitlisted' | null;
  submission_mode: 'internal' | 'external';
  submitted_at: ISO8601 | null;
  deadline: ISO8601 | null;
  readiness_pct: number;                   // 0-100
  checklist: ApplicationChecklistItem[];
  documents: DocumentRef[];
  essays: Essay[];
  recommenders: Recommender[];
  interviews: Interview[];
  guardrails: {
    intent: 'career_fit' | 'back_up' | 'dream' | 'cultural_fit' | 'family_input' | 'other' | null;
    rationale: string | null;
    fit_band: 'low' | 'medium' | 'high';
    blockers: string[];
  };
  offer: Offer | null;
};
```

Endpoints:
- `GET /me/applications` — list.
- `POST /me/applications` — create (from saved).
- `GET /me/applications/:id`.
- `PATCH /me/applications/:id` — partial.
- `POST /me/applications/:id/submit` — gated on readiness 100%.
- `POST /me/applications/:id/guardrail-scan` — returns fit_band + blockers.
- `POST /me/applications/:id/check-readiness` — re-evaluates per Adaptive Intake.

---

## 10. States

- **No applications:** "No applications yet. Start one from your Saved list or Match." → CTA.
- **Loading:** skeleton list.
- **Submit attempted when readiness < 100%:** modal shows the missing blockers; can't submit until clear.
- **Submit success:** confirmation modal with summary; status flips to Submitted.
- **Decision received:** banner + push notification.

---

## 11. AI integration

| Agent | Trigger | Purpose |
|---|---|---|
| `WorkshopCoach (Essay)` | Get feedback button | Essay feedback |
| `WorkshopCoach (Interview)` | Interview prep button | Practice questions / score response |
| (New) `OutcomeBriefForOfferLetter` (`45` §15) | On offer received | Plain-language brief |
| Rule-based + (future) `GuardrailScorer` | Guardrail scan | Fit-band + blockers |

---

## 12. Brand compliance

- Status timeline bar uses `--text-mut` for inactive segments, `--accent` for current, `--success` for completed.
- Submit button uses `--secondary` cobalt; disabled state per `02` §2.
- Sidebar checklist bullets: ● completed (`--success`), ◯ pending (`--text-mut`), ⚠ blocked (`--warning`).
- "Mark as ready to submit" toggle in `--primary` gold (the one accent on this page — earned, since it's THE moment).

---

## 13. Gaps (from `47`)

- G-S4 (major): Guardrails tab UI exists but `setGuardrailResult` is voided; no scan endpoint.
- Intent + rationale persistence missing.

---

## 14. Tests

- Create application from saved → expected fields populated.
- Submit blocked when readiness < 100%; allowed when 100%.
- External submission: marks the platform side without invoking institution-receive.
- Guardrail scan returns expected band for low-fit fixture.
- Offer response (accept / decline) updates state.

---

## 15. Copy

- "Your portfolio" (H1).
- "Status: In progress (X%)".
- "Next: <action>".
- "Mark as ready to submit" (the gate toggle).
- "Submit application" (final CTA).
- "Submit blocked. Resolve these items first:" (modal title).
- "Showing rule-based result" (fallback).

---

## 16. Open questions

- **External-portal deep-linking.** Some institutions expose direct deep-links per applicant (e.g., Common App, school portals); auto-fill where possible.
- **Submission receipts.** External: PDF screenshot upload. Internal: server-issued receipt with hash.
- **Application versioning.** If institution changes requirements mid-cycle, existing applications keep their original checklist; new applications get the new one. Document policy.

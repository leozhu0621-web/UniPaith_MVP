# 33b · Enrollment Confirmation & Yield

> The tail of the journey (architecture flow Stage 8 — "Enrollment Window / Enrollment Confirmed" student-side; "Enrollment Confirm / Yield Analytics" institution-side). After a student accepts an offer (`1A`/`33`), this is where intent is confirmed, deposits are recorded, waitlist movement is managed, and yield is measured. Closes the loop the architecture diagram ends on.
>
> Status: **draft v1.0** · 2026-05-29 · Routes: student `/s/applications/:appId?tab=enrollment`; institution `/i/admissions?tab=yield` + per-applicant `/i/pipeline/:studentId?tab=enrollment`. Splits out of `33` per its §12; closes `92` `33b` placeholder.
>
> **Scope boundary:** this doc covers enrollment *confirmation, intent, waitlist, and yield analytics*. The **payment gateway** (real deposit collection, refunds) is deferred to `37-fees-payments.md` (Phase-2). MVP records deposit *status* (paid/waived/pending) set manually or via a future gateway webhook — it does not process money.

---

## 1. Purpose

An accepted offer is not an enrollment. This stage converts "accepted" into "confirmed/enrolled," gives the student a clear pre-arrival path, and gives the institution real-time yield visibility and levers (waitlist movement, nudges).

State machine (per offer):
```
accepted → intent_confirmed → deposit_recorded → enrollment_confirmed → enrolled
                     ↘ withdrew (any point before enrolled)
waitlisted → offered (waitlist movement) → accepted → …
```

---

## 2. Student side — Enrollment window

Appears on the application workspace (`17`) once an offer is `accepted`.

### 2.1 Enrollment checklist
A program-defined post-accept checklist (mirrors the pre-submit checklist pattern in `17`):
- Confirm intent to enroll (single explicit action).
- Pay / mark enrollment deposit (status only in MVP; gateway in `37`).
- Submit final/official transcript.
- Health/immunization forms (if required, `40` §3.2).
- Housing intent form (if offered).
- Visa next steps (if `visa_required_flag`, links to the student's visa readiness from `40` §4.3 — student-facing only).
- Orientation registration.

Each item: status + due date + "what happens if I miss this." Overdue items escalate in Calendar (`18`) + Inbox (`19`).

### 2.2 Confirm / decline / defer
- **Confirm enrollment** — sets `intent_confirmed`; celebratory moment (the one place gold is fully earned, `02` §15).
- **Decline after accepting** (changed mind) — confirmation + reason capture; frees the seat (feeds institution yield + waitlist).
- **Request deferral** — to a later start term (institution policy-gated; routes to institution as a request).

### 2.3 Multiple offers
If the student holds multiple accepted offers (`1A` compare), confirming enrollment at one prompts: "You have 2 other active offers. Decline them?" — never auto-declines; the student chooses.

---

## 3. Institution side — Enrollment tracking

### 3.1 Per-applicant
On the review packet (`31`)/pipeline (`30`), an Enrollment tab shows the offer's enrollment state, deposit status, checklist completion, and a timeline. Staff can:
- Record deposit status (paid/waived/pending) — manual in MVP.
- Mark enrollment confirmed.
- Approve a deferral request.
- Send a reason-coded nudge (`27`).

### 3.2 Intent & deposit forms
Institution defines the enrollment-intent form + deposit amount/waiver rules per program/intake (`21`). Student responses land on the per-applicant Enrollment tab.

### 3.3 Waitlist movement
- Waitlist is ranked (`33` §2 `waitlisted` with rank).
- When a seat frees (a decline/withdraw), the dashboard surfaces "N seats open, M on waitlist."
- "Offer to next" → promotes the top-ranked waitlisted applicant → generates an offer (`33` §6, optional human approval) → student notified.
- Bulk waitlist release supported (audit-logged).

---

## 4. Yield analytics (institution)

A dashboard view (`/i/admissions?tab=yield`) — the analytical end the architecture diagram terminates on. Mirrors/extends `26` patterns.

Metrics:
- **Yield rate** = enrolled / admitted, overall + by program/intake/segment.
- **Funnel tail:** admitted → intent_confirmed → deposit → enrolled, with drop-off at each step.
- **Time-to-confirm** distribution.
- **Melt** = confirmed-but-not-enrolled (the "summer melt" competitors benchmark; `06` §7).
- **Waitlist conversion** rate.
- **Yield by cohort dimensions** — routed through the fairness lens (`43` §6): yield disparities across protected groups surface here and feed the bias dashboard. (Yield optimization must never become disparate selection.)
- **Predicted final class size** vs target (with `apply_propensity`/`yield_probability` from `40` §4.15 / `4.12`).

Next-best-action: "12 admits haven't confirmed and the deadline is in 5 days → send nudge" (one-click → bulk message `27`).

---

## 5. Data shape

```ts
type Enrollment = {
  application_id: string;
  offer_id: string;
  state: 'accepted' | 'intent_confirmed' | 'deposit_recorded' |
         'enrollment_confirmed' | 'enrolled' | 'withdrew' | 'deferred';
  deposit_status: 'none' | 'pending' | 'paid' | 'waived';   // status only in MVP
  deposit_amount: number | null;
  intent_confirmed_at: ISO8601 | null;
  enrollment_confirmed_at: ISO8601 | null;
  deferral: { requested: boolean; to_term: TermRef | null; approved: boolean } | null;
  checklist: Array<{ item: string; status: 'pending'|'complete'|'overdue'|'waived'; due: ISO8601|null }>;
};

type YieldSnapshot = {
  scope: { program_id?: string; intake_id?: string; segment_id?: string };
  admitted: number; intent_confirmed: number; deposited: number; enrolled: number;
  yield_rate: number; melt_rate: number; waitlist_conversion: number;
  predicted_final_class_size: number; target_class_size: number;
};
```

Endpoints:
- Student: `GET /me/applications/:id/enrollment`, `POST …/enrollment/confirm`, `POST …/enrollment/decline`, `POST …/enrollment/defer`.
- Institution: `GET /i/applications/:id/enrollment`, `POST …/enrollment/record-deposit`, `POST …/enrollment/confirm`, `POST …/enrollment/approve-deferral`.
- Waitlist: `GET /i/waitlist?program_id=…`, `POST /i/waitlist/offer-next`, `POST /i/waitlist/bulk-offer`.
- Yield: `GET /i/yield?scope=…`.

---

## 6. AI integration

| Agent | Trigger | Output |
|---|---|---|
| `YieldRiskScorer` (uses `40` §4.15 `apply_propensity`/yield signals) | Dashboard load | Per-admit confirm-probability + at-risk list |
| `NextBestActionForYield` | Dashboard | Ranked actions ("nudge these 12", "release N waitlist") |
| `EnrollmentNudgeDrafter` (reuses `27` `InstitutionReplyDrafter`) | Send nudge | Drafts the confirm-reminder message |

Fairness gate: yield models surface disparities (`43` §6) but never drive selection. Falls back to simple counts on agent failure.

---

## 7. States

- **Student, no offer accepted:** Enrollment tab hidden until an offer is `accepted`.
- **Student, confirmed:** celebratory confirmation card + pre-arrival checklist + "what's next."
- **Institution, pre-decisions:** Yield tab shows "Yield tracking begins once you release decisions."
- **Waitlist empty / full:** appropriate empty/at-capacity messaging.
- **Deferral pending:** badge on both ends.

---

## 8. Brand compliance

- The student **Confirm enrollment** moment is the single biggest celebratory beat in the product — gold glow (`01` §11 `--shadow-glow`), per `02` §15. Earned here.
- Institution yield dashboard: restrained, data-forward, **no gold** (operational); charts use the `26` palette.
- Fairness/disparity callouts use `--warning`, never alarm-red unless threshold breached (`43`).

---

## 9. Gaps (relative to current code)

- Enrollment state machine + tables NEW (extends the offer model in `33`).
- Yield dashboard NEW (reuses `26` chart infra).
- Waitlist ranking + movement NEW.
- Deposit is **status-only** in MVP — real payment is `37` (Phase-2). Mark clearly in UI ("deposit recorded by institution" vs "pay now").
- `YieldRiskScorer`/`NextBestActionForYield` agents NEW in `42`.

---

## 10. Tests

- Accept offer → Enrollment tab appears with program checklist.
- Confirm enrollment → state `intent_confirmed`; institution yield count increments; celebratory UI shown.
- Decline-after-accept → seat freed; appears in waitlist "seats open."
- Offer-to-next-waitlisted → top-ranked promoted, offer generated, student notified, audit-logged.
- Yield rate + melt + funnel-tail compute correctly on fixtures.
- Yield disparity by cohort routes to fairness dashboard (`43`).
- Deposit status changes are status-only (no money moved) and audit-logged.

---

## 11. Copy

- "Confirm your enrollment" / "You're in! Let's get you ready." (post-confirm)
- "You have other active offers. Decline them?" (multi-offer)
- "Request a deferral" / "Deferral requested — pending the school's approval."
- Institution: "12 admits haven't confirmed — deadline in 5 days." / "Offer to next on waitlist."
- "Deposit recorded" (MVP) vs future "Pay deposit".

---

## 12. Open questions

- **Deposit gateway timing.** MVP records status; when does `37-fees-payments.md` (Stripe/ACH) land? Tie to first institution that requires real collection.
- **Melt intervention.** Automated summer-melt nudges (the Mainstay-style win, `06` §7) — MVP manual nudges; automated cadence Phase-2.
- **SIS handoff.** Enrolled students eventually flow to the institution's SIS (Banner/Workday). Export format + webhook — integration scope, note in `05` §4.
- **Deferral term limits.** Per-institution policy on how far a deferral can push — capture in `21` program config.

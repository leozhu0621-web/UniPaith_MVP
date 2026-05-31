# 34 · Decisions & Offers (Institution-Side)

> Where institutions release decisions and offers, with terms (scholarship / conditions / response deadline). Mirrors the student-side `18-decisions-offers.md`.
>
> Status: **draft v1.0** · 2026-05-29 · Routes: per-applicant at `/i/pipeline/:studentId?tab=decision`, batch release from `/i/admissions?tab=pipeline`.

---

## 1. Purpose

Issue decisions at scale; capture offer terms; release to students; manage yield.

---

## 2. Decision types

- `accepted` — full admission.
- `rejected` — denied.
- `waitlisted` — on waitlist with rank.
- `deferred` — moved to later round.
- `conditional_admission` — accepted with conditions (prerequisites, etc.).

---

## 3. Per-decision flow

1. Reviewer/committee finalizes recommendation in `32-review-workspace.md`.
2. Admissions director releases (single or batch).
3. Offer record created (for `accepted` / `conditional_admission` / `waitlist_to_admit`).
4. Student notified (Inbox + email + push).
5. Student responds (accept / decline / negotiate); response captured.

---

## 4. Offer creation

```ts
type Offer = {
  application_id: string;
  decision_date: ISO8601;
  offer_type: 'full_admission' | 'conditional' | 'partial' | 'transfer_credit_offer' | 'waitlist_to_admit';
  conditions: string | null;
  scholarship_amount: number | null;
  scholarship_currency: string;
  tuition_estimate: number | null;
  total_cost_estimate: number | null;
  start_term: { season: string; year: number };
  response_deadline: ISO8601;
  next_step_actions: Array<{ action: string; by_date: ISO8601 }>;
  attached_letter: file_ref | null;
};
```

Templates per institution define standard offer letters; variable substitution (`{{student_name}}`, `{{scholarship_amount}}`, `{{deadline}}`).

---

## 5. Batch decision release

From the Pipeline page, select multiple Decision-stage applicants → "Release decisions" → modal:
- Confirm decision per applicant.
- Apply standard offer template (or per-applicant override).
- Schedule release date.
- Audit-logged batch action.

---

## 6. Yield management

After release:
- Track per-applicant response state.
- Surface "no response after X days" yield-risk alert on dashboard (per `31` §2).
- Trigger nudge follow-ups per institution's policy.

---

## 7. Data shape

Endpoints:
- `POST /i/applications/:id/decision` — body: `{decision, offer?}`.
- `POST /i/applications/batch-release-decision` — body: `{application_ids, decisions[], offer_template_id?}`.
- `GET /i/applications/:id/offer-status` — current student response state.
- `POST /i/offers/:id/extend-deadline`.

---

## 8. States

- **Single decision release:** confirmation modal lists the offer terms + sends.
- **Batch release in progress:** progress bar.
- **Student responded:** badge + timeline entry.
- **Deadline passed:** auto-rescind option (per institution policy).

---

## 9. AI integration

| Agent | Trigger | Purpose |
|---|---|---|
| `OutcomeBriefForOfferLetter` (`45` §15) | Generate offer | Plain-language brief that lands in student's offer view |
| AI draft for decision notice | Send notification | Drafts message body |

---

## 10. Brand compliance

- "Release decisions" button cobalt.
- Accept-rate KPI on dashboard.
- Decision badges color-coded but RESTRAINED (no celebratory gold on the institution side — students see the celebration).

---

## 11. Gaps (from `47`)

- Offer-letter template management exists (Templates page); batch release uses templates.

---

## 12. Tests

- Single decision release → student Inbox + email + Calendar updated.
- Batch release → audit-logged per application.
- Offer response flow updates institution-side state.
- Yield-risk alerts fire on threshold.

---

## 13. Copy

- "Release decisions" / "Confirm release" / "Cancel".
- "Awaiting response" / "Accepted" / "Declined" (per applicant).
- "Deadline passed" badge.

---

## 14. Open questions

- **Negotiation flow.** Student-initiated scholarship negotiation — supported? Defer; route through Inbox.
- **Waitlist movement.** When waitlist moves to admit, generate offer automatically? Yes, with optional human approval per institution policy.
- **Decision-letter formatting.** Institution branding on the letter — defer; MVP uses platform standard.

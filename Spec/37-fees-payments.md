# 37 · Fees & Payments

> The money layer: application-fee collection, fee-waiver workflow, enrollment-deposit collection, and refunds. The real payment gateway behind the status-only stubs in `17` §2A (application cost tracker) and `33b` (deposit status). Until this ships, those surfaces record status without moving money.
>
> Status: **draft v1.0 · Phase-2** · 2026-05-29 · Routes: student inline at `/s/applications/:appId` (pay fee) + `/s/applications/:appId?tab=enrollment` (pay deposit); institution `/i/settings?tab=billing` (fee config) + `/i/admissions` (waiver queue). Scope: ships when the first institution requires real collection (`33b` §12).

---

## 1. Purpose

Two distinct money flows:
1. **Application fees** — a student pays a per-application fee (or gets it waived) to submit.
2. **Enrollment deposits** — an admitted student pays a deposit to confirm enrollment (`33b`).

Plus the platform's own student subscription billing (`06` §4.1) and institution usage billing (`06` §4.2) — those are covered in `1D` §2.7 / §3.6; this doc is the **applicant-facing transactional** layer.

---

## 2. Application fees

### 2.1 Configuration (institution)
Per program/intake (`21`): fee amount + currency, or "no fee." Fee-waiver policy: auto-eligible rules (income band, fee-waiver code, first-gen, SRAR/NACAC waiver) + manual-request path.

### 2.2 Student flow
- At submit (`17`), if the program has a fee: a pay step (or "request waiver").
- **Pay** → gateway checkout (Stripe) → on success, `fee_paid=true`, submission proceeds.
- **Request waiver** → choose basis → routes to the institution waiver queue; submission can proceed in `pending_waiver` state per institution policy (block-until-approved vs allow-and-reconcile).
- Receipt + history in the application cost tracker (`17` §2A).

### 2.3 Waiver queue (institution)
- Pending waiver requests with basis + supporting evidence.
- Approve / deny / request-more-info. Audit-logged (`34`).
- Auto-approve rules optional (e.g., verified fee-waiver code).

---

## 3. Enrollment deposits

- Configured per program/intake (`21`): deposit amount, deadline, refundability rules.
- Student pays from the enrollment window (`33b` §2.1) → `deposit_status=paid`, enrollment state advances.
- Waiver/deferral of deposit per institution policy.
- Deposit feeds yield (`33b` §4).

---

## 4. Payments infrastructure

- **Gateway:** Stripe (cards) + ACH for larger deposits; provider abstracted behind a `PaymentProvider` interface (mirrors the model-portability pattern in `03` — swap providers, not call sites).
- **PCI:** never store raw card data; use the gateway's tokenized elements. Only store provider charge IDs + status.
- **Money movement:** platform processes on behalf of the institution (Stripe Connect — funds route to the institution's connected account, platform takes its fee per `06` §4.2).
- **Idempotency:** every charge keyed by `(application_id, fee_type)` to prevent double-charge on retry.
- **Webhooks:** gateway webhook updates `fee_paid` / `deposit_status` (the status fields `17`/`33b` record manually today).

---

## 5. Refunds

- Refund triggers: duplicate charge, deposit refundable-window withdrawal, institution-initiated goodwill.
- Refund requires institution approval (except auto duplicate-charge reversal); audit-logged.
- Partial refunds supported (deposit minus non-refundable portion).

---

## 6. Data shape

```ts
type Payment = {
  id: string;
  application_id: string;
  kind: 'application_fee' | 'enrollment_deposit';
  amount: number; currency: string;
  status: 'none' | 'pending' | 'paid' | 'waived' | 'refunded' | 'partially_refunded' | 'failed';
  provider: 'stripe'; provider_charge_id: string | null;
  waiver: { requested: boolean; basis: string | null; approved: boolean | null } | null;
  paid_at: ISO8601 | null; refunded_amount: number | null;
};
```
Endpoints: `POST /me/applications/:id/pay` (returns checkout session), `POST /me/applications/:id/request-waiver`, `POST /i/waivers/:id/decide`, `POST /i/payments/:id/refund`, `POST /webhooks/stripe`.

---

## 7. States

- **No fee:** pay step skipped entirely.
- **Payment processing:** "Confirming payment…" then receipt.
- **Payment failed:** retry + alternate method; submission held.
- **Waiver pending:** badge; per policy, submission allowed or blocked.
- **Refund issued:** receipt + history entry.

---

## 8. Brand compliance

- Checkout is calm + trustworthy: no gold pressure, clear amounts, currency explicit.
- Receipts plain + exportable.
- Never dark-pattern a fee over a waiver — the waiver path is equally prominent (equity value, `06` §2).

---

## 9. Gaps / dependencies

- Replaces the status-only stubs in `17` §2A + `33b` (deposit). Those docs explicitly defer real money here.
- Requires Stripe Connect onboarding per institution (KYC).
- Tax/receipt compliance per jurisdiction — legal review.

---

## 10. Tests

- Pay fee → `fee_paid` via webhook → submission proceeds; idempotent on retry (no double charge).
- Request waiver → queue → approve → fee marked `waived`.
- Deposit payment advances enrollment state (`33b`) + increments yield.
- Refund requires approval + audit log; partial refund math correct.
- No raw card data persisted (contract test).

---

## 11. Copy

- "Pay application fee ($75)" / "Request a fee waiver instead".
- "Confirming your payment…" / "Payment received — your application is submitted."
- "Waiver requested — the school will review it."
- "Pay enrollment deposit to confirm your spot."

---

## 12. Open questions

- **Block-until-paid vs allow-and-reconcile** for waivers — institution policy toggle; default allow-and-reconcile for equity.
- **Currency handling** for international fees — charge in institution currency; show student an estimate in theirs.
- **Subscription billing reuse** — does student `$15/mo` (`1D` §2.7) share this provider layer? Yes — same `PaymentProvider`.

# Stripe setup — student subscriptions (Spec 07 §4.1)

Payments default to a **mock provider** — no Stripe account or keys are needed
for dev/test/CI, and the trial → paywall → $15/mo flow is fully demoable. This
guide turns on **real Stripe** so the subscription actually charges a card.

Stripe also backs the fee/deposit checkout + refunds (Spec 39); the same
`payments_provider=stripe` switch turns on both. This doc focuses on the student
subscription.

---

## 1. One-time Stripe account setup

1. Create / open your Stripe account: <https://dashboard.stripe.com>.
2. Copy your API keys (**Developers → API keys**): publishable (`pk_…`, client-safe)
   and secret (`sk_…`, server-only).
3. Create the recurring Prices (idempotent — safe to re-run):

   ```bash
   STRIPE_SECRET_KEY=sk_test_xxx python scripts/setup_stripe_products.py
   ```

   It prints `STRIPE_PRICE_ID` ($15/mo Plus) and `STRIPE_ADFREE_PRICE_ID`
   ($5/mo ad-free). If you leave `STRIPE_PRICE_ID` unset the backend builds an
   inline price from `student_plan_price_usd`, so this step is optional for the
   base plan (but the ad-free add-on needs `STRIPE_ADFREE_PRICE_ID`).

---

## 2. Environment variables

| Var | Value | Notes |
|---|---|---|
| `PAYMENTS_PROVIDER` | `stripe` | Switches off the mock (default `mock`). |
| `STRIPE_SECRET_KEY` | `sk_…` | Server-only. |
| `STRIPE_PUBLISHABLE_KEY` | `pk_…` | Sent to the browser for Stripe Elements. |
| `STRIPE_WEBHOOK_SECRET` | `whsec_…` | From the webhook endpoint (step 3). |
| `STRIPE_PRICE_ID` | `price_…` | $15/mo Plus (optional — inline fallback). |
| `STRIPE_ADFREE_PRICE_ID` | `price_…` | $5/mo ad-free add-on (required for the toggle). |

The frontend reads the publishable key from `GET /students/me/billing`
(`publishable_key` field) — no separate frontend env var.

---

## 3. Webhook endpoint

Stripe owns the async lifecycle (renewals, failed payments, cancellations).
Point a webhook at the existing endpoint:

```
POST  https://api.unipaith.co/api/v1/webhooks/stripe
```

Subscribe to (covers subscriptions **and** fee/deposit checkout):

- `invoice.payment_succeeded`, `invoice.payment_failed`
- `customer.subscription.updated`, `customer.subscription.deleted`
- `checkout.session.completed`, `charge.refunded`

Copy the signing secret (`whsec_…`) into `STRIPE_WEBHOOK_SECRET`. The endpoint is
public; the Stripe signature is the auth (verified server-side).

---

## 4. Local testing

```bash
PAYMENTS_PROVIDER=stripe STRIPE_SECRET_KEY=sk_test_xxx STRIPE_PUBLISHABLE_KEY=pk_test_xxx \
  STRIPE_PRICE_ID=price_xxx STRIPE_ADFREE_PRICE_ID=price_yyy make dev-backend

stripe listen --forward-to localhost:8000/api/v1/webhooks/stripe
# → prints whsec_… ; export as STRIPE_WEBHOOK_SECRET and restart.
```

Test cards: `4242 4242 4242 4242` succeeds; `4000 0000 0000 0002` is declined →
the upgrade returns a 400 with the decline message. In Stripe mode the billing
card swaps its one-click button for **Stripe Elements**, so the PAN never
touches our servers (PCI, Spec 43 §10).

---

## 5. Production (ECS / Secrets Manager)

- Store `STRIPE_SECRET_KEY` + `STRIPE_WEBHOOK_SECRET` in AWS Secrets Manager and
  reference them from the ECS task definition (same pattern as `DB_PASSWORD`).
- `STRIPE_PUBLISHABLE_KEY`, `STRIPE_PRICE_ID`, `STRIPE_ADFREE_PRICE_ID`,
  `PAYMENTS_PROVIDER=stripe` can be plain env vars in `infra/ecs.tf`.
- A "no model training on UniPaith data" / DPA clause with Stripe is required
  per the sub-processor policy (Spec 43 §10).

Until the keys are set, everything keeps running on the mock provider — flipping
the flag is the only change needed to go live.

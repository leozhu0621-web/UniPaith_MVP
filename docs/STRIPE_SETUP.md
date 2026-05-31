# Stripe billing setup (Spec 06 §4)

The billing layer ships with a **mock provider by default** — no Stripe account or
keys needed for dev/test/CI. This guide turns on **real Stripe** payments.

Nothing here runs automatically: it needs *your* Stripe account, keys, and a
public webhook URL. Once these env vars are set, the app routes real cards
through Stripe with zero code changes.

---

## 1. One-time Stripe account setup

1. Create a Stripe account (or use an existing one): <https://dashboard.stripe.com>.
2. Grab your API keys from **Developers → API keys**:
   - **Publishable key** (`pk_test_…` / `pk_live_…`) — client-safe.
   - **Secret key** (`sk_test_…` / `sk_live_…`) — server-only, treat as a password.
3. Create the Product + recurring Prices with the helper (idempotent — safe to re-run):

   ```bash
   cd unipaith-backend && pip install stripe   # if not already installed
   STRIPE_SECRET_KEY=sk_test_xxx python ../scripts/setup_stripe_products.py
   ```

   It prints the `STRIPE_PRICE_ID` ($15/mo Plus) and `STRIPE_ADFREE_PRICE_ID`
   ($5/mo ad-free) to copy into your env. You can also create these by hand in
   **Product catalog** if you prefer.

---

## 2. Environment variables

| Var | Value | Notes |
|---|---|---|
| `BILLING_ENABLED` | `true` | Turns the whole layer on (default `false`). |
| `BILLING_PROVIDER` | `stripe` | Switches off the mock. |
| `BILLING_MOCK_MODE` | `false` | **Must be false** or the mock wins. |
| `STRIPE_SECRET_KEY` | `sk_…` | Server-only secret. |
| `STRIPE_PUBLISHABLE_KEY` | `pk_…` | Sent to the browser for Stripe Elements. |
| `STRIPE_WEBHOOK_SECRET` | `whsec_…` | From the webhook endpoint (step 3). |
| `STRIPE_PRICE_ID` | `price_…` | $15/mo Plus. If empty, an inline price is created from `BILLING_STUDENT_PLAN_PRICE_CENTS`. |
| `STRIPE_ADFREE_PRICE_ID` | `price_…` | $5/mo ad-free add-on (required for the ad-free toggle). |

The frontend reads the publishable key from `GET /students/me/billing` (the
`publishable_key` field) — no separate frontend env var needed.

---

## 3. Webhook endpoint

Stripe owns the async lifecycle (renewals, failed payments, cancellations), so
the app exposes a webhook that reconciles local state:

```
POST  https://api.unipaith.co/api/v1/billing/stripe/webhook
```

In **Developers → Webhooks → Add endpoint**, point it at that URL and subscribe to:

- `customer.subscription.updated`
- `customer.subscription.deleted`
- `invoice.payment_succeeded`
- `invoice.payment_failed`

Copy the **Signing secret** (`whsec_…`) into `STRIPE_WEBHOOK_SECRET`. The
endpoint is public; the Stripe signature is the auth (verified server-side).

---

## 4. Local testing

```bash
# Backend with Stripe enabled (test keys):
BILLING_ENABLED=true BILLING_PROVIDER=stripe BILLING_MOCK_MODE=false \
  STRIPE_SECRET_KEY=sk_test_xxx STRIPE_PUBLISHABLE_KEY=pk_test_xxx \
  STRIPE_PRICE_ID=price_xxx STRIPE_ADFREE_PRICE_ID=price_yyy \
  make dev-backend

# Forward webhooks to localhost (Stripe CLI):
stripe listen --forward-to localhost:8000/api/v1/billing/stripe/webhook
# -> prints a whsec_… ; export it as STRIPE_WEBHOOK_SECRET and restart the backend.
```

Test cards (Stripe test mode): `4242 4242 4242 4242` succeeds;
`4000 0000 0000 0002` is declined → surfaces the 402 paywall path.

The billing page swaps the raw card inputs for **Stripe Elements** automatically
whenever `provider === "stripe"`, so the PAN never touches our servers (PCI).

---

## 5. Production (ECS / Secrets Manager)

- Store `STRIPE_SECRET_KEY` and `STRIPE_WEBHOOK_SECRET` in AWS Secrets Manager and
  reference them from the ECS task definition (same pattern as `DB_PASSWORD`).
- `STRIPE_PUBLISHABLE_KEY`, `STRIPE_PRICE_ID`, `STRIPE_ADFREE_PRICE_ID`,
  `BILLING_ENABLED=true`, `BILLING_PROVIDER=stripe`, `BILLING_MOCK_MODE=false`
  can be plain env vars in `infra/ecs.tf`.
- A "no model training on UniPaith data" / DPA clause with Stripe is required
  per the sub-processor policy (Spec 43 §10).

If anything is half-configured (e.g. `BILLING_PROVIDER=stripe` but no secret
key), the provider raises a clear error rather than silently falling back — so
misconfiguration fails loud, not silent.

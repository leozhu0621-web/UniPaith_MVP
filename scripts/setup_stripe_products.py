"""Create the UniPaith Stripe Product + recurring Prices (Spec 07 §4.1).

Run ONCE against your Stripe account (test or live) to create the recurring
Prices the student subscription uses:
  - Product "UniPaith Plus"
  - $15/mo recurring Price  (lookup_key: unipaith_plus_monthly)
  - $5/mo recurring Price   (lookup_key: unipaith_adfree_monthly  — ad-free add-on)

Then set the printed ids as STRIPE_PRICE_ID / STRIPE_ADFREE_PRICE_ID.

Idempotent: re-runs reuse the existing Prices found by lookup_key. This script
NEVER stores your keys — it reads STRIPE_SECRET_KEY from the environment for the
duration of the call only. (If STRIPE_PRICE_ID is left unset the app falls back
to an inline price_data, so this script is a convenience, not a hard
requirement.)

Usage:
    STRIPE_SECRET_KEY=sk_test_... python scripts/setup_stripe_products.py
"""

from __future__ import annotations

import os
import sys

PLUS_LOOKUP = "unipaith_plus_monthly"
ADFREE_LOOKUP = "unipaith_adfree_monthly"
# Cents, derived from the app's USD config (student_plan_price_usd / addon).
PLUS_CENTS = int(os.environ.get("STUDENT_PLAN_PRICE_USD", "15")) * 100
ADFREE_CENTS = int(os.environ.get("STUDENT_AD_FREE_ADDON_USD", "5")) * 100
CURRENCY = "usd"


def _find_or_create_price(stripe, *, lookup_key, product_id, unit_amount, nickname):
    found = stripe.Price.list(lookup_keys=[lookup_key], active=True, limit=1).data
    if found and found[0].unit_amount == unit_amount:
        print(f"  reuse  {lookup_key} -> {found[0].id} (${unit_amount / 100:.2f}/mo)")
        return found[0].id
    price = stripe.Price.create(
        product=product_id,
        unit_amount=unit_amount,
        currency=CURRENCY,
        recurring={"interval": "month"},
        lookup_key=lookup_key,
        transfer_lookup_key=True,
        nickname=nickname,
    )
    print(f"  create {lookup_key} -> {price.id} (${unit_amount / 100:.2f}/mo)")
    return price.id


def main() -> int:
    secret = os.environ.get("STRIPE_SECRET_KEY")
    if not secret:
        print("ERROR: set STRIPE_SECRET_KEY in the environment.", file=sys.stderr)
        return 2
    try:
        import stripe
    except ImportError:
        print("ERROR: stripe SDK not installed (pip install stripe).", file=sys.stderr)
        return 2

    stripe.api_key = secret
    print(f"Stripe {'LIVE' if secret.startswith('sk_live') else 'TEST'} mode")

    products = stripe.Product.search(query="name:'UniPaith Plus'", limit=1).data
    if products:
        product = products[0]
        print(f"  reuse  product -> {product.id}")
    else:
        product = stripe.Product.create(
            name="UniPaith Plus",
            description="Full matching, workshops, and deadline tools.",
        )
        print(f"  create product -> {product.id}")

    plus = _find_or_create_price(
        stripe,
        lookup_key=PLUS_LOOKUP,
        product_id=product.id,
        unit_amount=PLUS_CENTS,
        nickname="UniPaith Plus monthly",
    )
    adfree = _find_or_create_price(
        stripe,
        lookup_key=ADFREE_LOOKUP,
        product_id=product.id,
        unit_amount=ADFREE_CENTS,
        nickname="UniPaith ad-free monthly",
    )

    print("\nSet these in your environment / Secrets Manager:")
    print(f"  STRIPE_PRICE_ID={plus}")
    print(f"  STRIPE_ADFREE_PRICE_ID={adfree}")
    print("  PAYMENTS_PROVIDER=stripe")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Create the UniPaith Stripe Product + recurring Prices (Spec 06 §4).

Run ONCE against your Stripe account (test or live) to create:
  - Product "UniPaith Plus"
  - $15/mo recurring Price  (lookup_key: unipaith_plus_monthly)
  - $5/mo recurring Price   (lookup_key: unipaith_adfree_monthly  — ad-free add-on)

Then set the printed ids as STRIPE_PRICE_ID / STRIPE_ADFREE_PRICE_ID.

Idempotent: re-runs reuse existing Prices found by lookup_key. This script
NEVER stores your keys — it reads STRIPE_SECRET_KEY from the environment for the
duration of the call only.

Usage:
    STRIPE_SECRET_KEY=sk_test_... python scripts/setup_stripe_products.py

Prices are immutable in Stripe; to change an amount, create a new Price and
update the env var (this script will create a new one if the amount differs).
"""

from __future__ import annotations

import os
import sys

PLUS_LOOKUP = "unipaith_plus_monthly"
ADFREE_LOOKUP = "unipaith_adfree_monthly"
PLUS_CENTS = int(os.environ.get("BILLING_STUDENT_PLAN_PRICE_CENTS", "1500"))
ADFREE_CENTS = int(os.environ.get("BILLING_STUDENT_ADFREE_PRICE_CENTS", "500"))
CURRENCY = os.environ.get("BILLING_CURRENCY", "usd")


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
        transfer_lookup_key=True,  # move the key off any prior price
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
    mode = "LIVE" if secret.startswith("sk_live") else "TEST"
    print(f"Stripe {mode} mode")

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

    plus_price = _find_or_create_price(
        stripe,
        lookup_key=PLUS_LOOKUP,
        product_id=product.id,
        unit_amount=PLUS_CENTS,
        nickname="UniPaith Plus monthly",
    )
    adfree_price = _find_or_create_price(
        stripe,
        lookup_key=ADFREE_LOOKUP,
        product_id=product.id,
        unit_amount=ADFREE_CENTS,
        nickname="UniPaith ad-free monthly",
    )

    print("\nSet these in your environment / Secrets Manager:")
    print(f"  STRIPE_PRICE_ID={plus_price}")
    print(f"  STRIPE_ADFREE_PRICE_ID={adfree_price}")
    print("  BILLING_PROVIDER=stripe")
    print("  BILLING_MOCK_MODE=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

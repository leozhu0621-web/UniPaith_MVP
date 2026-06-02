"""Pure fee/deposit config + view helpers (Spec 39 §2.1, §6, §7).

No service imports — only operates on already-loaded ``Institution`` / ``Program``
/ ``Payment`` objects, so both ``PaymentService`` and ``ApplicationService`` (the
submit gate) can use it without an import cycle.

Effective amounts resolve: program override (``program.cost_data``) →
``institution.payment_config`` → none. Money is in **cents**.
"""

from __future__ import annotations

from typing import Any

WAIVER_POLICIES = ("allow_and_reconcile", "block_until_approved")
# Recognized auto-waiver bases (Spec 39 §2.1). An institution lists a subset in
# ``payment_config.waiver.auto_rules``; a request whose basis matches is
# auto-approved.
WAIVER_BASES = ("fee_waiver_code", "first_gen", "income_band", "nacac_sram", "other")


def _pc(institution: Any) -> dict:
    return getattr(institution, "payment_config", None) or {}


def fee_config(institution: Any) -> dict:
    """Effective application-fee config for an institution."""
    cfg = _pc(institution).get("application_fee") or {}
    amount_cents = int(cfg.get("amount_cents") or 0)
    return {
        "enabled": bool(cfg.get("enabled")) and amount_cents > 0,
        "amount_cents": amount_cents,
        "currency": (cfg.get("currency") or "USD").upper(),
    }


def waiver_config(institution: Any) -> dict:
    w = _pc(institution).get("waiver") or {}
    policy = w.get("policy")
    if policy not in WAIVER_POLICIES:
        policy = "allow_and_reconcile"  # equity default (Spec 39 §12)
    rules = [r for r in (w.get("auto_rules") or []) if r in WAIVER_BASES]
    return {"policy": policy, "auto_rules": rules}


def _program_deposit_cents(program: Any) -> int | None:
    """Program-level deposit override (whole currency units in cost_data → cents).
    Mirrors EnrollmentService._deposit_amount without importing it."""
    cost = getattr(program, "cost_data", None) if program else None
    if isinstance(cost, dict):
        for k in ("enrollment_deposit", "deposit", "deposit_amount"):
            v = cost.get(k)
            if isinstance(v, (int, float)) and v > 0:
                return int(v) * 100
    return None


def deposit_config(institution: Any, program: Any = None) -> dict:
    """Effective enrollment-deposit config. Program override wins over the
    institution default."""
    cfg = _pc(institution).get("enrollment_deposit") or {}
    amount_cents = int(cfg.get("amount_cents") or 0)
    currency = (cfg.get("currency") or "USD").upper()
    enabled = bool(cfg.get("enabled")) and amount_cents > 0

    prog_cents = _program_deposit_cents(program)
    if prog_cents:
        amount_cents = prog_cents
        enabled = True

    return {
        "enabled": enabled and amount_cents > 0,
        "amount_cents": amount_cents,
        "currency": currency,
        "deadline_days": int(cfg.get("deadline_days") or 0),
        "refundable": bool(cfg.get("refundable", False)),
        "non_refundable_cents": int(cfg.get("non_refundable_cents") or 0),
    }


def display_status(payment: Any | None) -> str:
    """Spec 39 §7 display state derived from a Payment row (or None)."""
    if payment is None:
        return "due"
    status = payment.status
    if status in ("paid", "waived", "refunded", "partially_refunded", "failed"):
        return status
    if payment.waiver_requested:
        if payment.waiver_approved is None:
            return "waiver_pending"
        if payment.waiver_approved is False:
            return "waiver_denied"
    if status == "pending":
        return "processing"
    return "due"


def is_fee_clear(payment: Any | None, waiver_policy: str) -> bool:
    """Whether the application fee no longer blocks submission (Spec 39 §2.2/§7)."""
    if payment is None:
        return False
    if payment.status in ("paid", "waived"):
        return True
    # allow-and-reconcile: a *requested* (not denied) waiver lets submission
    # proceed in a pending_waiver state; block-until-approved does not.
    if (
        waiver_policy == "allow_and_reconcile"
        and payment.waiver_requested
        and payment.waiver_approved is not False
    ):
        return True
    return False


def _cents_to_amount(cents: int) -> float:
    return round((cents or 0) / 100, 2)


def fee_view(payment: Any | None, fee_cfg: dict, waiver_cfg: dict) -> dict:
    """The application-fee slice of the cost tracker (Spec 39 §2A/§6/§7)."""
    state = display_status(payment)
    refunded = getattr(payment, "refunded_cents", 0) if payment else 0
    return {
        "kind": "application_fee",
        "required": bool(fee_cfg["enabled"]),
        "status": state,
        "amount": _cents_to_amount(fee_cfg["amount_cents"]),
        "amount_cents": fee_cfg["amount_cents"],
        "currency": fee_cfg["currency"],
        "waiver_policy": waiver_cfg["policy"],
        "auto_rules": waiver_cfg["auto_rules"],
        "waiver": (
            {
                "requested": bool(payment.waiver_requested),
                "basis": payment.waiver_basis,
                "approved": payment.waiver_approved,
                "note": (payment.waiver_evidence or {}).get("decision_note")
                if payment.waiver_evidence
                else None,
            }
            if payment and payment.waiver_requested
            else None
        ),
        "paid_at": payment.paid_at.isoformat() if payment and payment.paid_at else None,
        "refunded_amount": _cents_to_amount(refunded) if refunded else None,
        "payment_id": str(payment.id) if payment else None,
    }


def deposit_view(payment: Any | None, dep_cfg: dict) -> dict:
    state = display_status(payment)
    refunded = getattr(payment, "refunded_cents", 0) if payment else 0
    payable = bool(dep_cfg["enabled"]) and state in ("due", "processing", "waiver_denied")
    return {
        "kind": "enrollment_deposit",
        "required": bool(dep_cfg["enabled"]),
        "payable": payable,
        "status": state,
        "amount": _cents_to_amount(dep_cfg["amount_cents"]),
        "amount_cents": dep_cfg["amount_cents"],
        "currency": dep_cfg["currency"],
        "refundable": dep_cfg["refundable"],
        "paid_at": payment.paid_at.isoformat() if payment and payment.paid_at else None,
        "refunded_amount": _cents_to_amount(refunded) if refunded else None,
        "payment_id": str(payment.id) if payment else None,
    }

"""Payment service (Spec 39 — Fees & Payments).

Owns the applicant-facing transactional layer: application-fee checkout +
fee-waiver workflow, enrollment-deposit checkout, refunds, and the provider
webhook. All money movement goes through the ``PaymentProvider`` seam
(``services/payments/provider.py``); the default mock provider moves no real
money, so the flow is live and demoable without Stripe keys.

Idempotency (Spec 39 §4): one ``Payment`` row per ``(application_id, kind)`` —
``apply_successful_payment`` is a no-op once a row is ``paid``, so a webhook
retry or a double-click never double-charges.

Downstream: a paid deposit advances the Spec 35 enrollment state machine (which
feeds yield); a paid fee clears the submission gate (enforced in
``ApplicationService.submit_application``).
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import settings
from unipaith.core.exceptions import (
    BadRequestException,
    ForbiddenException,
    NotFoundException,
)
from unipaith.models.application import Application
from unipaith.models.institution import Institution, Program
from unipaith.models.payment import Payment
from unipaith.models.user import User
from unipaith.services.application_service import ApplicationService
from unipaith.services.payments import config as fees
from unipaith.services.payments.provider import ProviderEvent, get_payment_provider

logger = logging.getLogger(__name__)


class PaymentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.provider = get_payment_provider()
        self._apps = ApplicationService(db)

    # ── resolution helpers ────────────────────────────────────────────────────

    async def _student_profile_id(self, user: User) -> UUID:
        from unipaith.services.student_service import StudentService

        profile = await StudentService(self.db)._get_student_profile(user.id)
        return profile.id

    async def _institution_for_admin(self, user: User) -> Institution:
        inst = (
            await self.db.execute(select(Institution).where(Institution.admin_user_id == user.id))
        ).scalar_one_or_none()
        if inst is None:
            raise NotFoundException("Institution not found")
        return inst

    async def _ctx(
        self, application_id: UUID
    ) -> tuple[Application, Program | None, Institution | None]:
        """Load application + its program + institution (with institution_name attached)."""
        app = await self.db.get(Application, application_id)
        if app is None:
            raise NotFoundException("Application not found")
        program = await self.db.get(Program, app.program_id)
        institution = await self.db.get(Institution, program.institution_id) if program else None
        if program is not None:
            await self._apps._attach_institution_names([app])
        return app, program, institution

    async def _payment_for(self, application_id: UUID, kind: str) -> Payment | None:
        return (
            await self.db.execute(
                select(Payment).where(
                    Payment.application_id == application_id, Payment.kind == kind
                )
            )
        ).scalar_one_or_none()

    async def _get_or_create_payment(
        self, application_id: UUID, kind: str, *, amount_cents: int, currency: str
    ) -> Payment:
        payment = await self._payment_for(application_id, kind)
        if payment is None:
            payment = Payment(
                application_id=application_id,
                kind=kind,
                amount_cents=amount_cents,
                currency=currency,
                provider=self.provider.name,
                status="none",
            )
            self.db.add(payment)
            await self.db.flush()
        elif payment.status in ("none", "pending", "failed"):
            # Keep the amount/currency/provider fresh from config until settled.
            payment.amount_cents = amount_cents
            payment.currency = currency
            payment.provider = self.provider.name
        return payment

    def _return_urls(self, application_id: UUID, kind: str) -> tuple[str, str]:
        base = settings.payments_app_base_url.rstrip("/")
        if kind == "enrollment_deposit":
            return (
                f"{base}/s/applications/{application_id}?tab=enrollment&paid=deposit",
                f"{base}/s/applications/{application_id}?tab=enrollment&pay=cancelled",
            )
        return (
            f"{base}/s/applications/{application_id}?paid=fee",
            f"{base}/s/applications/{application_id}?pay=cancelled",
        )

    def _checkout_response(self, payment: Payment, session=None) -> dict:
        return {
            "payment_id": str(payment.id),
            "provider": payment.provider,
            "inline": bool(session.inline) if session else (payment.provider == "mock"),
            "checkout_url": session.url if session else None,
            "publishable_key": session.publishable_key if session else None,
            "amount": round(payment.amount_cents / 100, 2),
            "amount_cents": payment.amount_cents,
            "currency": payment.currency,
            "kind": payment.kind,
            "status": payment.status,
        }

    # ── student: checkout ──────────────────────────────────────────────────────

    async def create_fee_checkout(self, user: User, application_id: UUID) -> dict:
        student_id = await self._student_profile_id(user)
        app = await self._apps._get_application_for_student(student_id, application_id)
        _app, program, institution = await self._ctx(app.id)
        if not settings.payments_enabled:
            raise BadRequestException("Payments are not enabled")
        fee = fees.fee_config(institution)
        if not fee["enabled"]:
            raise BadRequestException("No application fee is required for this program")

        payment = await self._get_or_create_payment(
            app.id, "application_fee", amount_cents=fee["amount_cents"], currency=fee["currency"]
        )
        if payment.status in ("paid", "waived"):
            return self._checkout_response(payment)

        success_url, cancel_url = self._return_urls(app.id, "application_fee")
        prog_name = program.program_name if program else "your program"
        connected = (institution.payment_config or {}).get("stripe_connect_account_id")
        session = self.provider.create_checkout_session(
            payment_id=payment.id,
            kind="application_fee",
            amount_cents=payment.amount_cents,
            currency=payment.currency,
            description=f"Application fee — {prog_name}",
            success_url=success_url,
            cancel_url=cancel_url,
            customer_email=user.email,
            connected_account_id=connected,
            metadata={"application_id": str(app.id)},
        )
        payment.status = "pending"
        payment.provider_session_id = session.session_id
        await self.db.flush()
        return self._checkout_response(payment, session)

    async def create_deposit_checkout(self, user: User, application_id: UUID) -> dict:
        student_id = await self._student_profile_id(user)
        app = await self._apps._get_application_for_student(student_id, application_id)
        _app, program, institution = await self._ctx(app.id)
        if not settings.payments_enabled:
            raise BadRequestException("Payments are not enabled")
        dep = fees.deposit_config(institution, program)
        if not dep["enabled"]:
            raise BadRequestException("No enrollment deposit is configured for this program")

        payment = await self._get_or_create_payment(
            app.id, "enrollment_deposit", amount_cents=dep["amount_cents"], currency=dep["currency"]
        )
        if payment.status in ("paid", "waived"):
            return self._checkout_response(payment)

        success_url, cancel_url = self._return_urls(app.id, "enrollment_deposit")
        prog_name = program.program_name if program else "your program"
        connected = (institution.payment_config or {}).get("stripe_connect_account_id")
        session = self.provider.create_checkout_session(
            payment_id=payment.id,
            kind="enrollment_deposit",
            amount_cents=payment.amount_cents,
            currency=payment.currency,
            description=f"Enrollment deposit — {prog_name}",
            success_url=success_url,
            cancel_url=cancel_url,
            customer_email=user.email,
            connected_account_id=connected,
            metadata={"application_id": str(app.id)},
        )
        payment.status = "pending"
        payment.provider_session_id = session.session_id
        await self.db.flush()
        return self._checkout_response(payment, session)

    async def confirm_mock_payment(self, user: User, payment_id: UUID) -> dict:
        """Complete an in-app mock checkout. Mock-only (404 in stripe mode) —
        runs the exact success path a real webhook would."""
        if self.provider.name != "mock":
            raise NotFoundException("Not found")
        student_id = await self._student_profile_id(user)
        payment = await self.db.get(Payment, payment_id)
        if payment is None:
            raise NotFoundException("Payment not found")
        # Ownership check — the payment's application must be the student's.
        await self._apps._get_application_for_student(student_id, payment.application_id)
        if payment.status not in ("paid", "waived"):
            await self.apply_successful_payment(
                payment, charge_id=f"mock_ch_{uuid.uuid4().hex[:20]}", actor_user_id=user.id
            )
        return await self.cost_tracker(user, payment.application_id)

    # ── student: waiver ─────────────────────────────────────────────────────────

    async def request_waiver(
        self, user: User, application_id: UUID, basis: str, evidence: dict | None = None
    ) -> dict:
        student_id = await self._student_profile_id(user)
        app = await self._apps._get_application_for_student(student_id, application_id)
        _app, program, institution = await self._ctx(app.id)
        fee = fees.fee_config(institution)
        if not fee["enabled"]:
            raise BadRequestException("No application fee to waive for this program")
        if basis not in fees.WAIVER_BASES:
            raise BadRequestException(f"Unknown waiver basis '{basis}'")

        payment = await self._get_or_create_payment(
            app.id, "application_fee", amount_cents=fee["amount_cents"], currency=fee["currency"]
        )
        if payment.status in ("paid", "waived"):
            raise BadRequestException("This fee is already settled")

        payment.waiver_requested = True
        payment.waiver_basis = basis
        if evidence:
            payment.waiver_evidence = {**(payment.waiver_evidence or {}), **evidence}

        waiver_cfg = fees.waiver_config(institution)
        auto = basis in waiver_cfg["auto_rules"]
        if auto:
            payment.waiver_approved = True
            payment.status = "waived"
            payment.waiver_decided_at = datetime.now(UTC)
            await self.db.flush()
            await self._audit(
                institution.id if institution else None,
                user.id,
                app,
                "waiver_auto_approved",
                description=f"Fee waiver auto-approved (basis: {basis})",
                reason=basis,
                actor_role="student",
            )
            await self._notify_student(
                app, "Fee waiver approved", "Your application fee was waived. You can submit now."
            )
        else:
            payment.waiver_approved = None  # pending institution review
            await self.db.flush()
            await self._audit(
                institution.id if institution else None,
                user.id,
                app,
                "waiver_requested",
                description=f"Fee waiver requested (basis: {basis})",
                reason=basis,
                actor_role="student",
            )
        return await self.cost_tracker(user, app.id)

    # ── student: cost tracker (Spec 15 §2A / 39 §6) ────────────────────────────

    async def cost_tracker(self, user: User, application_id: UUID) -> dict:
        student_id = await self._student_profile_id(user)
        app = await self._apps._get_application_for_student(student_id, application_id)
        _app, program, institution = await self._ctx(app.id)
        fee_cfg = fees.fee_config(institution)
        waiver_cfg = fees.waiver_config(institution)
        dep_cfg = fees.deposit_config(institution, program)
        fee_payment = await self._payment_for(app.id, "application_fee")
        dep_payment = await self._payment_for(app.id, "enrollment_deposit")
        return {
            "application_id": str(app.id),
            "payments_enabled": settings.payments_enabled,
            "fee": fees.fee_view(fee_payment, fee_cfg, waiver_cfg) if fee_cfg["enabled"] else None,
            "deposit": (fees.deposit_view(dep_payment, dep_cfg) if dep_cfg["enabled"] else None),
        }

    # ── apply success (webhook / mock confirm) ─────────────────────────────────

    async def apply_successful_payment(
        self, payment: Payment, *, charge_id: str | None = None, actor_user_id: UUID | None = None
    ) -> Payment:
        if payment.status == "paid":
            return payment  # idempotent — already applied (Spec 39 §4)
        payment.status = "paid"
        payment.paid_at = datetime.now(UTC)
        if charge_id:
            payment.provider_charge_id = charge_id
        await self.db.flush()

        app, program, institution = await self._ctx(payment.application_id)
        inst_id = institution.id if institution else None

        # Deposit → advance the enrollment state machine (Spec 35 §5 → feeds yield).
        if payment.kind == "enrollment_deposit":
            try:
                from unipaith.services.enrollment_service import EnrollmentService

                await EnrollmentService(self.db).apply_paid_deposit(
                    payment.application_id,
                    deposit_amount_cents=payment.amount_cents,
                    actor_user_id=actor_user_id,
                )
            except Exception as exc:  # noqa: BLE001 — receipt must not 5xx
                logger.warning("deposit→enrollment advance failed app=%s: %s", app.id, exc)

        await self._audit(
            inst_id,
            actor_user_id,
            app,
            "payment_succeeded",
            description=(
                f"{payment.kind} paid ({payment.currency} {payment.amount_cents / 100:.2f})"
            ),
            new_value={"kind": payment.kind, "amount_cents": payment.amount_cents},
        )
        label = "application fee" if payment.kind == "application_fee" else "enrollment deposit"
        await self._notify_student(
            app,
            "Payment received",
            f"Your {label} of {payment.currency} ${payment.amount_cents / 100:,.2f} was received. "
            + (
                "Your application is submitted."
                if payment.kind == "application_fee" and app.status != "draft"
                else "Thank you."
            ),
        )
        return payment

    async def handle_provider_event(self, event: ProviderEvent) -> None:
        """Webhook entry point (Spec 39 §4). Idempotent on retried events."""
        if event.type == "checkout.session.completed":
            payment = await self._payment_from_event(event)
            if payment is not None and payment.status != "paid":
                await self.apply_successful_payment(payment, charge_id=event.charge_id)
        elif event.type == "charge.refunded":
            payment = (
                await self.db.execute(
                    select(Payment).where(Payment.provider_charge_id == event.charge_id)
                )
            ).scalar_one_or_none()
            if payment is not None and event.amount_cents is not None:
                payment.refunded_cents = max(payment.refunded_cents, int(event.amount_cents))
                payment.status = (
                    "refunded"
                    if payment.refunded_cents >= payment.amount_cents
                    else "partially_refunded"
                )
                await self.db.flush()

    async def _payment_from_event(self, event: ProviderEvent) -> Payment | None:
        pid = (event.metadata or {}).get("payment_id")
        if pid:
            try:
                payment = await self.db.get(Payment, UUID(str(pid)))
                if payment is not None:
                    return payment
            except (ValueError, TypeError):
                pass
        if event.session_id:
            return (
                await self.db.execute(
                    select(Payment).where(Payment.provider_session_id == event.session_id)
                )
            ).scalar_one_or_none()
        return None

    # ── institution: fee config ────────────────────────────────────────────────

    async def get_fee_config(self, user: User) -> dict:
        inst = await self._institution_for_admin(user)
        cfg = inst.payment_config or {}
        dep = fees.deposit_config(inst)
        deposit_keys = (
            "enabled",
            "amount_cents",
            "currency",
            "deadline_days",
            "refundable",
            "non_refundable_cents",
        )
        return {
            "application_fee": fees.fee_config(inst),
            "waiver": fees.waiver_config(inst),
            "enrollment_deposit": {k: dep[k] for k in deposit_keys},
            "stripe_connect_account_id": cfg.get("stripe_connect_account_id"),
            "provider": settings.payments_provider,
            "publishable_key": settings.stripe_publishable_key or None,
        }

    async def update_fee_config(self, user: User, payload: dict) -> dict:
        inst = await self._institution_for_admin(user)
        cfg = dict(inst.payment_config or {})

        if "application_fee" in payload and payload["application_fee"] is not None:
            af = payload["application_fee"]
            cfg["application_fee"] = {
                "enabled": bool(af.get("enabled")),
                "amount_cents": max(0, int(af.get("amount_cents") or 0)),
                "currency": (af.get("currency") or "USD").upper()[:3],
            }
        if "waiver" in payload and payload["waiver"] is not None:
            w = payload["waiver"]
            policy = w.get("policy")
            cfg["waiver"] = {
                "policy": policy if policy in fees.WAIVER_POLICIES else "allow_and_reconcile",
                "auto_rules": [r for r in (w.get("auto_rules") or []) if r in fees.WAIVER_BASES],
            }
        if "enrollment_deposit" in payload and payload["enrollment_deposit"] is not None:
            ed = payload["enrollment_deposit"]
            cfg["enrollment_deposit"] = {
                "enabled": bool(ed.get("enabled")),
                "amount_cents": max(0, int(ed.get("amount_cents") or 0)),
                "currency": (ed.get("currency") or "USD").upper()[:3],
                "deadline_days": max(0, int(ed.get("deadline_days") or 0)),
                "refundable": bool(ed.get("refundable", False)),
                "non_refundable_cents": max(0, int(ed.get("non_refundable_cents") or 0)),
            }
        if "stripe_connect_account_id" in payload:
            cfg["stripe_connect_account_id"] = payload["stripe_connect_account_id"] or None

        inst.payment_config = cfg
        await self.db.flush()
        await self.db.refresh(inst)
        return await self.get_fee_config(user)

    # ── institution: waiver queue ───────────────────────────────────────────────

    async def _institution_payment(
        self, user: User, payment_id: UUID
    ) -> tuple[Payment, Application, Institution]:
        inst = await self._institution_for_admin(user)
        payment = await self.db.get(Payment, payment_id)
        if payment is None:
            raise NotFoundException("Payment not found")
        app = await self.db.get(Application, payment.application_id)
        program = await self.db.get(Program, app.program_id) if app else None
        if program is None or program.institution_id != inst.id:
            raise ForbiddenException("This payment belongs to another institution")
        return payment, app, inst

    async def list_waivers(self, user: User, status: str = "pending") -> list[dict]:
        inst = await self._institution_for_admin(user)
        stmt = (
            select(Payment, Application, Program)
            .join(Application, Payment.application_id == Application.id)
            .join(Program, Application.program_id == Program.id)
            .where(
                Program.institution_id == inst.id,
                Payment.kind == "application_fee",
                Payment.waiver_requested.is_(True),
            )
            .order_by(Payment.created_at.desc())
        )
        rows = (await self.db.execute(stmt)).all()
        apps = [a for _p, a, _pr in rows]
        await self._apps._attach_student_names(apps)
        out: list[dict] = []
        for payment, app, program in rows:
            state = fees.display_status(payment)
            if status == "pending" and state != "waiver_pending":
                continue
            if status == "decided" and payment.waiver_approved is None:
                continue
            out.append(
                {
                    "payment_id": str(payment.id),
                    "application_id": str(app.id),
                    "student_name": getattr(app, "student_name", None),
                    "program_id": str(program.id),
                    "program_name": program.program_name,
                    "basis": payment.waiver_basis,
                    "evidence": payment.waiver_evidence,
                    "status": state,
                    "approved": payment.waiver_approved,
                    "amount": round(payment.amount_cents / 100, 2),
                    "currency": payment.currency,
                    "requested_at": payment.created_at.isoformat() if payment.created_at else None,
                    "decided_at": payment.waiver_decided_at.isoformat()
                    if payment.waiver_decided_at
                    else None,
                }
            )
        return out

    async def decide_waiver(
        self, user: User, payment_id: UUID, decision: str, reason: str | None = None
    ) -> dict:
        if decision not in ("approve", "deny", "request_info"):
            raise BadRequestException("decision must be approve | deny | request_info")
        payment, app, inst = await self._institution_payment(user, payment_id)
        if not payment.waiver_requested:
            raise BadRequestException("No waiver was requested for this payment")
        if payment.status in ("paid", "refunded", "partially_refunded"):
            raise BadRequestException("This fee is already paid")

        now = datetime.now(UTC)
        if reason:
            payment.waiver_evidence = {**(payment.waiver_evidence or {}), "decision_note": reason}

        if decision == "approve":
            payment.waiver_approved = True
            payment.status = "waived"
            payment.waiver_decided_by = user.id
            payment.waiver_decided_at = now
            title, body = (
                "Fee waiver approved",
                "Your application fee was waived. You can submit your application.",
            )
        elif decision == "deny":
            payment.waiver_approved = False
            payment.waiver_decided_by = user.id
            payment.waiver_decided_at = now
            title, body = (
                "Fee waiver decision",
                "Your fee waiver request was not approved. "
                "You can pay the application fee to submit.",
            )
        else:  # request_info
            payment.waiver_approved = None
            title, body = (
                "More information needed",
                "The school needs more information for your fee waiver request."
                + (f" {reason}" if reason else ""),
            )
        await self.db.flush()
        await self._audit(
            inst.id,
            user.id,
            app,
            "waiver_decided",
            description=f"Fee waiver {decision} (basis: {payment.waiver_basis})",
            reason=reason or payment.waiver_basis,
            new_value={"decision": decision},
        )
        await self._notify_student(app, title, body)
        return await self._waiver_row(payment, app)

    async def _waiver_row(self, payment: Payment, app: Application) -> dict:
        return {
            "payment_id": str(payment.id),
            "application_id": str(app.id),
            "basis": payment.waiver_basis,
            "status": fees.display_status(payment),
            "approved": payment.waiver_approved,
        }

    # ── institution: payments list + refunds ────────────────────────────────────

    async def list_payments(self, user: User, kind: str | None = None) -> list[dict]:
        inst = await self._institution_for_admin(user)
        stmt = (
            select(Payment, Application, Program)
            .join(Application, Payment.application_id == Application.id)
            .join(Program, Application.program_id == Program.id)
            .where(Program.institution_id == inst.id)
            .order_by(Payment.created_at.desc())
        )
        if kind:
            stmt = stmt.where(Payment.kind == kind)
        rows = (await self.db.execute(stmt)).all()
        apps = [a for _p, a, _pr in rows]
        await self._apps._attach_student_names(apps)
        out: list[dict] = []
        for payment, app, program in rows:
            out.append(
                {
                    "payment_id": str(payment.id),
                    "application_id": str(app.id),
                    "student_name": getattr(app, "student_name", None),
                    "program_name": program.program_name,
                    "kind": payment.kind,
                    "status": fees.display_status(payment),
                    "amount": round(payment.amount_cents / 100, 2),
                    "amount_cents": payment.amount_cents,
                    "refunded_amount": round(payment.refunded_cents / 100, 2),
                    "currency": payment.currency,
                    "paid_at": payment.paid_at.isoformat() if payment.paid_at else None,
                    "refundable_cents": max(payment.amount_cents - payment.refunded_cents, 0)
                    if payment.status in ("paid", "partially_refunded")
                    else 0,
                }
            )
        return out

    async def refund(
        self,
        user: User,
        payment_id: UUID,
        *,
        amount_cents: int | None = None,
        reason: str | None = None,
    ) -> dict:
        payment, app, inst = await self._institution_payment(user, payment_id)
        if payment.status not in ("paid", "partially_refunded"):
            raise BadRequestException("Only a paid payment can be refunded")
        max_refundable = payment.amount_cents - payment.refunded_cents
        amount = max_refundable if amount_cents is None else int(amount_cents)
        if amount <= 0 or amount > max_refundable:
            raise BadRequestException(
                f"Refund must be between 1 and {max_refundable} cents (remaining balance)"
            )

        result = self.provider.refund(
            charge_id=payment.provider_charge_id or f"mock_ch_{payment.id}", amount_cents=amount
        )
        if result.status not in ("succeeded", "pending"):
            raise BadRequestException("The payment provider could not process this refund")

        payment.refunded_cents += amount
        payment.refund_reason = reason
        payment.status = (
            "refunded" if payment.refunded_cents >= payment.amount_cents else "partially_refunded"
        )
        await self.db.flush()
        await self._audit(
            inst.id,
            user.id,
            app,
            "payment_refunded",
            description=f"Refunded {payment.currency} ${amount / 100:,.2f} of {payment.kind}",
            reason=reason,
            new_value={"refunded_cents": payment.refunded_cents, "status": payment.status},
        )
        kind_label = payment.kind.replace("_", " ")
        await self._notify_student(
            app,
            "Refund issued",
            f"A refund of {payment.currency} ${amount / 100:,.2f} "
            f"was issued for your {kind_label}.",
        )
        return {
            "payment_id": str(payment.id),
            "status": payment.status,
            "refunded_amount": round(payment.refunded_cents / 100, 2),
            "amount": round(payment.amount_cents / 100, 2),
            "currency": payment.currency,
        }

    # ── audit + notify ──────────────────────────────────────────────────────────

    async def _audit(
        self,
        institution_id: UUID | None,
        actor_user_id: UUID | None,
        app: Application,
        action: str,
        *,
        description: str | None = None,
        reason: str | None = None,
        new_value: dict | None = None,
        actor_role: str | None = None,
    ) -> None:
        try:
            from unipaith.services.audit_service import AuditService

            await AuditService(self.db).log(
                institution_id=institution_id,
                actor_user_id=actor_user_id,
                action=action,
                entity_type="payment",
                entity_id=str(app.id),
                application_id=app.id,
                description=description,
                reason=reason,
                new_value=new_value,
                actor_role=actor_role,
            )
        except Exception:  # noqa: BLE001 — audit must not block the action
            pass

    async def _notify_student(self, app: Application, title: str, body: str) -> None:
        try:
            from unipaith.services.notification_service import NotificationService

            user_id = await self._apps._resolve_user_id(app.student_id)
            if user_id is not None:
                await NotificationService(self.db).notify(
                    user_id=user_id,
                    notification_type="deadline_reminders",
                    title=title,
                    body=body,
                    action_url=f"/s/applications/{app.id}",
                    metadata={"application_id": str(app.id)},
                )
        except Exception:  # noqa: BLE001 — notification is best-effort
            pass

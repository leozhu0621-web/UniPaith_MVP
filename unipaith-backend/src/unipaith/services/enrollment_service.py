"""Spec 35 — Enrollment Confirmation & Yield (service layer).

Converts an *accepted* offer (spec 18 / 34) into a confirmed enrolment, drives
the §5 state machine, owns the post-accept checklist, deposit status (status
only — Spec 39 owns real money), deferral requests, and waitlist movement.

Reuses ``ApplicationService`` for the notify/audit/offer plumbing it already
owns (``release_decision`` for waitlist promotion, ``_resolve_user_id`` +
``_post_decision_to_inbox`` for notifications) rather than duplicating it.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.core.exceptions import BadRequestException, NotFoundException
from unipaith.models.application import Application, EnrollmentRecord, OfferLetter
from unipaith.models.institution import IntakeRound, Program
from unipaith.models.student import StudentProfile
from unipaith.services.application_service import ApplicationService

# §5 state machine ordering — index = progress. ``withdrew`` / ``deferred`` are
# off-path branches handled explicitly.
_STATE_ORDER = [
    "accepted",
    "intent_confirmed",
    "deposit_recorded",
    "enrollment_confirmed",
    "enrolled",
]
# States that count as "the student has confirmed intent" (yield numerator tail).
_CONFIRMED_STATES = {"intent_confirmed", "deposit_recorded", "enrollment_confirmed", "enrolled"}
_DEPOSITED_STATES = {"deposit_recorded", "enrollment_confirmed", "enrolled"}


def _state_at_least(state: str, target: str) -> bool:
    """True when ``state`` is at or beyond ``target`` on the happy path."""
    if state in ("withdrew", "deferred"):
        return False
    try:
        return _STATE_ORDER.index(state) >= _STATE_ORDER.index(target)
    except ValueError:
        return False


class EnrollmentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self._apps = ApplicationService(db)

    # ── Checklist (§2.1) ─────────────────────────────────────────────────────

    @staticmethod
    def _program_flag(program: Program | None, *keys: str) -> bool:
        """Read an enrolment config flag from the program's requirement blobs."""
        if program is None:
            return False
        for blob_name in ("application_requirements", "requirements", "cost_data"):
            blob = getattr(program, blob_name, None)
            if isinstance(blob, dict):
                enr = blob.get("enrollment") if isinstance(blob.get("enrollment"), dict) else blob
                for k in keys:
                    if isinstance(enr, dict) and enr.get(k):
                        return True
        return False

    @staticmethod
    def _deposit_amount(program: Program | None, offer: OfferLetter | None) -> int | None:
        cost = getattr(program, "cost_data", None) if program else None
        if isinstance(cost, dict):
            for k in ("enrollment_deposit", "deposit", "deposit_amount"):
                v = cost.get(k)
                if isinstance(v, int | float):
                    return int(v)
        return None

    def _build_checklist(
        self, program: Program | None, offer: OfferLetter | None, deadline: date | None
    ) -> list[dict]:
        """The program-defined post-accept checklist (§2.1). Conditional items
        (health / housing / visa) appear when the program config flags them."""
        due_soon = (deadline or (datetime.now(UTC).date() + timedelta(days=21))).isoformat()
        later = (datetime.now(UTC).date() + timedelta(days=45)).isoformat()
        items: list[dict] = [
            {
                "key": "confirm_intent",
                "item": "Confirm your intent to enroll",
                "status": "pending",
                "due": (deadline.isoformat() if deadline else due_soon),
                "consequence": "Your seat is released if you don't confirm by the deadline.",
            },
            {
                "key": "deposit",
                "item": "Pay / mark your enrollment deposit",
                "status": "pending",
                "due": due_soon,
                "consequence": "Confirmation isn't final until the deposit is recorded or waived.",
            },
            {
                "key": "final_transcript",
                "item": "Submit your final/official transcript",
                "status": "pending",
                "due": later,
                "consequence": "Admission may be revoked if your final transcript isn't received.",
            },
        ]
        if self._program_flag(program, "health_forms_required", "immunization_required"):
            items.append(
                {
                    "key": "health_forms",
                    "item": "Complete health & immunization forms",
                    "status": "pending",
                    "due": later,
                    "consequence": "You may not be able to register for classes without these.",
                }
            )
        if self._program_flag(program, "housing_offered", "housing"):
            items.append(
                {
                    "key": "housing",
                    "item": "Submit your housing intent form",
                    "status": "pending",
                    "due": later,
                    "consequence": "On-campus housing isn't guaranteed after the deadline.",
                }
            )
        if self._program_flag(program, "visa_required_flag", "visa_required", "international"):
            items.append(
                {
                    "key": "visa",
                    "item": "Begin your visa next steps",
                    "status": "pending",
                    "due": later,
                    "consequence": (
                        "Visa processing can take weeks — start early to arrive on time."
                    ),
                }
            )
        items.append(
            {
                "key": "orientation",
                "item": "Register for orientation",
                "status": "pending",
                "due": later,
                "consequence": "You'll miss key onboarding if you don't register in time.",
            }
        )
        return items

    def _refresh_checklist_statuses(self, enr: EnrollmentRecord) -> list[dict]:
        """Derive each item's live status from the state machine + due date.
        ``confirm_intent`` and ``deposit`` are auto-derived; explicit toggles
        (set via ``toggle_checklist_item``) are preserved for the rest."""
        today = datetime.now(UTC).date()
        checklist = list(enr.checklist or [])
        for item in checklist:
            key = item.get("key")
            if key == "confirm_intent":
                item["status"] = (
                    "complete" if enr.state != "accepted" and enr.state != "withdrew" else "pending"
                )
            elif key == "deposit":
                if enr.deposit_status in ("paid", "waived"):
                    item["status"] = "complete" if enr.deposit_status == "paid" else "waived"
                elif enr.deposit_status == "pending":
                    item["status"] = "pending"
            # Overdue overlay for anything still pending past its due date.
            if item.get("status") == "pending" and item.get("due"):
                try:
                    if date.fromisoformat(str(item["due"])) < today:
                        item["status"] = "overdue"
                except ValueError:
                    pass
        return checklist

    # ── Row lifecycle ────────────────────────────────────────────────────────

    async def _offer_for(self, application_id: UUID) -> OfferLetter | None:
        res = await self.db.execute(
            select(OfferLetter).where(OfferLetter.application_id == application_id)
        )
        return res.scalar_one_or_none()

    @staticmethod
    def _is_accepted(app: Application, offer: OfferLetter | None) -> bool:
        return app.student_decision == "accepted_by_student" or (
            offer is not None and offer.student_response == "accepted"
        )

    async def _get_or_create(
        self, app: Application, offer: OfferLetter | None, program: Program | None
    ) -> EnrollmentRecord:
        res = await self.db.execute(
            select(EnrollmentRecord).where(EnrollmentRecord.application_id == app.id)
        )
        enr = res.scalar_one_or_none()
        if enr is not None:
            return enr
        deadline = offer.response_deadline if offer else None
        enr = EnrollmentRecord(
            application_id=app.id,
            student_id=app.student_id,
            program_id=app.program_id,
            offer_id=offer.id if offer else None,
            state="accepted",
            deposit_status="none",
            deposit_amount=self._deposit_amount(program, offer),
            checklist=self._build_checklist(program, offer, deadline),
            enrollment_status="accepted",
            start_term=(
                f"{offer.start_term_season} {offer.start_term_year}"
                if offer and offer.start_term_season and offer.start_term_year
                else None
            ),
        )
        self.db.add(enr)
        await self.db.flush()
        await self.db.refresh(enr)
        return enr

    # ── Serialization (§5 Enrollment shape) ──────────────────────────────────

    def _serialize(
        self,
        enr: EnrollmentRecord,
        app: Application,
        offer: OfferLetter | None,
        program: Program | None,
        *,
        student_name: str | None = None,
        other_active_offers: list[dict] | None = None,
    ) -> dict:
        checklist = self._refresh_checklist_statuses(enr)
        return {
            "application_id": str(app.id),
            "offer_id": str(enr.offer_id) if enr.offer_id else (str(offer.id) if offer else None),
            "state": enr.state,
            "deposit_status": enr.deposit_status,
            "deposit_amount": enr.deposit_amount,
            "intent_confirmed_at": enr.intent_confirmed_at,
            "enrollment_confirmed_at": enr.enrollment_confirmed_at,
            "decline_reason": enr.decline_reason,
            "deferral": enr.deferral,
            "checklist": checklist,
            "program_name": program.program_name if program else None,
            "institution_name": getattr(program, "institution_name", None) if program else None,
            "start_term": enr.start_term,
            "response_deadline": (
                offer.response_deadline.isoformat() if offer and offer.response_deadline else None
            ),
            "student_name": student_name,
            "other_active_offers": other_active_offers or [],
        }

    # ── Student actions ──────────────────────────────────────────────────────

    async def get_student_enrollment(self, student_id: UUID, application_id: UUID) -> dict:
        app = await self._apps._get_application_for_student(student_id, application_id)
        offer = await self._offer_for(app.id)
        program = await self.db.get(Program, app.program_id)
        if program is not None:
            await self._apps._attach_institution_names([app])
        if not self._is_accepted(app, offer):
            # §7 — enrollment window hidden until an offer is accepted.
            return {"available": False, "application_id": str(app.id)}
        enr = await self._get_or_create(app, offer, program)
        others = await self._other_active_accepted(student_id, application_id)
        return {
            "available": True,
            **self._serialize(enr, app, offer, program, other_active_offers=others),
        }

    async def confirm_intent(self, student_id: UUID, application_id: UUID) -> dict:
        app = await self._apps._get_application_for_student(student_id, application_id)
        offer = await self._offer_for(app.id)
        program = await self.db.get(Program, app.program_id)
        if program is not None:
            await self._apps._attach_institution_names([app])
        if not self._is_accepted(app, offer):
            raise BadRequestException("Confirm your offer acceptance before confirming enrollment")
        enr = await self._get_or_create(app, offer, program)
        if enr.state == "withdrew":
            raise BadRequestException("This enrollment was withdrawn")
        if enr.state == "accepted":
            enr.state = "intent_confirmed"
        enr.intent_confirmed_at = enr.intent_confirmed_at or datetime.now(UTC)
        enr.enrollment_status = "intent_confirmed"
        await self.db.flush()
        await self._notify_student(
            app,
            program,
            "You're in — enrollment confirmed",
            f"You've confirmed your intent to enroll at "
            f"{getattr(program, 'institution_name', None) or 'your school'}. "
            "Let's get you ready — check your pre-arrival checklist.",
        )
        await self.db.refresh(enr)
        others = await self._other_active_accepted(student_id, application_id)
        return self._serialize(enr, app, offer, program, other_active_offers=others)

    async def decline_after_accept(
        self, student_id: UUID, application_id: UUID, reason: str | None = None
    ) -> dict:
        app = await self._apps._get_application_for_student(student_id, application_id)
        offer = await self._offer_for(app.id)
        program = await self.db.get(Program, app.program_id)
        if program is not None:
            await self._apps._attach_institution_names([app])
        if not self._is_accepted(app, offer):
            raise BadRequestException("No accepted offer to decline")
        enr = await self._get_or_create(app, offer, program)
        if enr.state == "enrolled":
            raise BadRequestException("Cannot decline once fully enrolled")
        enr.state = "withdrew"
        enr.decline_reason = reason
        enr.enrollment_status = "withdrew"
        # Free the seat: flip the student decision + offer so yield / waitlist
        # no longer count this as a filled place.
        app.student_decision = "declined_by_student"
        if offer is not None:
            offer.student_response = "declined"
            offer.status = "declined"
            offer.decline_reason = reason
        await self.db.flush()
        await self._notify_student(
            app,
            program,
            "Enrollment declined",
            "You've declined your place after accepting. Your seat has been released.",
        )
        await self.db.refresh(enr)
        return self._serialize(enr, app, offer, program)

    async def request_deferral(
        self, student_id: UUID, application_id: UUID, to_term: dict | None = None
    ) -> dict:
        app = await self._apps._get_application_for_student(student_id, application_id)
        offer = await self._offer_for(app.id)
        program = await self.db.get(Program, app.program_id)
        if program is not None:
            await self._apps._attach_institution_names([app])
        if not self._is_accepted(app, offer):
            raise BadRequestException("Accept your offer before requesting a deferral")
        enr = await self._get_or_create(app, offer, program)
        if enr.state == "withdrew":
            raise BadRequestException("This enrollment was withdrawn")
        enr.deferral = {"requested": True, "to_term": to_term, "approved": False}
        await self.db.flush()
        await self._notify_student(
            app,
            program,
            "Deferral requested",
            "Your deferral request has been sent — it's pending the school's approval.",
        )
        await self.db.refresh(enr)
        others = await self._other_active_accepted(student_id, application_id)
        return self._serialize(enr, app, offer, program, other_active_offers=others)

    async def toggle_checklist_item(
        self, student_id: UUID, application_id: UUID, key: str, complete: bool
    ) -> dict:
        """Mark a self-serve checklist item complete/incomplete (§2.1). The
        ``confirm_intent`` / ``deposit`` items are state-driven and not toggled
        here."""
        app = await self._apps._get_application_for_student(student_id, application_id)
        offer = await self._offer_for(app.id)
        program = await self.db.get(Program, app.program_id)
        if program is not None:
            await self._apps._attach_institution_names([app])
        enr = await self._get_or_create(app, offer, program)
        if key in ("confirm_intent", "deposit"):
            raise BadRequestException("This step is updated through its own action")
        checklist = list(enr.checklist or [])
        found = False
        for item in checklist:
            if item.get("key") == key:
                item["status"] = "complete" if complete else "pending"
                found = True
        if not found:
            raise NotFoundException("Checklist item not found")
        enr.checklist = checklist
        await self.db.flush()
        await self.db.refresh(enr)
        others = await self._other_active_accepted(student_id, application_id)
        return self._serialize(enr, app, offer, program, other_active_offers=others)

    async def _other_active_accepted(
        self, student_id: UUID, exclude_application_id: UUID
    ) -> list[dict]:
        """Other offers the student has accepted but not yet enrolled into — the
        §2.3 multi-offer prompt ("you have N other active offers")."""
        rows = await self.db.execute(
            select(Application, OfferLetter)
            .join(OfferLetter, OfferLetter.application_id == Application.id)
            .where(
                Application.student_id == student_id,
                Application.id != exclude_application_id,
                Application.student_decision == "accepted_by_student",
            )
        )
        out: list[dict] = []
        apps = []
        for app, _offer in rows.all():
            apps.append(app)
        if apps:
            await self._apps._attach_institution_names(apps)
        for app in apps:
            out.append(
                {
                    "application_id": str(app.id),
                    "program_name": app.program.program_name if app.program else None,
                    "institution_name": getattr(app.program, "institution_name", None)
                    if app.program
                    else None,
                }
            )
        return out

    # ── Institution actions ──────────────────────────────────────────────────

    async def get_institution_enrollment(self, institution_id: UUID, application_id: UUID) -> dict:
        app = await self._apps._get_application_for_institution(institution_id, application_id)
        offer = await self._offer_for(app.id)
        program = await self.db.get(Program, app.program_id)
        if program is not None:
            await self._apps._attach_institution_names([app])
        name = await self._student_name(app.student_id)
        if not self._is_accepted(app, offer):
            return {
                "available": False,
                "application_id": str(app.id),
                "student_name": name,
                "decision": app.decision,
            }
        enr = await self._get_or_create(app, offer, program)
        data = self._serialize(enr, app, offer, program, student_name=name)
        data["available"] = True
        data["timeline"] = self._timeline(enr, offer)
        return data

    def _timeline(self, enr: EnrollmentRecord, offer: OfferLetter | None) -> list[dict]:
        events: list[dict] = []
        if offer and offer.response_at:
            events.append({"label": "Offer accepted", "at": offer.response_at})
        if enr.intent_confirmed_at:
            events.append({"label": "Intent confirmed", "at": enr.intent_confirmed_at})
        if enr.deposit_status in ("paid", "waived"):
            events.append({"label": f"Deposit {enr.deposit_status}", "at": enr.updated_at})
        if enr.enrollment_confirmed_at:
            events.append({"label": "Enrollment confirmed", "at": enr.enrollment_confirmed_at})
        if enr.state == "enrolled":
            events.append({"label": "Enrolled", "at": enr.enrolled_at})
        if enr.state == "withdrew":
            events.append({"label": "Withdrew after accepting", "at": enr.updated_at})
        if enr.deferral and enr.deferral.get("requested"):
            events.append(
                {
                    "label": "Deferral approved"
                    if enr.deferral.get("approved")
                    else "Deferral requested",
                    "at": enr.updated_at,
                }
            )
        return events

    async def record_deposit(
        self,
        institution_id: UUID,
        application_id: UUID,
        deposit_status: str,
        *,
        deposit_amount: int | None = None,
        actor_user_id: UUID | None = None,
    ) -> dict:
        if deposit_status not in ("none", "pending", "paid", "waived"):
            raise BadRequestException(f"Unknown deposit status '{deposit_status}'")
        app = await self._apps._get_application_for_institution(institution_id, application_id)
        offer = await self._offer_for(app.id)
        program = await self.db.get(Program, app.program_id)
        if program is not None:
            await self._apps._attach_institution_names([app])
        enr = await self._get_or_create(app, offer, program)
        old = enr.deposit_status
        enr.deposit_status = deposit_status
        if deposit_amount is not None:
            enr.deposit_amount = deposit_amount
        # Advance to deposit_recorded once paid/waived (status only — no money).
        if deposit_status in ("paid", "waived") and _state_at_least(enr.state, "intent_confirmed"):
            if not _state_at_least(enr.state, "deposit_recorded"):
                enr.state = "deposit_recorded"
        await self.db.flush()
        await self._audit(
            institution_id,
            actor_user_id,
            app,
            "enrollment_deposit_recorded",
            description=(
                f"Deposit status: {old} → {deposit_status} (status-only, no payment processed)"
            ),
            new_value={"deposit_status": deposit_status, "deposit_amount": enr.deposit_amount},
        )
        await self.db.refresh(enr)
        name = await self._student_name(app.student_id)
        data = self._serialize(enr, app, offer, program, student_name=name)
        data["available"] = True
        data["timeline"] = self._timeline(enr, offer)
        return data

    async def mark_enrollment_confirmed(
        self,
        institution_id: UUID,
        application_id: UUID,
        *,
        final: bool = False,
        actor_user_id: UUID | None = None,
    ) -> dict:
        app = await self._apps._get_application_for_institution(institution_id, application_id)
        offer = await self._offer_for(app.id)
        program = await self.db.get(Program, app.program_id)
        if program is not None:
            await self._apps._attach_institution_names([app])
        enr = await self._get_or_create(app, offer, program)
        if enr.state == "withdrew":
            raise BadRequestException("Cannot confirm a withdrawn enrollment")
        now = datetime.now(UTC)
        if final:
            enr.state = "enrolled"
            enr.enrolled_at = now
            enr.enrollment_status = "enrolled"
            enr.enrollment_confirmed_at = enr.enrollment_confirmed_at or now
        else:
            enr.state = "enrollment_confirmed"
            enr.enrollment_confirmed_at = now
            enr.enrollment_status = "enrollment_confirmed"
        await self.db.flush()
        await self._audit(
            institution_id,
            actor_user_id,
            app,
            "enrollment_confirmed",
            description=("Marked enrolled" if final else "Marked enrollment confirmed"),
            new_value={"state": enr.state},
        )
        await self._notify_student(
            app,
            program,
            "Enrollment confirmed by your school",
            f"{getattr(program, 'institution_name', None) or 'Your school'} has confirmed "
            "your enrollment. See you on campus!",
        )
        # D2 outcome hook — strongest calibration signal (event_hooks §248).
        if final:
            try:
                from unipaith.services.event_hooks import on_enrollment_confirmed

                await on_enrollment_confirmed(self.db, enr.id)
            except Exception:  # noqa: BLE001 — outcome recording is best-effort
                pass
        await self.db.refresh(enr)
        name = await self._student_name(app.student_id)
        data = self._serialize(enr, app, offer, program, student_name=name)
        data["available"] = True
        data["timeline"] = self._timeline(enr, offer)
        return data

    async def approve_deferral(
        self,
        institution_id: UUID,
        application_id: UUID,
        *,
        approved: bool = True,
        actor_user_id: UUID | None = None,
    ) -> dict:
        app = await self._apps._get_application_for_institution(institution_id, application_id)
        offer = await self._offer_for(app.id)
        program = await self.db.get(Program, app.program_id)
        if program is not None:
            await self._apps._attach_institution_names([app])
        enr = await self._get_or_create(app, offer, program)
        if not (enr.deferral and enr.deferral.get("requested")):
            raise BadRequestException("No deferral request to act on")
        deferral = dict(enr.deferral)
        deferral["approved"] = approved
        enr.deferral = deferral
        if approved:
            enr.state = "deferred"
            enr.enrollment_status = "deferred"
        await self.db.flush()
        await self._audit(
            institution_id,
            actor_user_id,
            app,
            "enrollment_deferral_reviewed",
            description=f"Deferral {'approved' if approved else 'declined'}",
            new_value={"deferral": enr.deferral},
        )
        await self._notify_student(
            app,
            program,
            "Deferral decision",
            f"Your deferral request was {'approved' if approved else 'declined'} by "
            f"{getattr(program, 'institution_name', None) or 'your school'}.",
        )
        await self.db.refresh(enr)
        name = await self._student_name(app.student_id)
        data = self._serialize(enr, app, offer, program, student_name=name)
        data["available"] = True
        data["timeline"] = self._timeline(enr, offer)
        return data

    # ── Waitlist movement (§3.3) ─────────────────────────────────────────────

    async def get_waitlist(self, institution_id: UUID, program_id: UUID | None = None) -> dict:
        """Ranked waitlist + seats-open headline ("N seats open, M on waitlist")."""
        stmt = (
            select(Application, Program)
            .join(Program, Application.program_id == Program.id)
            .where(Program.institution_id == institution_id, Application.decision == "waitlisted")
        )
        if program_id is not None:
            stmt = stmt.where(Application.program_id == program_id)
        rows = (await self.db.execute(stmt)).all()
        apps = [a for a, _p in rows]
        await self._apps._attach_student_names(apps)
        entries: list[dict] = []
        for app, program in rows:
            entries.append(
                {
                    "application_id": str(app.id),
                    "student_id": str(app.student_id),
                    "student_name": getattr(app, "student_name", None),
                    "program_id": str(app.program_id),
                    "program_name": program.program_name,
                    "waitlist_rank": app.waitlist_rank,
                    "waitlisted_at": app.waitlisted_at,
                }
            )
        entries.sort(key=lambda e: (e["waitlist_rank"] is None, e["waitlist_rank"] or 1_000_000))
        seats = await self._seats_open(institution_id, program_id)
        return {
            "waitlist": entries,
            "waitlist_count": len(entries),
            "seats_open": seats,
            "program_id": str(program_id) if program_id else None,
        }

    async def _seats_open(self, institution_id: UUID, program_id: UUID | None) -> int | None:
        target = await self._target_class_size(institution_id, program_id)
        if target is None:
            return None
        filled = await self._filled_seats(institution_id, program_id)
        return max(target - filled, 0)

    async def _target_class_size(self, institution_id: UUID, program_id: UUID | None) -> int | None:
        stmt = (
            select(IntakeRound)
            .join(Program, IntakeRound.program_id == Program.id)
            .where(Program.institution_id == institution_id)
        )
        if program_id is not None:
            stmt = stmt.where(IntakeRound.program_id == program_id)
        rounds = (await self.db.execute(stmt)).scalars().all()
        caps = [r.capacity for r in rounds if r.capacity]
        return sum(caps) if caps else None

    async def _filled_seats(self, institution_id: UUID, program_id: UUID | None) -> int:
        """Confirmed/enrolled seats — what the waitlist is competing for."""
        stmt = (
            select(EnrollmentRecord)
            .join(Program, EnrollmentRecord.program_id == Program.id)
            .where(Program.institution_id == institution_id)
        )
        if program_id is not None:
            stmt = stmt.where(EnrollmentRecord.program_id == program_id)
        enrs = (await self.db.execute(stmt)).scalars().all()
        return sum(1 for e in enrs if e.state in _CONFIRMED_STATES)

    async def offer_to_next(
        self,
        institution_id: UUID,
        program_id: UUID,
        *,
        offer_terms: dict | None = None,
        actor_user_id: UUID | None = None,
    ) -> dict:
        """Promote the top-ranked waitlisted applicant → admit + offer (reusing
        ``release_decision`` for the mint/notify/audit), notify, audit (§3.3)."""
        rows = await self.db.execute(
            select(Application).where(
                Application.program_id == program_id,
                Application.decision == "waitlisted",
            )
        )
        candidates = list(rows.scalars().all())
        if not candidates:
            raise BadRequestException("No applicants on the waitlist for this program")
        candidates.sort(key=lambda a: (a.waitlist_rank is None, a.waitlist_rank or 1_000_000))
        top = candidates[0]
        app, offer = await self._apps.release_decision(
            institution_id,
            top.id,
            "admitted",
            decision_notes="Promoted from waitlist",
            actor_user_id=actor_user_id,
            offer=offer_terms,
        )
        # Clear waitlist ranking now that they've been offered a place.
        app.waitlist_rank = None
        await self.db.flush()
        await self._audit(
            institution_id,
            actor_user_id,
            app,
            "waitlist_offer_made",
            description="Offered place to next applicant on the waitlist",
            new_value={"offer_id": str(offer.id) if offer else None},
        )
        return {
            "promoted_application_id": str(app.id),
            "offer_id": str(offer.id) if offer else None,
            "remaining_waitlist": len(candidates) - 1,
        }

    async def bulk_offer(
        self,
        institution_id: UUID,
        program_id: UUID,
        count: int,
        *,
        actor_user_id: UUID | None = None,
    ) -> dict:
        """Release places to the next ``count`` waitlisted applicants, each
        promotion individually audited (§3.3)."""
        results: list[dict] = []
        for _ in range(max(count, 0)):
            try:
                res = await self.offer_to_next(
                    institution_id, program_id, actor_user_id=actor_user_id
                )
                results.append({"ok": True, **res})
            except BadRequestException:
                break
        return {
            "results": results,
            "offered_count": sum(1 for r in results if r.get("ok")),
        }

    # ── Helpers ──────────────────────────────────────────────────────────────

    async def _student_name(self, student_id: UUID) -> str | None:
        row = await self.db.execute(
            select(StudentProfile.first_name, StudentProfile.last_name).where(
                StudentProfile.id == student_id
            )
        )
        rec = row.first()
        if rec is None:
            return None
        return " ".join(p for p in (rec[0], rec[1]) if p) or None

    async def _notify_student(
        self, app: Application, program: Program | None, title: str, body: str
    ) -> None:
        """Bell + email + inbox notification, reusing the application service's
        inbox helper. Best-effort — never blocks the transition."""
        try:
            from unipaith.services.notification_service import NotificationService

            user_id = await self._apps._resolve_user_id(app.student_id)
            if user_id is not None:
                await NotificationService(self.db).notify(
                    user_id=user_id,
                    notification_type="enrollment_update",
                    title=title,
                    body=body,
                    action_url=f"/s/applications/{app.id}?tab=enrollment",
                    metadata={"application_id": str(app.id)},
                )
        except Exception:  # noqa: BLE001
            pass
        await self._apps._post_decision_to_inbox(app, program, title, body)

    async def _audit(
        self,
        institution_id: UUID,
        actor_user_id: UUID | None,
        app: Application,
        action: str,
        *,
        description: str | None = None,
        new_value: dict | None = None,
    ) -> None:
        try:
            from unipaith.services.audit_service import AuditService

            await AuditService(self.db).log(
                institution_id=institution_id,
                actor_user_id=actor_user_id,
                action=action,
                entity_type="enrollment",
                entity_id=str(app.id),
                application_id=app.id,
                description=description,
                new_value=new_value,
            )
        except Exception:  # noqa: BLE001 — audit must not block the action
            pass

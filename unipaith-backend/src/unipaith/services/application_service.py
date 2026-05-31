from __future__ import annotations

import random
import string
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from unipaith.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
)
from unipaith.models.application import (
    Application,
    ApplicationSubmission,
    OfferLetter,
)
from unipaith.models.engagement import StudentEssay, StudentResume
from unipaith.models.institution import Institution, Program
from unipaith.models.matching import MatchResult
from unipaith.models.needs import StudentNeed
from unipaith.models.student import StudentProfile
from unipaith.services.guardrail_service import validate_intent

# Spec 18 §2 — institution decision → student-facing decision-state mapping.
_INSTITUTION_DECISION_STATE = {
    "admitted": "accepted",
    "accepted": "accepted",
    "rejected": "rejected",
    "denied": "rejected",
    "waitlisted": "waitlisted",
    "deferred": "deferred",
}


def _program_location(program) -> str | None:  # type: ignore[no-untyped-def]
    """Coarse location string for the comparison (spec 18 §5), from the
    institution city/country transiently attached in _attach_institution_names."""
    if program is None:
        return None
    city = getattr(program, "institution_city", None)
    country = getattr(program, "institution_country", None)
    parts = [p for p in (city, country) if p]
    return ", ".join(parts) if parts else None


def _comparison_indicators(offers: list[dict]) -> dict:
    """Spec 18 §5 — highlight best value / best fit / most affordable."""

    def _id_of(rows: list[dict]) -> str | None:
        return rows[0]["application_id"] if rows else None

    affordable = sorted(
        (o for o in offers if o["cost"]["net_cost"] is not None),
        key=lambda o: o["cost"]["net_cost"],
    )
    fits = sorted(
        (o for o in offers if o["fit"]["fitness"] is not None),
        key=lambda o: o["fit"]["fitness"],
        reverse=True,
    )
    valued = sorted(
        (
            o
            for o in offers
            if o["fit"]["fitness"] is not None and o["cost"]["net_cost"] is not None
        ),
        key=lambda o: o["fit"]["fitness"] / (o["cost"]["net_cost"] + 1),
        reverse=True,
    )
    return {
        "most_affordable": _id_of(affordable),
        "best_fit": _id_of(fits),
        "best_value": _id_of(valued) or _id_of(fits),
    }


class ApplicationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # --- Student-facing ---

    async def create_application(self, student_id: UUID, program_id: UUID) -> Application:
        result = await self.db.execute(
            select(Program).where(Program.id == program_id, Program.is_published.is_(True))
        )
        if not result.scalar_one_or_none():
            raise NotFoundException("Program not found or not published")

        existing = await self.db.execute(
            select(Application).where(
                Application.student_id == student_id,
                Application.program_id == program_id,
            )
        )
        if existing.scalar_one_or_none():
            raise ConflictException("Application already exists for this program")

        # Seed the match score/rationale from the latest match result so the
        # dashboard and guardrails have fit context for a newly-created app
        # (spec 15 §14 — "create from saved → expected fields populated").
        match = (
            await self.db.execute(
                select(MatchResult).where(
                    MatchResult.student_id == student_id,
                    MatchResult.program_id == program_id,
                )
            )
        ).scalar_one_or_none()

        app = Application(
            student_id=student_id,
            program_id=program_id,
            status="draft",
            submission_mode="internal",
            completeness_status="incomplete",
            readiness_pct=0,
            match_score=(match.fitness_score if match else None),
            match_reasoning_text=(
                (match.rationale_text or match.reasoning_text) if match else None
            ),
        )
        self.db.add(app)
        await self.db.flush()

        # Spec 20 §2 — starting an application auto-follows the institution.
        # This follow cannot be muted-away as a program_change item and cannot
        # be unfollowed while the application is active (enforced in
        # FollowService.unfollow via the live application check).
        from unipaith.services.follow_service import FollowService

        await FollowService(self.db).auto_follow_for_program(
            student_id, program_id, source="application"
        )
        return app

    async def list_student_applications(self, student_id: UUID) -> list[Application]:
        result = await self.db.execute(
            select(Application)
            .where(Application.student_id == student_id)
            .options(selectinload(Application.program))
            .order_by(Application.created_at.desc())
        )
        apps = list(result.scalars().all())
        await self._attach_institution_names(apps)
        await self._attach_offers(apps)
        return apps

    async def get_student_application(self, student_id: UUID, application_id: UUID) -> Application:
        app = await self._get_application_for_student(student_id, application_id)
        await self._attach_institution_names([app])
        await self._attach_offers([app])
        return app

    async def _attach_institution_names(self, apps: list[Application]) -> None:
        """Set a transient ``institution_name`` on each app's program brief so
        the dashboard can filter/group by institution (spec 15 §2)."""
        inst_ids = {
            a.program.institution_id
            for a in apps
            if a.program is not None and a.program.institution_id is not None
        }
        if not inst_ids:
            return
        rows = await self.db.execute(
            select(Institution.id, Institution.name, Institution.city, Institution.country).where(
                Institution.id.in_(inst_ids)
            )
        )
        info_by_id = {row.id: row for row in rows.all()}
        for a in apps:
            if a.program is not None:
                info = info_by_id.get(a.program.institution_id)
                if info is not None:
                    a.program.institution_name = info.name
                    a.program.institution_city = info.city
                    a.program.institution_country = info.country

    async def _attach_offers(self, apps: list[Application]) -> None:
        """Embed each app's offer (with brief + structured plain-language brief)
        and the derived §2 decision_state. Bulk-fetched in one query."""
        app_ids = [a.id for a in apps]
        offers_by_app: dict[UUID, OfferLetter] = {}
        if app_ids:
            rows = await self.db.execute(
                select(OfferLetter).where(OfferLetter.application_id.in_(app_ids))
            )
            offers_by_app = {o.application_id: o for o in rows.scalars().all()}
        for app in apps:
            offer = offers_by_app.get(app.id)
            if offer is not None:
                structured = offer.plain_language_brief or self._build_structured_brief(
                    offer, app.program
                )
                offer.plain_language_brief = structured
                offer.brief = structured.get("summary") or self._build_offer_brief(
                    offer, app.program
                )
            app.offer = offer
            app.decision_state = self._decision_state(app, offer)

    @staticmethod
    def _decision_state(app: Application, offer: OfferLetter | None) -> str:
        """Spec 18 §2 unified decision state. Student actions win, then the
        institution decision (admitted→accepted), else pending."""
        if app.student_decision:
            return app.student_decision
        if app.decision:
            return _INSTITUTION_DECISION_STATE.get(app.decision, app.decision)
        if offer is not None:
            return "accepted"
        return "pending"

    @staticmethod
    def _build_offer_brief(offer: OfferLetter, program: Program | None) -> str:
        """Rule-based one-line OutcomeBrief summary. The structured builder
        below is the richer form; this stays for the legacy ``brief`` field."""
        prog_name = program.program_name if program else "the program"
        otype = (offer.offer_type or "offer").replace("_", " ")
        parts = [f"You've received a {otype} from {prog_name}."]
        if offer.scholarship_amount:
            cur = offer.scholarship_currency or "USD"
            parts.append(f"Scholarship: {cur} ${offer.scholarship_amount:,}.")
        tuition = offer.tuition_amount or offer.tuition_estimate
        if tuition:
            parts.append(f"Tuition: ${tuition:,}.")
        if offer.financial_package_total or offer.total_cost_estimate:
            total = offer.financial_package_total or offer.total_cost_estimate
            parts.append(f"Total package: ${total:,}.")
        if offer.response_deadline:
            parts.append(f"Respond by {offer.response_deadline.isoformat()}.")
        return " ".join(parts)

    @staticmethod
    def _build_structured_brief(offer: OfferLetter, program: Program | None) -> dict:
        """Rule-based ``OutcomeBriefForOfferLetter`` fallback (45 §15). Returns
        {key_terms, deadlines, next_steps, summary}. The LLM agent (behind
        ``ai_outcome_brief_v2_enabled``) swaps in a richer version; on any
        failure the service falls back to exactly this shape — never a 5xx."""
        prog_name = program.program_name if program else "the program"
        inst_name = getattr(program, "institution_name", None) if program else None
        where = f"{prog_name}" + (f" at {inst_name}" if inst_name else "")
        cur = offer.scholarship_currency or "USD"

        key_terms: list[dict] = []
        if offer.scholarship_amount:
            key_terms.append(
                {
                    "label": "Scholarship",
                    "value": f"{cur} ${offer.scholarship_amount:,}",
                    "explanation": "Award applied toward your cost of attendance.",
                }
            )
        tuition = offer.tuition_amount or offer.tuition_estimate
        if tuition:
            key_terms.append(
                {
                    "label": "Tuition estimate",
                    "value": f"${tuition:,}/yr",
                    "explanation": "Estimated annual tuition before aid.",
                }
            )
        total = offer.financial_package_total or offer.total_cost_estimate
        if total:
            key_terms.append(
                {
                    "label": "Total cost estimate",
                    "value": f"${total:,}",
                    "explanation": "Estimated all-in cost across the program.",
                }
            )
        if offer.conditions:
            cond_text = (
                offer.conditions.get("summary")
                if isinstance(offer.conditions, dict)
                else str(offer.conditions)
            )
            key_terms.append(
                {
                    "label": "Conditions",
                    "value": cond_text or "Conditional offer",
                    "explanation": "Requirements you must meet for the offer to hold.",
                }
            )
        if offer.start_term_season and offer.start_term_year:
            key_terms.append(
                {
                    "label": "Start term",
                    "value": f"{offer.start_term_season} {offer.start_term_year}",
                    "explanation": "When you would begin the program.",
                }
            )

        deadlines: list[dict] = []
        if offer.response_deadline:
            days = (offer.response_deadline - datetime.now(UTC).date()).days
            deadlines.append(
                {
                    "label": "Respond by",
                    "date": offer.response_deadline.isoformat(),
                    "days_remaining": days,
                }
            )

        next_steps: list[dict] = []
        for action in offer.next_step_actions or []:
            if isinstance(action, dict) and action.get("action"):
                next_steps.append({"action": action["action"], "by_date": action.get("by_date")})
        if not next_steps and offer.response_deadline:
            next_steps.append(
                {
                    "action": "Confirm your decision",
                    "by_date": offer.response_deadline.isoformat(),
                }
            )

        otype = (offer.offer_type or "offer").replace("_", " ")
        summary_parts = [f"{where} offered you a {otype}."]
        if offer.scholarship_amount:
            summary_parts.append(f"It includes a {cur} ${offer.scholarship_amount:,} scholarship.")
        if offer.start_term_season and offer.start_term_year:
            summary_parts.append(
                f"You'd start in {offer.start_term_season} {offer.start_term_year}."
            )
        if offer.response_deadline:
            summary_parts.append(
                f"You have until {offer.response_deadline.isoformat()} to respond."
            )
        return {
            "key_terms": key_terms,
            "deadlines": deadlines,
            "next_steps": next_steps,
            "summary": " ".join(summary_parts),
            "source": "rule_based",
        }

    async def generate_offer_brief(self, offer: OfferLetter, program: Program | None) -> dict:
        """OutcomeBriefForOfferLetter (45 §15) when the flag is on, else the
        rule-based structured brief. Never raises — falls back on any error so
        the offer flow never 5xxes (Plan 2 integration invariant)."""
        from unipaith.config import settings as _cfg

        fallback = self._build_structured_brief(offer, program)
        if not _cfg.ai_outcome_brief_v2_enabled:
            return fallback
        try:
            from unipaith.ai.outcome_brief import OfferBriefInput, get_outcome_brief_agent

            view = OfferBriefInput(
                program_name=program.program_name if program else None,
                institution_name=getattr(program, "institution_name", None) if program else None,
                today=datetime.now(UTC).date().isoformat(),
                offer={
                    "offer_type": offer.offer_type,
                    "scholarship_amount": offer.scholarship_amount,
                    "scholarship_currency": offer.scholarship_currency,
                    "tuition": offer.tuition_amount or offer.tuition_estimate,
                    "total_cost_estimate": offer.total_cost_estimate
                    or offer.financial_package_total,
                    "conditions": offer.conditions,
                    "response_deadline": offer.response_deadline.isoformat()
                    if offer.response_deadline
                    else None,
                    "start_term": (
                        {"season": offer.start_term_season, "year": offer.start_term_year}
                        if offer.start_term_season
                        else None
                    ),
                    "next_step_actions": offer.next_step_actions,
                },
            )
            result = await get_outcome_brief_agent().generate(input_view=view, db=self.db)
            return result.brief if result else fallback
        except Exception:  # noqa: BLE001 — brief generation must never break the offer
            return fallback

    async def patch_application(
        self, student_id: UUID, application_id: UUID, updates: dict
    ) -> Application:
        """Student partial update: submission_mode + guardrail intent/rationale."""
        app = await self._get_application_for_student(student_id, application_id)

        if updates.get("submission_mode") is not None:
            mode = updates["submission_mode"]
            if mode not in ("internal", "external"):
                raise BadRequestException("submission_mode must be 'internal' or 'external'")
            app.submission_mode = mode

        if "intent_picker" in updates or "intent_rationale" in updates:
            new_intent = updates.get("intent_picker", app.intent_picker)
            new_rationale = updates.get("intent_rationale", app.intent_rationale)
            validate_intent(new_intent, new_rationale)
            if "intent_picker" in updates:
                app.intent_picker = updates["intent_picker"]
            if "intent_rationale" in updates:
                app.intent_rationale = updates["intent_rationale"]

        await self.db.flush()
        return await self.get_student_application(student_id, application_id)

    async def submit_application(self, student_id: UUID, application_id: UUID) -> Application:
        app = await self._get_application_for_student(student_id, application_id)

        if app.status != "draft":
            raise BadRequestException("Only draft applications can be submitted")

        # External: the student submits on the institution's own portal; we
        # record the platform side without invoking institution-receive (§7).
        if app.submission_mode == "external":
            now = datetime.now(UTC)
            app.status = "submitted"
            app.submitted_at = now
            app.completeness_status = "complete"
            await self.db.flush()
            await self.db.refresh(app)
            return app

        # Internal: enforce the readiness gate + freeze a submission snapshot.
        return await self.submit_application_with_guardrails(student_id, application_id)

    async def withdraw_application(self, student_id: UUID, application_id: UUID) -> None:
        app = await self._get_application_for_student(student_id, application_id)
        if app.status not in ("draft", "submitted"):
            raise BadRequestException("Cannot withdraw application in current state")
        await self.db.delete(app)
        await self.db.flush()

    # --- Institution-facing ---

    async def list_program_applications(
        self, institution_id: UUID, program_id: UUID
    ) -> list[Application]:
        program = await self.db.execute(
            select(Program).where(
                Program.id == program_id,
                Program.institution_id == institution_id,
            )
        )
        if not program.scalar_one_or_none():
            raise NotFoundException("Program not found")

        result = await self.db.execute(
            select(Application).where(
                Application.program_id == program_id,
                Application.status != "draft",
            )
        )
        return list(result.scalars().all())

    async def get_application_detail(
        self, institution_id: UUID, application_id: UUID
    ) -> Application:
        return await self._get_application_for_institution(institution_id, application_id)

    async def make_decision(
        self,
        institution_id: UUID,
        application_id: UUID,
        decision: str,
        decision_notes: str | None = None,
        reviewer_id: UUID | None = None,
    ) -> Application:
        app = await self._get_application_for_institution(institution_id, application_id)
        if app.status not in ("submitted", "under_review", "interview"):
            raise BadRequestException(
                "Application must be submitted/under review to make a decision"
            )

        app.status = "decision_made"
        app.decision = decision
        app.decision_at = datetime.now(UTC)
        app.decision_notes = decision_notes
        app.decision_by = reviewer_id
        await self.db.flush()
        await self.db.refresh(app)
        return app

    async def create_offer(
        self,
        institution_id: UUID,
        application_id: UUID,
        offer_type: str,
        tuition_amount: int | None = None,
        scholarship_amount: int = 0,
        assistantship_details: dict | None = None,
        financial_package_total: int | None = None,
        conditions: dict | None = None,
        response_deadline=None,
    ) -> OfferLetter:
        app = await self._get_application_for_institution(institution_id, application_id)
        if app.decision != "admitted":
            raise BadRequestException("Can only create offers for admitted applications")

        existing = await self.db.execute(
            select(OfferLetter).where(OfferLetter.application_id == application_id)
        )
        if existing.scalar_one_or_none():
            raise ConflictException("Offer already exists for this application")

        offer = OfferLetter(
            application_id=application_id,
            offer_type=offer_type,
            tuition_amount=tuition_amount,
            tuition_estimate=tuition_amount,
            scholarship_amount=scholarship_amount,
            assistantship_details=assistantship_details,
            financial_package_total=financial_package_total,
            total_cost_estimate=financial_package_total,
            conditions=conditions,
            response_deadline=response_deadline,
            decision_date=datetime.now(UTC).date(),
            status="sent",
        )
        self.db.add(offer)
        await self.db.flush()
        program = await self.db.get(Program, app.program_id)
        offer.plain_language_brief = await self.generate_offer_brief(offer, program)
        offer.brief = (offer.plain_language_brief or {}).get("summary") or self._build_offer_brief(
            offer, program
        )
        await self.db.flush()
        await self.db.refresh(offer)
        await self._notify_offer(app, offer)
        return offer

    # --- Student offer response ---

    async def respond_to_offer(
        self,
        student_id: UUID,
        application_id: UUID,
        response: str,
        decline_reason: str | None = None,
    ) -> OfferLetter:
        """Student accepts/declines an offer (spec 18 §4). Flips the offer and
        the application's ``student_decision`` (§2). On accept, seeds the
        post-acceptance milestone reminders (§6)."""
        app = await self._get_application_for_student(student_id, application_id)
        result = await self.db.execute(
            select(OfferLetter).where(OfferLetter.application_id == app.id)
        )
        offer = result.scalar_one_or_none()
        if not offer:
            raise NotFoundException("No offer found for this application")
        if offer.status in ("accepted", "declined"):
            raise BadRequestException("You have already responded to this offer")

        offer.student_response = response
        offer.response_at = datetime.now(UTC)
        offer.decline_reason = decline_reason if response == "declined" else None

        if response == "accepted":
            offer.status = "accepted"
            app.student_decision = "accepted_by_student"
            await self._create_acceptance_milestones(app, offer)
        else:
            offer.status = "declined"
            app.student_decision = "declined_by_student"

        await self.db.flush()
        await self.db.refresh(offer)
        try:
            from unipaith.services.event_hooks import on_offer_responded

            await on_offer_responded(self.db, application_id=app.id, offer_id=offer.id)
        except Exception:  # noqa: BLE001 — hook must not block accept/decline
            pass
        return offer

    async def respond_to_offer_with_context(
        self,
        student_id: UUID,
        application_id: UUID,
        response: str,
        decline_reason: str | None = None,
    ) -> dict:
        """Respond + return the other pending apps the student could now
        withdraw (spec 18 §6). Used by the PATCH offers endpoint."""
        offer = await self.respond_to_offer(student_id, application_id, response, decline_reason)
        withdrawable: list[dict] = []
        if response == "accepted":
            withdrawable = await self._other_pending_apps(student_id, application_id)
        return {"offer": offer, "withdrawable_apps": withdrawable}

    async def record_external_offer(
        self, student_id: UUID, application_id: UUID, payload: dict
    ) -> OfferLetter:
        """Record an offer the student received off-platform (spec 18 §14):
        same Offer row, ``received_externally=True``, flips the app to a
        decision so the offer surfaces."""
        app = await self._get_application_for_student(student_id, application_id)
        existing = await self.db.execute(
            select(OfferLetter).where(OfferLetter.application_id == app.id)
        )
        if existing.scalar_one_or_none():
            raise ConflictException("An offer already exists for this application")

        start_term = payload.get("start_term") or {}
        offer = OfferLetter(
            application_id=app.id,
            offer_type=payload.get("offer_type") or "full_admission",
            received_externally=True,
            status="sent",
            decision_date=payload.get("decision_date"),
            response_deadline=payload.get("response_deadline"),
            conditions=payload.get("conditions"),
            scholarship_amount=payload.get("scholarship_amount") or 0,
            scholarship_currency=payload.get("scholarship_currency") or "USD",
            tuition_amount=payload.get("tuition_amount"),
            tuition_estimate=payload.get("tuition_estimate"),
            total_cost_estimate=payload.get("total_cost_estimate"),
            financial_package_total=payload.get("financial_package_total"),
            start_term_season=start_term.get("season"),
            start_term_year=start_term.get("year"),
            next_step_actions=payload.get("next_step_actions"),
        )
        # An external offer means the student was admitted; reflect that so the
        # decision_state surfaces as `accepted` (offer received), not pending.
        if app.decision not in ("admitted", "accepted"):
            app.decision = "admitted"
        if app.status in (None, "draft", "submitted", "under_review", "interview"):
            app.status = "decision_made"
            app.decision_at = app.decision_at or datetime.now(UTC)
        self.db.add(offer)
        await self.db.flush()
        offer.plain_language_brief = await self.generate_offer_brief(offer, app.program)
        await self.db.flush()
        await self.db.refresh(offer)
        offer.brief = (offer.plain_language_brief or {}).get("summary")
        await self._notify_offer(app, offer)
        return offer

    async def withdraw_from_decisions(self, student_id: UUID, application_id: UUID) -> Application:
        """Status-preserving withdraw (spec 18 §2/§6) — keeps the row so the
        timeline shows ``withdrawn`` (unlike the hard-delete draft withdraw)."""
        app = await self._get_application_for_student(student_id, application_id)
        if app.student_decision == "accepted_by_student":
            raise BadRequestException("Cannot withdraw an application you've accepted")
        app.student_decision = "withdrawn"
        await self.db.flush()
        # Re-fetch so decision_state / offer / institution names are attached.
        return await self.get_student_application(student_id, application_id)

    async def bulk_withdraw(self, student_id: UUID, application_ids: list[UUID]) -> int:
        """Withdraw several applications at once (spec 18 §6) — the other
        pending apps after an acceptance. Skips any that can't be withdrawn."""
        count = 0
        for app_id in application_ids:
            try:
                await self.withdraw_from_decisions(student_id, app_id)
                count += 1
            except (NotFoundException, BadRequestException):
                continue
        return count

    async def _other_pending_apps(
        self, student_id: UUID, exclude_application_id: UUID
    ) -> list[dict]:
        """Other applications still awaiting a final student decision — the
        candidates for bulk-withdraw after accepting elsewhere (§6)."""
        rows = await self.db.execute(
            select(Application)
            .where(
                Application.student_id == student_id,
                Application.id != exclude_application_id,
                Application.student_decision.is_(None),
                Application.status != "draft",
            )
            .options(selectinload(Application.program))
        )
        apps = list(rows.scalars().all())
        await self._attach_institution_names(apps)
        return [
            {
                "id": str(a.id),
                "program_name": a.program.program_name if a.program else None,
                "institution_name": getattr(a.program, "institution_name", None)
                if a.program
                else None,
                "decision_state": self._decision_state(a, None),
            }
            for a in apps
        ]

    async def get_offers_comparison(self, student_id: UUID) -> dict:
        """Side-by-side comparison of every current offer (spec 18 §5)."""
        rows = await self.db.execute(
            select(Application)
            .where(Application.student_id == student_id)
            .options(selectinload(Application.program))
            .order_by(Application.created_at.desc())
        )
        apps = list(rows.scalars().all())
        await self._attach_institution_names(apps)
        await self._attach_offers(apps)

        need_rows = await self.db.execute(
            select(StudentNeed).where(
                StudentNeed.student_id == student_id,
                StudentNeed.severity == "must_have",
            )
        )
        must_haves = [{"need": n.need_type, "signal": n.signal} for n in need_rows.scalars().all()]

        offers_data: list[dict] = []
        for app in apps:
            offer = app.offer
            if offer is None:
                continue
            tuition = offer.tuition_amount or offer.tuition_estimate
            scholarship = offer.scholarship_amount or 0
            total = offer.total_cost_estimate or offer.financial_package_total
            if total is not None:
                net_cost = max(total - scholarship, 0)
            elif tuition is not None:
                net_cost = max(tuition - scholarship, 0)
            else:
                net_cost = None
            match = await self._latest_match(student_id, app.program_id)
            program = app.program
            offers_data.append(
                {
                    "application_id": str(app.id),
                    "offer_id": str(offer.id),
                    "program_name": program.program_name if program else None,
                    "institution_name": getattr(program, "institution_name", None)
                    if program
                    else None,
                    "degree_type": program.degree_type if program else None,
                    "decision_state": app.decision_state,
                    "cost": {
                        "tuition": tuition,
                        "scholarship": scholarship,
                        "currency": offer.scholarship_currency or "USD",
                        "net_cost": net_cost,
                    },
                    "fit": {
                        "fitness": float(match["fitness"])
                        if match["fitness"] is not None
                        else None,
                        "confidence": float(match["confidence"])
                        if match["confidence"] is not None
                        else None,
                    },
                    "outcomes": {"median_salary": None, "placement_rate": None},
                    "location": _program_location(program),
                    "response_deadline": offer.response_deadline.isoformat()
                    if offer.response_deadline
                    else None,
                    "conditions": offer.conditions,
                }
            )

        return {
            "offers": offers_data,
            "indicators": _comparison_indicators(offers_data),
            "must_have_constraints": must_haves,
            "count": len(offers_data),
        }

    async def _latest_match(self, student_id: UUID, program_id: UUID) -> dict:
        row = await self.db.execute(
            select(MatchResult).where(
                MatchResult.student_id == student_id,
                MatchResult.program_id == program_id,
            )
        )
        m = row.scalar_one_or_none()
        if m is None:
            return {"fitness": None, "confidence": None}
        return {
            "fitness": m.fitness_score if m.fitness_score is not None else m.match_score,
            "confidence": m.confidence_score,
        }

    async def _create_acceptance_milestones(self, app: Application, offer: OfferLetter) -> None:
        """Seed deposit / orientation / housing reminders after acceptance
        (spec 18 §6). Best-effort — failures never block the accept."""
        try:
            from unipaith.schemas.calendar import ReminderCreate
            from unipaith.services.calendar_service import CalendarService

            now = datetime.now(UTC)
            deposit_at = (
                datetime.combine(offer.response_deadline, datetime.min.time(), tzinfo=UTC)
                if offer.response_deadline
                else now + timedelta(days=14)
            )
            milestones = [
                ("Submit your enrollment deposit", deposit_at),
                ("Schedule orientation", now + timedelta(days=30)),
                ("Apply for housing", now + timedelta(days=30)),
            ]
            cal = CalendarService(self.db)
            for title, when in milestones:
                await cal.create_reminder(
                    app.student_id,
                    ReminderCreate(title=title, start_at=when, application_id=app.id),
                )
        except Exception:  # noqa: BLE001 — milestones are best-effort
            pass

    async def _notify_offer(self, app: Application, offer: OfferLetter) -> None:
        """Fire the offer-received notification (spec 18 §8). Best-effort."""
        try:
            from unipaith.services.notification_service import NotificationService

            user_id = await self._resolve_user_id(app.student_id)
            if user_id is None:
                return
            prog = app.program.program_name if app.program else "your program"
            await NotificationService(self.db).notify(
                user_id=user_id,
                notification_type="decision_made",
                title=f"Offer received from {prog}",
                body=offer.brief or self._build_offer_brief(offer, app.program),
                action_url=f"/s/applications/{app.id}?tab=offer",
                metadata={"application_id": str(app.id), "offer_id": str(offer.id)},
            )
        except Exception:  # noqa: BLE001 — notifications are best-effort
            pass

    async def _resolve_user_id(self, student_profile_id: UUID) -> UUID | None:
        row = await self.db.execute(
            select(StudentProfile.user_id).where(StudentProfile.id == student_profile_id)
        )
        return row.scalar_one_or_none()

    async def update_status(
        self,
        institution_id: UUID,
        application_id: UUID,
        new_status: str,
    ) -> Application:
        allowed_transitions: dict[str, list[str]] = {
            "submitted": ["under_review"],
            "under_review": ["interview", "decision_made"],
            "interview": ["decision_made", "under_review"],
        }

        app = await self._get_application_for_institution(institution_id, application_id)
        current = app.status
        allowed = allowed_transitions.get(current, [])
        if new_status not in allowed:
            raise BadRequestException(
                f"Cannot transition from '{current}' to '{new_status}'. Allowed: {allowed}"
            )
        app.status = new_status
        await self.db.flush()
        await self.db.refresh(app)
        return app

    # --- Submission with guardrails ---

    async def submit_application_with_guardrails(
        self, student_id: UUID, application_id: UUID
    ) -> Application:
        """Submit an application with full readiness validation and snapshot.

        1. Verifies the application exists, belongs to the student, and is in
           ``draft`` status.
        2. Runs a readiness check via :class:`ChecklistService`.
        3. If not ready, raises :class:`BadRequestException` with the list of
           missing items.
        4. Creates an :class:`ApplicationSubmission` with a frozen snapshot of
           all student materials.
        5. Generates a unique confirmation number (``UP-{year}-{6 chars}``).
        6. Transitions the application to ``submitted``.

        Returns:
            The updated :class:`Application` instance.
        """
        from unipaith.services.checklist_service import ChecklistService

        app = await self._get_application_for_student(student_id, application_id)

        if app.status != "draft":
            raise BadRequestException("Only draft applications can be submitted")

        # Run readiness check
        checklist_svc = ChecklistService(self.db)
        readiness = await checklist_svc.readiness_check(student_id, application_id)

        if not readiness["is_ready"]:
            missing = ", ".join(readiness["missing_items"])
            raise BadRequestException(
                f"Application is not ready for submission. Missing: {missing}"
            )

        # Build frozen snapshot
        snapshot = await self._build_submission_snapshot(student_id, application_id, app.program_id)

        # Generate unique confirmation number: UP-{year}-{6 random alphanumeric}
        year = datetime.now(UTC).year
        random_part = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        confirmation = f"UP-{year}-{random_part}"

        now = datetime.now(UTC)
        app.status = "submitted"
        app.submitted_at = now
        app.completeness_status = "complete"

        submission = ApplicationSubmission(
            application_id=app.id,
            submitted_documents=snapshot,
            submitted_at=now,
            confirmation_number=confirmation,
        )
        self.db.add(submission)
        await self.db.flush()
        await self.db.refresh(app)
        return app

    async def _build_submission_snapshot(
        self, student_id: UUID, application_id: UUID, program_id: UUID
    ) -> dict:
        """Build a frozen JSONB snapshot of all student materials at submission time.

        Captures profile, academic records, test scores, activities,
        documents, essays (for this program), and the latest resume.

        Returns:
            A dictionary suitable for storing in
            ``ApplicationSubmission.submitted_documents``.
        """
        # Load profile with eager-loaded relationships
        result = await self.db.execute(
            select(StudentProfile)
            .where(StudentProfile.id == student_id)
            .options(
                selectinload(StudentProfile.academic_records),
                selectinload(StudentProfile.test_scores),
                selectinload(StudentProfile.activities),
                selectinload(StudentProfile.documents),
            )
        )
        profile = result.scalar_one_or_none()
        if not profile:
            raise NotFoundException("Student profile not found")

        # Load essays for this program
        essay_result = await self.db.execute(
            select(StudentEssay).where(
                StudentEssay.student_id == student_id,
                StudentEssay.program_id == program_id,
            )
        )
        essays = list(essay_result.scalars().all())

        # Load latest resume
        resume_result = await self.db.execute(
            select(StudentResume)
            .where(StudentResume.student_id == student_id)
            .order_by(StudentResume.resume_version.desc())
            .limit(1)
        )
        resume = resume_result.scalar_one_or_none()

        snapshot: dict = {
            "snapshot_at": datetime.now(UTC).isoformat(),
            "profile": {
                "first_name": profile.first_name,
                "last_name": profile.last_name,
                "nationality": profile.nationality,
                "country_of_residence": profile.country_of_residence,
                "bio_text": profile.bio_text,
                "goals_text": profile.goals_text,
            },
            "academic_records": [
                {
                    "institution_name": r.institution_name,
                    "degree_type": r.degree_type,
                    "field_of_study": r.field_of_study,
                    "gpa": str(r.gpa) if r.gpa else None,
                    "gpa_scale": r.gpa_scale,
                    "start_date": r.start_date.isoformat() if r.start_date else None,
                    "end_date": r.end_date.isoformat() if r.end_date else None,
                    "is_current": r.is_current,
                    "honors": r.honors,
                    "thesis_title": r.thesis_title,
                    "country": r.country,
                }
                for r in profile.academic_records
            ],
            "test_scores": [
                {
                    "test_type": s.test_type,
                    "total_score": str(s.total_score) if s.total_score else None,
                    "section_scores": s.section_scores,
                    "test_date": s.test_date.isoformat() if s.test_date else None,
                }
                for s in profile.test_scores
            ],
            "activities": [
                {
                    "activity_type": a.activity_type,
                    "title": a.title,
                    "organization": a.organization,
                    "description": a.description,
                    "start_date": a.start_date.isoformat() if a.start_date else None,
                    "end_date": a.end_date.isoformat() if a.end_date else None,
                }
                for a in profile.activities
            ],
            "documents": [
                {
                    "document_type": d.document_type,
                    "file_name": d.file_name,
                    "file_url": d.file_url,
                }
                for d in profile.documents
            ],
            "essays": [
                {
                    "prompt_text": e.prompt_text,
                    "content": e.content,
                    "word_count": e.word_count,
                    "status": e.status,
                }
                for e in essays
            ],
            "resume": (
                {
                    "content": resume.content,
                    "rendered_pdf_url": resume.rendered_pdf_url,
                    "version": resume.resume_version,
                }
                if resume
                else None
            ),
        }
        return snapshot

    # --- Helpers ---

    async def _get_application_for_student(
        self, student_id: UUID, application_id: UUID
    ) -> Application:
        result = await self.db.execute(
            select(Application)
            .where(
                Application.id == application_id,
                Application.student_id == student_id,
            )
            .options(selectinload(Application.program))
        )
        app = result.scalar_one_or_none()
        if not app:
            raise NotFoundException("Application not found")
        return app

    async def _get_application_for_institution(
        self, institution_id: UUID, application_id: UUID
    ) -> Application:
        result = await self.db.execute(
            select(Application)
            .join(Program, Application.program_id == Program.id)
            .where(
                Application.id == application_id,
                Program.institution_id == institution_id,
            )
        )
        app = result.scalar_one_or_none()
        if not app:
            raise NotFoundException("Application not found")
        return app

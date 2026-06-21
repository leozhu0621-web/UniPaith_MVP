from __future__ import annotations

import logging
import random
import string
from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from unipaith.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
    PaymentRequiredException,
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
from unipaith.utils.calendar_dates import business_today

logger = logging.getLogger(__name__)

# Spec 18 §2 — institution decision → student-facing decision-state mapping.
_INSTITUTION_DECISION_STATE = {
    "admitted": "accepted",
    "accepted": "accepted",
    "conditional_admission": "accepted",
    "rejected": "rejected",
    "denied": "rejected",
    "waitlisted": "waitlisted",
    "deferred": "deferred",
}

# Spec 34 §2 — institution decision values the reviewer can release. ``admitted``
# is the canonical "accepted"; ``conditional_admission`` carries conditions.
_VALID_DECISIONS = {
    "admitted",
    "accepted",
    "conditional_admission",
    "rejected",
    "waitlisted",
    "deferred",
}
# Spec 34 §3 — decisions that mint a student-facing offer on release.
_OFFER_PRODUCING_DECISIONS = {"admitted", "accepted", "conditional_admission"}
# Default offer_type per decision when the reviewer doesn't pick one (§4).
_DEFAULT_OFFER_TYPE = {
    "admitted": "full_admission",
    "accepted": "full_admission",
    "conditional_admission": "conditional",
}
# Spec 34 §3/§13 — student-facing decision notice copy (restrained; the
# celebration lives on the student side per §10). ``{prog}`` / ``{inst}`` filled.
_DECISION_NOTICE: dict[str, tuple[str, str]] = {
    "admitted": (
        "You've been admitted to {prog}",
        "{inst} has admitted you to {prog}. Review your offer and respond by the deadline.",
    ),
    "conditional_admission": (
        "Conditional admission to {prog}",
        "{inst} has offered you conditional admission to {prog}. "
        "Review the conditions in your offer.",
    ),
    "waitlisted": (
        "Waitlist decision from {prog}",
        "{inst} has placed you on the waitlist for {prog}. We'll be in touch if a place opens.",
    ),
    "deferred": (
        "Decision deferred at {prog}",
        "{inst} has deferred your application to {prog} to a later round.",
    ),
    "rejected": (
        "Decision from {prog}",
        "{inst} has completed its review of your application to {prog}.",
    ),
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


def _outcomes_from_program(program: Program | None) -> dict:
    """Pull salary/placement bands from program.outcomes_data (spec 18 §5)."""
    if program is None or not program.outcomes_data:
        return {"median_salary": None, "placement_rate": None}
    data = program.outcomes_data
    if isinstance(data, str):
        try:
            import json as _json

            data = _json.loads(data)
        except (ValueError, TypeError):
            return {"median_salary": None, "placement_rate": None}
    if not isinstance(data, dict):
        return {"median_salary": None, "placement_rate": None}

    def _int(*keys: str) -> int | None:
        for key in keys:
            val = data.get(key)
            if val is None:
                continue
            try:
                return int(float(val))
            except (ValueError, TypeError):
                continue
        return None

    def _rate(*keys: str) -> float | None:
        for key in keys:
            val = data.get(key)
            if val is None:
                continue
            try:
                f = float(val)
                return f / 100 if f > 1 else f
            except (ValueError, TypeError):
                continue
        return None

    return {
        "median_salary": _int("median_salary", "earnings_4yr_median", "earnings_1yr_median"),
        "placement_rate": _rate("employment_rate", "placement_rate", "grad_employment_rate"),
    }


def _comparison_advisor_summary(offers: list[dict], indicators: dict) -> str | None:
    """Rule-based DecisionComparisonAdvisor (spec 18 §9) — surfaces tradeoffs."""
    if len(offers) < 2:
        return None

    by_id = {o["application_id"]: o for o in offers}
    parts: list[str] = []

    aff_id = indicators.get("most_affordable")
    if aff_id and aff_id in by_id:
        o = by_id[aff_id]
        net = o["cost"]["net_cost"]
        label = o["program_name"] or "One offer"
        if net is not None:
            parts.append(f"{label} has the lowest net cost (${net:,}).")

    fit_id = indicators.get("best_fit")
    if fit_id and fit_id in by_id:
        o = by_id[fit_id]
        fit = o["fit"]["fitness"]
        label = o["program_name"] or "One offer"
        if fit is not None:
            parts.append(f"{label} scores highest on fit ({int(round(fit * 100))}%).")

    soonest = sorted(
        (o for o in offers if o.get("response_deadline")),
        key=lambda o: o["response_deadline"],
    )
    if soonest:
        o = soonest[0]
        label = o["program_name"] or "An offer"
        parts.append(f"{label} has the earliest response deadline.")

    if not parts:
        return "Compare cost, fit, and deadlines side by side before you decide."
    return " ".join(parts)


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
            days = (offer.response_deadline - business_today()).days
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
                today=business_today().isoformat(),
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
            await self._post_submit_integrity_scan(app)
            await self._record_apply_outcome(app)
            await self.db.refresh(app)
            return app

        # Internal: enforce the readiness gate + freeze a submission snapshot.
        return await self.submit_application_with_guardrails(student_id, application_id)

    async def _post_submit_integrity_scan(self, app: Application) -> None:
        """Spec 37 G-AI4 — auto-run the AI integrity / authenticity scan on
        submit so flagged essays surface in the institution's integrity queue
        for human review. Best-effort: a savepoint isolates any failure so a
        submission never 5xxes (Spec 37 §1.3), and the scan is idempotent so a
        later manual rescan won't duplicate signals."""
        try:
            institution_id = await self.db.scalar(
                select(Program.institution_id).where(Program.id == app.program_id)
            )
            if institution_id is None:
                return
            from unipaith.services.review_pipeline_service import ReviewPipelineService

            async with self.db.begin_nested():
                await ReviewPipelineService(self.db).scan_integrity(institution_id, app.id)
        except Exception as exc:  # noqa: BLE001 — submission must never fail on the scan
            logger.info("post-submit integrity scan skipped for app=%s: %s", app.id, exc)

    async def _record_apply_outcome(self, app: Application) -> None:
        """Spec 67 — when a student commits to a matched program, record an
        ``applied`` outcome (a positive label for the confidence calibrator).
        Best-effort + consent-gated (no-op without training consent or a prior
        match prediction); a savepoint isolates failure so submission never
        5xxes."""
        try:
            from unipaith.services.learning_loop import LearningLoopService

            async with self.db.begin_nested():
                await LearningLoopService(self.db).record_outcome_for(
                    student_id=app.student_id,
                    program_id=app.program_id,
                    outcome_kind="applied",
                )
        except Exception as exc:  # noqa: BLE001 — submission must never fail on this
            logger.info("apply-outcome recording skipped for app=%s: %s", app.id, exc)

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
        apps = list(result.scalars().all())
        await self._attach_student_names(apps)
        return apps

    async def _attach_student_names(self, apps: list[Application]) -> None:
        """Spec 32 — attach each applicant's display name (instance attr read by
        ApplicationResponse.from_attributes) so institution lists show real names,
        never a raw UUID."""
        from unipaith.models.student import StudentProfile

        student_ids = list({a.student_id for a in apps})
        if not student_ids:
            return
        rows = await self.db.execute(
            select(StudentProfile.id, StudentProfile.first_name, StudentProfile.last_name).where(
                StudentProfile.id.in_(student_ids)
            )
        )
        names = {
            sid: (f"{(fn or '').strip()} {(ln or '').strip()}".strip() or None)
            for sid, fn, ln in rows.all()
        }
        for a in apps:
            a.student_name = names.get(a.student_id) or f"Applicant {str(a.student_id)[:8]}"

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
        # ``decision_made`` is allowed so a waitlisted/deferred applicant can be
        # re-decided (e.g. waitlist → admit, spec 34 §14). A finalized student
        # decision is the only hard stop.
        if app.status not in ("submitted", "under_review", "interview", "decision_made"):
            raise BadRequestException(
                "Application must be submitted/under review to make a decision"
            )
        if decision not in _VALID_DECISIONS:
            raise BadRequestException(f"Unknown decision '{decision}'")
        if app.student_decision == "accepted_by_student":
            raise BadRequestException("Cannot change a decision the student has already accepted")

        # Canonicalize "accepted" → "admitted" so analytics / badges stay uniform.
        app.status = "decision_made"
        app.decision = "admitted" if decision == "accepted" else decision
        app.decision_at = datetime.now(UTC)
        app.decision_notes = decision_notes
        app.decision_by = reviewer_id
        await self.db.flush()
        await self.db.refresh(app)
        return app

    # Decisions whose offer can be minted (spec 34 §3). ``waitlisted`` is allowed
    # so a waitlist-to-admit offer can be attached without re-deciding first.
    _OFFER_ELIGIBLE_DECISIONS = {"admitted", "accepted", "conditional_admission", "waitlisted"}

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
        *,
        scholarship_currency: str | None = None,
        tuition_estimate: int | None = None,
        total_cost_estimate: int | None = None,
        start_term_season: str | None = None,
        start_term_year: int | None = None,
        next_step_actions: list | None = None,
        notify: bool = True,
    ) -> OfferLetter:
        app = await self._get_application_for_institution(institution_id, application_id)
        if app.decision not in self._OFFER_ELIGIBLE_DECISIONS:
            raise BadRequestException(
                "Can only create offers for admitted / conditional / waitlist-to-admit applications"
            )

        existing = await self.db.execute(
            select(OfferLetter).where(OfferLetter.application_id == application_id)
        )
        if existing.scalar_one_or_none():
            raise ConflictException("Offer already exists for this application")

        offer = OfferLetter(
            application_id=application_id,
            offer_type=offer_type,
            tuition_amount=tuition_amount,
            tuition_estimate=tuition_estimate or tuition_amount,
            scholarship_amount=scholarship_amount or 0,
            scholarship_currency=scholarship_currency or "USD",
            assistantship_details=assistantship_details,
            financial_package_total=financial_package_total,
            total_cost_estimate=total_cost_estimate or financial_package_total,
            conditions=conditions,
            response_deadline=response_deadline,
            start_term_season=start_term_season,
            start_term_year=start_term_year,
            next_step_actions=next_step_actions,
            decision_date=business_today(),
            status="sent",
        )
        self.db.add(offer)
        await self.db.flush()
        program = await self.db.get(Program, app.program_id)
        if program is not None:
            await self._attach_institution_names([app])
        offer.plain_language_brief = await self.generate_offer_brief(offer, program)
        offer.brief = (offer.plain_language_brief or {}).get("summary") or self._build_offer_brief(
            offer, program
        )
        await self.db.flush()
        await self.db.refresh(offer)
        if notify:
            await self._notify_offer(app, offer)
            await self._seed_offer_deadline_reminder(app, program, offer)
        return offer

    # --- Spec 34 · Institution decision release + offer + yield ---------------

    async def release_decision(
        self,
        institution_id: UUID,
        application_id: UUID,
        decision: str,
        *,
        decision_notes: str | None = None,
        reviewer_id: UUID | None = None,
        actor_user_id: UUID | None = None,
        offer: dict | None = None,
        custom_message: str | None = None,
        notify: bool = True,
    ) -> tuple[Application, OfferLetter | None]:
        """Release a decision and (for accepted / conditional admits) the offer,
        notify the student (Inbox + email + Calendar), and audit — atomically
        (spec 34 §3). The single source of truth for both per-applicant and
        batch release. Returns ``(application, offer | None)``."""
        app = await self.make_decision(
            institution_id, application_id, decision, decision_notes, reviewer_id
        )
        program = await self.db.get(Program, app.program_id)
        if program is not None:
            await self._attach_institution_names([app])

        offer_row: OfferLetter | None = None
        norm = "admitted" if decision == "accepted" else decision
        if norm in _OFFER_PRODUCING_DECISIONS:
            offer_row = await self._ensure_release_offer(institution_id, app, program, norm, offer)

        if notify:
            await self._notify_decision(app, program, norm, offer_row, custom_message)

        if actor_user_id is not None:
            await self._audit_decision(institution_id, actor_user_id, app, norm, offer_row)

        await self.db.refresh(app)
        return app, offer_row

    async def _ensure_release_offer(
        self,
        institution_id: UUID,
        app: Application,
        program: Program | None,
        decision: str,
        offer: dict | None,
    ) -> OfferLetter:
        """Create the offer for an accepted/conditional release, or refresh the
        terms of one that already exists (re-release / waitlist-to-admit)."""
        terms = dict(offer or {})
        offer_type = terms.get("offer_type") or _DEFAULT_OFFER_TYPE.get(decision, "full_admission")
        start_term = terms.get("start_term") or {}
        if isinstance(start_term, dict):
            season, year = start_term.get("season"), start_term.get("year")
        else:
            season, year = None, None
        deadline = terms.get("response_deadline")
        if isinstance(deadline, str) and deadline:
            try:
                deadline = date.fromisoformat(deadline)
            except ValueError:
                deadline = None

        existing = await self.db.execute(
            select(OfferLetter).where(OfferLetter.application_id == app.id)
        )
        row = existing.scalar_one_or_none()
        if row is None:
            return await self.create_offer(
                institution_id,
                app.id,
                offer_type=offer_type,
                tuition_amount=terms.get("tuition_amount"),
                scholarship_amount=terms.get("scholarship_amount") or 0,
                conditions=terms.get("conditions"),
                financial_package_total=terms.get("financial_package_total"),
                response_deadline=deadline,
                scholarship_currency=terms.get("scholarship_currency"),
                tuition_estimate=terms.get("tuition_estimate"),
                total_cost_estimate=terms.get("total_cost_estimate"),
                start_term_season=season,
                start_term_year=year,
                next_step_actions=terms.get("next_step_actions"),
                notify=False,  # release sends one unified notice instead
            )
        # Refresh existing offer terms in place (clone-free re-release).
        row.offer_type = offer_type
        if terms.get("scholarship_amount") is not None:
            row.scholarship_amount = terms["scholarship_amount"]
        if terms.get("conditions") is not None:
            row.conditions = terms["conditions"]
        if deadline is not None:
            row.response_deadline = deadline
        if row.status == "rescinded":
            row.status = "sent"
        await self.db.flush()
        row.plain_language_brief = await self.generate_offer_brief(row, program)
        row.brief = (row.plain_language_brief or {}).get("summary") or self._build_offer_brief(
            row, program
        )
        await self.db.flush()
        await self.db.refresh(row)
        return row

    async def _audit_decision(
        self,
        institution_id: UUID,
        actor_user_id: UUID,
        app: Application,
        decision: str,
        offer: OfferLetter | None,
    ) -> None:
        """Per-application audit entry for a release (spec 34 §5/§12)."""
        try:
            from unipaith.services.audit_service import AuditService

            await AuditService(self.db).log(
                institution_id=institution_id,
                actor_user_id=actor_user_id,
                action="decision_release",
                entity_type="application",
                entity_id=str(app.id),
                application_id=app.id,
                description=f"Released decision: {decision}",
                new_value={
                    "decision": decision,
                    "offer_id": str(offer.id) if offer else None,
                },
            )
        except Exception:  # noqa: BLE001 — audit must not block the release
            pass

    async def _notify_decision(
        self,
        app: Application,
        program: Program | None,
        decision: str,
        offer: OfferLetter | None,
        custom_message: str | None = None,
    ) -> None:
        """Fire the decision notification across Inbox + email + Calendar
        (spec 34 §3.4). Best-effort — a failed channel never blocks release."""
        prog = program.program_name if program else "your program"
        inst = (
            getattr(program, "institution_name", None) if program else None
        ) or "the institution"
        title_t, body_t = _DECISION_NOTICE.get(decision, _DECISION_NOTICE["rejected"])
        title = title_t.format(prog=prog, inst=inst)
        body = custom_message or (
            offer.brief if (offer and offer.brief) else body_t.format(prog=prog, inst=inst)
        )

        # 1) In-app notification + email (NotificationService honors prefs).
        try:
            from unipaith.services.notification_service import NotificationService

            user_id = await self._resolve_user_id(app.student_id)
            if user_id is not None:
                await NotificationService(self.db).notify(
                    user_id=user_id,
                    notification_type="decision_made",
                    title=title,
                    body=body,
                    action_url=f"/s/applications/{app.id}?tab=offer",
                    metadata={
                        "application_id": str(app.id),
                        "decision": decision,
                        "offer_id": str(offer.id) if offer else None,
                    },
                )
        except Exception:  # noqa: BLE001
            pass

        # 2) Threaded system message in the student's Spec-17 inbox.
        await self._post_decision_to_inbox(app, program, title, body)

        # 3) Calendar: a respond-by reminder when the offer carries a deadline.
        if offer is not None:
            await self._seed_offer_deadline_reminder(app, program, offer)

    async def _post_decision_to_inbox(
        self, app: Application, program: Program | None, title: str, body: str
    ) -> None:
        """Append a system message to the application's inbox thread (creating
        the thread if needed) so the decision lands in the student's Messages."""
        try:
            from unipaith.models.engagement import Conversation, Message

            now = datetime.now(UTC)
            inst_id = getattr(program, "institution_id", None) if program else None
            res = await self.db.execute(
                select(Conversation).where(Conversation.application_id == app.id).limit(1)
            )
            conv = res.scalar_one_or_none()
            if conv is None:
                conv = Conversation(
                    student_id=app.student_id,
                    institution_id=inst_id,
                    program_id=app.program_id,
                    application_id=app.id,
                    subject=title,
                    thread_type="system",
                    action_label="status_update_only",
                    status="active",
                    started_at=now,
                    last_message_at=now,
                )
                self.db.add(conv)
                await self.db.flush()
            else:
                conv.last_message_at = now
                if conv.action_label not in ("needs_reply", "document_requested"):
                    conv.action_label = "status_update_only"
            self.db.add(
                Message(
                    conversation_id=conv.id,
                    sender_type="system",
                    sender_id=None,
                    message_body=f"{title}\n\n{body}",
                    status="sent",
                )
            )
            await self.db.flush()
        except Exception:  # noqa: BLE001 — inbox post is best-effort
            pass

    async def _seed_offer_deadline_reminder(
        self, app: Application, program: Program | None, offer: OfferLetter
    ) -> None:
        """Put a 'Respond to your offer' reminder on the student's calendar at
        the response deadline (spec 34 §3.4 — Calendar updated). Best-effort."""
        if not offer.response_deadline:
            return
        try:
            from unipaith.schemas.calendar import ReminderCreate
            from unipaith.services.calendar_service import CalendarService

            prog = program.program_name if program else "your program"
            when = datetime.combine(offer.response_deadline, datetime.min.time(), tzinfo=UTC)
            await CalendarService(self.db).create_reminder(
                app.student_id,
                ReminderCreate(
                    title=f"Respond to your {prog} offer",
                    start_at=when,
                    application_id=app.id,
                ),
            )
        except Exception:  # noqa: BLE001
            pass

    @staticmethod
    def _response_state(app: Application, offer: OfferLetter | None) -> str:
        """Coarse student-response state for the institution yield view (§7)."""
        if offer is None:
            if app.decision in ("rejected", "waitlisted", "deferred"):
                return "no_offer"
            return "no_offer"
        if offer.student_response == "accepted":
            return "accepted"
        if offer.student_response == "declined":
            return "declined"
        today = business_today()
        if offer.status == "rescinded":
            return "rescinded"
        if offer.response_deadline and offer.response_deadline < today:
            return "deadline_passed"
        return "awaiting_response"

    async def get_offer_status(self, institution_id: UUID, application_id: UUID) -> dict:
        """Current student-response state for an offer (spec 34 §7)."""
        app = await self._get_application_for_institution(institution_id, application_id)
        res = await self.db.execute(select(OfferLetter).where(OfferLetter.application_id == app.id))
        offer = res.scalar_one_or_none()
        today = business_today()
        deadline = offer.response_deadline if offer else None
        days_remaining = (deadline - today).days if deadline else None
        return {
            "application_id": str(app.id),
            "student_id": str(app.student_id),
            "decision": app.decision,
            "decision_at": app.decision_at,
            "has_offer": offer is not None,
            "offer_id": str(offer.id) if offer else None,
            "offer_type": offer.offer_type if offer else None,
            "offer_status": offer.status if offer else None,
            "student_response": offer.student_response if offer else None,
            "response_at": offer.response_at if offer else None,
            "response_deadline": deadline,
            "days_remaining": days_remaining,
            "deadline_passed": bool(
                deadline
                and days_remaining is not None
                and days_remaining < 0
                and (not offer or offer.student_response not in ("accepted", "declined"))
            ),
            "response_state": self._response_state(app, offer),
        }

    async def _get_offer_for_institution(
        self, institution_id: UUID, offer_id: UUID
    ) -> tuple[OfferLetter, Application]:
        res = await self.db.execute(
            select(OfferLetter, Application)
            .join(Application, OfferLetter.application_id == Application.id)
            .join(Program, Application.program_id == Program.id)
            .where(OfferLetter.id == offer_id, Program.institution_id == institution_id)
        )
        row = res.first()
        if row is None:
            raise NotFoundException("Offer not found")
        return row[0], row[1]

    async def extend_offer_deadline(
        self,
        institution_id: UUID,
        offer_id: UUID,
        new_deadline: date,
        *,
        notify: bool = True,
    ) -> OfferLetter:
        """Push an offer's response deadline out (spec 34 §7). Re-activates a
        deadline-rescinded offer and re-notifies the student."""
        offer, app = await self._get_offer_for_institution(institution_id, offer_id)
        if offer.student_response in ("accepted", "declined"):
            raise BadRequestException("Cannot extend the deadline after the student has responded")
        offer.response_deadline = new_deadline
        if offer.status == "rescinded":
            offer.status = "sent"
        await self.db.flush()
        program = await self.db.get(Program, app.program_id)
        if program is not None:
            await self._attach_institution_names([app])
        offer.plain_language_brief = await self.generate_offer_brief(offer, program)
        offer.brief = (offer.plain_language_brief or {}).get("summary") or self._build_offer_brief(
            offer, program
        )
        await self.db.flush()
        await self.db.refresh(offer)
        if notify:
            prog = program.program_name if program else "your program"
            await self._notify_decision(
                app,
                program,
                "admitted",
                offer,
                custom_message=(
                    f"Your response deadline for the {prog} offer has been extended to "
                    f"{new_deadline.isoformat()}."
                ),
            )
        return offer

    async def rescind_offer(self, institution_id: UUID, offer_id: UUID) -> OfferLetter:
        """Rescind an unanswered offer (spec 34 §8 — deadline-passed policy)."""
        offer, _app = await self._get_offer_for_institution(institution_id, offer_id)
        if offer.student_response in ("accepted", "declined"):
            raise BadRequestException("Cannot rescind an offer the student has answered")
        offer.status = "rescinded"
        await self.db.flush()
        await self.db.refresh(offer)
        return offer

    async def batch_release_decisions(
        self,
        institution_id: UUID,
        items: list[dict],
        *,
        actor_user_id: UUID | None = None,
        notify: bool = True,
    ) -> dict:
        """Per-applicant batch release (spec 34 §5). Each item is
        ``{application_id, decision, decision_notes?, offer?}``. Every applicant
        is audited individually; one failure never aborts the rest."""
        results: list[dict] = []
        success = 0
        for item in items:
            app_id = item.get("application_id")
            try:
                _app, offer = await self.release_decision(
                    institution_id,
                    UUID(str(app_id)),
                    item["decision"],
                    decision_notes=item.get("decision_notes"),
                    actor_user_id=actor_user_id,
                    offer=item.get("offer"),
                    custom_message=item.get("message"),
                    notify=notify,
                )
                success += 1
                results.append(
                    {
                        "application_id": str(app_id),
                        "ok": True,
                        "decision": item["decision"],
                        "offer_id": str(offer.id) if offer else None,
                    }
                )
            except Exception as exc:  # noqa: BLE001 — collect per-item errors
                results.append({"application_id": str(app_id), "ok": False, "error": str(exc)})
        return {
            "results": results,
            "success_count": success,
            "failed_count": len(items) - success,
        }

    async def get_yield_risk_alerts(self, institution_id: UUID, *, within_days: int = 14) -> dict:
        """Admitted students with an unanswered offer, flagged by deadline
        proximity (spec 34 §6 / spec 31 §2). High risk = deadline within 7 days
        or already past; medium otherwise."""
        today = business_today()
        res = await self.db.execute(
            select(OfferLetter, Application, StudentProfile)
            .join(Application, OfferLetter.application_id == Application.id)
            .join(Program, Application.program_id == Program.id)
            .join(StudentProfile, Application.student_id == StudentProfile.id)
            .where(
                Program.institution_id == institution_id,
                OfferLetter.student_response.is_(None),
                OfferLetter.status != "rescinded",
                Application.student_decision.is_(None),
            )
        )
        alerts: list[dict] = []
        for offer, app, profile in res.all():
            deadline = offer.response_deadline
            days = (deadline - today).days if deadline else None
            # Only surface offers approaching/past their deadline, or any
            # unanswered offer once it's older than a week.
            if days is not None:
                if days > within_days:
                    continue
                if days < 0:
                    reason = f"Deadline passed {abs(days)}d ago — no response"
                    risk = "high"
                elif days <= 7:
                    reason = f"No response — deadline in {days}d"
                    risk = "high"
                else:
                    reason = f"No response — deadline in {days}d"
                    risk = "medium"
            else:
                age = (today - offer.created_at.date()) if offer.created_at else None
                if age is None or age.days < 7:
                    continue
                reason = f"No response {age.days}d after offer"
                risk = "medium"
            name = profile.preferred_name or (
                f"{profile.first_name or ''} {profile.last_name or ''}".strip() or None
            )
            alerts.append(
                {
                    "application_id": str(app.id),
                    "student_id": str(app.student_id),
                    "student_name": name,
                    "offer_id": str(offer.id),
                    "reason": reason,
                    "risk_level": risk,
                    "days_remaining": days,
                    "response_deadline": deadline.isoformat() if deadline else None,
                }
            )

        # Highest urgency first (past-due / high risk, then soonest deadline).
        def _sort_key(a: dict) -> tuple:
            dr = a["days_remaining"]
            return (a["risk_level"] != "high", dr is None, dr if dr is not None else 999)

        alerts.sort(key=_sort_key)
        return {"alerts": alerts, "count": len(alerts)}

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
                    "outcomes": _outcomes_from_program(program),
                    "location": _program_location(program),
                    "response_deadline": offer.response_deadline.isoformat()
                    if offer.response_deadline
                    else None,
                    "conditions": offer.conditions,
                }
            )

        indicators = _comparison_indicators(offers_data)
        return {
            "offers": offers_data,
            "indicators": indicators,
            "must_have_constraints": must_haves,
            "count": len(offers_data),
            "advisor_summary": _comparison_advisor_summary(offers_data, indicators),
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
            milestones: list[tuple[str, datetime]] = []
            seen_titles: set[str] = set()

            for action in offer.next_step_actions or []:
                if not isinstance(action, dict) or not action.get("action"):
                    continue
                title = str(action["action"])
                if title in seen_titles:
                    continue
                seen_titles.add(title)
                by_date = action.get("by_date")
                when = now + timedelta(days=30)
                if by_date:
                    try:
                        if isinstance(by_date, str):
                            when = datetime.combine(
                                datetime.fromisoformat(by_date.replace("Z", "+00:00")).date(),
                                datetime.min.time(),
                                tzinfo=UTC,
                            )
                    except ValueError:
                        pass
                milestones.append((title, when))

            deposit_at = (
                datetime.combine(offer.response_deadline, datetime.min.time(), tzinfo=UTC)
                if offer.response_deadline
                else now + timedelta(days=14)
            )
            if "Submit your enrollment deposit" not in seen_titles:
                milestones.append(("Submit your enrollment deposit", deposit_at))
            if "Schedule orientation" not in seen_titles:
                milestones.append(("Schedule orientation", now + timedelta(days=30)))
            if "Apply for housing" not in seen_titles:
                milestones.append(("Apply for housing", now + timedelta(days=30)))
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

        # Spec 39 §2.2/§7 — gate internal submission on the application fee.
        await self._assert_fee_clear_for_submit(app)

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
        await self._post_submit_integrity_scan(app)
        await self._record_apply_outcome(app)
        await self.db.refresh(app)
        return app

    async def _assert_fee_clear_for_submit(self, app: Application) -> None:
        """Spec 39 §2.2/§7 — block internal submission until the application fee
        is paid or waived. Under ``allow_and_reconcile`` (the equity default) a
        *requested* waiver lets submission proceed (``pending_waiver``); under
        ``block_until_approved`` the waiver must be approved first. No-op when
        payments are disabled or the program has no fee."""
        from unipaith.config import settings as _cfg

        if not _cfg.payments_enabled:
            return
        from unipaith.models.payment import Payment
        from unipaith.services.payments import config as fees

        program = await self.db.get(Program, app.program_id)
        institution = await self.db.get(Institution, program.institution_id) if program else None
        fee_cfg = fees.fee_config(institution, program)
        if not fee_cfg["enabled"]:
            return
        waiver_cfg = fees.waiver_config(institution)
        payment = (
            await self.db.execute(
                select(Payment).where(
                    Payment.application_id == app.id,
                    Payment.kind == "application_fee",
                )
            )
        ).scalar_one_or_none()
        if fees.is_fee_clear(payment, waiver_cfg["policy"]):
            return
        raise PaymentRequiredException(
            {
                "message": "Pay the application fee or request a waiver to submit.",
                "amount": round(fee_cfg["amount_cents"] / 100, 2),
                "currency": fee_cfg["currency"],
                "waiver_allowed": True,
            }
        )

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

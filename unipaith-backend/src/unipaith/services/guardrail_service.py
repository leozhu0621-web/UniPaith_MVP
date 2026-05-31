"""
Guardrail service (spec 15 §6.5 / §8, gap G-S4).

Rule-based ``GuardrailScorer``: nudges students away from low-fit / mass
applications by surfacing a fit band, blockers, and a recommended action.
Persists the student's stated intent + rationale on the application.

A future LLM ``GuardrailScorer`` (spec 45) can swap in behind a feature flag;
the rule-based path is the always-available default (mirrors the platform's
"never 5xx — fall back to rule-based" invariant).
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.core.exceptions import BadRequestException, NotFoundException
from unipaith.models.application import Application
from unipaith.models.matching import MatchResult

# Intent enum per spec 15 §6.5 / §9.
INTENT_VALUES = {"career_fit", "back_up", "dream", "cultural_fit", "family_input", "other"}
# Intents that demand a written rationale (spec 15 §6.5).
RATIONALE_REQUIRED_INTENTS = {"back_up", "other"}
RATIONALE_MIN_CHARS = 80
# Fitness is stored 0-1; spec expresses the threshold on a 0-100 scale ("≤ 30").
LOW_FIT_THRESHOLD = 30.0
HIGH_FIT_THRESHOLD = 60.0


class GuardrailService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_application(self, student_id: UUID, application_id: UUID) -> Application:
        result = await self.db.execute(
            select(Application).where(
                Application.id == application_id,
                Application.student_id == student_id,
            )
        )
        app = result.scalar_one_or_none()
        if app is None:
            raise NotFoundException("Application not found")
        return app

    async def _fitness_pct(
        self, student_id: UUID, program_id: UUID, app: Application
    ) -> float | None:
        """Return the program fitness on a 0-100 scale, or None if unscored."""
        result = await self.db.execute(
            select(MatchResult).where(
                MatchResult.student_id == student_id,
                MatchResult.program_id == program_id,
            )
        )
        match = result.scalar_one_or_none()
        raw = None
        if match is not None and match.fitness_score is not None:
            raw = float(match.fitness_score)
        elif app.match_score is not None:
            raw = float(app.match_score)
        if raw is None:
            return None
        # Both fitness_score and the legacy match_score are stored 0-1.
        return round(raw * 100, 1)

    @staticmethod
    def _band(fitness_pct: float | None) -> str:
        if fitness_pct is None:
            return "medium"
        if fitness_pct <= LOW_FIT_THRESHOLD:
            return "low"
        if fitness_pct >= HIGH_FIT_THRESHOLD:
            return "high"
        return "medium"

    async def scan(self, student_id: UUID, application_id: UUID) -> dict:
        """Evaluate guardrails and persist the resulting band + blockers."""
        app = await self._get_application(student_id, application_id)
        fitness_pct = await self._fitness_pct(student_id, app.program_id, app)
        band = self._band(fitness_pct)

        blockers: list[str] = []
        if fitness_pct is not None and fitness_pct <= LOW_FIT_THRESHOLD:
            blockers.append(
                f"Fitness is very low ({round(fitness_pct)}%). "
                "Review your match analysis before committing effort here."
            )
        if not app.intent_picker:
            blockers.append("Set an application intent so we can sanity-check your fit.")
        elif app.intent_picker in RATIONALE_REQUIRED_INTENTS and not _rationale_ok(
            app.intent_rationale
        ):
            blockers.append(
                "Add a rationale (at least 80 characters) explaining why you're applying."
            )

        if band == "low":
            recommended_action = "reconsider"
        elif blockers:
            recommended_action = "review"
        else:
            recommended_action = "proceed"

        app.fit_band = band
        app.guardrail_blockers = blockers
        await self.db.flush()

        return {
            "fit_band": band,
            "fitness_score": fitness_pct,
            "recommended_action": recommended_action,
            "blockers": blockers,
            "is_rule_based": True,
        }

    async def set_intent(
        self,
        student_id: UUID,
        application_id: UUID,
        intent_picker: str | None,
        intent_rationale: str | None,
    ) -> Application:
        """Persist intent + rationale, enforcing the rationale rule (spec 15 §6.5)."""
        app = await self._get_application(student_id, application_id)
        validate_intent(intent_picker, intent_rationale)
        if intent_picker is not None:
            app.intent_picker = intent_picker
        if intent_rationale is not None:
            app.intent_rationale = intent_rationale
        await self.db.flush()
        return app


def _rationale_ok(rationale: str | None) -> bool:
    return bool(rationale and len(rationale.strip()) >= RATIONALE_MIN_CHARS)


def validate_intent(intent_picker: str | None, intent_rationale: str | None) -> None:
    """Raise BadRequestException if intent is invalid or rationale is missing."""
    if intent_picker is None:
        return
    if intent_picker not in INTENT_VALUES:
        raise BadRequestException(
            f"Invalid intent '{intent_picker}'. Allowed: {sorted(INTENT_VALUES)}"
        )
    if intent_picker in RATIONALE_REQUIRED_INTENTS and not _rationale_ok(intent_rationale):
        raise BadRequestException(
            "A rationale of at least 80 characters is required for 'back_up' or 'other' intents."
        )

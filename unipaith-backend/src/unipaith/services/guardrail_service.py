"""Guardrail scan for applications (Spec 15 §6.5)."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.core.exceptions import BadRequestException, NotFoundException
from unipaith.models.application import Application
from unipaith.models.matching import MatchResult

INTENT_VALUES = {"career_fit", "back_up", "dream", "cultural_fit", "family_input", "other"}
RATIONALE_REQUIRED_INTENTS = {"back_up", "other"}
RATIONALE_MIN_CHARS = 80
LOW_FIT_THRESHOLD = 30.0
HIGH_FIT_THRESHOLD = 60.0


def _rationale_ok(rationale: str | None) -> bool:
    return bool(rationale and len(rationale.strip()) >= RATIONALE_MIN_CHARS)


def validate_intent(intent_picker: str | None, intent_rationale: str | None) -> None:
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

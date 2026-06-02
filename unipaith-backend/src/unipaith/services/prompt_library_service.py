"""Spec 42 §3.19–§3.20 / §4.17 — Prompt Library + Story Bank service.

Owns the behavioral-prompt catalog (seeded), the student's responses (with
system-derived STAR/impact flags + §5 provenance on every write), the story
bank, and the §4.17 inference summary (PromptCoach overlay, flag-gated).

The catalog is seeded lazily (seed-if-empty) so prod needs no seed job. Every
write stamps the universal record metadata (§5) and appends to the provenance
chain — the chain is this surface's slice of the §7 audit ledger.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai import prompt_coach
from unipaith.config import settings
from unipaith.core.exceptions import BadRequestException, NotFoundException
from unipaith.models.prompt_library import (
    BehavioralPrompt,
    StudentBehavioralResponse,
    StudentStory,
)
from unipaith.models.student import StudentProfile
from unipaith.services.prompt_library_seed import seed_prompts

logger = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(UTC)


def _prov(event: str, actor: str = "student") -> dict:
    return {"event": event, "timestamp": _now().isoformat(), "actor": actor}


class PromptLibraryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _student_id(self, user_id: UUID) -> UUID:
        sid = await self.db.scalar(
            select(StudentProfile.id).where(StudentProfile.user_id == user_id)
        )
        if sid is None:
            raise NotFoundException("Student profile not found")
        return sid

    # ── Catalog ──────────────────────────────────────────────────────────────
    async def _ensure_seeded(self) -> None:
        """Seed the canonical prompt catalog if empty (idempotent, race-safe)."""
        count = await self.db.scalar(select(func.count()).select_from(BehavioralPrompt))
        if count and count > 0:
            return
        rows = seed_prompts()
        await self.db.execute(
            pg_insert(BehavioralPrompt)
            .values(rows)
            .on_conflict_do_nothing(index_elements=["prompt_key"])
        )
        await self.db.flush()
        logger.info("prompt_library: seeded %d behavioral prompts", len(rows))

    async def list_prompts(
        self, *, intent: str | None = None, channel: str | None = None
    ) -> list[BehavioralPrompt]:
        await self._ensure_seeded()
        stmt = select(BehavioralPrompt).where(BehavioralPrompt.is_active.is_(True))
        if intent:
            stmt = stmt.where(BehavioralPrompt.intent_tag == intent)
        if channel:
            stmt = stmt.where(BehavioralPrompt.target_channel == channel)
        stmt = stmt.order_by(BehavioralPrompt.sort_order)
        return list((await self.db.execute(stmt)).scalars().all())

    async def _prompt(self, prompt_key: str) -> BehavioralPrompt:
        await self._ensure_seeded()
        p = await self.db.scalar(
            select(BehavioralPrompt).where(BehavioralPrompt.prompt_key == prompt_key)
        )
        if p is None:
            raise NotFoundException(f"Unknown prompt: {prompt_key}")
        return p

    # ── Responses (§3.19) ──────────────────────────────────────────────────────
    async def get_responses(self, user_id: UUID) -> list[StudentBehavioralResponse]:
        student_id = await self._student_id(user_id)
        stmt = (
            select(StudentBehavioralResponse)
            .where(StudentBehavioralResponse.student_id == student_id)
            .order_by(StudentBehavioralResponse.updated_at.desc())
        )
        return list((await self.db.execute(stmt)).scalars().all())

    async def upsert_response(
        self,
        user_id: UUID,
        prompt_key: str,
        *,
        response_text: str | None,
        draft_status: str,
        confidence_self_rating: int | None,
        needs_feedback_flag: bool,
        linked_story_id: UUID | None,
    ) -> StudentBehavioralResponse:
        student_id = await self._student_id(user_id)
        prompt = await self._prompt(prompt_key)

        if linked_story_id is not None:
            owns = await self.db.scalar(
                select(StudentStory.id).where(
                    StudentStory.id == linked_story_id,
                    StudentStory.student_id == student_id,
                )
            )
            if owns is None:
                raise BadRequestException("linked_story_id does not belong to you")

        row = await self.db.scalar(
            select(StudentBehavioralResponse).where(
                StudentBehavioralResponse.student_id == student_id,
                StudentBehavioralResponse.prompt_key == prompt_key,
            )
        )
        # System-derived STAR + impact + authenticity (always rule-based, §5).
        analysis = prompt_coach.analyze_response(response_text, prompt.word_limit)
        star = analysis["star"]

        if row is None:
            row = StudentBehavioralResponse(
                student_id=student_id,
                prompt_key=prompt_key,
                version_count=0,
                record_version=0,
                provenance_chain=[],
            )
            self.db.add(row)
            event = "response_created"
        else:
            event = "response_updated"

        row.response_text = response_text
        row.draft_status = draft_status
        row.confidence_self_rating = confidence_self_rating
        row.needs_feedback_flag = needs_feedback_flag
        row.linked_story_id = linked_story_id
        row.last_edited = _now()
        row.version_count = (row.version_count or 0) + 1
        # STAR (system-derived).
        row.star_situation_present = star["situation"]
        row.star_task_present = star["task"]
        row.star_action_present = star["action"]
        row.star_result_present = star["result"]
        row.star_reflection_present = star["reflection"]
        row.impact_metric_present = analysis["impact_metric_present"]
        row.impact_metric_type = analysis["impact_metric_type"]
        row.impact_metric_value_band = analysis["impact_metric_value_band"]
        row.authenticity_confidence_flag = analysis["authenticity_confidence_flag"]
        # §5 record metadata — the response value is student-typed free-text → 70.
        row.source = "student-typed"
        row.confidence = 70 if (response_text or "").strip() else 0
        row.record_version = (row.record_version or 0) + 1
        row.value_normalized = {
            "star": star,
            "star_count": analysis["star_count"],
            "impact_metric_present": analysis["impact_metric_present"],
            "word_count": analysis["word_count"],
            "word_count_compliance": analysis["word_count_compliance"],
            "authenticity_risk_flags": analysis["authenticity_risk_flags"],
        }
        chain = list(row.provenance_chain or [])
        chain.append(_prov(event))
        if star and any(star.values()):
            chain.append(_prov("star_autodetected", actor="system"))
        row.provenance_chain = chain

        await self.db.flush()
        await self.db.refresh(row)
        return row

    # ── Story bank (§3.20) ─────────────────────────────────────────────────────
    async def get_stories(self, user_id: UUID) -> list[StudentStory]:
        student_id = await self._student_id(user_id)
        stmt = (
            select(StudentStory)
            .where(StudentStory.student_id == student_id)
            .order_by(StudentStory.updated_at.desc())
        )
        return list((await self.db.execute(stmt)).scalars().all())

    async def create_story(self, user_id: UUID, cleaned: dict) -> StudentStory:
        student_id = await self._student_id(user_id)
        row = StudentStory(
            student_id=student_id,
            source="student-typed",
            confidence=70,
            record_version=1,
            provenance_chain=[_prov("story_created")],
            **cleaned,
        )
        self.db.add(row)
        await self.db.flush()
        await self.db.refresh(row)
        return row

    async def _own_story(self, student_id: UUID, story_id: UUID) -> StudentStory:
        row = await self.db.scalar(
            select(StudentStory).where(
                StudentStory.id == story_id, StudentStory.student_id == student_id
            )
        )
        if row is None:
            raise NotFoundException("Story not found")
        return row

    async def update_story(self, user_id: UUID, story_id: UUID, cleaned: dict) -> StudentStory:
        student_id = await self._student_id(user_id)
        row = await self._own_story(student_id, story_id)
        for k, v in cleaned.items():
            setattr(row, k, v)
        row.record_version = (row.record_version or 1) + 1
        row.provenance_chain = list(row.provenance_chain or []) + [_prov("story_updated")]
        await self.db.flush()
        await self.db.refresh(row)
        return row

    async def delete_story(self, user_id: UUID, story_id: UUID) -> None:
        student_id = await self._student_id(user_id)
        row = await self._own_story(student_id, story_id)
        # Detach from any responses that referenced it (FK is SET NULL, but flush
        # the in-session rows so the relationship is consistent immediately).
        await self.db.delete(row)
        await self.db.flush()

    # ── Summary (§4.17) ────────────────────────────────────────────────────────
    @staticmethod
    def _resp_dict(r: StudentBehavioralResponse) -> dict:
        return {
            "prompt_key": r.prompt_key,
            "response_text": r.response_text,
            "draft_status": r.draft_status,
            "confidence_self_rating": r.confidence_self_rating,
            "star_situation_present": r.star_situation_present,
            "star_task_present": r.star_task_present,
            "star_action_present": r.star_action_present,
            "star_result_present": r.star_result_present,
            "star_reflection_present": r.star_reflection_present,
            "impact_metric_present": r.impact_metric_present,
        }

    @staticmethod
    def _story_dict(s: StudentStory) -> dict:
        return {
            "id": str(s.id),
            "title": s.title,
            "primary_competency": s.primary_competency,
            "secondary_competency": s.secondary_competency,
            "competency_tags": s.competency_tags or [],
        }

    @staticmethod
    def _prompt_dict(p: BehavioralPrompt) -> dict:
        return {
            "prompt_key": p.prompt_key,
            "title": p.title,
            "intent_tag": p.intent_tag,
            "target_channel": p.target_channel,
            "word_limit": p.word_limit,
        }

    async def summary(self, user_id: UUID) -> dict:
        student_id = await self._student_id(user_id)
        prompts = await self.list_prompts()
        responses = list(
            (
                await self.db.execute(
                    select(StudentBehavioralResponse).where(
                        StudentBehavioralResponse.student_id == student_id
                    )
                )
            )
            .scalars()
            .all()
        )
        stories = list(
            (
                await self.db.execute(
                    select(StudentStory).where(StudentStory.student_id == student_id)
                )
            )
            .scalars()
            .all()
        )

        answered = [r for r in responses if (r.response_text or "").strip()]
        out: dict = {
            "total_prompts": len(prompts),
            "answered_count": len(answered),
            "final_count": sum(1 for r in responses if r.draft_status == "final"),
            "draft_count": sum(1 for r in responses if r.draft_status in ("draft", "revised")),
            "stories_count": len(stories),
            "inference_enabled": settings.ai_prompt_library_v2_enabled,
        }
        # §4.17 inference overlay — PromptCoach (deterministic, never 5xx),
        # gated behind the feature flag like every other AI surface.
        if settings.ai_prompt_library_v2_enabled:
            try:
                overlay = prompt_coach.coach_summary(
                    [self._resp_dict(r) for r in responses],
                    [self._story_dict(s) for s in stories],
                    [self._prompt_dict(p) for p in prompts],
                )
                out.update(overlay)
            except Exception:  # pragma: no cover - defensive; engine is pure
                logger.exception("prompt_coach overlay failed; serving raw counts")
        return out

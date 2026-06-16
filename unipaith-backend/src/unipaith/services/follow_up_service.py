"""Follow-up questions — "Uni has a few questions" after a file import.

`detect` is a deterministic, source-agnostic GapEngine: given the current
profile snapshot and (optionally) a fresh import, it returns a short, ranked
list of gaps worth asking about — ambiguous items, missing high-value fields,
and one reflective "deepen" prompt. `answer` writes a confirmed reply into My
Space. Questions are warm and in Uni's voice via the templated `prompt_hint`;
the flag `ai_material_followups_v2_enabled` gates whether the card appears.

Phase-2 ready: `detect(user_id, None)` scans the profile alone (no import).
"""

from __future__ import annotations

import logging
import re
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

_MAX_QUESTIONS = 5

_TEST_TYPE_MAP = {
    "gre": "GRE",
    "gmat": "GMAT",
    "toefl": "TOEFL",
    "ielts": "IELTS",
    "sat": "SAT",
    "act": "ACT",
    "lsat": "LSAT",
    "mcat": "MCAT",
    "duolingo": "DUOLINGO",
}

_DEG_ABBR = {
    "bachelors": "BS",
    "masters": "MS",
    "phd": "PhD",
    "associate": "AA",
    "high_school": "HS",
    "diploma": "Diploma",
}


def _degree_label(record: dict[str, Any]) -> str:
    """A short subject label for an academic record, e.g. "BS, Business Administration"."""
    parts = [_DEG_ABBR.get(record.get("degree_type"), ""), record.get("field_of_study") or ""]
    return ", ".join(p for p in parts if p)


def _school_label(record: dict[str, Any]) -> str:
    """How a GPA question names the school it's asking about."""
    inst = record.get("institution_name") or "your school"
    deg = _degree_label(record)
    return f"{inst} ({deg})" if deg else inst


class FollowUpService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _student_id(self, user_id: UUID) -> UUID:
        from unipaith.services.student_service import StudentService

        return (await StudentService(self.db)._get_student_profile(user_id)).id

    # ── detect ───────────────────────────────────────────────────────────────
    async def detect(
        self, user_id: UUID, import_result: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        from unipaith.services.student_service import StudentService

        snapshot = await StudentService(self.db).get_full_snapshot(user_id)
        imp = import_result or {}
        ambiguous: list[dict[str, Any]] = []
        missing: list[dict[str, Any]] = []

        # ── ambiguous: imported activities with no stated role ──
        for a in imp.get("activities") or []:
            title = a.get("title")
            if title and not a.get("role"):
                ambiguous.append(
                    {
                        "category": "ambiguous",
                        "target_field": "activity_role",
                        "prompt_hint": f"What was your role in {title}?",
                        "kind": "choice",
                        "options": ["Member", "President", "Founder", "Captain", "Volunteer"],
                        "ref": {"title": title},
                    }
                )
                if len(ambiguous) >= 2:
                    break

        # ── missing high-value fields ──
        # GPA is asked PER SCHOOL (named), so a student with two degrees isn't
        # asked a subjectless "What's your GPA?". Each gap carries a ref so the
        # answer lands on the right academic record. Capped at 2.
        records = imp.get("academic_records") or []
        gpa_gaps = [
            {
                "category": "missing",
                "target_field": "gpa",
                "prompt_hint": f"What was your GPA at {_school_label(r)}? (e.g. 3.8/4.0)",
                "kind": "text",
                "ref": {
                    "institution_name": r.get("institution_name"),
                    "degree_type": r.get("degree_type"),
                    "label": _school_label(r),
                },
            }
            for r in records
            if not r.get("gpa") and r.get("institution_name")
        ]
        missing.extend(gpa_gaps[:2])
        if not (imp.get("test_scores")) and not await self._has_test_scores(user_id):
            missing.append(
                {
                    "category": "missing",
                    "target_field": "test_scores",
                    "prompt_hint": "Any test scores to add?",
                    "kind": "choice",
                    "options": ["GRE", "GMAT", "TOEFL", "IELTS", "SAT", "ACT", "None yet"],
                }
            )
        if not snapshot.get("goals"):
            missing.append(
                {
                    "category": "missing",
                    "target_field": "target_degree",
                    "prompt_hint": "What program or degree are you aiming for?",
                    "kind": "text",
                }
            )

        # ── deepen: one reflective prompt seeding a goal ──
        field = None
        for r in records:
            if r.get("field_of_study"):
                field = r["field_of_study"]
                break
        deepen = [
            {
                "category": "deepen",
                "target_field": "goal",
                "prompt_hint": (
                    f"What's pulling you toward {field}?"
                    if field
                    else "What are you hoping to get out of this next step?"
                ),
                "kind": "text",
            }
        ]

        ranked = ambiguous + missing + deepen
        out: list[dict[str, Any]] = []
        for i, g in enumerate(ranked[:_MAX_QUESTIONS]):
            g["id"] = f"{g['category']}:{g['target_field']}:{i}"
            out.append(g)
        return out

    async def _has_test_scores(self, user_id: UUID) -> bool:
        from unipaith.models.student import TestScore

        sid = await self._student_id(user_id)
        row = (
            await self.db.execute(select(TestScore.id).where(TestScore.student_id == sid).limit(1))
        ).first()
        return row is not None

    # ── answer ───────────────────────────────────────────────────────────────
    async def answer(self, user_id: UUID, gap: dict[str, Any], raw_answer: str) -> dict[str, Any]:
        target = gap.get("target_field")
        text = (raw_answer or "").strip()
        if not text or text.lower() in {"skip", "none yet", "none", "n/a"}:
            return {"applied": False, "target_field": target, "reason": "skipped"}
        try:
            if target == "goal":
                await self._apply_goal(user_id, text)
            elif target == "gpa":
                await self._apply_gpa(user_id, text, gap.get("ref") or {})
            elif target == "test_scores":
                await self._apply_test(user_id, text)
            elif target == "target_degree":
                await self._apply_target_degree(user_id, text)
            elif target == "activity_role":
                await self._apply_activity_role(user_id, gap.get("ref") or {}, text)
            else:
                return {"applied": False, "target_field": target, "reason": "unknown_target"}
        except Exception as exc:
            logger.info("follow-up answer apply failed (%s): %s", target, exc)
            return {"applied": False, "target_field": target, "reason": "error"}
        await self.db.commit()
        return {"applied": True, "target_field": target}

    async def _apply_goal(self, user_id: UUID, text: str) -> None:
        from unipaith.schemas.goals import CreateGoalRequest
        from unipaith.services.goals_service import GoalsService

        await GoalsService(self.db).create_goal(
            user_id, CreateGoalRequest(category="academic", specific=text[:2000], source="manual")
        )

    async def _apply_target_degree(self, user_id: UUID, text: str) -> None:
        from unipaith.schemas.student import UpdateProfileRequest
        from unipaith.services.student_service import StudentService

        await StudentService(self.db).update_profile(
            user_id, UpdateProfileRequest(goals_text=text[:2000])
        )

    async def _apply_gpa(self, user_id: UUID, text: str, ref: dict | None = None) -> None:
        m = re.search(r"\d+(\.\d+)?", text)
        if not m:
            raise ValueError("no number in gpa answer")
        gpa = float(m.group())
        from unipaith.models.student import AcademicRecord
        from unipaith.schemas.student import UpdateAcademicRecordRequest
        from unipaith.services.student_service import StudentService

        sid = await self._student_id(user_id)
        rec = None
        # Target the school the question named, so a two-degree student's answer
        # lands on the right record.
        inst = (ref or {}).get("institution_name")
        if inst:
            rec = (
                await self.db.execute(
                    select(AcademicRecord)
                    .where(
                        AcademicRecord.student_id == sid,
                        AcademicRecord.institution_name == inst,
                    )
                    .limit(1)
                )
            ).scalar_one_or_none()
        if rec is None:
            rec = (
                await self.db.execute(
                    select(AcademicRecord)
                    .where(AcademicRecord.student_id == sid)
                    .order_by(AcademicRecord.start_date.desc())
                    .limit(1)
                )
            ).scalar_one_or_none()
        if rec is None:
            raise ValueError("no academic record to attach gpa")
        await StudentService(self.db).update_academic_record(
            sid, rec.id, UpdateAcademicRecordRequest(gpa=gpa)
        )

    async def _apply_test(self, user_id: UUID, text: str) -> None:
        from unipaith.schemas.student import CreateTestScoreRequest
        from unipaith.services.student_service import StudentService

        low = text.lower()
        test_type = next((v for k, v in _TEST_TYPE_MAP.items() if k in low), None)
        if test_type is None:
            raise ValueError("no recognized test type")
        score_m = re.search(r"\b(\d{2,4})\b", text)
        sid = await self._student_id(user_id)
        await StudentService(self.db).create_test_score(
            sid,
            CreateTestScoreRequest(
                test_type=test_type, total_score=int(score_m.group()) if score_m else None
            ),
        )

    async def _apply_activity_role(self, user_id: UUID, ref: dict, text: str) -> None:
        from unipaith.models.student import Activity

        title = ref.get("title")
        if not title:
            raise ValueError("no activity ref")
        sid = await self._student_id(user_id)
        act = (
            await self.db.execute(
                select(Activity).where(Activity.student_id == sid, Activity.title == title).limit(1)
            )
        ).scalar_one_or_none()
        if act is None:
            raise ValueError("activity not found")
        prefix = f"{text}. "
        act.description = (prefix + (act.description or "")).strip()[:2000]

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

_MAX_QUESTIONS = 12

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
        """Every meaningful gap Uni found, grouped by `section` and ranked by
        priority (lower = asked first). Source-agnostic: `import_result=None`
        scans the profile alone (Phase 2)."""
        from unipaith.services.student_service import StudentService

        snapshot = await StudentService(self.db).get_full_snapshot(user_id)
        imp = import_result or {}
        # (priority, gap) — sorted then capped so the highest-value gaps survive.
        cand: list[tuple[int, dict[str, Any]]] = []

        # ── Activities: imported clubs with no stated role (max 2) ──
        for a in (imp.get("activities") or [])[:2]:
            title = a.get("title")
            if title and not a.get("role"):
                cand.append(
                    (
                        10,
                        {
                            "category": "ambiguous",
                            "section": "Activities",
                            "target_field": "activity_role",
                            "prompt_hint": f"What was your role in {title}?",
                            "kind": "choice",
                            "options": ["Member", "President", "Founder", "Captain", "Volunteer"],
                            "ref": {"title": title},
                        },
                    )
                )

        # ── Education: GPA + relevant courses, PER named school ──
        records = imp.get("academic_records") or []
        for r in records:
            inst = r.get("institution_name")
            if not inst:
                continue
            sl = _school_label(r)
            ref = {"institution_name": inst, "degree_type": r.get("degree_type"), "label": sl}
            if not r.get("gpa"):
                cand.append(
                    (
                        15,
                        {
                            "category": "missing",
                            "section": "Education",
                            "target_field": "gpa",
                            "prompt_hint": f"What was your GPA at {sl}? (e.g. 3.8/4.0)",
                            "kind": "text",
                            "ref": ref,
                        },
                    )
                )
            if not r.get("courses"):
                cand.append(
                    (
                        40,
                        {
                            "category": "missing",
                            "section": "Education",
                            "target_field": "courses",
                            "prompt_hint": f"What were some relevant courses at {inst}?",
                            "kind": "text",
                            "ref": ref,
                        },
                    )
                )
        if not (imp.get("test_scores")) and not await self._has_test_scores(user_id):
            cand.append(
                (
                    20,
                    {
                        "category": "missing",
                        "section": "Education",
                        "target_field": "test_scores",
                        "prompt_hint": "Any test scores to add?",
                        "kind": "choice",
                        "options": ["GRE", "GMAT", "TOEFL", "IELTS", "SAT", "ACT", "None yet"],
                    },
                )
            )

        # ── Experience: hours + compensation per imported role ──
        for w in imp.get("work_experiences") or []:
            role, org = w.get("role_title"), w.get("organization")
            if not (role and org):
                continue
            label = f"{role} at {org}"
            ref = {"role_title": role, "organization": org}
            if not w.get("hours_per_week"):
                cand.append(
                    (
                        30,
                        {
                            "category": "missing",
                            "section": "Experience",
                            "target_field": "work_hours",
                            "prompt_hint": f"About how many hours a week was {label}?",
                            "kind": "text",
                            "ref": ref,
                        },
                    )
                )
            if not w.get("compensation_type"):
                cand.append(
                    (
                        35,
                        {
                            "category": "missing",
                            "section": "Experience",
                            "target_field": "work_compensation",
                            "prompt_hint": f"Was {label} paid, unpaid, or a stipend?",
                            "kind": "choice",
                            "options": ["Paid", "Unpaid", "Stipend"],
                            "ref": ref,
                        },
                    )
                )

        # ── Skills ──
        if not (imp.get("profile") or {}).get("skills"):
            cand.append(
                (
                    25,
                    {
                        "category": "missing",
                        "section": "Skills",
                        "target_field": "skills",
                        "prompt_hint": "What are your strongest skills? (e.g. Python, SQL, Excel)",
                        "kind": "text",
                    },
                )
            )

        # ── Contact: LinkedIn ──
        has_linkedin = any(
            (o.get("platform_type") == "linkedin") for o in (imp.get("online_presence") or [])
        )
        if not has_linkedin:
            cand.append(
                (
                    45,
                    {
                        "category": "missing",
                        "section": "Contact",
                        "target_field": "link",
                        "prompt_hint": "What's your LinkedIn URL?",
                        "kind": "text",
                        "ref": {"platform_type": "linkedin"},
                    },
                )
            )

        # ── About you: one reflective prompt seeding a goal ──
        if not snapshot.get("goals"):
            field = next((r["field_of_study"] for r in records if r.get("field_of_study")), None)
            cand.append(
                (
                    50,
                    {
                        "category": "deepen",
                        "section": "About you",
                        "target_field": "goal",
                        "prompt_hint": (
                            f"What's pulling you toward {field}?"
                            if field
                            else "What are you hoping to get out of this next step?"
                        ),
                        "kind": "text",
                    },
                )
            )

        cand.sort(key=lambda x: x[0])
        out: list[dict[str, Any]] = []
        for i, (_, g) in enumerate(cand[:_MAX_QUESTIONS]):
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
            elif target == "work_hours":
                await self._apply_work_field(user_id, gap.get("ref") or {}, hours=text)
            elif target == "work_compensation":
                await self._apply_work_field(user_id, gap.get("ref") or {}, compensation=text)
            elif target == "courses":
                await self._apply_courses(user_id, gap.get("ref") or {}, text)
            elif target == "skills":
                await self._apply_skills(user_id, text)
            elif target == "link":
                await self._apply_link(user_id, gap.get("ref") or {}, text)
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

    async def _find_work(self, sid: UUID, ref: dict):
        from unipaith.models.student import StudentWorkExperience

        role, org = ref.get("role_title"), ref.get("organization")
        if not (role and org):
            raise ValueError("no work ref")
        return (
            await self.db.execute(
                select(StudentWorkExperience)
                .where(
                    StudentWorkExperience.student_id == sid,
                    StudentWorkExperience.role_title == role,
                    StudentWorkExperience.organization == org,
                )
                .limit(1)
            )
        ).scalar_one_or_none()

    async def _apply_work_field(
        self, user_id: UUID, ref: dict, *, hours: str | None = None, compensation: str | None = None
    ) -> None:
        sid = await self._student_id(user_id)
        work = await self._find_work(sid, ref)
        if work is None:
            raise ValueError("work experience not found")
        if hours is not None:
            m = re.search(r"\d+", hours)
            if m:
                work.hours_per_week = int(m.group())
        if compensation is not None:
            low = compensation.lower()
            comp = (
                "paid"
                if "paid" in low and "unpaid" not in low
                else "unpaid"
                if "unpaid" in low
                else "stipend"
                if "stipend" in low
                else None
            )
            if comp:
                work.compensation_type = comp

    async def _apply_courses(self, user_id: UUID, ref: dict, text: str) -> None:
        from unipaith.models.student import AcademicRecord
        from unipaith.schemas.student import CreateCourseRequest
        from unipaith.services.student_service import StudentService

        sid = await self._student_id(user_id)
        inst = ref.get("institution_name")
        rec = None
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
            raise ValueError("no academic record for courses")
        svc = StudentService(self.db)
        names = [c.strip() for c in re.split(r"[,;\n]", text) if c.strip()][:12]
        for name in names:
            await svc.create_course(
                sid, rec.id, CreateCourseRequest(course_name=name[:255], course_level="college")
            )

    async def _apply_skills(self, user_id: UUID, text: str) -> None:
        from unipaith.schemas.student import UpdateProfileRequest
        from unipaith.services.student_service import StudentService

        svc = StudentService(self.db)
        profile = await svc.get_profile(user_id)
        line = f"Skills: {text.strip()}"
        bio = ((profile.bio_text or "") + "\n" + line).strip() if profile.bio_text else line
        await svc.update_profile(user_id, UpdateProfileRequest(bio_text=bio[:4000]))

    async def _apply_link(self, user_id: UUID, ref: dict, text: str) -> None:
        from unipaith.schemas.student import CreateOnlinePresenceRequest
        from unipaith.services.student_service import StudentService

        url = text.strip()
        if not url:
            raise ValueError("empty link")
        if not url.startswith("http"):
            url = "https://" + url
        platform = ref.get("platform_type") or "other"
        sid = await self._student_id(user_id)
        await StudentService(self.db).create_online_presence(
            sid, CreateOnlinePresenceRequest(platform_type=platform, url=url[:1000])
        )

"""Material ingest service — upload → AI reads → review → confirm into My Space.

``ingest`` parses an uploaded file into a confirm-ready ``proposed`` payload (no
writes). ``apply`` writes the student-confirmed subset into the durable profile,
best-effort per item (one bad item never aborts the rest) with a counts summary.
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import settings
from unipaith.models.material_ingest import MaterialIngest

logger = logging.getLogger(__name__)


def _parse_date(value: Any) -> date | None:
    """Lenient YYYY-MM-DD / YYYY-MM / YYYY → date (first of month/year)."""
    if not value or not isinstance(value, str):
        return None
    s = value.strip()[:10]
    for fmt, pad in (("%Y-%m-%d", s), ("%Y-%m", s[:7]), ("%Y", s[:4])):
        try:
            return datetime.strptime(pad, fmt).date()
        except ValueError:
            continue
    return None


class MaterialIngestService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _student_id(self, user_id: UUID) -> UUID:
        from unipaith.services.student_service import StudentService

        profile = await StudentService(self.db)._get_student_profile(user_id)
        return profile.id

    # ── parse ──────────────────────────────────────────────────────────────
    async def ingest(
        self, user_id: UUID, *, filename: str | None, mime_type: str | None, data: bytes
    ) -> MaterialIngest:
        student_id = await self._student_id(user_id)
        proposed: dict[str, Any] | None = None
        error: str | None = None
        if settings.ai_material_ingest_v2_enabled:
            from unipaith.ai.material_ingest import MaterialIngestAgent

            proposed = await MaterialIngestAgent().read(
                filename=filename, mime_type=mime_type, data=data, student_id=student_id
            )
            if proposed is None:
                error = "Could not read this file automatically — you can add the details by hand."
        else:
            error = "Material reading is not enabled — please enter the details manually."

        row = MaterialIngest(
            student_id=student_id,
            filename=filename,
            mime_type=mime_type,
            status="parsed" if proposed is not None else "failed",
            proposed=proposed,
            error=error,
        )
        self.db.add(row)
        await self.db.commit()
        await self.db.refresh(row)
        return row

    async def list_ingests(self, user_id: UUID, *, limit: int = 20) -> list[MaterialIngest]:
        student_id = await self._student_id(user_id)
        rows = await self.db.execute(
            select(MaterialIngest)
            .where(MaterialIngest.student_id == student_id)
            .order_by(MaterialIngest.created_at.desc())
            .limit(limit)
        )
        return list(rows.scalars().all())

    # ── apply ──────────────────────────────────────────────────────────────
    async def apply(
        self, user_id: UUID, ingest_id: UUID, selection: dict[str, Any]
    ) -> dict[str, Any]:
        """Write the confirmed selection into My Space. Best-effort per item."""
        student_id = await self._student_id(user_id)
        row = (
            await self.db.execute(
                select(MaterialIngest).where(
                    MaterialIngest.id == ingest_id, MaterialIngest.student_id == student_id
                )
            )
        ).scalar_one_or_none()
        if row is None:
            from unipaith.core.exceptions import NotFoundException

            raise NotFoundException("Material ingest not found")

        counts: dict[str, int] = {}
        skipped: dict[str, int] = {}

        await self._apply_profile(user_id, selection.get("profile") or {}, counts, skipped)
        await self._apply_academics(
            student_id, selection.get("academic_records") or [], counts, skipped
        )
        await self._apply_tests(student_id, selection.get("test_scores") or [], counts, skipped)
        await self._apply_activities(student_id, selection.get("activities") or [], counts, skipped)
        await self._apply_work(student_id, selection.get("work_experiences") or [], counts, skipped)
        await self._apply_goals(user_id, selection.get("goals") or [], counts, skipped)
        await self._apply_needs(user_id, selection.get("needs") or [], counts, skipped)
        await self._apply_identity(user_id, selection.get("identity") or {}, counts, skipped)

        row.status = "applied"
        row.applied_at = datetime.now().astimezone()
        row.applied_summary = {"counts": counts, "skipped": skipped}
        await self.db.commit()
        return {"counts": counts, "skipped": skipped}

    # ── per-domain writers (each best-effort) ────────────────────────────────
    async def _apply_profile(self, user_id, profile, counts, skipped) -> None:
        if not profile:
            return
        from unipaith.schemas.student import UpdateProfileRequest
        from unipaith.services.student_service import StudentService

        allowed = {"first_name", "last_name", "bio_text", "country_of_residence"}
        data = {k: v for k, v in profile.items() if k in allowed and v}
        if not data:
            return
        try:
            await StudentService(self.db).update_profile(user_id, UpdateProfileRequest(**data))
            counts["profile_fields"] = len(data)
        except Exception as exc:
            logger.info("material apply profile skipped: %s", exc)
            skipped["profile"] = skipped.get("profile", 0) + 1

    async def _apply_academics(self, student_id, records, counts, skipped) -> None:
        if not records:
            return
        from unipaith.schemas.student import CreateAcademicRecordRequest
        from unipaith.services.student_service import StudentService

        svc = StudentService(self.db)
        for r in records:
            start = _parse_date(r.get("start_date")) or _parse_date(r.get("end_date"))
            if start is None:
                skipped["academic_records"] = skipped.get("academic_records", 0) + 1
                continue
            try:
                req = CreateAcademicRecordRequest(
                    institution_name=str(r["institution_name"])[:255],
                    degree_type=r["degree_type"],
                    field_of_study=r.get("field_of_study"),
                    gpa=r.get("gpa"),
                    gpa_scale=r.get("gpa_scale"),
                    honors=r.get("honors"),
                    start_date=start,
                    end_date=_parse_date(r.get("end_date")),
                    is_current=bool(r.get("is_current", False)),
                )
                await svc.create_academic_record(student_id, req)
                counts["academic_records"] = counts.get("academic_records", 0) + 1
            except Exception as exc:
                logger.info("material apply academic skipped: %s", exc)
                skipped["academic_records"] = skipped.get("academic_records", 0) + 1

    async def _apply_tests(self, student_id, scores, counts, skipped) -> None:
        if not scores:
            return
        from unipaith.schemas.student import CreateTestScoreRequest
        from unipaith.services.student_service import StudentService

        svc = StudentService(self.db)
        for s in scores:
            try:
                req = CreateTestScoreRequest(
                    test_type=s["test_type"],
                    total_score=s.get("total_score"),
                    test_date=_parse_date(s.get("test_date")),
                )
                await svc.create_test_score(student_id, req)
                counts["test_scores"] = counts.get("test_scores", 0) + 1
            except Exception as exc:
                logger.info("material apply test skipped: %s", exc)
                skipped["test_scores"] = skipped.get("test_scores", 0) + 1

    async def _apply_activities(self, student_id, activities, counts, skipped) -> None:
        if not activities:
            return
        from unipaith.schemas.student import CreateActivityRequest
        from unipaith.services.student_service import StudentService

        svc = StudentService(self.db)
        for a in activities:
            try:
                req = CreateActivityRequest(
                    activity_type=a["activity_type"],
                    title=str(a["title"])[:255],
                    organization=a.get("organization"),
                    description=a.get("description"),
                    start_date=_parse_date(a.get("start_date")),
                    end_date=_parse_date(a.get("end_date")),
                    hours_per_week=a.get("hours_per_week"),
                )
                await svc.create_activity(student_id, req)
                counts["activities"] = counts.get("activities", 0) + 1
            except Exception as exc:
                logger.info("material apply activity skipped: %s", exc)
                skipped["activities"] = skipped.get("activities", 0) + 1

    async def _apply_work(self, student_id, work, counts, skipped) -> None:
        if not work:
            return
        from unipaith.schemas.student import CreateWorkExperienceRequest
        from unipaith.services.student_service import StudentService

        svc = StudentService(self.db)
        for w in work:
            try:
                req = CreateWorkExperienceRequest(
                    experience_type=w["experience_type"],
                    organization=str(w["organization"])[:255],
                    role_title=str(w["role_title"])[:255],
                    description=w.get("description"),
                    start_date=_parse_date(w.get("start_date")),
                    end_date=_parse_date(w.get("end_date")),
                    is_current=bool(w.get("is_current", False)),
                )
                await svc.create_work_experience(student_id, req)
                counts["work_experiences"] = counts.get("work_experiences", 0) + 1
            except Exception as exc:
                logger.info("material apply work skipped: %s", exc)
                skipped["work_experiences"] = skipped.get("work_experiences", 0) + 1

    async def _apply_goals(self, user_id, goals, counts, skipped) -> None:
        if not goals:
            return
        from unipaith.schemas.goals import CreateGoalRequest
        from unipaith.services.goals_service import GoalsService

        svc = GoalsService(self.db)
        for g in goals:
            try:
                req = CreateGoalRequest(
                    category=g["category"],
                    specific=str(g["specific"])[:2000],
                    measurable=g.get("measurable"),
                    time_bound=_parse_date(g.get("time_bound")),
                    source="manual",
                )
                await svc.create_goal(user_id, req)
                counts["goals"] = counts.get("goals", 0) + 1
            except Exception as exc:
                logger.info("material apply goal skipped: %s", exc)
                skipped["goals"] = skipped.get("goals", 0) + 1

    async def _apply_needs(self, user_id, needs, counts, skipped) -> None:
        if not needs:
            return
        from unipaith.schemas.needs import CreateNeedRequest
        from unipaith.services.needs_service import NeedsService

        svc = NeedsService(self.db)
        for n in needs:
            try:
                req = CreateNeedRequest(
                    maslow_level=n["maslow_level"],
                    need_type=str(n["need_type"])[:120],
                    signal=str(n["signal"])[:4000],
                    severity=n["severity"],
                    source="manual",
                )
                await svc.create_need(user_id, req)
                counts["needs"] = counts.get("needs", 0) + 1
            except Exception as exc:
                logger.info("material apply need skipped: %s", exc)
                skipped["needs"] = skipped.get("needs", 0) + 1

    async def _apply_identity(self, user_id, identity, counts, skipped) -> None:
        if not identity:
            return
        from unipaith.schemas.identity import UpsertIdentityRequest
        from unipaith.services.identity_service import IdentityService

        payload: dict[str, Any] = {}
        if identity.get("core_values"):
            payload["core_values"] = [
                {
                    "value": str(v.get("value"))[:200],
                    "evidence": str(v.get("evidence") or v.get("value") or "")[:4000],
                }
                for v in identity["core_values"]
                if v.get("value")
            ]
        if identity.get("worldview"):
            payload["worldview"] = [
                {
                    "belief": str(v.get("belief"))[:400],
                    "context": str(v.get("context") or v.get("belief") or "")[:4000],
                }
                for v in identity["worldview"]
                if v.get("belief")
            ]
        if identity.get("self_awareness"):
            payload["self_awareness"] = [
                {"insight": str(v.get("insight"))[:400]}
                for v in identity["self_awareness"]
                if v.get("insight")
            ]
        if not payload:
            return
        try:
            await IdentityService(self.db).upsert(user_id, UpsertIdentityRequest(**payload))
            counts["identity"] = sum(len(v) for v in payload.values())
        except Exception as exc:
            logger.info("material apply identity skipped: %s", exc)
            skipped["identity"] = skipped.get("identity", 0) + 1

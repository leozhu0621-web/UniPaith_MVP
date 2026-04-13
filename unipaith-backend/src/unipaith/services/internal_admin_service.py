from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.core.data_safety import assert_core_role_coverage, ensure_can_deactivate_user
from unipaith.core.exceptions import BadRequestException, NotFoundException
from unipaith.models.admin_audit_event import AdminAuditEvent
from unipaith.models.application import Application
from unipaith.models.crawler import CrawlJob
from unipaith.models.engagement import StudentEngagementSignal
from unipaith.models.institution import Institution, Program
from unipaith.models.knowledge import CrawlFrontier, KnowledgeDocument
from unipaith.models.matching import Embedding, MatchResult
from unipaith.models.pipeline import PipelineStageSnapshot
from unipaith.models.student import RecommendationRequest, StudentProfile
from unipaith.models.user import User, UserRole


@dataclass(slots=True)
class UserListResult:
    items: list[dict]
    total: int
    page: int
    page_size: int


class InternalAdminService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_platform_stats(self) -> dict:
        students = (
            await self.db.execute(
                select(func.count()).select_from(User).where(User.role == UserRole.student)
            )
        ).scalar_one()
        institutions = (
            await self.db.execute(select(func.count()).select_from(Institution))
        ).scalar_one()
        programs = (
            await self.db.execute(
                select(func.count()).select_from(Program).where(Program.is_published.is_(True))
            )
        ).scalar_one()
        applications = (
            await self.db.execute(select(func.count()).select_from(Application))
        ).scalar_one()

        return {
            "total_students": students,
            "total_institutions": institutions,
            "published_programs": programs,
            "total_applications": applications,
        }

    async def list_users(
        self,
        role: str | None,
        q: str | None,
        is_active: bool | None,
        page: int,
        page_size: int,
    ) -> UserListResult:
        stmt = (
            select(
                User,
                Institution.id.label("institution_id"),
                Institution.is_verified.label("institution_verified"),
            )
            .outerjoin(Institution, Institution.admin_user_id == User.id)
            .order_by(User.created_at.desc())
        )
        if role:
            try:
                role_enum = UserRole(role)
            except ValueError as exc:
                raise BadRequestException("Invalid role filter") from exc
            stmt = stmt.where(User.role == role_enum)
        if q:
            stmt = stmt.where(User.email.ilike(f"%{q.strip()}%"))
        if is_active is not None:
            stmt = stmt.where(User.is_active.is_(is_active))

        total = (
            await self.db.execute(select(func.count()).select_from(stmt.subquery()))
        ).scalar_one()

        results = await self.db.execute(stmt.offset((page - 1) * page_size).limit(page_size))
        rows = results.all()

        return UserListResult(
            items=[
                {
                    "id": str(row.User.id),
                    "email": row.User.email,
                    "role": row.User.role.value,
                    "is_active": row.User.is_active,
                    "created_at": (
                        row.User.created_at.isoformat() if row.User.created_at else None
                    ),
                    "institution_id": (str(row.institution_id) if row.institution_id else None),
                    "institution_verified": row.institution_verified,
                }
                for row in rows
            ],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def set_user_active(
        self,
        user_id: UUID,
        active: bool,
        actor_user_id: UUID | None = None,
        reason: str | None = None,
    ) -> User:
        result = await self.db.execute(select(User).where(User.id == user_id))
        target = result.scalar_one_or_none()
        if not target:
            raise NotFoundException("User not found")

        if not active:
            await ensure_can_deactivate_user(self.db, target)

        target.is_active = active
        await self.db.flush()
        await assert_core_role_coverage(self.db)
        await self._append_admin_audit(
            actor_user_id=actor_user_id,
            action="user_activate" if active else "user_deactivate",
            entity_type="user",
            entity_id=str(target.id),
            payload={
                "email": target.email,
                "role": target.role.value,
                "active": target.is_active,
                "reason": reason,
            },
        )
        return target

    async def verify_institution(
        self,
        institution_id: UUID,
        actor_user_id: UUID | None = None,
        reason: str | None = None,
    ) -> Institution:
        result = await self.db.execute(select(Institution).where(Institution.id == institution_id))
        institution = result.scalar_one_or_none()
        if not institution:
            raise NotFoundException("Institution not found")
        institution.is_verified = True
        await self.db.flush()
        await self._append_admin_audit(
            actor_user_id=actor_user_id,
            action="institution_verify",
            entity_type="institution",
            entity_id=str(institution.id),
            payload={
                "name": institution.name,
                "verified": institution.is_verified,
                "reason": reason,
            },
        )
        return institution

    async def bulk_set_users_active(
        self,
        user_ids: list[UUID],
        active: bool,
        actor_user_id: UUID | None = None,
        reason: str | None = None,
    ) -> dict:
        requested_ids = list(dict.fromkeys(user_ids))
        if not requested_ids:
            raise BadRequestException("user_ids cannot be empty")

        result = await self.db.execute(select(User).where(User.id.in_(requested_ids)))
        targets = {u.id: u for u in result.scalars().all()}

        updated_user_ids: list[str] = []
        for user_id in requested_ids:
            user = targets.get(user_id)
            if user is None:
                continue
            if active is False:
                await ensure_can_deactivate_user(self.db, user)
            user.is_active = active
            updated_user_ids.append(str(user.id))

        await self.db.flush()
        await assert_core_role_coverage(self.db)
        await self._append_admin_audit(
            actor_user_id=actor_user_id,
            action="users_bulk_activate" if active else "users_bulk_deactivate",
            entity_type="user_bulk",
            entity_id="bulk",
            payload={
                "requested_user_ids": [str(user_id) for user_id in requested_ids],
                "updated_user_ids": updated_user_ids,
                "not_found_user_ids": [
                    str(user_id) for user_id in requested_ids if user_id not in targets
                ],
                "active": active,
                "reason": reason,
            },
        )
        return {
            "requested_count": len(requested_ids),
            "updated_count": len(updated_user_ids),
            "updated_user_ids": updated_user_ids,
            "not_found_user_ids": [
                str(user_id) for user_id in requested_ids if user_id not in targets
            ],
        }

    async def bulk_verify_institutions(
        self,
        institution_ids: list[UUID],
        actor_user_id: UUID | None = None,
        reason: str | None = None,
    ) -> dict:
        requested_ids = list(dict.fromkeys(institution_ids))
        if not requested_ids:
            raise BadRequestException("institution_ids cannot be empty")

        result = await self.db.execute(select(Institution).where(Institution.id.in_(requested_ids)))
        targets = {inst.id: inst for inst in result.scalars().all()}

        verified_ids: list[str] = []
        for institution_id in requested_ids:
            inst = targets.get(institution_id)
            if inst is None:
                continue
            inst.is_verified = True
            verified_ids.append(str(inst.id))

        await self.db.flush()
        await self._append_admin_audit(
            actor_user_id=actor_user_id,
            action="institutions_bulk_verify",
            entity_type="institution_bulk",
            entity_id="bulk",
            payload={
                "requested_institution_ids": [
                    str(institution_id) for institution_id in requested_ids
                ],
                "verified_institution_ids": verified_ids,
                "not_found_institution_ids": [
                    str(institution_id)
                    for institution_id in requested_ids
                    if institution_id not in targets
                ],
                "reason": reason,
            },
        )
        return {
            "requested_count": len(requested_ids),
            "verified_count": len(verified_ids),
            "verified_institution_ids": verified_ids,
            "not_found_institution_ids": [
                str(institution_id)
                for institution_id in requested_ids
                if institution_id not in targets
            ],
        }

    async def list_admin_audit_events(
        self,
        limit: int = 50,
        entity_type: str | None = None,
    ) -> list[dict]:
        stmt = select(AdminAuditEvent).order_by(AdminAuditEvent.created_at.desc()).limit(limit)
        if entity_type:
            stmt = stmt.where(AdminAuditEvent.entity_type == entity_type)
        result = await self.db.execute(stmt)
        events = result.scalars().all()
        return [
            {
                "id": str(event.id),
                "actor_user_id": str(event.actor_user_id) if event.actor_user_id else None,
                "action": event.action,
                "entity_type": event.entity_type,
                "entity_id": event.entity_id,
                "payload_json": event.payload_json,
                "created_at": event.created_at.isoformat() if event.created_at else None,
            }
            for event in events
        ]

    async def get_database_health(self) -> dict:
        db_timer = time.monotonic()
        await self.db.execute(select(func.count()).select_from(User))
        db_latency_ms = round((time.monotonic() - db_timer) * 1000, 1)

        total_tables = 6
        total_users = int(await self.db.scalar(select(func.count()).select_from(User)) or 0)
        total_institutions = int(
            await self.db.scalar(select(func.count()).select_from(Institution)) or 0
        )
        total_programs = int(await self.db.scalar(select(func.count()).select_from(Program)) or 0)
        total_applications = int(
            await self.db.scalar(select(func.count()).select_from(Application)) or 0
        )
        total_matches = int(
            await self.db.scalar(select(func.count()).select_from(MatchResult)) or 0
        )
        total_embeddings = int(
            await self.db.scalar(select(func.count()).select_from(Embedding)) or 0
        )

        failed_jobs_24h = int(
            await self.db.scalar(
                select(func.count())
                .select_from(CrawlJob)
                .where(
                    CrawlJob.status == "failed",
                    CrawlJob.created_at
                    >= datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0),
                )
            )
            or 0
        )

        latest_job_at = await self.db.scalar(
            select(func.max(CrawlJob.created_at)).select_from(CrawlJob)
        )
        latest_admin_action = await self.db.scalar(
            select(func.max(AdminAuditEvent.created_at)).select_from(AdminAuditEvent)
        )

        return {
            "api_reachable": True,
            "database": {
                "status": "healthy" if db_latency_ms < 1500 else "degraded",
                "latency_ms": db_latency_ms,
            },
            "jobs": {
                "recent_failed_24h": failed_jobs_24h,
                "last_job_at": latest_job_at.isoformat() if latest_job_at else None,
            },
            "footprint": {
                "tracked_entities": total_tables,
                "users": total_users,
                "institutions": total_institutions,
                "programs": total_programs,
                "applications": total_applications,
                "matches": total_matches,
                "embeddings": total_embeddings,
            },
            "last_admin_action_at": (
                latest_admin_action.isoformat() if latest_admin_action else None
            ),
            "generated_at": datetime.now(UTC).isoformat(),
        }

    async def get_database_quality(
        self,
        scope: str | None = None,
        limit: int = 20,
    ) -> dict:
        scopes = (
            [scope]
            if scope
            else [
                "users",
                "institutions",
                "programs",
                "applications",
                "matches",
                "embeddings",
            ]
        )
        items: list[dict] = []

        for entity in scopes:
            if entity == "users":
                missing_count = int(
                    await self.db.scalar(
                        select(func.count())
                        .select_from(User)
                        .where((User.email.is_(None)) | (User.email == ""))
                    )
                    or 0
                )
                duplicate_count = await self._count_duplicate_groups(
                    select(User.email)
                    .where(User.email.is_not(None))
                    .group_by(User.email)
                    .having(func.count() > 1)
                )
                invalid_count = int(
                    await self.db.scalar(
                        select(func.count()).select_from(User).where(User.role.is_(None))
                    )
                    or 0
                )
            elif entity == "institutions":
                missing_count = int(
                    await self.db.scalar(
                        select(func.count())
                        .select_from(Institution)
                        .where(
                            (Institution.name.is_(None))
                            | (Institution.name == "")
                            | (Institution.country.is_(None))
                            | (Institution.country == "")
                        )
                    )
                    or 0
                )
                duplicate_count = await self._count_duplicate_groups(
                    select(Institution.name, Institution.country)
                    .group_by(Institution.name, Institution.country)
                    .having(func.count() > 1)
                )
                invalid_count = int(
                    await self.db.scalar(
                        select(func.count())
                        .select_from(Institution)
                        .where(Institution.is_verified.is_(None))
                    )
                    or 0
                )
            elif entity == "programs":
                missing_count = int(
                    await self.db.scalar(
                        select(func.count())
                        .select_from(Program)
                        .where((Program.program_name.is_(None)) | (Program.program_name == ""))
                    )
                    or 0
                )
                duplicate_count = await self._count_duplicate_groups(
                    select(Program.institution_id, Program.program_name)
                    .group_by(Program.institution_id, Program.program_name)
                    .having(func.count() > 1)
                )
                invalid_count = int(
                    await self.db.scalar(
                        select(func.count())
                        .select_from(Program)
                        .where(Program.degree_type.is_(None))
                    )
                    or 0
                )
            elif entity == "applications":
                missing_count = int(
                    await self.db.scalar(
                        select(func.count())
                        .select_from(Application)
                        .where(
                            (Application.student_id.is_(None)) | (Application.program_id.is_(None))
                        )
                    )
                    or 0
                )
                duplicate_count = await self._count_duplicate_groups(
                    select(Application.student_id, Application.program_id)
                    .group_by(Application.student_id, Application.program_id)
                    .having(func.count() > 1)
                )
                invalid_count = int(
                    await self.db.scalar(
                        select(func.count())
                        .select_from(Application)
                        .where(Application.status.is_(None))
                    )
                    or 0
                )
            elif entity == "matches":
                missing_count = int(
                    await self.db.scalar(
                        select(func.count())
                        .select_from(MatchResult)
                        .where(
                            (MatchResult.student_id.is_(None)) | (MatchResult.program_id.is_(None))
                        )
                    )
                    or 0
                )
                duplicate_count = await self._count_duplicate_groups(
                    select(MatchResult.student_id, MatchResult.program_id)
                    .group_by(MatchResult.student_id, MatchResult.program_id)
                    .having(func.count() > 1)
                )
                invalid_count = int(
                    await self.db.scalar(
                        select(func.count())
                        .select_from(MatchResult)
                        .where(MatchResult.match_score.is_(None))
                    )
                    or 0
                )
            elif entity == "embeddings":
                missing_count = int(
                    await self.db.scalar(
                        select(func.count())
                        .select_from(Embedding)
                        .where(Embedding.embedding.is_(None))
                    )
                    or 0
                )
                duplicate_count = await self._count_duplicate_groups(
                    select(Embedding.entity_type, Embedding.entity_id)
                    .group_by(Embedding.entity_type, Embedding.entity_id)
                    .having(func.count() > 1)
                )
                invalid_count = int(
                    await self.db.scalar(
                        select(func.count())
                        .select_from(Embedding)
                        .where((Embedding.entity_type.is_(None)) | (Embedding.entity_type == ""))
                    )
                    or 0
                )
            else:
                continue

            risk_score = (duplicate_count * 4) + (missing_count * 2) + (invalid_count * 3)
            severity = "high" if risk_score >= 25 else "medium" if risk_score >= 8 else "low"
            if duplicate_count > 0:
                recommendation = "run_dedupe"
            elif (missing_count + invalid_count) > 0:
                recommendation = "run_repair"
            else:
                recommendation = "monitor"
            items.append(
                {
                    "entity": entity,
                    "missing_count": missing_count,
                    "duplicate_count": duplicate_count,
                    "invalid_count": invalid_count,
                    "risk_score": risk_score,
                    "severity": severity,
                    "recommended_action": recommendation,
                }
            )

        ranked = sorted(items, key=lambda item: item["risk_score"], reverse=True)[:limit]
        return {
            "items": ranked,
            "generated_at": datetime.now(UTC).isoformat(),
        }

    async def get_database_recommendations(self, limit: int = 10) -> dict:
        quality = await self.get_database_quality(limit=50)
        recommendations: list[dict] = []

        for item in quality["items"]:
            if item["recommended_action"] == "monitor":
                continue
            recommendations.append(
                {
                    "entity": item["entity"],
                    "action": item["recommended_action"],
                    "priority_score": item["risk_score"],
                    "reason": (
                        f"{item['duplicate_count']} duplicate groups, "
                        f"{item['missing_count']} missing, {item['invalid_count']} invalid"
                    ),
                    "auto_generated": True,
                }
            )
        return {
            "items": recommendations[:limit],
            "generated_at": datetime.now(UTC).isoformat(),
        }

    async def get_database_jobs(self, limit: int = 20) -> dict:
        job_rows = await self.db.execute(
            select(
                CrawlJob.id,
                CrawlJob.status,
                CrawlJob.pages_crawled,
                CrawlJob.items_extracted,
                CrawlJob.items_ingested,
                CrawlJob.error_log,
                CrawlJob.created_at,
                CrawlJob.completed_at,
            )
            .order_by(CrawlJob.created_at.desc())
            .limit(limit)
        )
        action_rows = await self.db.execute(
            select(AdminAuditEvent)
            .where(AdminAuditEvent.action.like("database_%"))
            .order_by(AdminAuditEvent.created_at.desc())
            .limit(limit)
        )
        return {
            "crawl_jobs": [
                {
                    "id": str(row[0]),
                    "status": row[1],
                    "pages_crawled": row[2],
                    "items_extracted": row[3],
                    "items_ingested": row[4],
                    "error_log": row[5],
                    "created_at": row[6].isoformat() if row[6] else None,
                    "completed_at": row[7].isoformat() if row[7] else None,
                }
                for row in job_rows.all()
            ],
            "actions": [
                {
                    "id": str(event.id),
                    "action": event.action,
                    "entity_type": event.entity_type,
                    "entity_id": event.entity_id,
                    "payload_json": event.payload_json,
                    "created_at": event.created_at.isoformat() if event.created_at else None,
                }
                for event in action_rows.scalars().all()
            ],
        }

    async def run_database_dedupe_action(
        self,
        scope: str = "all",
        dry_run: bool = True,
        reason: str | None = None,
        actor_user_id: UUID | None = None,
    ) -> dict:
        quality = await self.get_database_quality(scope=None if scope == "all" else scope, limit=50)
        candidate_duplicates = sum(item["duplicate_count"] for item in quality["items"])
        rollback_ref = f"rollback:{uuid.uuid4()}"
        result = {
            "scope": scope,
            "dry_run": dry_run,
            "candidate_duplicates": candidate_duplicates,
            "deduped_records": 0 if dry_run else 0,
            "rollback": {
                "reference": rollback_ref,
                "can_rollback": False,
                "mode": "metadata_only",
            },
            "executed_at": datetime.now(UTC).isoformat(),
        }
        await self._append_admin_audit(
            actor_user_id=actor_user_id,
            action="database_dedupe_run",
            entity_type="database",
            entity_id=scope,
            payload={
                **result,
                "reason": reason,
            },
        )
        return result

    async def run_database_repair_action(
        self,
        scope: str = "all",
        dry_run: bool = True,
        reason: str | None = None,
        actor_user_id: UUID | None = None,
    ) -> dict:
        quality = await self.get_database_quality(scope=None if scope == "all" else scope, limit=50)
        candidate_repairs = sum(
            item["missing_count"] + item["invalid_count"] for item in quality["items"]
        )
        rollback_ref = f"rollback:{uuid.uuid4()}"
        result = {
            "scope": scope,
            "dry_run": dry_run,
            "candidate_repairs": candidate_repairs,
            "repaired_records": 0 if dry_run else 0,
            "rollback": {
                "reference": rollback_ref,
                "can_rollback": False,
                "mode": "metadata_only",
            },
            "executed_at": datetime.now(UTC).isoformat(),
        }
        await self._append_admin_audit(
            actor_user_id=actor_user_id,
            action="database_repair_run",
            entity_type="database",
            entity_id=scope,
            payload={
                **result,
                "reason": reason,
            },
        )
        return result

    async def _count_duplicate_groups(self, grouped_stmt) -> int:  # type: ignore[no-untyped-def]
        return int(
            await self.db.scalar(select(func.count()).select_from(grouped_stmt.subquery())) or 0
        )

    async def _append_admin_audit(
        self,
        actor_user_id: UUID | None,
        action: str,
        entity_type: str,
        entity_id: str,
        payload: dict | None = None,
    ) -> None:
        self.db.add(
            AdminAuditEvent(
                actor_user_id=actor_user_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                payload_json=payload or {},
            )
        )
        await self.db.flush()

    async def get_dashboard_stats(self) -> dict:
        total_users = await self.db.scalar(select(func.count(User.id)))
        student_users = await self.db.scalar(
            select(func.count(User.id)).where(User.role == UserRole.student)
        )
        institution_users = await self.db.scalar(
            select(func.count(User.id)).where(User.role == UserRole.institution_admin)
        )
        total_profiles = await self.db.scalar(select(func.count(StudentProfile.id)))
        total_institutions = await self.db.scalar(select(func.count(Institution.id)))
        total_programs = await self.db.scalar(select(func.count(Program.id)))
        published_programs = await self.db.scalar(
            select(func.count(Program.id)).where(Program.is_published == True)  # noqa: E712
        )
        total_applications = await self.db.scalar(select(func.count(Application.id)))

        app_by_status: dict[str, int] = {}
        for status in ["draft", "submitted", "under_review", "interview", "decision_made"]:
            count = await self.db.scalar(
                select(func.count(Application.id)).where(Application.status == status)
            )
            app_by_status[status] = int(count or 0)

        app_by_decision: dict[str, int] = {}
        for decision in ["admitted", "rejected", "waitlisted", "deferred"]:
            count = await self.db.scalar(
                select(func.count(Application.id)).where(Application.decision == decision)
            )
            app_by_decision[decision] = int(count or 0)

        total_matches = await self.db.scalar(select(func.count(MatchResult.id)))
        avg_match_score = await self.db.scalar(select(func.avg(MatchResult.match_score)))
        total_engagements = await self.db.scalar(select(func.count(StudentEngagementSignal.id)))

        recent_users_result = await self.db.execute(
            select(User.id, User.email, User.role, User.created_at)
            .order_by(User.created_at.desc())
            .limit(10)
        )
        recent_users = [
            {
                "id": str(row.id),
                "email": row.email,
                "role": row.role.value,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in recent_users_result.all()
        ]

        recent_apps_result = await self.db.execute(
            select(
                Application.id,
                Application.student_id,
                Application.program_id,
                Application.status,
                Application.decision,
                Application.created_at,
            )
            .order_by(Application.created_at.desc())
            .limit(10)
        )
        recent_apps = [
            {
                "id": str(row.id),
                "student_id": str(row.student_id),
                "program_id": str(row.program_id),
                "status": row.status,
                "decision": row.decision,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in recent_apps_result.all()
        ]

        # Recommendation counts
        total_recs = await self.db.scalar(select(func.count(RecommendationRequest.id))) or 0
        rec_by_status: dict[str, int] = {}
        for rec_status in ["draft", "requested", "submitted", "received"]:
            rc = await self.db.scalar(
                select(func.count(RecommendationRequest.id)).where(
                    RecommendationRequest.status == rec_status
                )
            )
            rec_by_status[rec_status] = int(rc or 0)

        # Pipeline / crawl status
        pipeline_stages: dict[str, dict] = {}
        for stage_name in ("crawl", "extract", "ml"):
            snap = await self.db.get(PipelineStageSnapshot, stage_name)
            if snap:
                pipeline_stages[stage_name] = {
                    "status": snap.status,
                    "items_processed_total": snap.items_processed_total,
                    "items_processed_hour": snap.items_processed_hour,
                    "last_activity_at": (
                        snap.last_activity_at.isoformat() if snap.last_activity_at else None
                    ),
                }
            else:
                pipeline_stages[stage_name] = {"status": "not_started"}

        frontier_pending = (
            await self.db.scalar(
                select(func.count())
                .select_from(CrawlFrontier)
                .where(CrawlFrontier.status == "pending")
            )
            or 0
        )
        frontier_completed = (
            await self.db.scalar(
                select(func.count())
                .select_from(CrawlFrontier)
                .where(CrawlFrontier.status == "completed")
            )
            or 0
        )
        frontier_failed = (
            await self.db.scalar(
                select(func.count())
                .select_from(CrawlFrontier)
                .where(CrawlFrontier.status == "failed")
            )
            or 0
        )
        total_knowledge_docs = (
            await self.db.scalar(select(func.count()).select_from(KnowledgeDocument)) or 0
        )

        return {
            "users": {
                "total": total_users or 0,
                "students": student_users or 0,
                "institutions": institution_users or 0,
            },
            "profiles": total_profiles or 0,
            "institutions": total_institutions or 0,
            "programs": {
                "total": total_programs or 0,
                "published": published_programs or 0,
            },
            "applications": {
                "total": total_applications or 0,
                "by_status": app_by_status,
                "by_decision": app_by_decision,
            },
            "matching": {
                "total_matches": total_matches or 0,
                "avg_score": round(float(avg_match_score), 2) if avg_match_score else 0,
            },
            "engagement": {
                "total_signals": total_engagements or 0,
            },
            "recommendations": {
                "total": total_recs,
                "by_status": rec_by_status,
            },
            "pipeline": {
                "stages": pipeline_stages,
                "frontier": {
                    "pending": frontier_pending,
                    "completed": frontier_completed,
                    "failed": frontier_failed,
                },
                "knowledge_docs": total_knowledge_docs,
            },
            "recent_users": recent_users,
            "recent_applications": recent_apps,
        }

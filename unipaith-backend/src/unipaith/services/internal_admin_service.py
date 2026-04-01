from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.core.data_safety import assert_core_role_coverage, ensure_can_deactivate_user
from unipaith.core.exceptions import BadRequestException, NotFoundException
from unipaith.models.admin_audit_event import AdminAuditEvent
from unipaith.models.application import Application
from unipaith.models.engagement import StudentEngagementSignal
from unipaith.models.institution import Institution, Program
from unipaith.models.matching import MatchResult
from unipaith.models.student import StudentProfile
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
                    "institution_id": (
                        str(row.institution_id) if row.institution_id else None
                    ),
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

        result = await self.db.execute(
            select(Institution).where(Institution.id.in_(requested_ids))
        )
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
            "recent_users": recent_users,
            "recent_applications": recent_apps,
        }

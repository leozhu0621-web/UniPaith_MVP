from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.core.data_safety import assert_core_role_coverage, ensure_can_deactivate_user
from unipaith.core.exceptions import NotFoundException
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
        page: int,
        page_size: int,
    ) -> UserListResult:
        stmt = select(User)
        if role:
            stmt = stmt.where(User.role == UserRole(role))

        total = (
            await self.db.execute(select(func.count()).select_from(stmt.subquery()))
        ).scalar_one()

        results = await self.db.execute(stmt.offset((page - 1) * page_size).limit(page_size))
        users = results.scalars().all()

        return UserListResult(
            items=[
                {
                    "id": str(u.id),
                    "email": u.email,
                    "role": u.role.value,
                    "is_active": u.is_active,
                    "created_at": u.created_at.isoformat() if u.created_at else None,
                }
                for u in users
            ],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def set_user_active(self, user_id: UUID, active: bool) -> User:
        result = await self.db.execute(select(User).where(User.id == user_id))
        target = result.scalar_one_or_none()
        if not target:
            raise NotFoundException("User not found")

        if not active:
            await ensure_can_deactivate_user(self.db, target)

        target.is_active = active
        await self.db.flush()
        await assert_core_role_coverage(self.db)
        return target

    async def verify_institution(self, institution_id: UUID) -> Institution:
        result = await self.db.execute(select(Institution).where(Institution.id == institution_id))
        institution = result.scalar_one_or_none()
        if not institution:
            raise NotFoundException("Institution not found")
        institution.is_verified = True
        await self.db.flush()
        return institution

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

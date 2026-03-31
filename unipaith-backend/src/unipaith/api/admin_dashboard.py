"""Admin dashboard API — system-wide overview stats."""

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.models.user import User, UserRole
from unipaith.models.student import StudentProfile
from unipaith.models.institution import Institution
from unipaith.models.program import Program
from unipaith.models.application import Application
from unipaith.models.matching import MatchResult
from unipaith.models.engagement import EngagementSignal

router = APIRouter(prefix="/admin/dashboard", tags=["admin-dashboard"])


@router.get("/stats")
async def get_system_stats(db: AsyncSession = Depends(get_db)):
    """Get system-wide statistics for the admin dashboard."""

    # User counts by role
    total_users = await db.scalar(select(func.count(User.id)))
    student_users = await db.scalar(
        select(func.count(User.id)).where(User.role == UserRole.student)
    )
    institution_users = await db.scalar(
        select(func.count(User.id)).where(User.role == UserRole.institution_admin)
    )

    # Profile counts
    total_profiles = await db.scalar(select(func.count(StudentProfile.id)))

    # Institution counts
    total_institutions = await db.scalar(select(func.count(Institution.id)))

    # Program counts
    total_programs = await db.scalar(select(func.count(Program.id)))
    published_programs = await db.scalar(
        select(func.count(Program.id)).where(Program.is_published == True)  # noqa: E712
    )

    # Application counts and breakdown
    total_applications = await db.scalar(select(func.count(Application.id)))

    app_by_status = {}
    for status in ["draft", "submitted", "under_review", "interview", "decision_made"]:
        count = await db.scalar(
            select(func.count(Application.id)).where(Application.status == status)
        )
        app_by_status[status] = count or 0

    app_by_decision = {}
    for decision in ["admitted", "rejected", "waitlisted", "deferred"]:
        count = await db.scalar(
            select(func.count(Application.id)).where(Application.decision == decision)
        )
        app_by_decision[decision] = count or 0

    # Matching
    total_matches = await db.scalar(select(func.count(MatchResult.id)))
    avg_match_score = await db.scalar(select(func.avg(MatchResult.match_score)))

    # Engagement
    total_engagements = await db.scalar(select(func.count(EngagementSignal.id)))

    # Recent users (last 10)
    recent_users_result = await db.execute(
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

    # Recent applications (last 10)
    recent_apps_result = await db.execute(
        select(Application.id, Application.student_id, Application.program_id,
               Application.status, Application.decision, Application.created_at)
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

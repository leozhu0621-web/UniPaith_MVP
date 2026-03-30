from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.dependencies import require_admin
from unipaith.models.application import Application
from unipaith.models.institution import Institution, Program
from unipaith.models.student import StudentProfile
from unipaith.models.user import User, UserRole
from unipaith.services.matching_service import MatchingService

router = APIRouter(prefix="/internal", tags=["internal"])


@router.get("/stats")
async def platform_stats(
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    students = (await db.execute(
        select(func.count()).select_from(User).where(User.role == UserRole.student)
    )).scalar_one()
    institutions = (await db.execute(
        select(func.count()).select_from(Institution)
    )).scalar_one()
    programs = (await db.execute(
        select(func.count()).select_from(Program).where(Program.is_published.is_(True))
    )).scalar_one()
    applications = (await db.execute(
        select(func.count()).select_from(Application)
    )).scalar_one()

    return {
        "total_students": students,
        "total_institutions": institutions,
        "published_programs": programs,
        "total_applications": applications,
    }


@router.get("/users")
async def list_users(
    role: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(User)
    if role:
        stmt = stmt.where(User.role == UserRole(role))

    total = (await db.execute(
        select(func.count()).select_from(stmt.subquery())
    )).scalar_one()

    results = await db.execute(
        stmt.offset((page - 1) * page_size).limit(page_size)
    )
    users = results.scalars().all()

    return {
        "items": [
            {
                "id": str(u.id),
                "email": u.email,
                "role": u.role.value,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.patch("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    import uuid as _uuid
    result = await db.execute(select(User).where(User.id == _uuid.UUID(user_id)))
    target = result.scalar_one_or_none()
    if not target:
        from unipaith.core.exceptions import NotFoundException
        raise NotFoundException("User not found")
    target.is_active = False
    await db.flush()
    return {"message": f"User {user_id} deactivated"}


@router.patch("/users/{user_id}/activate")
async def activate_user(
    user_id: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    import uuid as _uuid
    result = await db.execute(select(User).where(User.id == _uuid.UUID(user_id)))
    target = result.scalar_one_or_none()
    if not target:
        from unipaith.core.exceptions import NotFoundException
        raise NotFoundException("User not found")
    target.is_active = True
    await db.flush()
    return {"message": f"User {user_id} activated"}


@router.patch("/institutions/{institution_id}/verify")
async def verify_institution(
    institution_id: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    import uuid as _uuid
    result = await db.execute(
        select(Institution).where(Institution.id == _uuid.UUID(institution_id))
    )
    inst = result.scalar_one_or_none()
    if not inst:
        from unipaith.core.exceptions import NotFoundException
        raise NotFoundException("Institution not found")
    inst.is_verified = True
    await db.flush()
    return {"message": f"Institution {inst.name} verified"}


# --- AI Admin ---


@router.post("/ai/bootstrap-programs")
async def bootstrap_program_features(
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Extract features + generate embeddings for all published programs."""
    svc = MatchingService(db)
    return await svc.bootstrap_all_programs()


@router.post("/ai/refresh-student/{student_id}")
async def refresh_student_features(
    student_id: UUID,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger feature re-extraction for a student."""
    svc = MatchingService(db)
    features = await svc.refresh_student_features(student_id)
    return {"student_id": str(student_id), "features": features}


@router.post("/ai/refresh-program/{program_id}")
async def refresh_program_features(
    program_id: UUID,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger feature re-extraction for a program."""
    svc = MatchingService(db)
    features = await svc.refresh_program_features(program_id)
    return {"program_id": str(program_id), "features": features}

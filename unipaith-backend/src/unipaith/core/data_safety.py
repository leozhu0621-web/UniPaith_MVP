from __future__ import annotations

from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.core.exceptions import ConflictException
from unipaith.models.user import User, UserRole

CORE_ROLES: tuple[UserRole, ...] = (
    UserRole.student,
    UserRole.institution_admin,
    UserRole.admin,
)


async def assert_core_role_coverage(db: AsyncSession) -> None:
    """
    Ensure the system still has at least one active account per core role.

    This protects the minimum account foundation required by the product:
    student, institution admin, and platform admin.
    """
    for role in CORE_ROLES:
        result = await db.execute(
            select(func.count())
            .select_from(User)
            .where(
                User.role == role,
                User.is_active.is_(True),
            )
        )
        active_count = int(result.scalar_one() or 0)
        if active_count == 0:
            raise ConflictException(
                f"Safety check failed: no active '{role.value}' accounts remain"
            )


async def ensure_can_deactivate_user(db: AsyncSession, target: User) -> None:
    """
    Prevent deactivation of the last active account for any core role.
    """
    if target.role not in CORE_ROLES or not target.is_active:
        return

    result = await db.execute(
        select(func.count())
        .select_from(User)
        .where(
            and_(
                User.role == target.role,
                User.is_active.is_(True),
                User.id != target.id,
            )
        )
    )
    remaining_active = int(result.scalar_one() or 0)
    if remaining_active == 0:
        raise ConflictException(f"Cannot deactivate the last active '{target.role.value}' account")


async def ensure_can_delete_user(db: AsyncSession, user_id: UUID, role: UserRole) -> None:
    """
    Generic guard for destructive account operations.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    target = result.scalar_one_or_none()
    if target is None:
        return
    if target.role != role:
        raise ConflictException("User role mismatch for delete operation")
    await ensure_can_deactivate_user(db, target)

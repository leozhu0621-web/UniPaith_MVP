from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.core.data_safety import assert_core_role_coverage
from unipaith.core.exceptions import ConflictException
from unipaith.models.user import User, UserRole
from unipaith.services.internal_admin_service import InternalAdminService


async def _seed_core_users(db: AsyncSession) -> tuple[User, User, User]:
    student = User(email="student-core@example.com", role=UserRole.student, is_active=True)
    institution_admin = User(
        email="institution-core@example.com",
        role=UserRole.institution_admin,
        is_active=True,
    )
    admin = User(email="admin-core@example.com", role=UserRole.admin, is_active=True)
    db.add_all([student, institution_admin, admin])
    await db.commit()
    return student, institution_admin, admin


@pytest.mark.asyncio
async def test_core_role_coverage_passes_with_minimum_accounts(db_session: AsyncSession):
    await _seed_core_users(db_session)
    await assert_core_role_coverage(db_session)


@pytest.mark.asyncio
async def test_cannot_deactivate_last_active_admin(db_session: AsyncSession):
    _student, _institution_admin, admin = await _seed_core_users(db_session)
    service = InternalAdminService(db_session)

    with pytest.raises(ConflictException, match="last active 'admin'"):
        await service.set_user_active(admin.id, active=False)

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from unipaith.core.data_safety import (
    assert_core_role_coverage,
    ensure_can_deactivate_user,
)
from unipaith.core.exceptions import ConflictException
from unipaith.models.user import User, UserRole


async def _seed_core_users(db: AsyncSession) -> tuple[User, User]:
    student = User(email="student-core@example.com", role=UserRole.student, is_active=True)
    institution_admin = User(
        email="institution-core@example.com",
        role=UserRole.institution_admin,
        is_active=True,
    )
    db.add_all([student, institution_admin])
    await db.commit()
    return student, institution_admin


@pytest.mark.asyncio
async def test_core_role_coverage_passes_with_minimum_accounts(db_session: AsyncSession):
    await _seed_core_users(db_session)
    await assert_core_role_coverage(db_session)


@pytest.mark.asyncio
async def test_cannot_deactivate_last_active_institution_admin(db_session: AsyncSession):
    _student, institution_admin = await _seed_core_users(db_session)

    with pytest.raises(ConflictException, match="last active 'institution_admin'"):
        await ensure_can_deactivate_user(db_session, institution_admin)

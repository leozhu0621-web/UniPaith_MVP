"""Shared seed helpers for the Uni managed-agent tests.

Underscore-prefixed so pytest does not collect it as a test module.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.student import StudentProfile
from unipaith.models.user import User


async def ensure_profile(db: AsyncSession, user: User) -> StudentProfile:
    """Persist the mock user + a StudentProfile so user→profile resolution works."""
    profile = StudentProfile(user_id=user.id)
    db.add(user)
    db.add(profile)
    await db.commit()
    return profile

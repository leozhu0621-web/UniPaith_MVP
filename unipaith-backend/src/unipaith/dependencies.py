import uuid

from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import settings
from unipaith.core.exceptions import ForbiddenException
from unipaith.core.security import CognitoClaims, verify_token
from unipaith.database import get_db
from unipaith.models.student import StudentProfile
from unipaith.models.user import User, UserRole


async def authenticate_token(token: str, db: AsyncSession) -> User:
    """Resolve a raw bearer token to a ``User``, applying dev-bypass + auto-provision.

    Extracted from ``get_current_user`` so the SSE / WebSocket endpoints (Spec 57)
    can authenticate from a ``?access_token=`` query param — EventSource and the
    browser WebSocket can't set an ``Authorization`` header. Raises
    ``ForbiddenException`` on an unknown user, exactly like the HTTP path.
    """
    claims: CognitoClaims = await verify_token(token)

    # In dev bypass mode, the sub is the user_id (UUID), so look up by id first
    user = None
    if settings.cognito_bypass:
        try:
            user_id = uuid.UUID(claims.sub)
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
        except ValueError:
            pass

    if user is None:
        result = await db.execute(select(User).where(User.cognito_sub == claims.sub))
        user = result.scalar_one_or_none()

    if user is None and settings.cognito_bypass:
        # Dev-mode resilience: when local DB is reset but a valid dev token remains,
        # auto-provision a matching user (and student profile) to avoid auth dead-ends.
        try:
            dev_user_id = uuid.UUID(claims.sub)
        except ValueError:
            dev_user_id = None

        if dev_user_id is not None:
            try:
                role = UserRole(claims.role)
            except ValueError:
                role = UserRole.student

            user = User(
                id=dev_user_id,
                email=claims.email or f"dev-{claims.sub[:8]}@dev.local",
                cognito_sub=claims.sub,
                role=role,
            )
            db.add(user)
            await db.flush()

            if role == UserRole.student:
                db.add(StudentProfile(user_id=user.id))
                await db.flush()

    if user is None:
        raise ForbiddenException("User not found")

    return user


async def get_current_user(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
) -> User:
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise ForbiddenException("Invalid authorization header")
    return await authenticate_token(token, db)


async def require_student(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.student:
        raise ForbiddenException("Student access required")
    return user


async def require_institution_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.institution_admin:
        raise ForbiddenException("Institution admin access required")
    return user


async def require_faculty_or_institution_admin(user: User = Depends(get_current_user)) -> User:
    """Spec 41 §8 — faculty *and* central admins may read their department's
    applicants, score, recommend, and propose funding. Releasing a decision stays
    behind ``require_institution_admin`` (the two-stage gate: faculty recommend,
    central releases, §2.4)."""
    if user.role not in (UserRole.institution_admin, UserRole.faculty):
        raise ForbiddenException("Faculty or institution admin access required")
    return user

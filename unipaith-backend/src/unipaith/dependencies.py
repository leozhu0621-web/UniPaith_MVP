from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.core.exceptions import ForbiddenException
from unipaith.core.security import CognitoClaims, verify_token
from unipaith.database import get_db
from unipaith.models.user import User, UserRole
from unipaith.models.student import StudentProfile


async def get_current_user(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
) -> User:
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise ForbiddenException("Invalid authorization header")

    claims: CognitoClaims = await verify_token(token)

    result = await db.execute(select(User).where(User.cognito_sub == claims.sub))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            email=claims.email,
            cognito_sub=claims.sub,
            role=UserRole(claims.role),
        )
        db.add(user)

        if claims.role == "student":
            profile = StudentProfile(user_id=user.id)
            db.add(profile)

        await db.flush()

    return user


async def require_student(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.student:
        raise ForbiddenException("Student access required")
    return user


async def require_institution_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.institution_admin:
        raise ForbiddenException("Institution admin access required")
    return user


async def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.admin:
        raise ForbiddenException("Admin access required")
    return user

"""Publishing an institution post notifies its non-muted followers — the
"Posts from saved programs" feature that previously did nothing (publish never
fanned a post out to anyone).
"""

from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.follow import InstitutionFollow
from unipaith.models.institution import Institution
from unipaith.models.student import StudentProfile
from unipaith.models.user import User, UserRole
from unipaith.models.workflow import Notification
from unipaith.services.institution_service import InstitutionService


async def _admin_inst(db: AsyncSession) -> Institution:
    admin = User(
        id=uuid4(),
        email=f"a{uuid4().hex[:6]}@e.co",
        cognito_sub=f"s{uuid4().hex[:8]}",
        role=UserRole.institution_admin,
        is_active=True,
    )
    db.add(admin)
    await db.flush()
    inst = Institution(admin_user_id=admin.id, name="Followed U", type="university", country="US")
    db.add(inst)
    await db.flush()
    return inst


async def _follower(db: AsyncSession, institution_id, *, muted: bool) -> StudentProfile:
    user = User(
        id=uuid4(),
        email=f"st{uuid4().hex[:6]}@e.co",
        cognito_sub=f"ss{uuid4().hex[:8]}",
        role=UserRole.student,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    profile = StudentProfile(user_id=user.id)
    db.add(profile)
    await db.flush()
    db.add(
        InstitutionFollow(
            student_id=profile.id,
            institution_id=institution_id,
            source="explicit",
            muted=muted,
        )
    )
    await db.flush()
    return profile


async def _posts_for(db: AsyncSession, user_id) -> int:
    return await db.scalar(
        select(func.count())
        .select_from(Notification)
        .where(
            Notification.user_id == user_id,
            Notification.notification_type == "institution_post",
        )
    )


async def test_post_fanout_notifies_active_followers_once(db_session: AsyncSession):
    inst = await _admin_inst(db_session)
    follower = await _follower(db_session, inst.id, muted=False)
    muted = await _follower(db_session, inst.id, muted=True)

    post = SimpleNamespace(
        id=uuid4(), title="Open house this Friday", body="Join us to learn more."
    )
    svc = InstitutionService(db_session)
    await svc._notify_followers_of_post(inst.id, post)

    # Active follower notified once; muted follower not notified.
    assert await _posts_for(db_session, follower.user_id) == 1
    assert await _posts_for(db_session, muted.user_id) == 0

    # Idempotent: a re-publish (same post id) does not double-notify.
    await svc._notify_followers_of_post(inst.id, post)
    assert await _posts_for(db_session, follower.user_id) == 1

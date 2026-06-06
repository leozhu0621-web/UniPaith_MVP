"""Unified track-less Uni discovery session (Plan task 3)."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.student import StudentProfile
from unipaith.models.user import User
from unipaith.services.discovery_service import DiscoveryService


async def _ensure_profile(db: AsyncSession, user: User) -> StudentProfile:
    profile = StudentProfile(user_id=user.id)
    db.add(user)
    db.add(profile)
    await db.commit()
    return profile


@pytest.mark.asyncio
async def test_start_unified_session_is_trackless(
    db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    svc = DiscoveryService(db_session)
    s = await svc.start_unified_session(mock_student_user.id)
    assert s.track == "discovery"  # CHECK constraint allows it
    assert s.layer is None
    assert float(s.completion_pct) == 0.0


@pytest.mark.asyncio
async def test_unified_session_turn_runs_without_error(
    db_session: AsyncSession, mock_student_user: User
):
    """A turn on a discovery session runs the combined-validator branch and
    sets a numeric completion (flag off → stub reply; the path still works)."""
    await _ensure_profile(db_session, mock_student_user)
    svc = DiscoveryService(db_session)
    s = await svc.start_unified_session(mock_student_user.id)
    student_msg, _assistant = await svc.append_message(
        mock_student_user.id,
        s.id,
        role="student",
        content="I love building robots and want to become an engineer; I'll need aid.",
    )
    assert student_msg.content
    await db_session.refresh(s)
    assert s.completion_pct is not None
    assert float(s.completion_pct) >= 0.0

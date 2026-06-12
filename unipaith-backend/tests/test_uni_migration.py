"""discovery_sessions.agent_session_id — column round-trips."""

import pytest
from sqlalchemy import select

from tests._uni_helpers import ensure_profile
from unipaith.models.discovery import DiscoverySession
from unipaith.services.student_service import StudentService


@pytest.mark.asyncio
async def test_discovery_session_has_agent_session_id(db_session, mock_student_user):
    await ensure_profile(db_session, mock_student_user)
    sp = await StudentService(db_session)._get_student_profile(mock_student_user.id)
    ds = DiscoverySession(
        student_id=sp.id, track="profile", layer="basic", agent_session_id="sesn_x"
    )
    db_session.add(ds)
    await db_session.flush()
    row = (
        await db_session.execute(select(DiscoverySession).where(DiscoverySession.id == ds.id))
    ).scalar_one()
    assert row.agent_session_id == "sesn_x"

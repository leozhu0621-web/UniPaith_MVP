"""StudentService.get_full_snapshot — the consolidated counselor snapshot."""

import pytest

from tests._uni_helpers import ensure_profile
from unipaith.services.student_service import StudentService


@pytest.mark.asyncio
async def test_get_full_snapshot_shape(db_session, mock_student_user):
    await ensure_profile(db_session, mock_student_user)
    snap = await StudentService(db_session).get_full_snapshot(mock_student_user.id)
    assert set(snap.keys()) == {
        "profile",
        "goals",
        "needs",
        "identity",
        "active_strategy",
        "completion",
    }
    assert isinstance(snap["goals"], list)
    assert isinstance(snap["needs"], list)
    assert isinstance(snap["completion"], dict)
    # Fresh student: no strategy yet, identity lists default to [].
    assert snap["active_strategy"] is None
    assert snap["identity"]["core_values"] == []

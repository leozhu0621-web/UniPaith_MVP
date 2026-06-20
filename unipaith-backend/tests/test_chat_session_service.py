"""ChatSessionService — folder/session CRUD + invariants (sessions data model)."""

import pytest
from sqlalchemy import select

from tests._uni_helpers import ensure_profile
from unipaith.core.exceptions import BadRequestException
from unipaith.models.chat_session import ChatFolder, ChatSession
from unipaith.services.chat.session_service import ChatSessionService
from unipaith.services.intake.intake_engine_service import IntakeEngineService


async def _pid(db, user):
    return await IntakeEngineService(db).profile_id_for_user(user.id)


@pytest.mark.asyncio
async def test_ensure_preset_folders_creates_eight_once(db_session, mock_student_user):
    await ensure_profile(db_session, mock_student_user)
    pid = await _pid(db_session, mock_student_user)
    svc = ChatSessionService(db_session)
    await svc.ensure_preset_folders(pid)
    await svc.ensure_preset_folders(pid)  # idempotent
    folders = (
        (await db_session.execute(select(ChatFolder).where(ChatFolder.student_id == pid)))
        .scalars()
        .all()
    )
    assert len([f for f in folders if f.kind == "preset"]) == 8


@pytest.mark.asyncio
async def test_create_session_auto_files_by_text(db_session, mock_student_user):
    await ensure_profile(db_session, mock_student_user)
    pid = await _pid(db_session, mock_student_user)
    svc = ChatSessionService(db_session)
    s = await svc.create_session(pid, title="How do I pay for this?")
    folder = (
        await db_session.execute(select(ChatFolder).where(ChatFolder.id == s.folder_id))
    ).scalar_one()
    assert folder.topic_key == "needs"


@pytest.mark.asyncio
async def test_rename_and_pin_session(db_session, mock_student_user):
    await ensure_profile(db_session, mock_student_user)
    pid = await _pid(db_session, mock_student_user)
    svc = ChatSessionService(db_session)
    s = await svc.create_session(pid, title="draft my statement")
    await svc.update_session(pid, s.id, title="My CMU SOP", pinned=True)
    again = await svc._get_owned_session(pid, s.id)
    assert again.title == "My CMU SOP" and again.pinned is True


@pytest.mark.asyncio
async def test_delete_preset_folder_rejected_custom_allowed(db_session, mock_student_user):
    await ensure_profile(db_session, mock_student_user)
    pid = await _pid(db_session, mock_student_user)
    svc = ChatSessionService(db_session)
    folders = await svc.ensure_preset_folders(pid)
    with pytest.raises(BadRequestException):
        await svc.delete_folder(pid, folders["schools"].id)  # preset → protected
    custom = await svc.create_folder(pid, name="Reach schools")
    await svc.delete_folder(pid, custom.id)  # custom → ok


@pytest.mark.asyncio
async def test_preset_folder_rename_rejected(db_session, mock_student_user):
    await ensure_profile(db_session, mock_student_user)
    pid = await _pid(db_session, mock_student_user)
    svc = ChatSessionService(db_session)
    folders = await svc.ensure_preset_folders(pid)
    with pytest.raises(BadRequestException):
        await svc.update_folder(pid, folders["schools"].id, name="My schools")


@pytest.mark.asyncio
async def test_reorder_sessions_within_folder(db_session, mock_student_user):
    await ensure_profile(db_session, mock_student_user)
    pid = await _pid(db_session, mock_student_user)
    svc = ChatSessionService(db_session)
    a = await svc.create_session(pid, title="compare schools")  # → schools, order 0
    b = await svc.create_session(pid, title="add a school")  # → schools, order 1
    assert a.folder_id == b.folder_id
    await svc.reorder_sessions(pid, a.folder_id, [b.id, a.id])
    assert (await svc._get_owned_session(pid, b.id)).sort_order == 0
    assert (await svc._get_owned_session(pid, a.id)).sort_order == 1


@pytest.mark.asyncio
async def test_spawn_from_program_files_under_schools(db_session, mock_student_user):
    await ensure_profile(db_session, mock_student_user)
    pid = await _pid(db_session, mock_student_user)
    svc = ChatSessionService(db_session)
    s = await svc.spawn_from_context(
        pid, origin_kind="discover_program", origin_ref="cmu-mscs", title="Carnegie Mellon"
    )
    folder = await svc._get_owned_folder(pid, s.folder_id)
    assert folder.topic_key == "schools" and s.origin_kind == "discover_program"


@pytest.mark.asyncio
async def test_delete_session(db_session, mock_student_user):
    await ensure_profile(db_session, mock_student_user)
    pid = await _pid(db_session, mock_student_user)
    svc = ChatSessionService(db_session)
    s = await svc.create_session(pid, title="add a school")
    await svc.delete_session(pid, s.id)
    gone = (
        await db_session.execute(select(ChatSession).where(ChatSession.id == s.id))
    ).scalar_one_or_none()
    assert gone is None

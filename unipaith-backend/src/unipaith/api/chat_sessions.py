"""Uni chat-tab sessions API — /students/me/chat/* (folders + sessions CRUD).

The backend for the redesigned left-rail session browser (2026-06-19 chat-tab
spec §3): preset (protected) + custom folders, sessions auto-filed into a folder,
pin/within-folder reorder, and context-spawn.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.dependencies import require_student
from unipaith.models.user import User
from unipaith.services.chat.session_service import ChatSessionService
from unipaith.services.intake.intake_engine_service import IntakeEngineService

router = APIRouter(prefix="/students/me/chat", tags=["chat-sessions"])


def _folder(f) -> dict:
    return {
        "id": str(f.id),
        "name": f.name,
        "kind": f.kind,
        "topic_key": f.topic_key,
        "stage": f.stage,
        "sort_order": f.sort_order,
    }


def _session(s, folder=None) -> dict:
    return {
        "id": str(s.id),
        "title": s.title,
        "pinned": s.pinned,
        "sort_order": s.sort_order,
        "folder_id": str(s.folder_id),
        "origin_kind": s.origin_kind,
        "topic_key": folder.topic_key if folder is not None else None,
    }


class SessionCreate(BaseModel):
    title: str
    topic_key: str | None = None
    origin_kind: str = "manual"
    origin_ref: str | None = None


class SessionPatch(BaseModel):
    title: str | None = None
    pinned: bool | None = None
    sort_order: int | None = None


class FolderCreate(BaseModel):
    name: str


class FolderPatch(BaseModel):
    name: str | None = None
    sort_order: int | None = None


class ReorderIn(BaseModel):
    folder_id: UUID
    ordered_ids: list[UUID]


async def _pid(db: AsyncSession, user: User) -> UUID:
    return await IntakeEngineService(db).profile_id_for_user(user.id)


@router.get("/folders")
async def folders_tree(user: User = Depends(require_student), db: AsyncSession = Depends(get_db)):
    pid = await _pid(db, user)
    tree = await ChatSessionService(db).list_tree(pid)
    return {
        "folders": [
            {
                **_folder(node["folder"]),
                "sessions": [_session(s, node["folder"]) for s in node["sessions"]],
            }
            for node in tree
        ]
    }


@router.post("/sessions")
async def create_session(
    body: SessionCreate,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    pid = await _pid(db, user)
    s = await ChatSessionService(db).create_session(
        pid,
        title=body.title,
        topic_key=body.topic_key,
        origin_kind=body.origin_kind,
        origin_ref=body.origin_ref,
    )
    await db.refresh(s, ["folder"])
    return _session(s, s.folder)


@router.patch("/sessions/{session_id}")
async def patch_session(
    session_id: UUID,
    body: SessionPatch,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    pid = await _pid(db, user)
    s = await ChatSessionService(db).update_session(
        pid, session_id, title=body.title, pinned=body.pinned, sort_order=body.sort_order
    )
    return _session(s)


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    await ChatSessionService(db).delete_session(await _pid(db, user), session_id)
    return {"ok": True}


@router.post("/sessions/reorder")
async def reorder(
    body: ReorderIn,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    await ChatSessionService(db).reorder_sessions(
        await _pid(db, user), body.folder_id, body.ordered_ids
    )
    return {"ok": True}


@router.post("/folders")
async def create_folder(
    body: FolderCreate,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    f = await ChatSessionService(db).create_folder(await _pid(db, user), name=body.name)
    return _folder(f)


@router.patch("/folders/{folder_id}")
async def patch_folder(
    folder_id: UUID,
    body: FolderPatch,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    f = await ChatSessionService(db).update_folder(
        await _pid(db, user), folder_id, name=body.name, sort_order=body.sort_order
    )
    return _folder(f)


@router.delete("/folders/{folder_id}")
async def delete_folder(
    folder_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    await ChatSessionService(db).delete_folder(await _pid(db, user), folder_id)
    return {"ok": True}

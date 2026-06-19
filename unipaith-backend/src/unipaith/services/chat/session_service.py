"""ChatSessionService — the chat-tab session/folder organization layer.

Owns the spec invariants: preset folders are un-deletable / un-renamable; a
session is auto-filed into a folder and never user-moved across folders; pin +
within-folder/group reorder are user-controlled.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.core.exceptions import BadRequestException, NotFoundException
from unipaith.models.chat_session import ChatFolder, ChatSession
from unipaith.services.chat.folders import PRESET_FOLDERS, categorize

# context-spawn origin -> the topic folder it files into.
_ORIGIN_TOPIC = {
    "discover_program": "schools",
    "discover_school": "schools",
    "scholarship": "needs",
    "event": "connect",
    "peer": "connect",
    "upload": "profile",
}


class ChatSessionService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def ensure_preset_folders(self, student_id: UUID) -> dict[str, ChatFolder]:
        existing = {
            f.topic_key: f
            for f in (
                await self.db.execute(
                    select(ChatFolder).where(
                        ChatFolder.student_id == student_id, ChatFolder.kind == "preset"
                    )
                )
            ).scalars()
        }
        for spec in PRESET_FOLDERS:
            if spec["topic_key"] not in existing:
                f = ChatFolder(
                    student_id=student_id,
                    kind="preset",
                    name=spec["name"],
                    topic_key=spec["topic_key"],
                    stage=spec["stage"],
                    sort_order=spec["sort_order"],
                )
                self.db.add(f)
                existing[spec["topic_key"]] = f
        await self.db.flush()
        return existing

    async def create_session(
        self,
        student_id: UUID,
        *,
        title: str,
        topic_key: str | None = None,
        origin_kind: str = "manual",
        origin_ref: str | None = None,
        agent_session_id: str | None = None,
    ) -> ChatSession:
        folders = await self.ensure_preset_folders(student_id)
        key = topic_key or categorize(title)
        folder = folders.get(key) or folders["profile"]
        n = len(
            (await self.db.execute(select(ChatSession).where(ChatSession.folder_id == folder.id)))
            .scalars()
            .all()
        )
        s = ChatSession(
            student_id=student_id,
            folder_id=folder.id,
            title=(title[:120] or "New session"),
            origin_kind=origin_kind,
            origin_ref=origin_ref,
            agent_session_id=agent_session_id,
            sort_order=n,
        )
        self.db.add(s)
        await self.db.flush()
        return s

    async def spawn_from_context(
        self, student_id: UUID, *, origin_kind: str, origin_ref: str | None, title: str
    ) -> ChatSession:
        topic = _ORIGIN_TOPIC.get(origin_kind) or categorize(title)
        return await self.create_session(
            student_id,
            title=title,
            topic_key=topic,
            origin_kind=origin_kind,
            origin_ref=origin_ref,
        )

    async def list_tree(self, student_id: UUID) -> list[dict]:
        await self.ensure_preset_folders(student_id)
        folders = (
            (
                await self.db.execute(
                    select(ChatFolder)
                    .where(ChatFolder.student_id == student_id)
                    .order_by(ChatFolder.kind.desc(), ChatFolder.sort_order)
                )
            )
            .scalars()
            .all()
        )
        sessions = (
            (
                await self.db.execute(
                    select(ChatSession)
                    .where(ChatSession.student_id == student_id, ChatSession.status == "active")
                    .order_by(ChatSession.sort_order)
                )
            )
            .scalars()
            .all()
        )
        by_folder: dict[UUID, list[ChatSession]] = {}
        for s in sessions:
            by_folder.setdefault(s.folder_id, []).append(s)
        return [{"folder": f, "sessions": by_folder.get(f.id, [])} for f in folders]

    async def _get_owned_session(self, student_id: UUID, session_id: UUID) -> ChatSession:
        s = (
            await self.db.execute(
                select(ChatSession).where(
                    ChatSession.id == session_id, ChatSession.student_id == student_id
                )
            )
        ).scalar_one_or_none()
        if s is None:
            raise NotFoundException("Session not found")
        return s

    async def _get_owned_folder(self, student_id: UUID, folder_id: UUID) -> ChatFolder:
        f = (
            await self.db.execute(
                select(ChatFolder).where(
                    ChatFolder.id == folder_id, ChatFolder.student_id == student_id
                )
            )
        ).scalar_one_or_none()
        if f is None:
            raise NotFoundException("Folder not found")
        return f

    async def update_session(
        self,
        student_id: UUID,
        session_id: UUID,
        *,
        title: str | None = None,
        pinned: bool | None = None,
        sort_order: int | None = None,
    ) -> ChatSession:
        s = await self._get_owned_session(student_id, session_id)
        if title is not None:
            s.title = title[:120] or s.title
        if pinned is not None:
            s.pinned = pinned
        if sort_order is not None:
            s.sort_order = sort_order
        await self.db.flush()
        return s

    async def delete_session(self, student_id: UUID, session_id: UUID) -> None:
        s = await self._get_owned_session(student_id, session_id)
        await self.db.delete(s)
        await self.db.flush()

    async def reorder_sessions(
        self, student_id: UUID, folder_id: UUID, ordered_ids: list[UUID]
    ) -> None:
        # Only reorders WITHIN the folder — a session is never moved across
        # folders (auto-categorization owns folder placement).
        rows = {
            s.id: s
            for s in (
                await self.db.execute(
                    select(ChatSession).where(
                        ChatSession.student_id == student_id,
                        ChatSession.folder_id == folder_id,
                    )
                )
            ).scalars()
        }
        for i, sid in enumerate(ordered_ids):
            if sid in rows:
                rows[sid].sort_order = i
        await self.db.flush()

    async def create_folder(self, student_id: UUID, *, name: str) -> ChatFolder:
        n = len(
            (await self.db.execute(select(ChatFolder).where(ChatFolder.student_id == student_id)))
            .scalars()
            .all()
        )
        f = ChatFolder(
            student_id=student_id, kind="custom", name=(name[:80] or "Folder"), sort_order=n
        )
        self.db.add(f)
        await self.db.flush()
        return f

    async def update_folder(
        self,
        student_id: UUID,
        folder_id: UUID,
        *,
        name: str | None = None,
        sort_order: int | None = None,
    ) -> ChatFolder:
        f = await self._get_owned_folder(student_id, folder_id)
        if f.kind == "preset" and name is not None:
            raise BadRequestException("Preset folders cannot be renamed")
        if name is not None:
            f.name = name[:80] or f.name
        if sort_order is not None:
            f.sort_order = sort_order
        await self.db.flush()
        return f

    async def delete_folder(self, student_id: UUID, folder_id: UUID) -> None:
        f = await self._get_owned_folder(student_id, folder_id)
        if f.kind == "preset":
            raise BadRequestException("Preset folders cannot be deleted")
        await self.db.delete(f)
        await self.db.flush()

# Uni Sessions Data Model — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax. **TDD is mandatory** — write the failing test, watch it fail, then implement.

**Goal:** Build the net-new multi-session / foldered data model behind the 2026-06-19 Uni chat-tab redesign — named sessions organized into preset (white-paper-topic) and custom folders, with pin/order, auto-categorization, context-spawn, full CRUD, and a backfill — so the redesigned left rail (`docs/superpowers/specs/2026-06-19-uni-chat-tab-redesign-design.md` §3) has a backend.

**Architecture:** Two new tables — `chat_folders` (preset, protected white-paper topics + user custom folders) and `chat_sessions` (named threads filed into a folder, linked to the managed-agent conversation via `agent_session_id`). A deterministic auto-categorizer maps free text / context to a preset topic. A service layer owns the invariants (preset folders un-deletable, sessions never user-moved across folders, drag-reorder within a folder/group). A thin FastAPI router exposes CRUD. Messages stay in the existing managed-agent / `discovery_messages` layer — this model owns the *organization*, not the transcript.

**Tech Stack:** Python 3.12 · FastAPI · SQLAlchemy 2 (async) · PostgreSQL 16 · Alembic (hand-written migrations — env.py runs create_all, so autogenerate is unreliable). Tests: pytest-asyncio with the `student_client` / `db_session` / `mock_student_user` fixtures + `tests._uni_helpers.ensure_profile`.

**Run tests with:** `cd unipaith-backend && DATABASE_URL="postgresql+asyncpg://unipaith:unipaith@localhost:5432/unipaith" COGNITO_BYPASS=true AI_MOCK_MODE=true S3_LOCAL_MODE=true PYTHONPATH=src .venv/bin/pytest <file> -q` (use the main checkout's venv at `/Users/leozhu/Desktop/工作/UniPAith/App_MVP/unipaith-backend/.venv` if the worktree has none). <!-- pragma: allowlist secret (local dev DB credential) -->

---

## File structure

| File | Responsibility |
|---|---|
| `src/unipaith/models/chat_session.py` (create) | `ChatFolder` + `ChatSession` ORM models |
| `src/unipaith/models/__init__.py` (modify) | import + `__all__` register the two models |
| `src/unipaith/services/chat/__init__.py` (create) | package marker |
| `src/unipaith/services/chat/folders.py` (create) | `PRESET_FOLDERS` constant + `categorize()` pure auto-categorizer |
| `src/unipaith/services/chat/session_service.py` (create) | `ChatSessionService` — folders + sessions CRUD, invariants, context-spawn |
| `src/unipaith/api/chat_sessions.py` (create) | router `/students/me/chat/*` + inline Pydantic schemas |
| `src/unipaith/api/router.py` (modify) | register the router |
| `alembic/versions/chatsess1_*.py` (create) | create the two tables |
| `alembic/versions/chatsessbf1_*.py` (create) | backfill preset folders + name existing discovery threads |
| `tests/test_chat_folders_categorize.py` (create) | pure categorizer tests |
| `tests/test_chat_session_service.py` (create) | service invariants tests |
| `tests/test_chat_sessions_api.py` (create) | API integration tests |

**Canonical white-paper topics** (the preset folders), grouped by stage:
- `discovery`: `profile` · `goals` · `needs`
- `recommendation`: `strategy` · `schools`
- `application`: `connect` · `prepare` · `manage`

---

### Task 1: Models — ChatFolder + ChatSession

**Files:**
- Create: `src/unipaith/models/chat_session.py`
- Modify: `src/unipaith/models/__init__.py`
- Test: `tests/test_chat_session_service.py` (model import smoke is covered by Task 4; this task is verified by the migration + Task 4)

- [ ] **Step 1: Write the models** (mirror `models/discovery.py` conventions)

```python
# src/unipaith/models/chat_session.py
"""Uni chat-tab sessions + folders (2026-06-19 chat-tab redesign, spec §3).

The organization layer for the Advisor chat: named sessions filed into preset
(white-paper-topic) or custom folders. The conversation transcript itself lives
in the managed-agent / discovery layer (linked via `agent_session_id`); this
model owns titling, foldering, pin/order, and context-spawn provenance.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from unipaith.models.base import Base

# White-paper topic keys (preset folders) and their stage.
TOPIC_STAGE: dict[str, str] = {
    "profile": "discovery", "goals": "discovery", "needs": "discovery",
    "strategy": "recommendation", "schools": "recommendation",
    "connect": "application", "prepare": "application", "manage": "application",
}


class ChatFolder(Base):
    __tablename__ = "chat_folders"
    __table_args__ = (
        CheckConstraint("kind IN ('preset','custom')", name="ck_chat_folders_kind"),
        CheckConstraint(
            "(kind = 'preset') = (topic_key IS NOT NULL)",
            name="ck_chat_folders_preset_has_topic",
        ),
        UniqueConstraint("student_id", "topic_key", name="uq_chat_folders_student_topic"),
        Index("ix_chat_folders_student_sort", "student_id", "sort_order"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    kind: Mapped[str] = mapped_column(String(10), nullable=False, default="custom")
    topic_key: Mapped[str | None] = mapped_column(String(30))  # preset only
    stage: Mapped[str | None] = mapped_column(String(20))  # preset only
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    sessions: Mapped[list[ChatSession]] = relationship(
        back_populates="folder", cascade="all, delete-orphan"
    )


class ChatSession(Base):
    __tablename__ = "chat_sessions"
    __table_args__ = (
        CheckConstraint("status IN ('active','archived')", name="ck_chat_sessions_status"),
        Index("ix_chat_sessions_folder_sort", "folder_id", "sort_order"),
        Index("ix_chat_sessions_student_pinned", "student_id", "pinned"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False
    )
    folder_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chat_folders.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # context-spawn provenance: kind ∈ {manual, discover_program, discover_school,
    # scholarship, event, peer, upload, …}; ref = the source object id/slug.
    origin_kind: Mapped[str] = mapped_column(String(30), nullable=False, default="manual")
    origin_ref: Mapped[str | None] = mapped_column(String(255))
    agent_session_id: Mapped[str | None] = mapped_column(String(64))  # managed-agent link
    status: Mapped[str] = mapped_column(String(12), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    folder: Mapped[ChatFolder] = relationship(back_populates="sessions")
```

- [ ] **Step 2: Register in `models/__init__.py`** — add next to the discovery import:

```python
from unipaith.models.chat_session import ChatFolder, ChatSession  # noqa: F401
```
and add `"ChatFolder", "ChatSession",` to `__all__`.

- [ ] **Step 3: Commit**

```bash
git add src/unipaith/models/chat_session.py src/unipaith/models/__init__.py
git commit -m "feat(chat): ChatFolder + ChatSession models"
```

---

### Task 2: Migration — create the two tables

**Files:**
- Create: `alembic/versions/chatsess1_chat_sessions_and_folders.py`

- [ ] **Step 1: Write the migration** (mirror `92064a3f1d8d_add_program_preferences.py`; `down_revision` = the current single head — confirm with `alembic heads`, it is `pennnames1` as of 2026-06-19).

```python
"""chat_folders + chat_sessions (Uni chat-tab sessions model)

Hand-written; autogenerate is unreliable (env.py runs create_all).

Revision ID: chatsess1
Revises: pennnames1
Create Date: 2026-06-19
"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "chatsess1"  # pragma: allowlist secret
down_revision: str | None = "pennnames1"  # pragma: allowlist secret — VERIFY via `alembic heads`
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has(table: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(table)


def upgrade() -> None:
    if not _has("chat_folders"):
        op.create_table(
            "chat_folders",
            sa.Column("id", postgresql.UUID(as_uuid=True),
                      server_default=sa.text("gen_random_uuid()"), nullable=False),
            sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("name", sa.String(length=80), nullable=False),
            sa.Column("kind", sa.String(length=10), server_default="custom", nullable=False),
            sa.Column("topic_key", sa.String(length=30), nullable=True),
            sa.Column("stage", sa.String(length=20), nullable=True),
            sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True),
                      server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True),
                      server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["student_id"], ["student_profiles.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.CheckConstraint("kind IN ('preset','custom')", name="ck_chat_folders_kind"),
            sa.CheckConstraint("(kind = 'preset') = (topic_key IS NOT NULL)",
                               name="ck_chat_folders_preset_has_topic"),
            sa.UniqueConstraint("student_id", "topic_key", name="uq_chat_folders_student_topic"),
        )
        op.create_index("ix_chat_folders_student_sort", "chat_folders",
                        ["student_id", "sort_order"])
    if not _has("chat_sessions"):
        op.create_table(
            "chat_sessions",
            sa.Column("id", postgresql.UUID(as_uuid=True),
                      server_default=sa.text("gen_random_uuid()"), nullable=False),
            sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("folder_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("title", sa.String(length=120), nullable=False),
            sa.Column("pinned", sa.Boolean(), server_default=sa.text("false"), nullable=False),
            sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
            sa.Column("origin_kind", sa.String(length=30), server_default="manual", nullable=False),
            sa.Column("origin_ref", sa.String(length=255), nullable=True),
            sa.Column("agent_session_id", sa.String(length=64), nullable=True),
            sa.Column("status", sa.String(length=12), server_default="active", nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True),
                      server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True),
                      server_default=sa.text("now()"), nullable=False),
            sa.Column("last_activity_at", sa.DateTime(timezone=True),
                      server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["student_id"], ["student_profiles.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["folder_id"], ["chat_folders.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.CheckConstraint("status IN ('active','archived')", name="ck_chat_sessions_status"),
        )
        op.create_index("ix_chat_sessions_folder_sort", "chat_sessions",
                        ["folder_id", "sort_order"])
        op.create_index("ix_chat_sessions_student_pinned", "chat_sessions",
                        ["student_id", "pinned"])


def downgrade() -> None:
    op.drop_table("chat_sessions")
    op.drop_table("chat_folders")
```

- [ ] **Step 2: Verify single head, then apply**

Run: `alembic heads` → expect ONE head `chatsess1`. Then `alembic upgrade head`. (Tests recreate the schema from models, so this mainly guards prod + dual-head CI.)

- [ ] **Step 3: Commit** — `git add alembic/versions/chatsess1_*.py && git commit -m "feat(chat): migration for chat_folders + chat_sessions"`

---

### Task 3: Preset folders + the pure auto-categorizer

**Files:**
- Create: `src/unipaith/services/chat/__init__.py` (empty), `src/unipaith/services/chat/folders.py`
- Test: `tests/test_chat_folders_categorize.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_chat_folders_categorize.py
import pytest
from unipaith.services.chat.folders import PRESET_FOLDERS, categorize

def test_preset_folders_cover_all_eight_topics():
    keys = [f["topic_key"] for f in PRESET_FOLDERS]
    assert keys == ["profile", "goals", "needs", "strategy", "schools",
                    "connect", "prepare", "manage"]

@pytest.mark.parametrize("text,topic", [
    ("How do I pay for this?", "needs"),
    ("scholarships I qualify for", "needs"),
    ("draft my statement of purpose", "prepare"),
    ("who should write my recommendation", "prepare"),
    ("when is the deadline", "manage"),
    ("compare Carnegie Mellon and Toronto", "schools"),
    ("why a master's, not a job", "goals"),
    ("reach out to a professor", "connect"),
    ("sharpen my angle", "strategy"),
    ("something totally unrelated zzz", "profile"),  # default bucket
])
def test_categorize_maps_text_to_topic(text, topic):
    assert categorize(text) == topic
```

- [ ] **Step 2: Run → FAIL** (`ModuleNotFoundError: unipaith.services.chat.folders`).

- [ ] **Step 3: Implement**

```python
# src/unipaith/services/chat/folders.py
"""Preset (white-paper-topic) folders + a deterministic auto-categorizer.

Pure (no DB). The categorizer files a free-text session into one of the eight
white-paper topics by keyword; default → 'profile'. An LLM seam can replace this
later, but deterministic keeps it testable and free.
"""
from __future__ import annotations

from unipaith.models.chat_session import TOPIC_STAGE

# Display order = the left rail order.
_TOPIC_NAME = {
    "profile": "Profile", "goals": "Goals", "needs": "Needs",
    "strategy": "Strategy", "schools": "Schools",
    "connect": "Connect", "prepare": "Prepare", "manage": "Manage",
}
PRESET_FOLDERS = [
    {"topic_key": k, "name": _TOPIC_NAME[k], "stage": TOPIC_STAGE[k], "sort_order": i}
    for i, k in enumerate(
        ["profile", "goals", "needs", "strategy", "schools", "connect", "prepare", "manage"]
    )
]

# Keyword → topic. Checked in priority order (first match wins).
_KEYWORDS: list[tuple[str, tuple[str, ...]]] = [
    ("needs", ("pay", "afford", "fund", "scholarship", "aid", "cost", "tuition", "budget", "loan")),
    ("prepare", ("statement", "essay", "sop", "recommend", "letter", "interview",
                 "gre", "toefl", "ielts", "test", "resume", "cv", "portfolio")),
    ("manage", ("deadline", "due", "submit", "checklist", "track", "status", "application")),
    ("connect", ("reach out", "professor", "faculty", "event", "fair", "info session", "connect")),
    ("strategy", ("strategy", "angle", "position", "balance", "reach", "target", "safety")),
    ("schools", ("school", "university", "college", "program", "compare", "list")),
    ("goals", ("goal", "career", "future", "why a", "dream", "aspir")),
    ("profile", ("value", "identity", "story", "who am i", "background", "personality")),
]


def categorize(text: str | None) -> str:
    t = (text or "").lower()
    for topic, words in _KEYWORDS:
        if any(w in t for w in words):
            return topic
    return "profile"
```

- [ ] **Step 4: Run → PASS.**
- [ ] **Step 5: Commit** — `git commit -m "feat(chat): preset folders + deterministic auto-categorizer"`

---

### Task 4: ChatSessionService — ensure folders, create (auto-cat), list

**Files:**
- Create: `src/unipaith/services/chat/session_service.py`
- Test: `tests/test_chat_session_service.py`

- [ ] **Step 1: Write the failing tests** (uses `ensure_profile` → profile id; service takes the profile id as `student_id`).

```python
# tests/test_chat_session_service.py
import pytest
from sqlalchemy import select
from tests._uni_helpers import ensure_profile
from unipaith.models.chat_session import ChatFolder, ChatSession
from unipaith.services.intake.intake_engine_service import IntakeEngineService
from unipaith.services.chat.session_service import ChatSessionService

async def _pid(db, user):
    return await IntakeEngineService(db).profile_id_for_user(user.id)

@pytest.mark.asyncio
async def test_ensure_preset_folders_creates_eight_once(db_session, mock_student_user):
    await ensure_profile(db_session, mock_student_user)
    pid = await _pid(db_session, mock_student_user)
    svc = ChatSessionService(db_session)
    await svc.ensure_preset_folders(pid)
    await svc.ensure_preset_folders(pid)  # idempotent
    folders = (await db_session.execute(
        select(ChatFolder).where(ChatFolder.student_id == pid))).scalars().all()
    assert len([f for f in folders if f.kind == "preset"]) == 8

@pytest.mark.asyncio
async def test_create_session_auto_files_by_text(db_session, mock_student_user):
    await ensure_profile(db_session, mock_student_user)
    pid = await _pid(db_session, mock_student_user)
    svc = ChatSessionService(db_session)
    s = await svc.create_session(pid, title="How do I pay for this?")
    folder = (await db_session.execute(
        select(ChatFolder).where(ChatFolder.id == s.folder_id))).scalar_one()
    assert folder.topic_key == "needs"
```

- [ ] **Step 2: Run → FAIL** (no `session_service`).

- [ ] **Step 3: Implement** (folders + create + list; CRUD comes in Task 5)

```python
# src/unipaith/services/chat/session_service.py
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
                    student_id=student_id, kind="preset", name=spec["name"],
                    topic_key=spec["topic_key"], stage=spec["stage"], sort_order=spec["sort_order"],
                )
                self.db.add(f)
                existing[spec["topic_key"]] = f
        await self.db.flush()
        return existing

    async def create_session(
        self, student_id: UUID, *, title: str, topic_key: str | None = None,
        origin_kind: str = "manual", origin_ref: str | None = None,
        agent_session_id: str | None = None,
    ) -> ChatSession:
        folders = await self.ensure_preset_folders(student_id)
        key = topic_key or categorize(title)
        folder = folders.get(key) or folders["profile"]
        # append to the end of the folder
        n = len(
            (
                await self.db.execute(
                    select(ChatSession).where(ChatSession.folder_id == folder.id)
                )
            ).scalars().all()
        )
        s = ChatSession(
            student_id=student_id, folder_id=folder.id, title=title[:120] or "New session",
            origin_kind=origin_kind, origin_ref=origin_ref, agent_session_id=agent_session_id,
            sort_order=n,
        )
        self.db.add(s)
        await self.db.flush()
        return s

    async def list_tree(self, student_id: UUID) -> list[dict]:
        await self.ensure_preset_folders(student_id)
        folders = (
            await self.db.execute(
                select(ChatFolder).where(ChatFolder.student_id == student_id)
                .order_by(ChatFolder.kind.desc(), ChatFolder.sort_order)
            )
        ).scalars().all()
        sessions = (
            await self.db.execute(
                select(ChatSession).where(
                    ChatSession.student_id == student_id, ChatSession.status == "active"
                ).order_by(ChatSession.sort_order)
            )
        ).scalars().all()
        by_folder: dict[UUID, list[ChatSession]] = {}
        for s in sessions:
            by_folder.setdefault(s.folder_id, []).append(s)
        return [
            {"folder": f, "sessions": by_folder.get(f.id, [])} for f in folders
        ]

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
```

- [ ] **Step 4: Run → PASS.**
- [ ] **Step 5: Commit** — `git commit -m "feat(chat): ChatSessionService — preset folders, create (auto-categorize), list_tree"`

---

### Task 5: Session + folder CRUD with the invariants

**Files:**
- Modify: `src/unipaith/services/chat/session_service.py`
- Test: `tests/test_chat_session_service.py` (append)

- [ ] **Step 1: Write the failing tests**

```python
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
async def test_reorder_sessions_within_folder(db_session, mock_student_user):
    await ensure_profile(db_session, mock_student_user)
    pid = await _pid(db_session, mock_student_user)
    svc = ChatSessionService(db_session)
    a = await svc.create_session(pid, title="compare schools")   # → schools, order 0
    b = await svc.create_session(pid, title="add a school")       # → schools, order 1
    await svc.reorder_sessions(pid, a.folder_id, [b.id, a.id])
    assert (await svc._get_owned_session(pid, b.id)).sort_order == 0
    assert (await svc._get_owned_session(pid, a.id)).sort_order == 1
```

- [ ] **Step 2: Run → FAIL** (methods missing).

- [ ] **Step 3: Implement** (append to `ChatSessionService`)

```python
    async def update_session(
        self, student_id: UUID, session_id: UUID, *,
        title: str | None = None, pinned: bool | None = None, sort_order: int | None = None,
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
        # Only reorders WITHIN the folder — a session is never moved across folders
        # (auto-categorization owns folder placement).
        rows = {
            s.id: s
            for s in (
                await self.db.execute(
                    select(ChatSession).where(
                        ChatSession.student_id == student_id, ChatSession.folder_id == folder_id
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
            (
                await self.db.execute(
                    select(ChatFolder).where(ChatFolder.student_id == student_id)
                )
            ).scalars().all()
        )
        f = ChatFolder(student_id=student_id, kind="custom", name=name[:80] or "Folder", sort_order=n)
        self.db.add(f)
        await self.db.flush()
        return f

    async def update_folder(
        self, student_id: UUID, folder_id: UUID, *, name: str | None = None,
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
```

- [ ] **Step 4: Run → PASS.**
- [ ] **Step 5: Commit** — `git commit -m "feat(chat): session/folder CRUD with preset-protection + within-folder reorder"`

---

### Task 6: Context-spawn (create a session from an app object)

**Files:**
- Modify: `src/unipaith/services/chat/session_service.py`
- Test: `tests/test_chat_session_service.py` (append)

- [ ] **Step 1: Failing test**

```python
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
```

- [ ] **Step 2: Run → FAIL.**

- [ ] **Step 3: Implement** (append) — origin_kind → topic map, falls back to text categorize.

```python
    _ORIGIN_TOPIC = {
        "discover_program": "schools", "discover_school": "schools",
        "scholarship": "needs", "event": "connect", "peer": "connect", "upload": "profile",
    }

    async def spawn_from_context(
        self, student_id: UUID, *, origin_kind: str, origin_ref: str | None, title: str
    ) -> ChatSession:
        topic = self._ORIGIN_TOPIC.get(origin_kind) or categorize(title)
        return await self.create_session(
            student_id, title=title, topic_key=topic,
            origin_kind=origin_kind, origin_ref=origin_ref,
        )
```

- [ ] **Step 4: Run → PASS.** **Step 5: Commit** — `git commit -m "feat(chat): context-spawn sessions (origin_kind → folder)"`

---

### Task 7: API router + schemas

**Files:**
- Create: `src/unipaith/api/chat_sessions.py`
- Modify: `src/unipaith/api/router.py`
- Test: `tests/test_chat_sessions_api.py`

- [ ] **Step 1: Failing tests** (mirror `tests/test_enrichment_api.py`)

```python
# tests/test_chat_sessions_api.py
import pytest
from tests._uni_helpers import ensure_profile
BASE = "/api/v1/students/me/chat"

@pytest.mark.asyncio
async def test_folders_tree_has_eight_presets(student_client, db_session, mock_student_user):
    await ensure_profile(db_session, mock_student_user)
    r = await student_client.get(f"{BASE}/folders")
    assert r.status_code == 200, r.text
    presets = [f for f in r.json()["folders"] if f["kind"] == "preset"]
    assert len(presets) == 8

@pytest.mark.asyncio
async def test_create_session_auto_categorizes(student_client, db_session, mock_student_user):
    await ensure_profile(db_session, mock_student_user)
    r = await student_client.post(f"{BASE}/sessions", json={"title": "How do I pay for this?"})
    assert r.status_code == 200, r.text
    assert r.json()["topic_key"] == "needs"

@pytest.mark.asyncio
async def test_delete_preset_folder_rejected(student_client, db_session, mock_student_user):
    await ensure_profile(db_session, mock_student_user)
    tree = (await student_client.get(f"{BASE}/folders")).json()["folders"]
    schools = next(f for f in tree if f.get("topic_key") == "schools")
    r = await student_client.delete(f"{BASE}/folders/{schools['id']}")
    assert r.status_code == 400, r.text
```

- [ ] **Step 2: Run → FAIL.**

- [ ] **Step 3: Implement the router**

```python
# src/unipaith/api/chat_sessions.py
"""Uni chat-tab sessions API — /students/me/chat/* (folders + sessions CRUD)."""
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
    return {"id": str(f.id), "name": f.name, "kind": f.kind,
            "topic_key": f.topic_key, "stage": f.stage, "sort_order": f.sort_order}


def _session(s) -> dict:
    folder = s.folder if "folder" in s.__dict__ else None
    return {"id": str(s.id), "title": s.title, "pinned": s.pinned, "sort_order": s.sort_order,
            "folder_id": str(s.folder_id), "origin_kind": s.origin_kind,
            "topic_key": folder.topic_key if folder else None}


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
    return {"folders": [{**_folder(node["folder"]),
                         "sessions": [_session(s) for s in node["sessions"]]} for node in tree]}


@router.post("/sessions")
async def create_session(body: SessionCreate, user: User = Depends(require_student),
                         db: AsyncSession = Depends(get_db)):
    pid = await _pid(db, user)
    s = await ChatSessionService(db).create_session(
        pid, title=body.title, topic_key=body.topic_key,
        origin_kind=body.origin_kind, origin_ref=body.origin_ref)
    await db.refresh(s, ["folder"])
    return _session(s)


@router.patch("/sessions/{session_id}")
async def patch_session(session_id: UUID, body: SessionPatch,
                        user: User = Depends(require_student), db: AsyncSession = Depends(get_db)):
    pid = await _pid(db, user)
    s = await ChatSessionService(db).update_session(
        pid, session_id, title=body.title, pinned=body.pinned, sort_order=body.sort_order)
    return _session(s)


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: UUID, user: User = Depends(require_student),
                         db: AsyncSession = Depends(get_db)):
    await ChatSessionService(db).delete_session(await _pid(db, user), session_id)
    return {"ok": True}


@router.post("/sessions/reorder")
async def reorder(body: ReorderIn, user: User = Depends(require_student),
                  db: AsyncSession = Depends(get_db)):
    await ChatSessionService(db).reorder_sessions(await _pid(db, user), body.folder_id,
                                                  body.ordered_ids)
    return {"ok": True}


@router.post("/folders")
async def create_folder(body: FolderCreate, user: User = Depends(require_student),
                        db: AsyncSession = Depends(get_db)):
    f = await ChatSessionService(db).create_folder(await _pid(db, user), name=body.name)
    return _folder(f)


@router.patch("/folders/{folder_id}")
async def patch_folder(folder_id: UUID, body: FolderPatch,
                       user: User = Depends(require_student), db: AsyncSession = Depends(get_db)):
    f = await ChatSessionService(db).update_folder(
        await _pid(db, user), folder_id, name=body.name, sort_order=body.sort_order)
    return _folder(f)


@router.delete("/folders/{folder_id}")
async def delete_folder(folder_id: UUID, user: User = Depends(require_student),
                        db: AsyncSession = Depends(get_db)):
    await ChatSessionService(db).delete_folder(await _pid(db, user), folder_id)
    return {"ok": True}
```

- [ ] **Step 2b: Register in `api/router.py`** — `from unipaith.api.chat_sessions import router as chat_sessions_router` and `api_router.include_router(chat_sessions_router)` next to the enrichment router.

- [ ] **Step 4: Run → PASS.** **Step 5: Commit** — `git commit -m "feat(chat): /students/me/chat folders + sessions API"`

---

### Task 8: Backfill migration — preset folders + name existing discovery threads

**Files:**
- Create: `alembic/versions/chatsessbf1_backfill_chat_sessions.py`

- [ ] **Step 1: Write the migration** (`down_revision = "chatsess1"`). Idempotent, sync `Session`. For every student profile, insert the 8 preset folders (skip existing); for each existing `discovery_sessions` row, insert a `chat_sessions` row titled from its track, filed under the matching topic folder (`profile`→profile, `goals`→goals, `needs`→needs, `discovery`→profile), carrying `agent_session_id`.

```python
"""backfill chat folders + name existing discovery threads

Revision ID: chatsessbf1
Revises: chatsess1
Create Date: 2026-06-19
"""
from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op

revision = "chatsessbf1"  # pragma: allowlist secret
down_revision = "chatsess1"  # pragma: allowlist secret
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_PRESETS = [("profile","Profile","discovery",0),("goals","Goals","discovery",1),
            ("needs","Needs","discovery",2),("strategy","Strategy","recommendation",3),
            ("schools","Schools","recommendation",4),("connect","Connect","application",5),
            ("prepare","Prepare","application",6),("manage","Manage","application",7)]
_TRACK_TITLE = {"profile":"Your story","goals":"Your goals","needs":"What you need",
                "discovery":"Getting to know you"}

def upgrade() -> None:
    bind = op.get_bind()
    sids = [r[0] for r in bind.execute(sa.text("SELECT id FROM student_profiles"))]
    for sid in sids:
        for key, name, stage, order in _PRESETS:
            bind.execute(sa.text(
                "INSERT INTO chat_folders (id, student_id, name, kind, topic_key, stage, sort_order)"
                " VALUES (gen_random_uuid(), :sid, :n, 'preset', :k, :st, :o)"
                " ON CONFLICT (student_id, topic_key) DO NOTHING"),
                {"sid": sid, "n": name, "k": key, "st": stage, "o": order})
    # name existing discovery threads into chat_sessions
    rows = bind.execute(sa.text(
        "SELECT id, student_id, track, agent_session_id FROM discovery_sessions"))
    for (did, sid, track, agent_sid) in rows:
        topic = "profile" if track == "discovery" else (track if track in ("goals","needs") else "profile")
        fid = bind.execute(sa.text(
            "SELECT id FROM chat_folders WHERE student_id=:sid AND topic_key=:k"),
            {"sid": sid, "k": topic}).scalar()
        if fid is None:
            continue
        exists = bind.execute(sa.text(
            "SELECT 1 FROM chat_sessions WHERE student_id=:sid AND agent_session_id IS NOT DISTINCT FROM :a AND title=:t"),
            {"sid": sid, "a": agent_sid, "t": _TRACK_TITLE.get(track, "Session")}).scalar()
        if exists:
            continue
        bind.execute(sa.text(
            "INSERT INTO chat_sessions (id, student_id, folder_id, title, origin_kind, agent_session_id)"
            " VALUES (gen_random_uuid(), :sid, :fid, :t, 'manual', :a)"),
            {"sid": sid, "fid": fid, "t": _TRACK_TITLE.get(track, "Session"), "a": agent_sid})

def downgrade() -> None:
    pass  # data backfill — non-reversible
```

- [ ] **Step 2: `alembic heads` → ONE (`chatsessbf1`); `alembic upgrade head`.**
- [ ] **Step 3: Commit** — `git commit -m "feat(chat): backfill preset folders + name existing discovery threads"`

---

### Task 9: Full verify + ship

- [ ] Run the new suites + a broad regression: `pytest tests/test_chat_*.py tests/test_enrichment_api.py tests/test_discovery*.py -q`.
- [ ] `ruff check` + `ruff format` the new files; confirm `alembic heads` is single.
- [ ] Commit, push a fresh branch off `origin/main`, PR, squash-merge, verify the deploy + `GET api.unipaith.co/api/v1/students/me/chat/folders` responds (401/200, not 404).

---

## Self-review

- **Spec coverage** (chat-tab spec §3): folders=topics preset-protected ✓ (Task 1 CHECK + Task 5 delete/rename guards) · custom folders ✓ (Task 5) · sessions-in-folders ✓ (Task 1 FK) · pin/order ✓ (Task 1 cols + Task 5) · auto-categorization ✓ (Task 3 + Task 4) · context-spawn ✓ (Task 6) · CRUD ✓ (Task 7) · backfill ✓ (Task 8). No-cross-folder-move ✓ (reorder is folder-scoped; PATCH has no folder field).
- **Placeholders:** none — every step has runnable code/commands.
- **Type consistency:** `ChatSessionService` method names (`ensure_preset_folders`, `create_session`, `list_tree`, `update_session`, `delete_session`, `reorder_sessions`, `create_folder`, `update_folder`, `delete_folder`, `spawn_from_context`) are used identically across Tasks 4–7. `topic_key`, `folder_id`, `origin_kind` consistent.
- **Open follow-ups (not blocking this plan):** LLM-backed categorizer (the deterministic seam is replaceable); wiring `agent_session_id` when the managed-agent stream creates a session; the frontend consuming `/students/me/chat/*` (lands with the chat-tab UI build).

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from unipaith.models.base import Base


class StudentEngagementSignal(Base):
    __tablename__ = "student_engagement_signals"
    __table_args__ = (
        Index("ix_engagement_student_program_type", "student_id", "program_id", "signal_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("programs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    signal_type: Mapped[str] = mapped_column(String(30), nullable=False)
    signal_value: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class SavedList(Base):
    __tablename__ = "saved_lists"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False
    )
    list_name: Mapped[str] = mapped_column(String(100), nullable=False, default="My List")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    items: Mapped[list[SavedListItem]] = relationship(
        back_populates="saved_list", cascade="all, delete-orphan"
    )


class SavedListItem(Base):
    __tablename__ = "saved_list_items"
    __table_args__ = (UniqueConstraint("list_id", "program_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    list_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("saved_lists.id", ondelete="CASCADE"), nullable=False
    )
    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("programs.id", ondelete="CASCADE"), nullable=False
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text)
    # Spec 13 §4.2 (G-S5) — student-set priority on a saved program, persisted
    # server-side (was localStorage-only). One of:
    # considering | planning_to_apply | applied | dropped.
    priority: Mapped[str] = mapped_column(
        String(20), nullable=False, default="considering", server_default=text("'considering'")
    )
    # Spec 13 §4.3 — free-text tags from the student's own tag dictionary.
    tags: Mapped[list] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )

    saved_list: Mapped[SavedList] = relationship(back_populates="items")


class StudentCompareItem(Base):
    """Spec 10 §8 — a program in the student's global compare tray.

    Server-persisted so the compare set accumulates across sessions and
    devices. Capped at 4 programs in the service layer (spec 10 §8).
    """

    __tablename__ = "student_compare_lists"
    __table_args__ = (UniqueConstraint("student_id", "program_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("programs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class StudentCalendar(Base):
    """Spec 16 — student-CREATED calendar entries (reminders + work blocks).

    Admissions items (deadlines, interviews, events, offers) are NOT stored
    here; they are aggregated live from their source tables by
    ``CalendarService``. This table owns only the items the student adds
    themselves, plus the fields Spec 16 §6 requires on a ``CalendarItem``.
    """

    __tablename__ = "student_calendar"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # 'reminder' | 'work_block' (Spec 16 §4 student-created types).
    entry_type: Mapped[str | None] = mapped_column(String(20))
    reference_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reminder_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Spec 16 §6 CalendarItem fields ---------------------------------------
    # Spec 17 reuses `status` ("completed") to mark an inbox-linked deadline
    # done when the thread is marked complete (via reference_id = thread id).
    status: Mapped[str] = mapped_column(String(20), default="scheduled", nullable=False)
    category: Mapped[str | None] = mapped_column(String(30))
    location: Mapped[str | None] = mapped_column(String(500))
    meeting_link: Mapped[str | None] = mapped_column(String(1000))
    application_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="SET NULL")
    )
    reminder_settings: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class CalendarItemState(Base):
    """Spec 16 §5 — per-student overlay on a DERIVED calendar item.

    Lets a student mark a deadline complete, add notes, or attach an
    off-platform confirmation without mutating the source domain table
    (application / interview / offer / event). Keyed by the calendar item's
    stable composite id, e.g. ``submission_deadline:<application_id>``.
    """

    __tablename__ = "calendar_item_states"
    __table_args__ = (UniqueConstraint("student_id", "item_key", name="uq_calendar_state_item"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    item_key: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str | None] = mapped_column(String(20))
    notes: Mapped[str | None] = mapped_column(Text)
    confirmation_url: Mapped[str | None] = mapped_column(String(1000))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class CRMRecord(Base):
    __tablename__ = "crm_records"
    __table_args__ = (Index("ix_crm_institution_student", "institution_id", "student_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    touchpoint_type: Mapped[str | None] = mapped_column(String(50))
    touchpoint_detail: Mapped[dict | None] = mapped_column(JSONB)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False
    )
    institution_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=True
    )
    program_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("programs.id", ondelete="SET NULL")
    )
    subject: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str | None] = mapped_column(String(20))
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # ── Spec 17 (Inbox) — application-threaded conversation metadata ──
    # All nullable / server-defaulted so institution messaging (Spec 29),
    # which shares this table, is unaffected.
    application_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="SET NULL"), index=True
    )
    # 'human' (admissions officer / coordinator) | 'system' (alerts, status
    # updates, AI-run notices). System threads have institution_id = NULL.
    thread_type: Mapped[str] = mapped_column(String(20), server_default="human", nullable=False)
    # needs_reply | document_requested | clarification_required |
    # interview_invite | status_update_only | completed
    action_label: Mapped[str | None] = mapped_column(String(40))
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # who the thread is waiting on: 'student' | 'school' | 'none'
    waiting_on: Mapped[str] = mapped_column(String(20), server_default="none", nullable=False)
    # category of the checklist item this thread's request maps to (Spec 15);
    # mark-complete writes application_checklists.manual_overrides[category].
    linked_checklist_item_category: Mapped[str | None] = mapped_column(String(50))

    messages: Mapped[list[Message]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # 'student' | 'admissions_officer' | 'institution' | 'system'
    sender_type: Mapped[str | None] = mapped_column(String(20))
    # Nullable (Spec 17): system messages have no human author.
    sender_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    message_body: Mapped[str] = mapped_column(Text, nullable=False)
    # Spec 17 — list of {id, name, kind: 'document'|'link', url?} attached to
    # an inbox reply. Defaults to an empty list.
    attachments: Mapped[list] = mapped_column(JSONB, server_default="[]", nullable=False)
    # delivery status: 'sent' | 'delivered' | 'read'
    status: Mapped[str] = mapped_column(String(20), server_default="sent", nullable=False)
    # Spec 17 §14 — provenance: was this reply seeded from an AI draft?
    ai_draft_used: Mapped[bool] = mapped_column(Boolean, server_default="false", nullable=False)
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    conversation: Mapped[Conversation] = relationship(back_populates="messages")


class ConversationSession(Base):
    """Persisted state for the guided-discovery conversation flow."""

    __tablename__ = "conversation_sessions"
    __table_args__ = (UniqueConstraint("student_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    current_stage: Mapped[str] = mapped_column(String(50), default="understand_context")
    active_domain: Mapped[str] = mapped_column(String(50), default="career_outcome")
    turn_count: Mapped[int] = mapped_column(Integer, default=0)
    requirements_json: Mapped[dict | None] = mapped_column(JSONB)
    conflicts_json: Mapped[dict | None] = mapped_column(JSONB)
    last_assistant_prompt: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class StudentResume(Base):
    __tablename__ = "student_resumes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False
    )
    resume_version: Mapped[int] = mapped_column(Integer, default=1)
    content: Mapped[dict | None] = mapped_column(JSONB)
    rendered_pdf_url: Mapped[str | None] = mapped_column(String(1000))
    ai_suggestions: Mapped[dict | None] = mapped_column(JSONB)
    target_program_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("programs.id", ondelete="SET NULL")
    )
    status: Mapped[str | None] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class StudentEssay(Base):
    __tablename__ = "student_essays"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False
    )
    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("programs.id", ondelete="CASCADE"), nullable=False
    )
    prompt_text: Mapped[str | None] = mapped_column(Text)
    essay_version: Mapped[int] = mapped_column(Integer, default=1)
    content: Mapped[str | None] = mapped_column(Text)
    word_count: Mapped[int | None] = mapped_column(Integer)
    ai_feedback: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[str | None] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

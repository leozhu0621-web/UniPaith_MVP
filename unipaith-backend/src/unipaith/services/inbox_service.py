"""Inbox service (Spec 17) — application-threaded conversations + system
notifications, surfaced to the student at ``/s/manage?tab=messages``.

This is a richer student-side *view* layered over the shared
``conversations`` / ``messages`` tables (also used by institution
messaging, Spec 29). Human replies reuse ``MessagingService`` for the
rate-limit + length validation; system threads are read-only here.

Action semantics (spec 17 §5):
- ``waiting_on`` flips to ``school`` when the student replies.
- "Mark complete" sets ``action_label='completed'`` and propagates to the
  linked checklist item (durably, via ``manual_overrides``) and the linked
  calendar deadline (``completed_at``).
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai.inbox_reply import (
    InboxReplyDrafter,
    InboxReplyInput,
    get_inbox_reply_drafter,
)
from unipaith.config import settings
from unipaith.core.exceptions import ForbiddenException, NotFoundException
from unipaith.models.application import Application, ApplicationChecklist
from unipaith.models.engagement import Conversation, Message, StudentCalendar
from unipaith.models.institution import Institution, Program
from unipaith.models.student import StudentProfile
from unipaith.schemas.inbox import (
    InboxMessageResponse,
    SuggestedReplyResponse,
    ThreadApplication,
    ThreadParticipant,
    ThreadResponse,
    ThreadSummary,
)
from unipaith.services.checklist_service import ChecklistService
from unipaith.services.messaging_service import MessagingService

logger = logging.getLogger(__name__)

# Action-state filter groups (spec 17 §3).
_REQUESTED_LABELS = ("document_requested", "clarification_required", "interview_invite")
# AI-assist is offered for these two (spec 17 §7).
_AI_REPLY_LABELS = ("needs_reply", "clarification_required")
# Sort priority for "most action-required".
_ACTION_PRIORITY = {
    "needs_reply": 0,
    "clarification_required": 1,
    "document_requested": 2,
    "interview_invite": 3,
    "status_update_only": 4,
    "completed": 5,
}
# Far-future sentinel so threads without a due date sort after dated ones.
_NO_DUE = datetime.max.replace(tzinfo=UTC)


def _norm_sender(sender_type: str | None) -> str:
    """Map the DB sender_type to the spec's Message.sender enum."""
    if sender_type == "student":
        return "student"
    if sender_type == "system":
        return "system"
    return "admissions_officer"  # 'institution' / 'admissions_officer' / None


class InboxService:
    def __init__(
        self,
        db: AsyncSession,
        *,
        reply_drafter: InboxReplyDrafter | None = None,
    ):
        self.db = db
        self.messaging = MessagingService(db)
        # Injectable for tests; defaults to the process singleton.
        self._drafter = reply_drafter or get_inbox_reply_drafter()

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    async def _require_student_id(self, user_id: UUID) -> UUID:
        student_id, _institution_id = await self.messaging._resolve_user_context(user_id)
        if not student_id:
            raise ForbiddenException("Only students have an inbox")
        return student_id

    async def _owned_conversation(self, student_id: UUID, thread_id: UUID) -> Conversation:
        conv = await self.db.scalar(
            select(Conversation).where(
                Conversation.id == thread_id,
                Conversation.student_id == student_id,
            )
        )
        if conv is None:
            raise NotFoundException("Conversation not found")
        return conv

    # ------------------------------------------------------------------
    # Name + linkage resolution
    # ------------------------------------------------------------------

    async def _name_maps(
        self, convs: list[Conversation]
    ) -> tuple[dict[UUID, str], dict[UUID, str], dict[UUID, UUID]]:
        """Batch-resolve program names, institution names, and the
        program→institution link for a set of conversations."""
        program_ids = {c.program_id for c in convs if c.program_id}
        institution_ids = {c.institution_id for c in convs if c.institution_id}

        program_name: dict[UUID, str] = {}
        program_institution: dict[UUID, UUID] = {}
        if program_ids:
            rows = await self.db.execute(
                select(Program.id, Program.program_name, Program.institution_id).where(
                    Program.id.in_(program_ids)
                )
            )
            for pid, pname, inst_id in rows.all():
                program_name[pid] = pname
                if inst_id:
                    program_institution[pid] = inst_id
                    institution_ids.add(inst_id)

        institution_name: dict[UUID, str] = {}
        if institution_ids:
            rows = await self.db.execute(
                select(Institution.id, Institution.name).where(Institution.id.in_(institution_ids))
            )
            institution_name = {iid: name for iid, name in rows.all()}

        return program_name, institution_name, program_institution

    async def _unread_map(self, conv_ids: list[UUID]) -> dict[UUID, int]:
        """Count messages not from the student and still unread, per thread.

        Uses ``sender_type != 'student'`` rather than ``sender_id`` so
        author-less *system* messages count as unread too."""
        if not conv_ids:
            return {}
        rows = await self.db.execute(
            select(Message.conversation_id, func.count())
            .where(
                Message.conversation_id.in_(conv_ids),
                func.coalesce(Message.sender_type, "") != "student",
                Message.read_at.is_(None),
            )
            .group_by(Message.conversation_id)
        )
        out: dict[UUID, int] = defaultdict(int)
        for cid, count in rows.all():
            out[cid] = int(count or 0)
        return out

    async def _calendar_link_map(self, conv_ids: list[UUID]) -> dict[UUID, UUID]:
        """Map thread id → linked StudentCalendar row id (via reference_id)."""
        if not conv_ids:
            return {}
        rows = await self.db.execute(
            select(StudentCalendar.reference_id, StudentCalendar.id).where(
                StudentCalendar.reference_id.in_(conv_ids)
            )
        )
        return {ref: cal_id for ref, cal_id in rows.all() if ref is not None}

    def _summary(
        self,
        conv: Conversation,
        *,
        program_name: dict[UUID, str],
        institution_name: dict[UUID, str],
        program_institution: dict[UUID, UUID],
        unread: dict[UUID, int],
        calendar_link: dict[UUID, UUID],
    ) -> ThreadSummary:
        inst_id = conv.institution_id or (
            program_institution.get(conv.program_id) if conv.program_id else None
        )
        return ThreadSummary(
            id=conv.id,
            application_id=conv.application_id,
            application=ThreadApplication(
                program_name=program_name.get(conv.program_id) if conv.program_id else None,
                institution_name=institution_name.get(inst_id) if inst_id else None,
            ),
            type=conv.thread_type or "human",
            subject=conv.subject,
            action_label=conv.action_label,
            due_date=conv.due_date,
            waiting_on=conv.waiting_on or "none",
            unread=bool(unread.get(conv.id, 0)),
            last_message_at=conv.last_message_at,
            linked_checklist_item_category=conv.linked_checklist_item_category,
            linked_calendar_item_id=calendar_link.get(conv.id),
        )

    @staticmethod
    def _sort_key(summary: ThreadSummary, sort: str):
        if sort == "recent":
            last = summary.last_message_at or datetime.min.replace(tzinfo=UTC)
            return (-last.timestamp(),)
        if sort == "action_required":
            prio = _ACTION_PRIORITY.get(summary.action_label or "", 4)
            due = summary.due_date or _NO_DUE
            return (prio, due.timestamp())
        # urgent (default): student-blocked first, soonest due, unread, recent
        waiting_rank = 0 if summary.waiting_on == "student" else 1
        completed_rank = 1 if summary.action_label == "completed" else 0
        due = summary.due_date or _NO_DUE
        last = summary.last_message_at or datetime.min.replace(tzinfo=UTC)
        return (
            completed_rank,
            waiting_rank,
            due.timestamp(),
            0 if summary.unread else 1,
            -last.timestamp(),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def list_threads(
        self,
        user_id: UUID,
        *,
        application_id: UUID | None = None,
        thread_type: str | None = None,
        action_state: str | None = None,
        sort: str = "urgent",
    ) -> list[ThreadSummary]:
        student_id = await self._require_student_id(user_id)

        q = select(Conversation).where(Conversation.student_id == student_id)
        if application_id is not None:
            q = q.where(Conversation.application_id == application_id)
        if thread_type in ("human", "system"):
            q = q.where(Conversation.thread_type == thread_type)
        if action_state == "needs_reply":
            q = q.where(Conversation.action_label == "needs_reply")
        elif action_state == "requested":
            q = q.where(Conversation.action_label.in_(_REQUESTED_LABELS))
        elif action_state == "completed":
            q = q.where(Conversation.action_label == "completed")
        elif action_state == "status_update_only":
            q = q.where(Conversation.action_label == "status_update_only")

        convs = list((await self.db.execute(q)).scalars().all())
        if not convs:
            return []

        program_name, institution_name, program_institution = await self._name_maps(convs)
        conv_ids = [c.id for c in convs]
        unread = await self._unread_map(conv_ids)
        calendar_link = await self._calendar_link_map(conv_ids)

        summaries = [
            self._summary(
                c,
                program_name=program_name,
                institution_name=institution_name,
                program_institution=program_institution,
                unread=unread,
                calendar_link=calendar_link,
            )
            for c in convs
        ]
        summaries.sort(key=lambda s: self._sort_key(s, sort))
        return summaries

    async def get_thread(self, user_id: UUID, thread_id: UUID) -> ThreadResponse:
        student_id = await self._require_student_id(user_id)
        conv = await self._owned_conversation(student_id, thread_id)

        # Mark school/system messages read on open (system msgs have no
        # sender_id, so key on sender_type).
        await self.db.execute(
            update(Message)
            .where(
                Message.conversation_id == thread_id,
                func.coalesce(Message.sender_type, "") != "student",
                Message.read_at.is_(None),
            )
            .values(read_at=datetime.now(UTC))
        )
        await self.db.flush()

        msgs = list(
            (
                await self.db.execute(
                    select(Message)
                    .where(Message.conversation_id == thread_id)
                    .order_by(Message.sent_at.asc())
                )
            )
            .scalars()
            .all()
        )

        program_name, institution_name, program_institution = await self._name_maps([conv])
        unread = await self._unread_map([conv.id])
        calendar_link = await self._calendar_link_map([conv.id])
        summary = self._summary(
            conv,
            program_name=program_name,
            institution_name=institution_name,
            program_institution=program_institution,
            unread=unread,
            calendar_link=calendar_link,
        )

        participants = await self._participants(conv, summary)
        messages = [
            InboxMessageResponse(
                id=m.id,
                thread_id=m.conversation_id,
                sender=_norm_sender(m.sender_type),
                body=m.message_body,
                attachments=list(m.attachments or []),
                sent_at=m.sent_at,
                read_at=m.read_at,
                status=m.status or "sent",
            )
            for m in msgs
        ]
        return ThreadResponse(**summary.model_dump(), participants=participants, messages=messages)

    async def _participants(
        self, conv: Conversation, summary: ThreadSummary
    ) -> list[ThreadParticipant]:
        row = (
            await self.db.execute(
                select(StudentProfile.first_name, StudentProfile.last_name).where(
                    StudentProfile.id == conv.student_id
                )
            )
        ).first()
        student_name = " ".join(p for p in (row or ("", "")) if p).strip() if row else ""
        out = [
            ThreadParticipant(
                id=str(conv.student_id),
                role="student",
                name=student_name or "You",
            )
        ]
        if (conv.thread_type or "human") == "system":
            out.append(ThreadParticipant(id="system", role="system", name="UniPaith"))
        else:
            inst = summary.application.institution_name or "Admissions"
            out.append(
                ThreadParticipant(
                    id=str(conv.institution_id or "institution"),
                    role="admissions_officer",
                    name=f"{inst} Admissions",
                )
            )
        return out

    async def post_message(
        self,
        user_id: UUID,
        thread_id: UUID,
        *,
        body: str,
        attachments: list[dict] | None = None,
        ai_draft_used: bool = False,
    ) -> InboxMessageResponse:
        student_id = await self._require_student_id(user_id)
        conv = await self._owned_conversation(student_id, thread_id)

        # Reuse MessagingService for rate-limit + length validation.
        message = await self.messaging.send_message(
            conversation_id=thread_id,
            sender_id=user_id,
            content=body,
            sender_type="student",
        )
        # Reassign (not in-place mutate) so SQLAlchemy detects the JSONB change.
        message.attachments = list(attachments or [])
        message.status = "sent"
        message.ai_draft_used = bool(ai_draft_used)

        # The student has responded → the ball is now in the school's court.
        conv.waiting_on = "school"
        if conv.action_label in ("needs_reply", "clarification_required"):
            conv.action_label = "status_update_only"

        await self.db.flush()
        return InboxMessageResponse(
            id=message.id,
            thread_id=message.conversation_id,
            sender="student",
            body=message.message_body,
            attachments=list(message.attachments or []),
            sent_at=message.sent_at,
            read_at=message.read_at,
            status=message.status or "sent",
        )

    async def mark_complete(self, user_id: UUID, thread_id: UUID) -> ThreadResponse:
        student_id = await self._require_student_id(user_id)
        conv = await self._owned_conversation(student_id, thread_id)

        conv.action_label = "completed"
        conv.waiting_on = "none"

        # Propagate to the linked checklist item (durably) + calendar deadline.
        await self._complete_linked_checklist(student_id, conv)
        await self._complete_linked_calendar(thread_id)

        await self.db.flush()
        return await self.get_thread(user_id, thread_id)

    async def _complete_linked_checklist(self, student_id: UUID, conv: Conversation) -> None:
        """Mark the linked checklist item complete via the Spec 15
        ``manual_complete`` flag — durable across ``generate_checklist``
        (``_load_manual_keys`` re-applies it by item key)."""
        category = conv.linked_checklist_item_category
        if not category or conv.application_id is None:
            return
        checklist = await self.db.scalar(
            select(ApplicationChecklist)
            .join(Application, Application.program_id == ApplicationChecklist.program_id)
            .where(
                Application.id == conv.application_id,
                ApplicationChecklist.student_id == student_id,
            )
        )
        if checklist is None:
            # Generate one so there's a real (keyed) item to mark complete.
            try:
                checklist = await ChecklistService(self.db).generate_checklist(
                    student_id, conv.application_id
                )
            except Exception:  # noqa: BLE001 — best-effort; calendar still updates
                return
        if not checklist.items:
            return

        # Match by item key or category; reassigning the list triggers the
        # ORM JSONB change detection (no flag_modified needed).
        items = [dict(it) for it in checklist.items]
        changed = False
        for it in items:
            if it.get("key") == category or it.get("category") == category:
                it["manual_complete"] = True
                it["status"] = "completed"
                it["completed"] = True
                changed = True
        if changed:
            checklist.items = items
            checklist.completion_percentage = ChecklistService._compute_completion(items)

    async def _complete_linked_calendar(self, thread_id: UUID) -> None:
        """Mark the linked calendar deadline done via the Spec 16
        ``status`` column (linkage by reference_id = thread id)."""
        await self.db.execute(
            update(StudentCalendar)
            .where(
                StudentCalendar.reference_id == thread_id,
                StudentCalendar.status != "completed",
            )
            .values(status="completed")
        )

    async def suggested_reply(
        self, user_id: UUID, thread_id: UUID
    ) -> SuggestedReplyResponse | None:
        """Return an AI-drafted reply, or None when unavailable (flag off /
        consent denied / agent failure) — the UI hides the card (spec 17 §7)."""
        if not settings.ai_inbox_v2_enabled:
            return None
        student_id = await self._require_student_id(user_id)
        conv = await self._owned_conversation(student_id, thread_id)

        # Only offered for needs_reply / clarification_required threads.
        if conv.action_label not in _AI_REPLY_LABELS:
            return None

        thread = await self.get_thread(user_id, thread_id)
        student_name = next((p.name for p in thread.participants if p.role == "student"), "")
        input_view = InboxReplyInput(
            student_id=student_id,
            student_name=student_name if student_name != "You" else "",
            thread_subject=conv.subject or "",
            action_label=conv.action_label,
            waiting_on=conv.waiting_on,
            due_date=conv.due_date.isoformat() if conv.due_date else None,
            application={
                "program_name": thread.application.program_name,
                "institution_name": thread.application.institution_name,
            },
            messages=[{"sender": m.sender, "body": m.body} for m in thread.messages],
        )
        result = await self._drafter.draft(input_view=input_view, db=self.db)
        if result is None:
            return None
        return SuggestedReplyResponse(
            draft=result.draft,
            tone=result.tone,
            length=result.length,
            alternate_drafts=result.alternate_drafts,
        )

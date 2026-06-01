"""Institution inbox service (Spec 29) — staff view over shared conversations."""

from __future__ import annotations

import logging
import uuid as uuid_mod
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai.institution_inbox_reply import (
    InstitutionReplyDrafter,
    InstitutionReplyInput,
    get_institution_reply_drafter,
)
from unipaith.config import settings
from unipaith.core.exceptions import BadRequestException, ForbiddenException, NotFoundException
from unipaith.models.application import Application, ApplicationChecklist
from unipaith.models.engagement import Conversation, Message, StudentCalendar
from unipaith.models.institution import Institution, Program, TargetSegment
from unipaith.models.student import StudentDataConsent, StudentProfile
from unipaith.models.user import User
from unipaith.schemas.inbox import InboxMessageResponse
from unipaith.schemas.institution_inbox import (
    REASON_CODES,
    REASON_REQUIRES_DUE,
    REASON_TO_ACTION_LABEL,
    AssignThreadRequest,
    BulkMessageRequest,
    BulkMessageResponse,
    InstProgramRef,
    InstStudentRef,
    InstSuggestedReplyResponse,
    InstThreadContext,
    InstThreadParticipant,
    InstThreadResponse,
    InstThreadSummary,
    PostInstInboxMessageRequest,
)
from unipaith.services.audit_service import AuditService
from unipaith.services.checklist_service import ChecklistService
from unipaith.services.communication_service import CommunicationService, _personalize
from unipaith.services.messaging_service import MessagingService
from unipaith.services.notification_service import NotificationService
from unipaith.services.segment_service import SegmentService

logger = logging.getLogger(__name__)

_ACTION_TO_REASON = {v: k for k, v in REASON_TO_ACTION_LABEL.items()}

_MARKETING_REASONS = frozenset({"status_update", "general_reply"})


def _derive_status(conv: Conversation) -> str:
    if (conv.status or "").lower() == "closed":
        return "closed"
    if conv.waiting_on == "student":
        return "awaiting_student"
    if conv.waiting_on == "school":
        return "awaiting_us"
    return "open"


def _norm_sender(sender_type: str | None) -> str:
    if sender_type == "student":
        return "student"
    if sender_type == "system":
        return "system"
    return "admissions_officer"


class InstitutionInboxService:
    def __init__(
        self,
        db: AsyncSession,
        *,
        reply_drafter: InstitutionReplyDrafter | None = None,
    ):
        self.db = db
        self.messaging = MessagingService(db)
        self._drafter = reply_drafter or get_institution_reply_drafter()

    async def _require_institution_id(self, user_id: UUID) -> UUID:
        _student_id, institution_id = await self.messaging._resolve_user_context(user_id)
        if not institution_id:
            raise ForbiddenException("Only institution admins have an inbox")
        return institution_id

    async def _owned_conversation(self, institution_id: UUID, thread_id: UUID) -> Conversation:
        conv = await self.db.scalar(
            select(Conversation).where(
                Conversation.id == thread_id,
                Conversation.institution_id == institution_id,
                Conversation.thread_type == "human",
            )
        )
        if conv is None:
            raise NotFoundException("Conversation not found")
        return conv

    async def _student_names(self, student_ids: set[UUID]) -> dict[UUID, str]:
        if not student_ids:
            return {}
        rows = await self.db.execute(
            select(
                StudentProfile.id,
                StudentProfile.first_name,
                StudentProfile.last_name,
                StudentProfile.preferred_name,
            ).where(StudentProfile.id.in_(student_ids))
        )
        out: dict[UUID, str] = {}
        for sid, first, last, pref in rows.all():
            name = (pref or "").strip() or " ".join(p for p in (first, last) if p).strip()
            out[sid] = name or "Applicant"
        return out

    async def _context_for(self, conv: Conversation) -> InstThreadContext:
        if conv.application_id is None:
            return InstThreadContext()
        app = await self.db.scalar(select(Application).where(Application.id == conv.application_id))
        if app is None:
            return InstThreadContext()
        checklist = await self.db.scalar(
            select(ApplicationChecklist).where(
                ApplicationChecklist.student_id == conv.student_id,
                ApplicationChecklist.program_id == app.program_id,
            )
        )
        items = list(checklist.items) if checklist and checklist.items else []
        if not items and conv.application_id:
            try:
                checklist = await ChecklistService(self.db).generate_checklist(
                    conv.student_id, conv.application_id
                )
                items = list(checklist.items or [])
            except Exception:  # noqa: BLE001
                items = []
        total = len(items)
        complete = sum(1 for it in items if it.get("completed") or it.get("manual_complete"))
        missing = [
            str(it.get("label") or it.get("key") or it.get("category"))
            for it in items
            if not (it.get("completed") or it.get("manual_complete"))
        ]
        missing = [m for m in missing if m][:8]
        return InstThreadContext(
            stage=app.status,
            checklist_complete=complete,
            checklist_total=total,
            missing_items=missing,
        )

    async def _unread_counts(self, conv_ids: list[UUID]) -> dict[UUID, int]:
        if not conv_ids:
            return {}
        rows = await self.db.execute(
            select(Message.conversation_id, func.count())
            .where(
                Message.conversation_id.in_(conv_ids),
                Message.sender_type == "student",
                Message.read_at.is_(None),
            )
            .group_by(Message.conversation_id)
        )
        return {cid: int(n or 0) for cid, n in rows.all()}

    def _summary(
        self,
        conv: Conversation,
        *,
        student_name: str,
        program_name: str | None,
        unread: int,
        context: InstThreadContext,
    ) -> InstThreadSummary:
        return InstThreadSummary(
            id=conv.id,
            application_id=conv.application_id,
            student_ref=InstStudentRef(id=conv.student_id, name=student_name),
            program_ref=InstProgramRef(id=conv.program_id, name=program_name),
            assigned_to=conv.assigned_to,
            reason_label=_ACTION_TO_REASON.get(conv.action_label or ""),
            action_label=conv.action_label,
            status=_derive_status(conv),
            due_date=conv.due_date,
            waiting_on=conv.waiting_on or "none",
            unread_count=unread,
            last_message_at=conv.last_message_at,
            subject=conv.subject,
            context=context,
        )

    async def list_threads(
        self,
        user_id: UUID,
        *,
        filter: str = "all",
        reason: str | None = None,
        program_id: UUID | None = None,
    ) -> list[InstThreadSummary]:
        institution_id = await self._require_institution_id(user_id)
        q = select(Conversation).where(
            Conversation.institution_id == institution_id,
            Conversation.thread_type == "human",
        )
        if filter == "mine":
            q = q.where(Conversation.assigned_to == user_id)
        elif filter == "unassigned":
            q = q.where(Conversation.assigned_to.is_(None))
        if program_id:
            q = q.where(Conversation.program_id == program_id)
        if reason and reason in REASON_CODES:
            action = REASON_TO_ACTION_LABEL[reason]
            q = q.where(Conversation.action_label == action)

        convs = list(
            (await self.db.execute(q.order_by(Conversation.last_message_at.desc()))).scalars()
        )
        if not convs:
            return []

        student_names = await self._student_names({c.student_id for c in convs})
        program_names: dict[UUID, str] = {}
        pids = {c.program_id for c in convs if c.program_id}
        if pids:
            rows = await self.db.execute(
                select(Program.id, Program.program_name).where(Program.id.in_(pids))
            )
            program_names = {pid: name for pid, name in rows.all()}

        unread = await self._unread_counts([c.id for c in convs])
        summaries: list[InstThreadSummary] = []
        for c in convs:
            ctx = await self._context_for(c)
            summaries.append(
                self._summary(
                    c,
                    student_name=student_names.get(c.student_id, "Applicant"),
                    program_name=program_names.get(c.program_id) if c.program_id else None,
                    unread=unread.get(c.id, 0),
                    context=ctx,
                )
            )
        summaries.sort(
            key=lambda s: (
                0 if s.status == "awaiting_us" else 1,
                0 if s.unread_count else 1,
                -(s.last_message_at.timestamp() if s.last_message_at else 0),
            )
        )
        return summaries

    async def get_thread(self, user_id: UUID, thread_id: UUID) -> InstThreadResponse:
        institution_id = await self._require_institution_id(user_id)
        conv = await self._owned_conversation(institution_id, thread_id)

        await self.db.execute(
            update(Message)
            .where(
                Message.conversation_id == thread_id,
                Message.sender_type == "student",
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

        inst_name = await self.db.scalar(
            select(Institution.name).where(Institution.id == institution_id)
        )
        program_name = None
        if conv.program_id:
            program_name = await self.db.scalar(
                select(Program.program_name).where(Program.id == conv.program_id)
            )
        student_names = await self._student_names({conv.student_id})
        ctx = await self._context_for(conv)
        summary = self._summary(
            conv,
            student_name=student_names.get(conv.student_id, "Applicant"),
            program_name=program_name,
            unread=0,
            context=ctx,
        )

        staff_name = "Admissions"
        if conv.assigned_to:
            row = await self.db.execute(
                select(User.first_name, User.last_name).where(User.id == conv.assigned_to)
            )
            u = row.first()
            if u:
                staff_name = " ".join(p for p in u if p).strip() or staff_name

        participants = [
            InstThreadParticipant(
                id=str(conv.student_id),
                role="student",
                name=summary.student_ref.name,
            ),
            InstThreadParticipant(
                id=str(conv.assigned_to or institution_id),
                role="admissions_officer",
                name=f"{staff_name}, {inst_name or 'Admissions'}",
            ),
        ]
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
        return InstThreadResponse(
            **summary.model_dump(), participants=participants, messages=messages
        )

    async def post_message(
        self,
        user_id: UUID,
        thread_id: UUID,
        body: PostInstInboxMessageRequest,
    ) -> InboxMessageResponse:
        institution_id = await self._require_institution_id(user_id)
        if body.reason_code not in REASON_CODES:
            raise BadRequestException(f"Invalid reason_code: {body.reason_code}")
        if body.reason_code in REASON_REQUIRES_DUE and body.due_date is None:
            raise BadRequestException("due_date is required for this reason code")

        conv = await self._owned_conversation(institution_id, thread_id)
        action_label = REASON_TO_ACTION_LABEL[body.reason_code]

        message = await self.messaging.send_message(
            conversation_id=thread_id,
            sender_id=user_id,
            content=body.body,
            sender_type="institution",
        )
        message.attachments = [a.model_dump() for a in body.attachments]
        message.ai_draft_used = bool(body.ai_draft_used)
        message.status = "sent"

        conv.action_label = action_label
        conv.waiting_on = "student"
        conv.due_date = body.due_date
        conv.status = "open"
        if body.checklist_category or body.attachments:
            conv.linked_checklist_item_category = (
                body.checklist_category
                or (body.attachments[0].name if body.attachments else None)
                or "document"
            )
        await self._sync_checklist_request(conv)
        await self._sync_calendar_deadline(conv)
        await self._notify_student(conv, body.reason_code, body.body)
        await AuditService(self.db).log(
            institution_id=institution_id,
            actor_user_id=user_id,
            action="inbox_message_sent",
            entity_type="conversation",
            entity_id=str(thread_id),
            application_id=conv.application_id,
            description=f"Reason: {body.reason_code}",
            metadata_json={
                "reason_code": body.reason_code,
                "ai_assisted": body.ai_draft_used,
            },
        )
        await self.db.flush()
        return InboxMessageResponse(
            id=message.id,
            thread_id=message.conversation_id,
            sender="admissions_officer",
            body=message.message_body,
            attachments=list(message.attachments or []),
            sent_at=message.sent_at,
            read_at=message.read_at,
            status=message.status,
        )

    async def assign_thread(
        self,
        user_id: UUID,
        thread_id: UUID,
        body: AssignThreadRequest,
    ) -> InstThreadSummary:
        institution_id = await self._require_institution_id(user_id)
        conv = await self._owned_conversation(institution_id, thread_id)
        old = str(conv.assigned_to) if conv.assigned_to else None
        new_id = body.staff_user_id or user_id
        conv.assigned_to = new_id
        await AuditService(self.db).log(
            institution_id=institution_id,
            actor_user_id=user_id,
            action="inbox_thread_assigned",
            entity_type="conversation",
            entity_id=str(thread_id),
            application_id=conv.application_id,
            old_value={"assigned_to": old},
            new_value={"assigned_to": str(new_id)},
        )
        await self.db.flush()
        thread = await self.get_thread(user_id, thread_id)
        return InstThreadSummary(**thread.model_dump(exclude={"participants", "messages"}))

    async def close_thread(self, user_id: UUID, thread_id: UUID) -> InstThreadSummary:
        institution_id = await self._require_institution_id(user_id)
        conv = await self._owned_conversation(institution_id, thread_id)
        conv.status = "closed"
        conv.waiting_on = "none"
        conv.action_label = "completed"
        await AuditService(self.db).log(
            institution_id=institution_id,
            actor_user_id=user_id,
            action="inbox_thread_closed",
            entity_type="conversation",
            entity_id=str(thread_id),
            application_id=conv.application_id,
        )
        await self.db.flush()
        thread = await self.get_thread(user_id, thread_id)
        return InstThreadSummary(**thread.model_dump(exclude={"participants", "messages"}))

    async def ai_draft(
        self, user_id: UUID, thread_id: UUID, *, reason_code: str | None = None
    ) -> InstSuggestedReplyResponse | None:
        if not settings.ai_institution_inbox_v2_enabled:
            return None
        institution_id = await self._require_institution_id(user_id)
        conv = await self._owned_conversation(institution_id, thread_id)
        thread = await self.get_thread(user_id, thread_id)
        inst_name = thread.program_ref.name or "Admissions"
        result = await self._drafter.draft(
            input_view=InstitutionReplyInput(
                institution_name=inst_name,
                student_name=thread.student_ref.name,
                thread_subject=conv.subject or "",
                reason_code=reason_code or thread.reason_label,
                action_label=conv.action_label,
                application={
                    "application_id": str(conv.application_id) if conv.application_id else None,
                    "stage": thread.context.stage,
                },
                context=thread.context.model_dump(),
                messages=[{"sender": m.sender, "body": m.body} for m in thread.messages],
            ),
            db=self.db,
            student_id=conv.student_id,
        )
        if result is None or not result.draft.strip():
            return None
        return InstSuggestedReplyResponse(
            draft=result.draft,
            tone=result.tone,
            length=result.length,
            alternate_drafts=result.alternate_drafts,
            suggested_reason_code=result.suggested_reason_code,
        )

    async def bulk_message(
        self,
        user_id: UUID,
        body: BulkMessageRequest,
    ) -> BulkMessageResponse:
        institution_id = await self._require_institution_id(user_id)
        if body.reason_code not in REASON_CODES:
            raise BadRequestException(f"Invalid reason_code: {body.reason_code}")

        student_ids: set[UUID] = set()
        app_by_student: dict[UUID, UUID] = {}

        if body.application_ids:
            rows = await self.db.execute(
                select(Application.id, Application.student_id, Application.program_id).where(
                    Application.id.in_(body.application_ids),
                    Application.program_id.in_(
                        select(Program.id).where(Program.institution_id == institution_id)
                    ),
                )
            )
            for app_id, sid, _pid in rows.all():
                student_ids.add(sid)
                app_by_student[sid] = app_id
        elif body.segment_id:
            seg = await self.db.scalar(
                select(TargetSegment).where(
                    TargetSegment.id == body.segment_id,
                    TargetSegment.institution_id == institution_id,
                )
            )
            if seg is None:
                raise NotFoundException("Segment not found")
            members = await SegmentService(self.db).evaluate_rules(
                institution_id, seg.rules or {}, seg.program_id
            )
            members = await SegmentService(self.db).apply_suppression(members)
            student_ids = members
        else:
            raise BadRequestException("segment_id or application_ids required")

        rendered_body = body.body or ""
        if body.template_id:
            comm = CommunicationService(self.db)
            preview = await comm.preview_template(
                institution_id, body.template_id, next(iter(app_by_student.values()), None)
            )
            rendered_body = _personalize(preview.rendered_body, body.variables)

        if not rendered_body.strip():
            raise BadRequestException("Message body is required")

        batch_id = str(uuid_mod.uuid4())
        sent = 0
        skipped = 0
        failed: list[UUID] = []
        is_marketing = not body.application_ids and body.reason_code in _MARKETING_REASONS

        for sid in student_ids:
            try:
                if is_marketing:
                    consent = await self.db.scalar(
                        select(StudentDataConsent.consent_outreach).where(
                            StudentDataConsent.student_id == sid
                        )
                    )
                    if consent is False:
                        skipped += 1
                        continue

                app_id = app_by_student.get(sid)
                if app_id is None and body.application_ids:
                    failed.append(sid)
                    continue

                conv = await self._find_or_create_thread(
                    institution_id=institution_id,
                    student_id=sid,
                    application_id=app_id,
                    program_id=await self._program_for_app(app_id) if app_id else None,
                )
                await self.post_message(
                    user_id,
                    conv.id,
                    PostInstInboxMessageRequest(
                        body=rendered_body,
                        reason_code=body.reason_code,
                        due_date=body.due_date,
                    ),
                )
                sent += 1
            except Exception:  # noqa: BLE001
                logger.exception("bulk message failed for student %s", sid)
                failed.append(sid)

        await AuditService(self.db).log(
            institution_id=institution_id,
            actor_user_id=user_id,
            action="inbox_bulk_message",
            entity_type="batch",
            entity_id=batch_id,
            metadata_json={
                "reason_code": body.reason_code,
                "sent_count": sent,
                "skipped_count": skipped,
                "segment_id": str(body.segment_id) if body.segment_id else None,
            },
        )
        return BulkMessageResponse(
            batch_id=batch_id,
            sent_count=sent,
            skipped_count=skipped,
            failed_ids=failed,
        )

    async def _program_for_app(self, application_id: UUID | None) -> UUID | None:
        if not application_id:
            return None
        return await self.db.scalar(
            select(Application.program_id).where(Application.id == application_id)
        )

    async def _find_or_create_thread(
        self,
        *,
        institution_id: UUID,
        student_id: UUID,
        application_id: UUID | None,
        program_id: UUID | None,
    ) -> Conversation:
        q = select(Conversation).where(
            Conversation.institution_id == institution_id,
            Conversation.student_id == student_id,
            Conversation.thread_type == "human",
        )
        if application_id:
            q = q.where(Conversation.application_id == application_id)
        existing = (
            await self.db.execute(q.order_by(Conversation.last_message_at.desc()).limit(1))
        ).scalar_one_or_none()
        if existing:
            return existing
        now = datetime.now(UTC)
        conv = Conversation(
            student_id=student_id,
            institution_id=institution_id,
            program_id=program_id,
            application_id=application_id,
            thread_type="human",
            status="open",
            started_at=now,
            last_message_at=now,
        )
        self.db.add(conv)
        await self.db.flush()
        return conv

    async def _sync_checklist_request(self, conv: Conversation) -> None:
        if conv.application_id is None or not conv.linked_checklist_item_category:
            return
        category = conv.linked_checklist_item_category
        checklist = await self.db.scalar(
            select(ApplicationChecklist)
            .join(Application, Application.program_id == ApplicationChecklist.program_id)
            .where(
                Application.id == conv.application_id,
                ApplicationChecklist.student_id == conv.student_id,
            )
        )
        if checklist is None:
            try:
                checklist = await ChecklistService(self.db).generate_checklist(
                    conv.student_id, conv.application_id
                )
            except Exception:  # noqa: BLE001
                return
        items = [dict(it) for it in (checklist.items or [])]
        found = False
        for it in items:
            if it.get("key") == category or it.get("category") == category:
                it["status"] = "pending"
                it["completed"] = False
                it["manual_complete"] = False
                found = True
        if not found:
            items.append(
                {
                    "key": category,
                    "category": category,
                    "label": category.replace("_", " ").title(),
                    "status": "pending",
                    "completed": False,
                    "required_level": "required",
                }
            )
        checklist.items = items
        checklist.completion_percentage = ChecklistService._compute_completion(items)

    async def _sync_calendar_deadline(self, conv: Conversation) -> None:
        if conv.due_date is None:
            return
        existing = await self.db.scalar(
            select(StudentCalendar).where(StudentCalendar.reference_id == conv.id)
        )
        title = conv.subject or "Inbox deadline"
        if existing:
            existing.start_time = conv.due_date
            existing.title = title
            existing.status = "scheduled"
            return
        self.db.add(
            StudentCalendar(
                student_id=conv.student_id,
                entry_type="inbox_deadline",
                reference_id=conv.id,
                title=title,
                start_time=conv.due_date,
                application_id=conv.application_id,
                status="scheduled",
            )
        )

    async def _notify_student(self, conv: Conversation, reason_code: str, body: str) -> None:
        user_id = await self.db.scalar(
            select(StudentProfile.user_id).where(StudentProfile.id == conv.student_id)
        )
        if not user_id:
            return
        ntype = (
            "application_missing_item"
            if reason_code in ("request_document", "request_clarification")
            else "interview_invites"
            if reason_code == "interview_invite"
            else "messages"
        )
        inst_name = await self.db.scalar(
            select(Institution.name).where(Institution.id == conv.institution_id)
        )
        await NotificationService(self.db).notify(
            user_id=user_id,
            notification_type=ntype,
            title=f"Message from {inst_name or 'Admissions'}",
            body=body[:500],
            action_url=f"/s/manage?tab=messages&thread={conv.id}",
            metadata={"thread_id": str(conv.id), "reason_code": reason_code},
        )

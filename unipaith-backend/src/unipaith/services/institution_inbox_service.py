"""Institution inbox service (Spec 29) — the institution side of the
conversation, mirror of the student inbox (Spec 17).

A richer *institution-side* view over the shared ``conversations`` /
``messages`` tables. Staff read & reply to applicant threads with **reason
codes** (the institution-side write that produces the student's action labels,
spec 29 §4), assign threads to staff (§2), draft replies with AI (§8), and
message a segment in bulk for operational comms (§6).

Reason code → student action label (§4): the institution sets a reason code on
send; we map it to the shared ``Conversation.action_label`` that the student's
Spec 17 inbox renders, and store the reason code on ``Conversation.reason_code``
for the institution-side view.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai.consent import get_consent_mask
from unipaith.ai.inbound_intent import (
    InboundIntentClassifier,
    InboundIntentInput,
    get_inbound_intent_classifier,
)
from unipaith.ai.institution_reply import (
    InstitutionReplyDrafter,
    InstitutionReplyInput,
    get_institution_reply_drafter,
)
from unipaith.config import settings
from unipaith.core.exceptions import BadRequestException, ForbiddenException, NotFoundException
from unipaith.models.application import Application, ApplicationChecklist
from unipaith.models.engagement import Conversation, Message, StudentCalendar
from unipaith.models.institution import CommunicationTemplate, Institution, Program
from unipaith.models.student import StudentProfile
from unipaith.models.user import User
from unipaith.schemas.institution_inbox import (
    BulkMessageResult,
    InstMessageResponse,
    InstSuggestedReplyResponse,
    InstThreadContext,
    InstThreadResponse,
    InstThreadStudent,
    InstThreadSummary,
    IntentSuggestionResponse,
    StaffMember,
)
from unipaith.services.audit_service import AuditService
from unipaith.services.messaging_service import MessagingService
from unipaith.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

# ── Reason-code mapping (spec 29 §4) ────────────────────────────────────────
REASON_TO_ACTION: dict[str, str] = {
    "request_document": "document_requested",
    "request_clarification": "clarification_required",
    "interview_invite": "interview_invite",
    "status_update": "status_update_only",
    "general_reply": "needs_reply",
    "decision_notice": "status_update_only",
}
# Reasons that REQUIRE a due date on send (spec 29 §5).
REASON_REQUIRES_DUE = {"request_document", "request_clarification", "interview_invite"}
# Student notification type per reason (essential types keep in-app on, §6).
REASON_NOTIF_TYPE: dict[str, str] = {
    "request_document": "application_missing_item",
    "request_clarification": "application_missing_item",
    "interview_invite": "interview_invites",
    "status_update": "messages",
    "general_reply": "messages",
    "decision_notice": "decisions",
}
# Marketing-class reasons are suppressible by consent.outreach; transactional
# reasons tied to an active application are NOT (spec 29 §6).
MARKETING_CLASS = {"status_update", "general_reply"}
VALID_REASONS = set(REASON_TO_ACTION)

# Known student-checklist categories a document request can link to.
_CHECKLIST_CATEGORIES = {
    "documents",
    "test_scores",
    "essays",
    "recommendation_letters",
    "resume",
    "academic_records",
    "personal_info",
    "transcripts",
}

_HUMAN = "human"


def _norm_sender(sender_type: str | None) -> str:
    if sender_type == "student":
        return "student"
    if sender_type == "system":
        return "system"
    if sender_type == "institution":
        return "institution"
    return "admissions_officer"


class InstitutionInboxService:
    def __init__(
        self,
        db: AsyncSession,
        *,
        reply_drafter: InstitutionReplyDrafter | None = None,
        intent_classifier: InboundIntentClassifier | None = None,
    ):
        self.db = db
        self.messaging = MessagingService(db)
        self.audit = AuditService(db)
        self.notifications = NotificationService(db)
        # Injectable for tests; default to the process singletons.
        self._drafter = reply_drafter or get_institution_reply_drafter()
        self._classifier = intent_classifier or get_inbound_intent_classifier()

    # ------------------------------------------------------------------
    # Identity / ownership
    # ------------------------------------------------------------------

    async def _require_institution(self, user_id: UUID) -> Institution:
        inst = await self.db.scalar(select(Institution).where(Institution.admin_user_id == user_id))
        if inst is None:
            raise ForbiddenException("Only institution admins have an inbox")
        return inst

    async def _owned_thread(self, institution_id: UUID, thread_id: UUID) -> Conversation:
        conv = await self.db.scalar(
            select(Conversation).where(
                Conversation.id == thread_id,
                Conversation.institution_id == institution_id,
            )
        )
        if conv is None:
            raise NotFoundException("Conversation not found")
        return conv

    # ------------------------------------------------------------------
    # Derivations
    # ------------------------------------------------------------------

    @staticmethod
    def _derive_status(conv: Conversation) -> str:
        if conv.status == "closed":
            return "closed"
        if conv.waiting_on == "school":
            return "awaiting_us"
        if conv.waiting_on == "student":
            return "awaiting_student"
        return "open"

    async def _name_maps(
        self, convs: list[Conversation]
    ) -> tuple[dict[UUID, str], dict[UUID, str], dict[UUID, str]]:
        """Batch-resolve program names, student display names, and staff
        (assigned_to) display names for a set of conversations."""
        program_ids = {c.program_id for c in convs if c.program_id}
        student_ids = {c.student_id for c in convs if c.student_id}
        staff_ids = {c.assigned_to for c in convs if c.assigned_to}

        program_name: dict[UUID, str] = {}
        if program_ids:
            rows = await self.db.execute(
                select(Program.id, Program.program_name).where(Program.id.in_(program_ids))
            )
            program_name = {pid: name for pid, name in rows.all()}

        student_name: dict[UUID, str] = {}
        if student_ids:
            rows = await self.db.execute(
                select(
                    StudentProfile.id,
                    StudentProfile.first_name,
                    StudentProfile.last_name,
                ).where(StudentProfile.id.in_(student_ids))
            )
            for sid, first, last in rows.all():
                student_name[sid] = " ".join(p for p in (first, last) if p).strip() or "Applicant"

        staff_name: dict[UUID, str] = {}
        if staff_ids:
            rows = await self.db.execute(select(User.id, User.email).where(User.id.in_(staff_ids)))
            # Display the email local-part (consistent with the staff roster).
            staff_name = {uid: ((email or "Staff").split("@")[0]) for uid, email in rows.all()}

        return program_name, student_name, staff_name

    async def _unread_map(self, conv_ids: list[UUID]) -> dict[UUID, int]:
        """Count messages from the applicant (student) still unread, per thread —
        the institution's unread is the inbound side."""
        if not conv_ids:
            return {}
        rows = await self.db.execute(
            select(Message.conversation_id, func.count())
            .where(
                Message.conversation_id.in_(conv_ids),
                func.coalesce(Message.sender_type, "") == "student",
                Message.read_at.is_(None),
            )
            .group_by(Message.conversation_id)
        )
        out: dict[UUID, int] = defaultdict(int)
        for cid, count in rows.all():
            out[cid] = int(count or 0)
        return out

    async def _context_map(self, convs: list[Conversation]) -> dict[UUID, InstThreadContext]:
        """Build the right-rail applicant context for threads tied to an
        application: stage + checklist progress + missing items (spec 29 §3)."""
        app_ids = {c.application_id for c in convs if c.application_id}
        if not app_ids:
            return {c.id: InstThreadContext() for c in convs}

        app_rows = await self.db.execute(
            select(
                Application.id,
                Application.student_id,
                Application.program_id,
                Application.status,
                Application.completeness_status,
            ).where(Application.id.in_(app_ids))
        )
        apps = {r.id: r for r in app_rows.all()}

        pairs = {(r.student_id, r.program_id) for r in apps.values()}
        checklist_by_pair: dict[tuple[UUID, UUID], ApplicationChecklist] = {}
        if pairs:
            student_ids = {p[0] for p in pairs}
            program_ids = {p[1] for p in pairs}
            cl_rows = await self.db.execute(
                select(ApplicationChecklist).where(
                    ApplicationChecklist.student_id.in_(student_ids),
                    ApplicationChecklist.program_id.in_(program_ids),
                )
            )
            for cl in cl_rows.scalars().all():
                checklist_by_pair[(cl.student_id, cl.program_id)] = cl

        out: dict[UUID, InstThreadContext] = {}
        for c in convs:
            if not c.application_id or c.application_id not in apps:
                out[c.id] = InstThreadContext()
                continue
            app = apps[c.application_id]
            stage = app.status or app.completeness_status
            cl = checklist_by_pair.get((app.student_id, app.program_id))
            complete = total = 0
            missing: list[str] = []
            if cl and cl.items:
                items = list(cl.items)
                total = len(items)
                for it in items:
                    done = bool(it.get("completed")) or it.get("status") == "completed"
                    if done:
                        complete += 1
                    else:
                        label = it.get("label") or it.get("category") or it.get("key")
                        if label:
                            missing.append(str(label))
            out[c.id] = InstThreadContext(
                stage=stage,
                checklist_complete=complete,
                checklist_total=total,
                missing_items=missing[:8],
            )
        return out

    def _summary(
        self,
        conv: Conversation,
        *,
        program_name: dict[UUID, str],
        student_name: dict[UUID, str],
        staff_name: dict[UUID, str],
        unread: dict[UUID, int],
        context: dict[UUID, InstThreadContext],
    ) -> InstThreadSummary:
        return InstThreadSummary(
            id=conv.id,
            application_id=conv.application_id,
            student=InstThreadStudent(
                id=conv.student_id,
                name=student_name.get(conv.student_id, "Applicant"),
            ),
            program_name=program_name.get(conv.program_id) if conv.program_id else None,
            reason_label=conv.reason_code,
            action_label=conv.action_label,
            status=self._derive_status(conv),
            assigned_to=conv.assigned_to,
            assigned_to_name=staff_name.get(conv.assigned_to) if conv.assigned_to else None,
            due_date=conv.due_date,
            unread_count=unread.get(conv.id, 0),
            last_message_at=conv.last_message_at,
            context=context.get(conv.id, InstThreadContext()),
        )

    @staticmethod
    def _sort_key(s: InstThreadSummary):
        # Urgent: closed last; "we owe a reply" (awaiting_us) first; then soonest
        # due; then unread; then most recent.
        closed_rank = 1 if s.status == "closed" else 0
        owe_rank = 0 if s.status == "awaiting_us" else 1
        due = s.due_date or datetime.max.replace(tzinfo=UTC)
        last = s.last_message_at or datetime.min.replace(tzinfo=UTC)
        return (
            closed_rank,
            owe_rank,
            due.timestamp(),
            0 if s.unread_count else 1,
            -last.timestamp(),
        )

    # ------------------------------------------------------------------
    # Public — read
    # ------------------------------------------------------------------

    async def list_threads(
        self,
        user_id: UUID,
        *,
        filter: str = "all",
        reason: str | None = None,
        program_id: UUID | None = None,
        status: str | None = None,
    ) -> list[InstThreadSummary]:
        inst = await self._require_institution(user_id)

        q = select(Conversation).where(
            Conversation.institution_id == inst.id,
            func.coalesce(Conversation.thread_type, _HUMAN) == _HUMAN,
        )
        if filter == "mine":
            q = q.where(Conversation.assigned_to == user_id)
        elif filter == "unassigned":
            q = q.where(Conversation.assigned_to.is_(None))
        if reason:
            q = q.where(Conversation.reason_code == reason)
        if program_id is not None:
            q = q.where(Conversation.program_id == program_id)

        convs = list((await self.db.execute(q)).scalars().all())
        if not convs:
            return []

        program_name, student_name, staff_name = await self._name_maps(convs)
        conv_ids = [c.id for c in convs]
        unread = await self._unread_map(conv_ids)
        context = await self._context_map(convs)

        summaries = [
            self._summary(
                c,
                program_name=program_name,
                student_name=student_name,
                staff_name=staff_name,
                unread=unread,
                context=context,
            )
            for c in convs
        ]
        if status in {"open", "awaiting_student", "awaiting_us", "closed"}:
            summaries = [s for s in summaries if s.status == status]
        summaries.sort(key=self._sort_key)
        return summaries

    async def get_thread(self, user_id: UUID, thread_id: UUID) -> InstThreadResponse:
        inst = await self._require_institution(user_id)
        conv = await self._owned_thread(inst.id, thread_id)

        # Mark applicant messages read on open (institution side).
        await self.db.execute(
            update(Message)
            .where(
                Message.conversation_id == thread_id,
                func.coalesce(Message.sender_type, "") == "student",
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

        program_name, student_name, staff_name = await self._name_maps([conv])
        unread = await self._unread_map([conv.id])
        context = await self._context_map([conv])
        summary = self._summary(
            conv,
            program_name=program_name,
            student_name=student_name,
            staff_name=staff_name,
            unread=unread,
            context=context,
        )
        messages = [
            InstMessageResponse(
                id=m.id,
                thread_id=m.conversation_id,
                sender=_norm_sender(m.sender_type),
                body=m.message_body,
                attachments=list(m.attachments or []),
                sent_at=m.sent_at,
                read_at=m.read_at,
                status=m.status or "sent",
                ai_draft_used=bool(m.ai_draft_used),
            )
            for m in msgs
        ]
        return InstThreadResponse(**summary.model_dump(), messages=messages)

    # ------------------------------------------------------------------
    # Public — write
    # ------------------------------------------------------------------

    async def post_message(
        self,
        user_id: UUID,
        thread_id: UUID,
        *,
        body: str,
        reason_code: str,
        attachments: list[dict] | None = None,
        due_date: datetime | None = None,
        request_document: bool = False,
        requested_item: str | None = None,
        ai_draft_used: bool = False,
    ) -> InstMessageResponse:
        if reason_code not in VALID_REASONS:
            raise BadRequestException(f"Unknown reason_code: {reason_code}")
        if reason_code in REASON_REQUIRES_DUE and due_date is None:
            raise BadRequestException(f"A due date is required for reason '{reason_code}'")

        inst = await self._require_institution(user_id)
        conv = await self._owned_thread(inst.id, thread_id)

        message = await self.messaging.send_message(
            conversation_id=thread_id,
            sender_id=user_id,
            content=body,
            sender_type="institution",
        )
        message.attachments = list(attachments or [])
        message.status = "sent"
        message.ai_draft_used = bool(ai_draft_used)

        # Apply the reason → student action mapping + thread state.
        conv.reason_code = reason_code
        conv.action_label = REASON_TO_ACTION[reason_code]
        conv.due_date = due_date
        conv.waiting_on = "student"  # ball is now in the applicant's court
        if conv.status == "closed":
            conv.status = "open"

        # request_document + attach → link/create a student checklist item +
        # a calendar nudge so the due date lands on both ends (spec 29 §5/§12).
        if request_document or reason_code == "request_document":
            await self._link_document_request(conv, requested_item, due_date)

        await self.db.flush()

        # Notify the applicant (essential types keep in-app on, §6).
        await self._notify_student(conv, inst, reason_code, body)

        # Audit (§2/§8 — AI-assisted vs hand-written tagged for the ledger).
        await self.audit.log(
            institution_id=inst.id,
            actor_user_id=user_id,
            action="inbox.message_sent",
            entity_type="conversation",
            entity_id=str(thread_id),
            application_id=conv.application_id,
            description=f"Sent {reason_code} message",
            metadata_json={"reason_code": reason_code, "ai_assisted": bool(ai_draft_used)},
        )

        return InstMessageResponse(
            id=message.id,
            thread_id=message.conversation_id,
            sender="institution",
            body=message.message_body,
            attachments=list(message.attachments or []),
            sent_at=message.sent_at,
            read_at=message.read_at,
            status=message.status or "sent",
            ai_draft_used=bool(message.ai_draft_used),
        )

    async def _link_document_request(
        self, conv: Conversation, requested_item: str | None, due_date: datetime | None
    ) -> None:
        """Link the thread to a student checklist item + drop a calendar nudge.

        The student's "Mark complete" (Spec 17) then propagates back to the
        checklist item via ``linked_checklist_item_category``.
        """
        category = (requested_item or "").strip().lower().replace(" ", "_")
        if category not in _CHECKLIST_CATEGORIES:
            category = "documents"
        conv.linked_checklist_item_category = category

        if conv.application_id is None:
            return

        app = await self.db.scalar(select(Application).where(Application.id == conv.application_id))
        if app is None:
            return

        # Append a durable requested-document item to the application checklist
        # so the applicant literally sees a new line (best-effort, §12).
        checklist = await self.db.scalar(
            select(ApplicationChecklist).where(
                ApplicationChecklist.student_id == app.student_id,
                ApplicationChecklist.program_id == app.program_id,
            )
        )
        item_key = f"inst_request:{conv.id}"
        label = (requested_item or "Requested document").strip() or "Requested document"
        if checklist is not None:
            items = [dict(it) for it in (checklist.items or [])]
            if not any(it.get("key") == item_key for it in items):
                items.append(
                    {
                        "key": item_key,
                        "category": category,
                        "label": label,
                        "item_type": "document",
                        "owner": "student",
                        "status": "pending",
                        "completed": False,
                        "requested_by_institution": True,
                    }
                )
                checklist.items = items
                completed = sum(
                    1 for it in items if it.get("completed") or it.get("status") == "completed"
                )
                checklist.completion_percentage = (
                    round(completed / len(items) * 100) if items else 0
                )

        # Calendar nudge keyed by the thread id (Spec 16/17 linkage).
        if due_date is not None:
            existing = await self.db.scalar(
                select(StudentCalendar).where(StudentCalendar.reference_id == conv.id)
            )
            if existing is None:
                self.db.add(
                    StudentCalendar(
                        student_id=app.student_id,
                        entry_type="reminder",
                        reference_id=conv.id,
                        title=f"Requested: {label}",
                        start_time=due_date,
                        reminder_at=due_date,
                        status="scheduled",
                        category="application",
                        application_id=conv.application_id,
                    )
                )

    async def _notify_student(
        self, conv: Conversation, inst: Institution, reason_code: str, body: str
    ) -> None:
        student_user_id = await self.db.scalar(
            select(StudentProfile.user_id).where(StudentProfile.id == conv.student_id)
        )
        if not student_user_id:
            return
        notif_type = REASON_NOTIF_TYPE.get(reason_code, "messages")
        preview = (body or "").strip()
        if len(preview) > 160:
            preview = preview[:157] + "…"
        try:
            await self.notifications.notify(
                student_user_id,
                notif_type,
                title=f"{inst.name}: new message",
                body=preview,
                action_url=f"/s/manage?tab=messages&thread={conv.id}",
                metadata={"thread_id": str(conv.id), "reason_code": reason_code},
            )
        except Exception as e:  # noqa: BLE001 — notification failure must not 5xx the send
            logger.warning("inbox notify failed for thread %s: %s", conv.id, e)

    async def assign(
        self, user_id: UUID, thread_id: UUID, staff_user_id: UUID | None
    ) -> InstThreadResponse:
        inst = await self._require_institution(user_id)
        conv = await self._owned_thread(inst.id, thread_id)

        if staff_user_id is not None:
            roster_ids = {m.id for m in await self._roster(inst)}
            if staff_user_id not in roster_ids:
                raise BadRequestException("Assignee is not a member of this institution")

        old = conv.assigned_to
        conv.assigned_to = staff_user_id
        await self.db.flush()

        await self.audit.log(
            institution_id=inst.id,
            actor_user_id=user_id,
            action="inbox.assigned",
            entity_type="conversation",
            entity_id=str(thread_id),
            application_id=conv.application_id,
            old_value={"assigned_to": str(old) if old else None},
            new_value={"assigned_to": str(staff_user_id) if staff_user_id else None},
        )

        # Reassignment notifies the new owner (spec 29 §2) — not when self-claim.
        if staff_user_id and staff_user_id != old and staff_user_id != user_id:
            try:
                await self.notifications.notify(
                    staff_user_id,
                    "messages",
                    title="A conversation was assigned to you",
                    body="You've been assigned an applicant conversation in the inbox.",
                    action_url=f"/i/communications?tab=inbox&thread={thread_id}",
                    metadata={"thread_id": str(thread_id)},
                )
            except Exception as e:  # noqa: BLE001
                logger.warning("assignment notify failed: %s", e)

        return await self.get_thread(user_id, thread_id)

    async def close(self, user_id: UUID, thread_id: UUID) -> InstThreadResponse:
        inst = await self._require_institution(user_id)
        conv = await self._owned_thread(inst.id, thread_id)
        conv.status = "closed"
        conv.waiting_on = "none"
        await self.db.flush()
        await self.audit.log(
            institution_id=inst.id,
            actor_user_id=user_id,
            action="inbox.closed",
            entity_type="conversation",
            entity_id=str(thread_id),
            application_id=conv.application_id,
        )
        return await self.get_thread(user_id, thread_id)

    # ------------------------------------------------------------------
    # AI
    # ------------------------------------------------------------------

    async def ai_draft(self, user_id: UUID, thread_id: UUID) -> InstSuggestedReplyResponse | None:
        """Return an AI-drafted reply, or None when unavailable (flag off /
        agent failure) — the UI hides the card (spec 29 §9)."""
        if not settings.ai_institution_reply_v2_enabled:
            return None
        inst = await self._require_institution(user_id)
        # Spec 37 §5 — respect the institution's message-draft AI toggle.
        from unipaith.services.ai_config_service import AIConfigService

        if not await AIConfigService(self.db).is_surface_enabled(inst.id, "message_draft"):
            return None
        conv = await self._owned_thread(inst.id, thread_id)
        thread = await self.get_thread(user_id, thread_id)

        reason_code = conv.reason_code or "general_reply"
        # Spec 29 §8 — applicant matching consent gates use of profile context.
        # When denied, pass thread text only (no application/checklist context).
        mask = await get_consent_mask(self.db, conv.student_id)
        if mask.get("matching", True):
            application = {
                "program_name": thread.program_name,
                "stage": thread.context.stage,
            }
            context = {
                "checklist_complete": thread.context.checklist_complete,
                "checklist_total": thread.context.checklist_total,
                "missing_items": thread.context.missing_items,
            }
        else:
            application = {}
            context = {}

        staff_email = await self.db.scalar(select(User.email).where(User.id == user_id))
        input_view = InstitutionReplyInput(
            student_id=conv.student_id,
            institution_name=inst.name,
            staff_name=(staff_email or "").split("@")[0] if staff_email else "",
            applicant_name=thread.student.name,
            reason_code=reason_code,
            requested_item=conv.linked_checklist_item_category,
            thread_subject=conv.subject or "",
            waiting_on=conv.waiting_on,
            due_date=conv.due_date.isoformat() if conv.due_date else None,
            application=application,
            context=context,
            messages=[{"sender": m.sender, "body": m.body} for m in thread.messages],
        )
        result = await self._drafter.draft(input_view=input_view, db=self.db)
        if result is None:
            return None
        # Spec 37 §3 — record the AI-generated reply; token lets the send action
        # capture the human edit diff.
        from unipaith.services.ai_config_service import AIConfigService
        from unipaith.services.ai_surface_service import AISurfaceService

        no_training = await AIConfigService(self.db).is_no_training(inst.id)
        token = await AISurfaceService(self.db).record_generated(
            institution_id=inst.id,
            actor_user_id=user_id,
            surface="message_draft",
            agent="institution_reply_drafter",
            ai_output={"body": result.draft},
            no_training=no_training,
        )
        return InstSuggestedReplyResponse(
            draft=result.draft,
            tone=result.tone,
            length=result.length,
            alternate_drafts=result.alternate_drafts,
            draft_token=str(token),
        )

    async def intent_suggestion(
        self, user_id: UUID, thread_id: UUID
    ) -> IntentSuggestionResponse | None:
        """Suggest a reason code for the latest inbound message (spec 29 §8,
        suggestion-only). None when flag off / no inbound message / failure."""
        if not settings.ai_inbound_intent_v2_enabled:
            return None
        inst = await self._require_institution(user_id)
        await self._owned_thread(inst.id, thread_id)
        thread = await self.get_thread(user_id, thread_id)

        latest = next((m.body for m in reversed(thread.messages) if m.sender == "student"), None)
        if not latest:
            return None
        result = await self._classifier.classify(
            input_view=InboundIntentInput(
                student_id=thread.student.id,
                latest_message=latest,
                application={"program_name": thread.program_name, "stage": thread.context.stage},
                context={"missing_items": thread.context.missing_items},
            ),
            db=self.db,
        )
        if result is None:
            return None
        return IntentSuggestionResponse(
            reason_code=result.reason_code,
            confidence=result.confidence,
            rationale=result.rationale,
        )

    # ------------------------------------------------------------------
    # Staff roster (§2)
    # ------------------------------------------------------------------

    async def _roster(self, inst: Institution) -> list[StaffMember]:
        """Assignable staff for an institution. MVP = the institution admin;
        forward-compatible if accepted-invite→user linkage is added later."""
        admin = await self.db.scalar(select(User).where(User.id == inst.admin_user_id))
        out: list[StaffMember] = []
        if admin is not None:
            out.append(
                StaffMember(
                    id=admin.id,
                    name=(admin.email or "Admin").split("@")[0],
                    email=admin.email or "",
                    role="admin",
                )
            )
        return out

    async def staff_roster(self, user_id: UUID) -> list[StaffMember]:
        inst = await self._require_institution(user_id)
        return await self._roster(inst)

    # ------------------------------------------------------------------
    # Bulk / segment messaging (§6)
    # ------------------------------------------------------------------

    async def bulk_message(
        self,
        user_id: UUID,
        *,
        segment_id: UUID | None = None,
        application_ids: list[UUID] | None = None,
        template_id: UUID | None = None,
        body: str | None = None,
        variables: dict | None = None,
        reason_code: str = "status_update",
        due_date: datetime | None = None,
    ) -> BulkMessageResult:
        if reason_code not in VALID_REASONS:
            raise BadRequestException(f"Unknown reason_code: {reason_code}")
        if reason_code in REASON_REQUIRES_DUE and due_date is None:
            raise BadRequestException(f"A due date is required for reason '{reason_code}'")
        inst = await self._require_institution(user_id)

        # Resolve the message body (template body wins; variables substituted
        # per-recipient below).
        base_body = (body or "").strip()
        if template_id is not None:
            tmpl = await self.db.scalar(
                select(CommunicationTemplate).where(
                    CommunicationTemplate.id == template_id,
                    CommunicationTemplate.institution_id == inst.id,
                )
            )
            if tmpl is None:
                raise NotFoundException("Template not found")
            base_body = tmpl.body
        if not base_body:
            raise BadRequestException("Provide a template_id or a message body")

        # Resolve recipients → {student_id: application_id|None}.
        recipients = await self._resolve_recipients(inst, segment_id, application_ids or [])
        recipient_count = len(recipients)

        # Reason-aware suppression (spec 29 §6): marketing-class respects
        # consent.outreach; transactional reasons are not suppressed.
        suppressed_count = 0
        if reason_code in MARKETING_CLASS and recipients:
            from unipaith.services.segment_service import SegmentService

            kept = await SegmentService(self.db).apply_suppression(set(recipients.keys()))
            suppressed_count = recipient_count - len(kept)
            recipients = {sid: app for sid, app in recipients.items() if sid in kept}

        # Resolve display data for substitution.
        sids = list(recipients.keys())
        student_meta = await self._student_meta(sids)
        program_name_for_app = await self._program_names_for_apps(
            [a for a in recipients.values() if a]
        )

        thread_ids: list[UUID] = []
        action_label = REASON_TO_ACTION[reason_code]
        due_str = due_date.strftime("%b %d, %Y") if due_date else ""
        now = datetime.now(UTC)

        for sid, app_id in recipients.items():
            meta = student_meta.get(sid, {})
            program_id = meta.get("program_id")
            prog_name = (program_name_for_app.get(app_id) if app_id else None) or meta.get(
                "program_name"
            )
            rendered = self._render(
                base_body,
                variables or {},
                student_name=meta.get("name", "there"),
                program=prog_name or "",
                deadline=due_str,
                missing_items=meta.get("missing_items", ""),
            )
            conv = await self._find_or_create_conv(inst, user_id, sid, program_id, app_id)
            # Insert the message directly (bulk bypasses the per-sender hourly
            # rate limit that governs single replies).
            msg = Message(
                conversation_id=conv.id,
                sender_type="institution",
                sender_id=user_id,
                message_body=rendered,
                status="sent",
                sent_at=now,
            )
            self.db.add(msg)
            conv.last_message_at = now
            conv.reason_code = reason_code
            conv.action_label = action_label
            conv.due_date = due_date
            conv.waiting_on = "student"
            if conv.status == "closed":
                conv.status = "open"
            await self.db.flush()
            thread_ids.append(conv.id)
            await self._notify_student(conv, inst, reason_code, rendered)
            # Per-recipient audit row (part of the batch, §6).
            await self.audit.log(
                institution_id=inst.id,
                actor_user_id=user_id,
                action="inbox.message_sent",
                entity_type="conversation",
                entity_id=str(conv.id),
                application_id=conv.application_id,
                description="Bulk operational message",
                metadata_json={"reason_code": reason_code, "bulk": True},
            )

        # Single batch summary row (spec 29 §6).
        await self.audit.log(
            institution_id=inst.id,
            actor_user_id=user_id,
            action="inbox.bulk_message",
            entity_type="segment" if segment_id else "applications",
            entity_id=str(segment_id) if segment_id else "ad_hoc",
            description=f"Bulk {reason_code} to {len(thread_ids)} recipients",
            metadata_json={
                "reason_code": reason_code,
                "recipient_count": recipient_count,
                "sent_count": len(thread_ids),
                "suppressed_count": suppressed_count,
                "thread_ids": [str(t) for t in thread_ids],
            },
        )

        return BulkMessageResult(
            sent_count=len(thread_ids),
            suppressed_count=suppressed_count,
            recipient_count=recipient_count,
            thread_ids=thread_ids,
        )

    async def _resolve_recipients(
        self, inst: Institution, segment_id: UUID | None, application_ids: list[UUID]
    ) -> dict[UUID, UUID | None]:
        """Return {student_id: application_id|None} for the bulk audience."""
        out: dict[UUID, UUID | None] = {}
        if application_ids:
            # Validate the applications belong to this institution's programs.
            prog_ids = {p.id for p in await self._inst_programs(inst.id)}
            rows = await self.db.execute(
                select(Application.id, Application.student_id, Application.program_id).where(
                    Application.id.in_(application_ids)
                )
            )
            for app_id, student_id, program_id in rows.all():
                if program_id in prog_ids:
                    out[student_id] = app_id
            return out
        if segment_id is not None:
            from unipaith.services.institution_service import InstitutionService

            members = await InstitutionService(self.db).resolve_segment_members(inst.id, segment_id)
            for sid in members:
                out.setdefault(sid, None)
            return out
        raise BadRequestException("Provide a segment_id or application_ids")

    async def _inst_programs(self, institution_id: UUID) -> list[Program]:
        rows = await self.db.execute(
            select(Program).where(Program.institution_id == institution_id)
        )
        return list(rows.scalars().all())

    async def _student_meta(self, student_ids: list[UUID]) -> dict[UUID, dict]:
        if not student_ids:
            return {}
        out: dict[UUID, dict] = {}
        rows = await self.db.execute(
            select(StudentProfile.id, StudentProfile.first_name, StudentProfile.last_name).where(
                StudentProfile.id.in_(student_ids)
            )
        )
        for sid, first, last in rows.all():
            out[sid] = {"name": (first or "there"), "program_id": None, "program_name": None}
        return out

    async def _program_names_for_apps(self, app_ids: list[UUID]) -> dict[UUID, str]:
        if not app_ids:
            return {}
        rows = await self.db.execute(
            select(Application.id, Program.program_name)
            .join(Program, Program.id == Application.program_id)
            .where(Application.id.in_(app_ids))
        )
        return {app_id: name for app_id, name in rows.all()}

    async def _find_or_create_conv(
        self,
        inst: Institution,
        user_id: UUID,
        student_id: UUID,
        program_id: UUID | None,
        application_id: UUID | None,
    ) -> Conversation:
        q = select(Conversation).where(
            Conversation.institution_id == inst.id,
            Conversation.student_id == student_id,
            func.coalesce(Conversation.thread_type, _HUMAN) == _HUMAN,
        )
        if application_id is not None:
            q = q.where(Conversation.application_id == application_id)
        conv = await self.db.scalar(q.order_by(Conversation.last_message_at.desc().nullslast()))
        if conv is not None:
            return conv
        conv = await self.messaging.create_conversation(
            actor_user_id=user_id,
            student_id=student_id,
            institution_id=inst.id,
            subject="Message from admissions",
            program_id=program_id,
        )
        if application_id is not None:
            conv.application_id = application_id
        return conv

    @staticmethod
    def _render(
        body: str,
        variables: dict,
        *,
        student_name: str,
        program: str,
        deadline: str,
        missing_items: str,
    ) -> str:
        """Substitute the spec 29 §5 template variables. Explicit overrides in
        ``variables`` win; the rest come from the recipient context."""
        subs = {
            "student_name": student_name,
            "program": program,
            "deadline": deadline,
            "missing_items": missing_items,
        }
        subs.update({k: str(v) for k, v in (variables or {}).items()})
        out = body
        for key, val in subs.items():
            out = out.replace("{{" + key + "}}", val).replace("{{ " + key + " }}", val)
        return out

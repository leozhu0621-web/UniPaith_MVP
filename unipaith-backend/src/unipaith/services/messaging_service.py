"""
Messaging service — conversations and messages between students and institutions.
Supports real-time messaging with rate limiting, read tracking, and pagination.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import settings
from unipaith.core.exceptions import (
    BadRequestException,
    ForbiddenException,
    NotFoundException,
)
from unipaith.models.engagement import Conversation, Message
from unipaith.models.institution import Institution
from unipaith.models.student import StudentProfile

logger = logging.getLogger(__name__)


class MessagingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # Conversations
    # ------------------------------------------------------------------

    async def create_conversation(
        self,
        actor_user_id: UUID,
        student_id: UUID,
        institution_id: UUID,
        subject: str | None = None,
        program_id: UUID | None = None,
    ) -> Conversation:
        """Create a new conversation between a student and an institution."""
        actor_student_id, actor_institution_id = await self._resolve_user_context(actor_user_id)
        if actor_student_id:
            if actor_student_id != student_id:
                raise ForbiddenException("Students can only create conversations for themselves")
        elif actor_institution_id:
            if actor_institution_id != institution_id:
                raise ForbiddenException(
                    "Institution admins can only create conversations for their institution"
                )
        else:
            raise ForbiddenException("Only students or institution admins can create conversations")

        now = datetime.now(UTC)
        conversation = Conversation(
            student_id=student_id,
            institution_id=institution_id,
            program_id=program_id,
            subject=subject,
            status="active",
            started_at=now,
            last_message_at=now,
        )
        self.db.add(conversation)
        await self.db.flush()
        return conversation

    async def list_conversations(self, user_id: UUID) -> list[Conversation]:
        """
        List conversations for a user with unread counts.

        For students: returns conversations where student_id matches their profile.
        For institution admins: returns conversations where institution_id matches.
        """
        # Determine the user's role and relevant IDs
        student_profile_id, institution_id = await self._resolve_user_context(user_id)

        # Build the base query
        if student_profile_id:
            query = select(Conversation).where(Conversation.student_id == student_profile_id)
        elif institution_id:
            query = select(Conversation).where(Conversation.institution_id == institution_id)
        else:
            return []

        query = query.order_by(Conversation.last_message_at.desc())
        result = await self.db.execute(query)
        conversations = list(result.scalars().all())

        if not conversations:
            return conversations

        conversation_ids = [conv.id for conv in conversations]
        unread_counts_result = await self.db.execute(
            select(Message.conversation_id, func.count())
            .where(
                Message.conversation_id.in_(conversation_ids),
                Message.sender_id != user_id,
                Message.read_at.is_(None),
            )
            .group_by(Message.conversation_id)
        )
        unread_counts = defaultdict(int)
        for conversation_id, count in unread_counts_result.all():
            unread_counts[conversation_id] = int(count or 0)

        for conv in conversations:
            conv.unread_count = unread_counts[conv.id]  # type: ignore[attr-defined]
        return conversations

    # ------------------------------------------------------------------
    # Messages
    # ------------------------------------------------------------------

    async def send_message(
        self,
        conversation_id: UUID,
        sender_id: UUID,
        content: str,
        sender_type: str = "student",
    ) -> Message:
        """
        Send a message in a conversation.

        Validates content length and enforces per-sender rate limiting.
        """
        # Validate content length
        if len(content) > settings.message_max_length:
            raise BadRequestException(
                f"Message exceeds maximum length of {settings.message_max_length} characters"
            )
        if not content.strip():
            raise BadRequestException("Message cannot be empty")

        # Rate limit check
        one_hour_ago = datetime.now(UTC) - timedelta(hours=1)
        rate_result = await self.db.execute(
            select(func.count())
            .select_from(Message)
            .where(
                Message.sender_id == sender_id,
                Message.sent_at >= one_hour_ago,
            )
        )
        count = rate_result.scalar() or 0
        if count >= settings.message_rate_limit_per_hour:
            raise BadRequestException(
                f"Rate limit exceeded. Maximum {settings.message_rate_limit_per_hour} "
                "messages per hour"
            )

        # Verify conversation exists
        conv = await self._get_conversation(conversation_id)
        await self._verify_participant(conv, sender_id)
        if sender_type == "student":
            sender_type = await self._resolve_sender_type(sender_id)

        now = datetime.now(UTC)
        message = Message(
            conversation_id=conversation_id,
            sender_type=sender_type,
            sender_id=sender_id,
            message_body=content,
            sent_at=now,
        )
        self.db.add(message)

        # Update conversation timestamp
        conv.last_message_at = now
        await self.db.flush()
        return message

    async def get_messages(
        self,
        conversation_id: UUID,
        user_id: UUID,
        limit: int = 50,
        before: datetime | None = None,
    ) -> list[Message]:
        """
        Get messages in a conversation with pagination.

        Verifies the user is a participant and marks unread messages from
        the other party as read.
        """
        conv = await self._get_conversation(conversation_id)
        await self._verify_participant(conv, user_id)

        # Mark messages from the other party as read
        await self._mark_other_party_read(conversation_id, user_id)

        # Fetch messages with pagination
        query = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.sent_at.desc())
            .limit(limit)
        )
        if before:
            query = query.where(Message.sent_at < before)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def mark_messages_read(self, conversation_id: UUID, user_id: UUID) -> int:
        """
        Mark all messages in a conversation as read where sender_id != user_id.
        Returns the number of messages marked as read.
        """
        now = datetime.now(UTC)
        result = await self.db.execute(
            update(Message)
            .where(
                Message.conversation_id == conversation_id,
                Message.sender_id != user_id,
                Message.read_at.is_(None),
            )
            .values(read_at=now)
        )
        await self.db.flush()
        return result.rowcount  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _resolve_user_context(self, user_id: UUID) -> tuple[UUID | None, UUID | None]:
        """Return (student_profile_id, institution_id) based on user role."""
        # Check student profile
        result = await self.db.execute(
            select(StudentProfile.id).where(StudentProfile.user_id == user_id)
        )
        student_profile_id = result.scalar_one_or_none()
        if student_profile_id:
            return student_profile_id, None

        # Check institution admin
        result = await self.db.execute(
            select(Institution.id).where(Institution.admin_user_id == user_id)
        )
        institution_id = result.scalar_one_or_none()
        if institution_id:
            return None, institution_id

        return None, None

    async def _get_conversation(self, conversation_id: UUID) -> Conversation:
        result = await self.db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conv = result.scalar_one_or_none()
        if not conv:
            raise NotFoundException("Conversation not found")
        return conv

    async def _verify_participant(self, conv: Conversation, user_id: UUID) -> None:
        """Verify that user_id is a participant in the conversation."""
        # Check if user is the student
        result = await self.db.execute(
            select(StudentProfile.id).where(
                StudentProfile.user_id == user_id,
                StudentProfile.id == conv.student_id,
            )
        )
        if result.scalar_one_or_none():
            return

        # Check if user is the institution admin
        result = await self.db.execute(
            select(Institution.id).where(
                Institution.admin_user_id == user_id,
                Institution.id == conv.institution_id,
            )
        )
        if result.scalar_one_or_none():
            return

        raise ForbiddenException("You are not a participant in this conversation")

    async def _mark_other_party_read(self, conversation_id: UUID, user_id: UUID) -> None:
        """Mark unread messages from others as read."""
        now = datetime.now(UTC)
        await self.db.execute(
            update(Message)
            .where(
                Message.conversation_id == conversation_id,
                Message.sender_id != user_id,
                Message.read_at.is_(None),
            )
            .values(read_at=now)
        )
        await self.db.flush()

    async def _unread_count(self, conversation_id: UUID, user_id: UUID) -> int:
        """Count unread messages in a conversation for a specific user."""
        result = await self.db.execute(
            select(func.count())
            .select_from(Message)
            .where(
                Message.conversation_id == conversation_id,
                Message.sender_id != user_id,
                Message.read_at.is_(None),
            )
        )
        return result.scalar() or 0

    async def _resolve_sender_type(self, user_id: UUID) -> str:
        student_profile_id, institution_id = await self._resolve_user_context(user_id)
        if student_profile_id:
            return "student"
        if institution_id:
            return "institution"
        return "unknown"

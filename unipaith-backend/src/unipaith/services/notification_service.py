"""
Notification service — in-app + optional SES email delivery.
Used by event hooks to notify users of application status changes,
messages, interviews, decisions, and other platform events.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import settings
from unipaith.core.exceptions import NotFoundException
from unipaith.models.user import User
from unipaith.models.workflow import Notification, NotificationPreference

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ========================================================================
    # SEND NOTIFICATIONS
    # ========================================================================

    async def notify(
        self,
        user_id: UUID,
        notification_type: str,
        title: str,
        body: str,
        action_url: str | None = None,
        metadata: dict | None = None,
    ) -> Notification:
        """
        Create an in-app notification and optionally send an email.

        Args:
            user_id: Recipient user ID
            notification_type: Category (e.g. application_submitted, decision_made)
            title: Short title for the notification
            body: Full notification text
            action_url: Deep link into the app (e.g. /applications/123)
            metadata: Extra context (application_id, event_id, etc.)
        """
        notification = Notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            body=body,
            action_url=action_url,
            metadata_=metadata,
        )
        self.db.add(notification)
        await self.db.flush()

        # Optionally send email
        if settings.notifications_enabled:
            prefs = await self.get_preferences(user_id)
            type_prefs = (prefs.preferences or {}).get(notification_type, {})
            should_email = prefs.email_enabled and type_prefs.get("email", True)

            if should_email:
                email_sent = await self._send_email(user_id, title, body)
                if email_sent:
                    notification.is_emailed = True
                    await self.db.flush()

        return notification

    # ========================================================================
    # READ & MANAGE
    # ========================================================================

    async def list_notifications(
        self,
        user_id: UUID,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Notification]:
        """List notifications for a user, newest first."""
        query = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            query = query.where(Notification.is_read.is_(False))
        query = query.order_by(Notification.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def unread_count(self, user_id: UUID) -> int:
        """Get count of unread notifications."""
        result = await self.db.execute(
            select(func.count())
            .select_from(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
        )
        return result.scalar() or 0

    async def mark_read(self, user_id: UUID, notification_id: UUID) -> Notification:
        """Mark a single notification as read."""
        result = await self.db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
        )
        notification = result.scalar_one_or_none()
        if not notification:
            raise NotFoundException("Notification not found")

        notification.is_read = True
        notification.read_at = datetime.now(UTC)
        await self.db.flush()
        return notification

    async def mark_all_read(self, user_id: UUID) -> int:
        """Mark all unread notifications as read. Returns count updated."""
        result = await self.db.execute(
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
            .values(is_read=True, read_at=datetime.now(UTC))
        )
        await self.db.flush()
        return result.rowcount  # type: ignore[return-value]

    # ========================================================================
    # PREFERENCES
    # ========================================================================

    async def get_preferences(self, user_id: UUID) -> NotificationPreference:
        """Get or create default notification preferences."""
        result = await self.db.execute(
            select(NotificationPreference).where(NotificationPreference.user_id == user_id)
        )
        prefs = result.scalar_one_or_none()
        if not prefs:
            prefs = NotificationPreference(
                user_id=user_id,
                email_enabled=True,
                preferences={},
            )
            self.db.add(prefs)
            await self.db.flush()
        return prefs

    async def update_preferences(
        self,
        user_id: UUID,
        email_enabled: bool | None = None,
        preferences: dict | None = None,
    ) -> NotificationPreference:
        """Update notification preferences."""
        prefs = await self.get_preferences(user_id)
        if email_enabled is not None:
            prefs.email_enabled = email_enabled
        if preferences is not None:
            prefs.preferences = preferences
        await self.db.flush()
        return prefs

    # ========================================================================
    # EMAIL (SES)
    # ========================================================================

    async def _send_email(self, user_id: UUID, subject: str, body: str) -> bool:
        """
        Send email via Amazon SES.
        Returns True if sent successfully, False otherwise.
        In dev mode (notifications_enabled=False), this is never called.
        """
        try:
            # Load user email
            result = await self.db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if not user or not user.email:
                return False

            import boto3

            ses = boto3.client("ses", region_name=settings.ses_region)
            ses.send_email(
                Source=f"{settings.ses_sender_name} <{settings.ses_sender_email}>",
                Destination={"ToAddresses": [user.email]},
                Message={
                    "Subject": {"Data": subject, "Charset": "UTF-8"},
                    "Body": {
                        "Text": {"Data": body, "Charset": "UTF-8"},
                    },
                },
            )
            return True
        except Exception as e:
            logger.error("Failed to send email to user %s: %s", user_id, e)
            return False

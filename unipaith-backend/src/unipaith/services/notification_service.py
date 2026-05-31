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

# Canonical notification types × the channels each can fire on (Spec 21 §2.4).
# `essential` types are transactional/active-application messages: they can be
# down-ranked but never fully silenced — in-app stays on (safety, Spec 29 §6).
CHANNELS = ("email", "sms", "in_app", "push")
NOTIFICATION_TYPES: list[dict] = [
    {"key": "match_updates", "label": "Match updates", "essential": False},
    {"key": "application_missing_item", "label": "Application missing items", "essential": True},
    {"key": "interview_invites", "label": "Interview invites", "essential": True},
    {"key": "deadline_reminders", "label": "Deadline reminders", "essential": True},
    {"key": "decisions", "label": "Admission decisions", "essential": True},
    {"key": "institution_posts", "label": "Posts from saved programs", "essential": False},
    {"key": "messages", "label": "Messages", "essential": False},
]
_DEFAULT_CHANNELS = {"email": True, "sms": False, "in_app": True, "push": True}


def _coerce_channels(raw: object, essential: bool) -> dict[str, bool]:
    """Coerce a stored entry (dict matrix OR legacy flat bool) into the full channel map."""
    channels = dict(_DEFAULT_CHANNELS)
    if isinstance(raw, dict):
        for ch in CHANNELS:
            if ch in raw:
                channels[ch] = bool(raw[ch])
    elif isinstance(raw, bool):
        # Legacy {type: bool} — the bool governed email; keep in-app/push on.
        channels["email"] = raw
    if essential:
        channels["in_app"] = True  # safety: cannot silence in-app for transactional types
    return channels


def normalize_matrix(preferences: dict | None) -> list[dict]:
    """Return the full canonical per-type × per-channel matrix, defaults filled in."""
    stored = preferences or {}
    out: list[dict] = []
    for t in NOTIFICATION_TYPES:
        out.append(
            {
                "type": t["key"],
                "label": t["label"],
                "essential": t["essential"],
                "channels": _coerce_channels(stored.get(t["key"]), t["essential"]),
            }
        )
    return out


def matrix_to_storage(matrix: dict | list | None) -> dict:
    """Coerce an incoming matrix (dict or list of {type,channels}) into {type: {channels}}."""
    essential = {t["key"]: t["essential"] for t in NOTIFICATION_TYPES}
    items: dict[str, object] = {}
    if isinstance(matrix, list):
        for row in matrix:
            if isinstance(row, dict) and "type" in row:
                items[str(row["type"])] = row.get("channels", {})
    elif isinstance(matrix, dict):
        items = dict(matrix)
    return {
        key: _coerce_channels(items.get(key), essential[key])
        for key in (t["key"] for t in NOTIFICATION_TYPES)
    }


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
            raw = (prefs.preferences or {}).get(notification_type)
            if isinstance(raw, dict):
                type_email = bool(raw.get("email", True))
            elif isinstance(raw, bool):  # legacy flat {type: bool}
                type_email = raw
            else:
                type_email = True
            should_email = prefs.email_enabled and type_email and prefs.email_frequency != "none"

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

    async def unread_count(self, user_id: UUID) -> dict:
        """Get count of unread notifications."""
        result = await self.db.execute(
            select(func.count())
            .select_from(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
        )
        return {"count": result.scalar() or 0}

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
            # Populate server-generated columns (updated_at) within the async
            # context so later sync attribute access doesn't trigger lazy IO.
            await self.db.refresh(prefs)
        return prefs

    async def update_preferences(
        self,
        user_id: UUID,
        email_enabled: bool | None = None,
        preferences: dict | list | None = None,
        email_frequency: str | None = None,
    ) -> NotificationPreference:
        """Update notification preferences (per-channel × per-type matrix + frequency)."""
        prefs = await self.get_preferences(user_id)
        if email_enabled is not None:
            prefs.email_enabled = email_enabled
        if preferences is not None:
            # Normalise to the canonical matrix; essential types keep in-app on.
            prefs.preferences = matrix_to_storage(preferences)
        if email_frequency is not None:
            if email_frequency not in {"all", "weekly", "important", "none"}:
                raise ValueError("Invalid email_frequency")
            prefs.email_frequency = email_frequency
        await self.db.flush()
        await self.db.refresh(prefs)  # populate server-generated updated_at
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

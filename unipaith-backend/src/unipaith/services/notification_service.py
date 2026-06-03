"""
Notification service — in-app + optional SES email delivery.
Used by event hooks to notify users of application status changes,
messages, interviews, decisions, and other platform events.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import settings
from unipaith.core.exceptions import NotFoundException
from unipaith.core.realtime import broker
from unipaith.core.realtime import event as rt_event
from unipaith.models.user import User
from unipaith.models.workflow import Notification, NotificationPreference
from unipaith.services import notification_catalog as catalog
from unipaith.services.notification_delivery import deliver_with_retry

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
        event_id: str | None = None,
        urgency: str | None = None,
    ) -> Notification:
        """
        Create an in-app notification, fan out to channels, and push it live.

        Spec 57 §3/§4: the central write path — idempotent on ``event_id`` (a
        repeated hook writes one row), catalog-resolved urgency + per-type/channel
        preferences, transactional email via the retry/DLQ wrapper (with §6 digest
        deferral for low-urgency events), and a Redis-bridged live push to the
        recipient's open SSE/WS stream so the bell updates without a refetch.

        Args:
            user_id: Recipient user ID
            notification_type: Concrete event type (e.g. decision_made), resolved
                against ``notification_catalog`` for urgency / preference category.
            title: Short title for the notification
            body: Full notification text
            action_url: Deep link into the app (e.g. /applications/123)
            metadata: Extra context (application_id, etc.)
            event_id: Optional idempotency key — a second call with the same key
                returns the existing row instead of writing a duplicate.
            urgency: Override the catalog urgency (urgent | digest).
        """
        entry = catalog.get_entry(notification_type)
        urgency = urgency or entry.urgency

        # ── Idempotency (§3): one row per source event ──────────────────────
        if event_id:
            existing = await self.db.execute(
                select(Notification).where(
                    Notification.user_id == user_id,
                    Notification.event_id == event_id,
                )
            )
            found = existing.scalar_one_or_none()
            if found is not None:
                return found

        notification = Notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            body=body,
            action_url=action_url,
            metadata_=metadata,
            event_id=event_id,
            urgency=urgency,
        )
        self.db.add(notification)
        await self.db.flush()

        delivery: dict[str, str] = {}

        # ── In-app channel (§4): always written; pushed live to open streams ─
        delivery["in_app"] = "sent"
        await self._publish_created(notification)

        # ── Email channel (§4) with §6 digest deferral ──────────────────────
        delivery["email"] = await self._maybe_email(
            user_id=user_id,
            notification_type=notification_type,
            pref_key=entry.pref_key,
            essential=entry.essential,
            urgency=urgency,
            title=title,
            body=body,
            notification=notification,
        )

        # Web push (§4) is the planned fast-follow; recorded as skipped for now.
        if not settings.web_push_enabled:
            delivery["push"] = "planned"

        notification.delivery_status = delivery
        await self.db.flush()
        return notification

    async def emit(
        self,
        *,
        event_type: str,
        user_id: UUID,
        context: dict | None = None,
        event_id: str | None = None,
        title: str | None = None,
        body: str | None = None,
        action_url: str | None = None,
        metadata: dict | None = None,
    ) -> Notification:
        """Catalog-driven, idempotent emit (Spec 57 §3).

        Renders copy + deep-link from the catalog templates (overridable per call)
        and delegates to :meth:`notify`. The convenience entry point hooks should
        prefer — it guarantees catalog-consistent urgency, copy and deep-links.
        """
        r_title, r_body, r_link = catalog.render(event_type, context)
        # The context may carry UUIDs/datetimes; coerce non-JSON-native values to
        # strings so it stores cleanly in the JSONB metadata column.
        meta = metadata
        if meta is None and context:
            meta = {
                str(k): (v if isinstance(v, str | int | float | bool | type(None)) else str(v))
                for k, v in context.items()
            }
        return await self.notify(
            user_id=user_id,
            notification_type=event_type,
            title=title or r_title or event_type.replace("_", " ").title(),
            body=body or r_body or "",
            action_url=action_url if action_url is not None else r_link,
            metadata=meta,
            event_id=event_id,
        )

    async def _maybe_email(
        self,
        *,
        user_id: UUID,
        notification_type: str,
        pref_key: str,
        essential: bool,
        urgency: str,
        title: str,
        body: str,
        notification: Notification,
    ) -> str:
        """Decide + perform the email send. Returns the per-channel status string."""
        if not settings.notifications_enabled:
            return "skipped"

        prefs = await self.get_preferences(user_id)
        channels = _coerce_channels((prefs.preferences or {}).get(pref_key), essential)
        if not (prefs.email_enabled and channels["email"]) or prefs.email_frequency == "none":
            return "skipped"

        # §6 — low-urgency events batch into the digest instead of emailing now.
        if urgency == catalog.DIGEST and settings.notification_digest_enabled:
            return "deferred_digest"

        ok = await deliver_with_retry(
            "email",
            lambda: self._send_email(user_id, title, body),
            user_id=user_id,
            event_type=notification_type,
        )
        if ok:
            notification.is_emailed = True
        return "sent" if ok else "failed"

    async def _publish_created(self, notification: Notification) -> None:
        """Push a new notification to the recipient's live stream + a fresh count."""
        payload = {
            "id": str(notification.id),
            "notification_type": notification.notification_type,
            "title": notification.title,
            "body": notification.body,
            "action_url": notification.action_url,
            "urgency": notification.urgency,
            "is_read": False,
            "created_at": datetime.now(UTC).isoformat(),
        }
        await broker.publish(notification.user_id, rt_event("notification.created", payload))
        await self._publish_unread(notification.user_id)

    async def _publish_unread(self, user_id: UUID) -> None:
        count = (await self.unread_count(user_id))["count"]
        await broker.publish(user_id, rt_event("notification.unread_count", {"count": count}))

    # ========================================================================
    # DIGEST & BATCHING (Spec 57 §6)
    # ========================================================================

    async def run_digest(self, lookback_hours: int = 168) -> int:
        """Batch un-emailed digest-class notifications into one email per user.

        Urgent notifications are emailed immediately by :meth:`notify`; this only
        sweeps the ``digest`` class (feed updates, non-urgent change events,
        saved-search hits). Once a notification is folded into a digest it's marked
        ``is_emailed=True`` so the next run skips it — idempotent across runs.
        Returns the number of digest emails sent. Caller commits.
        """
        since = datetime.now(UTC) - timedelta(hours=max(1, lookback_hours))
        rows = (
            (
                await self.db.execute(
                    select(Notification)
                    .where(
                        Notification.urgency == catalog.DIGEST,
                        Notification.is_emailed.is_(False),
                        Notification.created_at >= since,
                    )
                    .order_by(Notification.user_id, Notification.created_at.desc())
                )
            )
            .scalars()
            .all()
        )
        if not rows:
            return 0

        by_user: dict[UUID, list[Notification]] = {}
        for n in rows:
            by_user.setdefault(n.user_id, []).append(n)

        sent = 0
        for user_id, items in by_user.items():
            prefs = await self.get_preferences(user_id)
            email_allowed = (
                settings.notifications_enabled
                and prefs.email_enabled
                and prefs.email_frequency != "none"
            )
            if not email_allowed:
                continue
            plural = "s" if len(items) != 1 else ""
            subject = f"Your UniPaith digest — {len(items)} new update{plural}"
            body = "Here's what's new on UniPaith:\n\n" + "\n".join(
                f"• {n.title}: {n.body}" for n in items[:25]
            )
            ok = await deliver_with_retry(
                "email",
                lambda uid=user_id, subj=subject, bdy=body: self._send_email(uid, subj, bdy),
                user_id=user_id,
                event_type="digest",
            )
            if ok:
                for n in items:
                    n.is_emailed = True
                sent += 1
        await self.db.flush()
        return sent

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
        # Spec 57 §5 — read-state syncs across tabs/devices: echo to the user's
        # other open streams so their bell count + row update without a refetch.
        await broker.publish(user_id, rt_event("notification.read", {"id": str(notification_id)}))
        await self._publish_unread(user_id)
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
        await broker.publish(user_id, rt_event("notification.read_all", {}))
        await self._publish_unread(user_id)
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

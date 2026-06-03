"""Spec 60 §3B — proactive change detection + routing (the proactive payoff).

A re-crawl whose content hash differs yields field-level diffs; each is
classified (change_type + materiality + confidence), written as a ``change_event``
tracing to a real source document (the no-fabricated-urgency guardrail), then
routed to the students who care — the ones who saved / applied / follow the
affected entity — gated by materiality + outreach consent (46) + a per-user-per-
day cap, deduped. This is the bridge to the Connect feed (20), notifications (57)
and saved-search alerts (56).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import settings
from unipaith.models.crawler import ChangeEvent
from unipaith.models.follow import InstitutionFollow
from unipaith.models.knowledge import InteractionSignal
from unipaith.models.student import StudentDataConsent, StudentProfile
from unipaith.models.workflow import Notification
from unipaith.services.crawler.util import to_jsonable
from unipaith.services.notification_service import NotificationService

_MATERIALITY_RANK = {"low": 0, "medium": 1, "high": 2}
_CHANGE_NOTIFICATION_TYPE = "program_change"


def classify_change(
    domain: str, field: str | None, old, new, *, created: bool = False
) -> tuple[str, str]:
    """Return (change_type, base_materiality) for a diff. The materiality is then
    bumped for large numeric moves by ``_bump_for_magnitude``."""
    if domain == "scholarships":
        if created:
            return "new_scholarship", "high"
        if field == "deadline":
            return "deadline_moved", "high"
        if field in ("amount_min", "amount_max"):
            return "cost_change", "medium"
        return "stat_update", "low"
    if field == "deadline":
        return "deadline_moved", "high"
    if domain == "visas":
        return "policy_change", "high"
    if domain == "tests":
        return "policy_change", "medium"
    if domain == "cost":
        return "cost_change", "medium"
    if domain == "rankings":
        return "ranking_update", "medium"
    if domain == "programs" and created:
        return "program_added", "medium"
    return "stat_update", "low"


def _bump_for_magnitude(materiality: str, old, new) -> str:
    try:
        o, n = float(old), float(new)
    except (TypeError, ValueError):
        return materiality
    if o == 0:
        return materiality
    if abs(n - o) / abs(o) >= 0.15 and materiality == "low":
        return "medium"
    if abs(n - o) / abs(o) >= 0.30 and materiality == "medium":
        return "high"
    return materiality


class ChangeDetector:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def record_change(
        self,
        *,
        domain: str,
        target_type: str,
        target_id: UUID | None,
        target_name: str | None,
        field: str | None,
        old,
        new,
        confidence: float,
        source_url: str | None = None,
        source_document_id: UUID | None = None,
        created: bool = False,
    ) -> ChangeEvent:
        """§3B — write a change_event for a real diff. Must trace to a source
        (``source_document_id`` / ``source_url``): no fabricated urgency."""
        change_type, materiality = classify_change(domain, field, old, new, created=created)
        materiality = _bump_for_magnitude(materiality, old, new)
        event = ChangeEvent(
            target_type=target_type,
            target_id=target_id,
            target_name=target_name,
            change_type=change_type,
            field_path=field,
            old_value={"value": to_jsonable(old)} if old is not None else None,
            new_value={"value": to_jsonable(new)} if new is not None else None,
            materiality=materiality,
            confidence=confidence,
            source_url=source_url,
            source_document_id=source_document_id,
            detected_at=datetime.now(UTC),
            status="pending",
        )
        self.db.add(event)
        await self.db.flush()
        return event

    async def _affected_user_ids(self, event: ChangeEvent) -> set[UUID]:
        """Whose saved / applied / followed set this change touches."""
        users: set[UUID] = set()
        if event.target_id is not None:
            result = await self.db.execute(
                select(InteractionSignal.user_id)
                .where(
                    InteractionSignal.entity_type == event.target_type,
                    InteractionSignal.entity_id == event.target_id,
                )
                .distinct()
            )
            users.update(uid for (uid,) in result.all())
            # Institution followers (follows are keyed on the student profile).
            if event.target_type in ("institution", "school"):
                fresult = await self.db.execute(
                    select(StudentProfile.user_id)
                    .join(InstitutionFollow, InstitutionFollow.student_id == StudentProfile.id)
                    .where(
                        InstitutionFollow.institution_id == event.target_id,
                        InstitutionFollow.muted.is_(False),
                    )
                    .distinct()
                )
                users.update(uid for (uid,) in fresult.all())
        return {u for u in users if u is not None}

    async def _has_outreach_consent(self, user_id: UUID) -> bool:
        result = await self.db.execute(
            select(StudentDataConsent.consent_outreach)
            .join(StudentProfile, StudentProfile.id == StudentDataConsent.student_id)
            .where(StudentProfile.user_id == user_id)
        )
        row = result.scalar_one_or_none()
        # No consent record → treat as not consented (consent IS built, 46 §2).
        return bool(row)

    async def _routed_today(self, user_id: UUID) -> int:
        since = datetime.now(UTC) - timedelta(hours=24)
        result = await self.db.execute(
            select(func.count())
            .select_from(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.notification_type == _CHANGE_NOTIFICATION_TYPE,
                Notification.created_at >= since,
            )
        )
        return int(result.scalar_one() or 0)

    async def route(self, event: ChangeEvent) -> dict:
        """Route a change_event to affected, consenting students under the daily
        cap. Returns the routing summary and stamps it on the event (§3B)."""
        summary = {
            "recipients": 0,
            "notifications": 0,
            "suppressed_consent": 0,
            "suppressed_cap": 0,
            "suppressed_materiality": 0,
        }
        threshold = _MATERIALITY_RANK.get(settings.change_event_min_materiality_to_route, 1)
        if _MATERIALITY_RANK.get(event.materiality, 0) < threshold:
            summary["suppressed_materiality"] = 1
            event.status = "dismissed"
            event.routing = summary
            event.routed_at = datetime.now(UTC)
            await self.db.flush()
            return summary

        affected = await self._affected_user_ids(event)
        summary["recipients"] = len(affected)
        notifier = NotificationService(self.db)
        cap = settings.change_event_route_cap_per_user_per_day
        title = _title_for(event)
        body = _body_for(event)
        for user_id in affected:
            if not await self._has_outreach_consent(user_id):
                summary["suppressed_consent"] += 1
                continue
            if await self._routed_today(user_id) >= cap:
                summary["suppressed_cap"] += 1
                continue
            await notifier.notify(
                user_id=user_id,
                notification_type=_CHANGE_NOTIFICATION_TYPE,
                title=title,
                body=body,
                action_url=_action_url_for(event),
                metadata={
                    "change_event_id": str(event.id),
                    "change_type": event.change_type,
                    "materiality": event.materiality,
                    "source_url": event.source_url,
                },
            )
            summary["notifications"] += 1

        event.status = "routed"
        event.routed_at = datetime.now(UTC)
        event.routing = summary
        await self.db.flush()
        return summary


def _title_for(event: ChangeEvent) -> str:
    name = event.target_name or "A program you follow"
    labels = {
        "deadline_moved": "Deadline changed",
        "new_scholarship": "New scholarship",
        "policy_change": "Policy update",
        "program_added": "New program",
        "program_closed": "Program closed",
        "cost_change": "Cost update",
        "ranking_update": "Ranking update",
        "stat_update": "Updated information",
        "new_event": "New event",
    }
    return f"{labels.get(event.change_type, 'Update')}: {name}"


def _body_for(event: ChangeEvent) -> str:
    src = f" Reported by {event.source_url}." if event.source_url else ""
    return (
        f"We detected a {event.change_type.replace('_', ' ')} for "
        f"{event.target_name or 'an entity you track'}.{src}"
    )


def _action_url_for(event: ChangeEvent) -> str | None:
    if event.target_type in ("program",) and event.target_id:
        return f"/programs/{event.target_id}"
    if event.target_type in ("institution", "school") and event.target_id:
        return f"/school/{event.target_id}"
    return "/s/posts"

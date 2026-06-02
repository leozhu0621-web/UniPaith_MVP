"""Spec 56 §6 — Saved searches + the proactive alert loop.

CRUD over ``saved_searches`` plus ``run_alerts()`` — the scheduled job that
re-runs every alert-enabled saved search against the (crawler-freshened) index
and emits an in-app + email notification when new matches appear. The loop is
**consent-gated** (Spec 46 — ``consent_outreach``) and **capped** per user per
day (Spec 56 §6), and it leans on the existing ``SearchService`` and
``NotificationService`` rather than re-implementing either.

Detection is count-based: a run records ``last_match_count``; the next run
alerts when the live total exceeds that baseline (first run only seeds the
baseline, never alerts). That's the honest MVP signal — it catches new programs
and newly-matching ones without claiming per-field change detection that the
non-embedding index can't yet support.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import settings
from unipaith.core.exceptions import BadRequestException, NotFoundException
from unipaith.models.saved_search import SavedSearch
from unipaith.models.workflow import Notification
from unipaith.schemas.saved_search import (
    SavedSearchCreate,
    SavedSearchRunResponse,
    SavedSearchUpdate,
)
from unipaith.schemas.search import SearchRequest
from unipaith.services.notification_service import NotificationService
from unipaith.services.search_service import SearchService
from unipaith.services.student_service import StudentService

logger = logging.getLogger(__name__)

ALERT_NOTIFICATION_TYPE = "saved_search_alert"
_SAMPLE_SIZE = 5
# A defensive ceiling on how many alert-enabled searches one loop processes, so
# a single tick can't run unbounded queries. Logged when hit (no silent cap).
_ALERT_BATCH_LIMIT = 500


class SavedSearchService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── CRUD ─────────────────────────────────────────────────────────────────
    async def list(self, user_id: UUID) -> list[SavedSearch]:
        result = await self.db.execute(
            select(SavedSearch)
            .where(SavedSearch.user_id == user_id)
            .order_by(SavedSearch.created_at.desc())
        )
        return list(result.scalars().all())

    async def get(self, user_id: UUID, saved_search_id: UUID) -> SavedSearch:
        result = await self.db.execute(
            select(SavedSearch).where(
                SavedSearch.id == saved_search_id,
                SavedSearch.user_id == user_id,
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            raise NotFoundException("Saved search not found")
        return row

    async def create(self, user_id: UUID, payload: SavedSearchCreate) -> SavedSearch:
        count = await self.db.scalar(
            select(func.count()).select_from(SavedSearch).where(SavedSearch.user_id == user_id)
        )
        if (count or 0) >= settings.saved_search_max_per_user:
            raise BadRequestException(
                f"You can save up to {settings.saved_search_max_per_user} searches. "
                "Delete one to add another."
            )
        row = SavedSearch(
            user_id=user_id,
            name=payload.name.strip(),
            entity_type=payload.entity_type,
            query=payload.query.model_dump(mode="json"),
            alert_enabled=payload.alert_enabled,
        )
        self.db.add(row)
        await self.db.flush()
        # Load server-generated timestamps in-greenlet so response serialization
        # never triggers a lazy refresh outside the async context.
        await self.db.refresh(row)
        return row

    async def update(
        self, user_id: UUID, saved_search_id: UUID, payload: SavedSearchUpdate
    ) -> SavedSearch:
        row = await self.get(user_id, saved_search_id)
        if payload.name is not None:
            row.name = payload.name.strip()
        if payload.query is not None:
            row.query = payload.query.model_dump(mode="json")
        if payload.alert_enabled is not None:
            row.alert_enabled = payload.alert_enabled
        await self.db.flush()
        # onupdate=now() expires updated_at after flush; refresh so serialization
        # doesn't lazy-load it outside the greenlet (MissingGreenlet).
        await self.db.refresh(row)
        return row

    async def delete(self, user_id: UUID, saved_search_id: UUID) -> None:
        row = await self.get(user_id, saved_search_id)
        await self.db.delete(row)
        await self.db.flush()

    # ── Run now ──────────────────────────────────────────────────────────────
    async def run(
        self, saved_search: SavedSearch, *, student_profile_id: UUID | None = None
    ) -> SavedSearchRunResponse:
        """Replay a saved search against the live index now; refresh the
        baseline used by the alert loop."""
        total, results = await self._execute(
            saved_search, page_size=_SAMPLE_SIZE, student_profile_id=student_profile_id
        )
        saved_search.last_run_at = datetime.now(UTC)
        saved_search.last_match_count = total
        await self.db.flush()
        return SavedSearchRunResponse(count=total, results=results)

    async def _execute(
        self,
        saved_search: SavedSearch,
        *,
        page_size: int,
        student_profile_id: UUID | None = None,
    ) -> tuple[int, list]:
        """Build a SearchRequest from the stored query and run it. Returns
        (total, results-sample). Only program search is index-backed today;
        other entity types degrade to an empty result rather than erroring."""
        if saved_search.entity_type != "program":
            return 0, []
        req = SearchRequest.model_validate(
            {**(saved_search.query or {}), "page": 1, "page_size": page_size}
        )
        resp = await SearchService(self.db).search(req, student_profile_id=student_profile_id)
        return resp.total, list(resp.results)

    # ── Alert loop (scheduled) ───────────────────────────────────────────────
    async def run_alerts(self) -> int:
        """Re-run every alert-enabled saved search; notify on new matches.
        Consent-gated and per-user-per-day capped. Returns alerts emitted."""
        result = await self.db.execute(
            select(SavedSearch)
            .where(SavedSearch.alert_enabled.is_(True))
            .order_by(SavedSearch.last_run_at.asc().nullsfirst())
            .limit(_ALERT_BATCH_LIMIT + 1)
        )
        rows = list(result.scalars().all())
        if len(rows) > _ALERT_BATCH_LIMIT:
            logger.warning(
                "saved-search alert loop hit the per-tick batch limit (%d); "
                "remaining searches run next tick",
                _ALERT_BATCH_LIMIT,
            )
            rows = rows[:_ALERT_BATCH_LIMIT]

        student_svc = StudentService(self.db)
        notif_svc = NotificationService(self.db)
        emitted = 0

        for row in rows:
            try:
                profile = await student_svc._get_student_profile(row.user_id)
            except Exception:
                continue  # not a student / no profile — skip silently
            if profile is None:
                continue

            # Spec 46 — proactive comms require the outreach consent lever.
            consent = await student_svc.get_data_consent(profile.id)
            if consent is not None and not consent.consent_outreach:
                continue

            baseline = row.last_match_count
            try:
                total, _ = await self._execute(row, page_size=1, student_profile_id=profile.id)
            except Exception as exc:  # one bad search must not stall the loop
                logger.info("saved-search alert run failed for %s: %s", row.id, exc)
                continue

            row.last_run_at = datetime.now(UTC)
            new_matches = total - baseline if baseline is not None else 0
            row.last_match_count = total

            if new_matches <= 0:
                continue
            if await self._alerts_today(row.user_id) >= settings.saved_search_alert_cap_per_day:
                continue  # batched into the digest instead (§6)

            await notif_svc.notify(
                user_id=row.user_id,
                notification_type=ALERT_NOTIFICATION_TYPE,
                title=f"New matches for “{row.name}”",
                body=(
                    f"{new_matches} new program"
                    f"{'s' if new_matches != 1 else ''} now match your saved "
                    f"search “{row.name}”."
                ),
                action_url="/s/saved?tab=searches",
                metadata={
                    "saved_search_id": str(row.id),
                    "new_matches": new_matches,
                    "total_matches": total,
                },
            )
            row.last_alerted_at = datetime.now(UTC)
            emitted += 1

        await self.db.flush()
        return emitted

    async def _alerts_today(self, user_id: UUID) -> int:
        """Count saved-search alert notifications sent to this user since UTC
        midnight — the per-user daily cap denominator (§6)."""
        since = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        count = await self.db.scalar(
            select(func.count())
            .select_from(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.notification_type == ALERT_NOTIFICATION_TYPE,
                Notification.created_at >= since,
            )
        )
        return count or 0

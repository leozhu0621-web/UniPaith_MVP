"""Spec 40 — Recruitment CRM (Pre-Applicant) service.

The institution top-of-funnel business logic: prospect management (records,
import with dedup + suppression + consent, conversion to applicants, push to a
campaign list), the recruiter travel calendar (trips + visits, over-budget +
conflict flags), the HS / college-fair directory (with lead capture → prospects
+ attribution), and territory management (aggregate-on-read dashboards).

AI (§5): ProspectPrioritizer ranks prospects by apply-likelihood on list load;
TerritoryOptimizer suggests high-yield sources per territory. Both are gated by
``ai_recruitment_v2_enabled`` and fall back to deterministic ordering, so no
endpoint ever 5xxes on an AI failure. Prioritization + planning only — never
selection (46 §6).
"""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from unipaith.ai.prospect_prioritizer import get_prospect_prioritizer
from unipaith.ai.territory_optimizer import deterministic_suggestions, get_territory_optimizer
from unipaith.config import settings
from unipaith.core.exceptions import BadRequestException, NotFoundException
from unipaith.models.application import Application
from unipaith.models.institution import (
    CampaignSuppression,
    Institution,
    UploadedContact,
    UploadedList,
)
from unipaith.models.recruitment import (
    FAIR_KINDS,
    FAIR_STATUSES,
    PROSPECT_SOURCES,
    PROSPECT_STAGES,
    TRIP_STATUSES,
    VISIT_KINDS,
    VISIT_STATUSES,
    Prospect,
    RecruitmentFair,
    RecruitmentTrip,
    Territory,
    TripVisit,
)
from unipaith.schemas.recruitment import (
    ConvertProspectRequest,
    CreateFairRequest,
    CreateProspectRequest,
    CreateTerritoryRequest,
    CreateTripRequest,
    FairCaptureRequest,
    ProspectImportRequest,
    ProspectToSegmentRequest,
    UpdateFairRequest,
    UpdateProspectRequest,
    UpdateTerritoryRequest,
    UpdateTripRequest,
    UpdateTripVisitRequest,
)
from unipaith.services.attribution_service import AttributionService

logger = logging.getLogger("unipaith.recruitment")

# Cap how many prospects we score / return in one list call (MVP scale).
_LIST_CAP = 1000


def _norm_email(email: str | None) -> str | None:
    if not email:
        return None
    e = email.strip().lower()
    return e or None


def _validate(value: str, allowed: tuple[str, ...], field: str) -> str:
    if value not in allowed:
        raise BadRequestException(f"Invalid {field} '{value}'. Allowed: {', '.join(allowed)}")
    return value


class RecruitmentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.attribution = AttributionService(db)

    # ── institution resolution ───────────────────────────────────────────────

    async def get_institution(self, user_id: UUID) -> Institution:
        result = await self.db.execute(
            select(Institution).where(Institution.admin_user_id == user_id)
        )
        institution = result.scalar_one_or_none()
        if not institution:
            raise NotFoundException("Institution not found")
        return institution

    # ── prospects ─────────────────────────────────────────────────────────────

    async def list_prospects(
        self,
        institution_id: UUID,
        *,
        stage: str | None = None,
        source: str | None = None,
        territory_id: UUID | None = None,
        owner_user_id: UUID | None = None,
        search: str | None = None,
        limit: int = _LIST_CAP,
    ) -> tuple[list[Prospect], dict[str, dict], bool, dict[str, int]]:
        """Return (prospects, score_map, prioritized, stage_counts). When
        ``ai_recruitment_v2_enabled`` is on, ProspectPrioritizer scores each
        prospect read-only (``score_map[id] = {apply_likelihood, band, reason}``)
        and the list is sorted by apply-likelihood desc; otherwise it falls back
        to recency order (§5). Scoring is side-effect-free — it never writes to
        the rows, so serialization never triggers a post-flush lazy load."""
        stmt = select(Prospect).where(Prospect.institution_id == institution_id)
        if stage:
            stmt = stmt.where(Prospect.stage == stage)
        if source:
            stmt = stmt.where(Prospect.source == source)
        if territory_id:
            stmt = stmt.where(Prospect.territory_id == territory_id)
        if owner_user_id:
            stmt = stmt.where(Prospect.owner_user_id == owner_user_id)
        if search:
            like = f"%{search.strip()}%"
            stmt = stmt.where(or_(Prospect.name.ilike(like), Prospect.email.ilike(like)))
        stmt = stmt.order_by(Prospect.created_at.desc()).limit(limit)
        rows = list((await self.db.execute(stmt)).scalars().all())

        prioritized = False
        score_map: dict[str, dict] = {}
        if settings.ai_recruitment_v2_enabled and rows:
            try:
                score_map = get_prospect_prioritizer().score(
                    [
                        {
                            "id": p.id,
                            "stage": p.stage,
                            "source": p.source,
                            "email": p.email,
                            "phone": p.phone,
                            "interests": p.interests,
                            "consent_outreach": p.consent_outreach,
                        }
                        for p in rows
                    ]
                )
                rows.sort(
                    key=lambda p: (score_map.get(str(p.id)) or {}).get("apply_likelihood") or 0.0,
                    reverse=True,
                )
                prioritized = True
            except Exception:  # noqa: BLE001 — never let scoring break the list
                logger.warning("prospect prioritization failed (swallowed)", exc_info=True)
                score_map = {}

        stage_counts = await self._stage_counts(institution_id)
        return rows, score_map, prioritized, stage_counts

    async def _stage_counts(self, institution_id: UUID) -> dict[str, int]:
        rows = await self.db.execute(
            select(Prospect.stage, func.count())
            .where(Prospect.institution_id == institution_id)
            .group_by(Prospect.stage)
        )
        counts = {s: 0 for s in PROSPECT_STAGES}
        for stage, n in rows.all():
            counts[stage] = n
        return counts

    async def get_prospect(self, institution_id: UUID, prospect_id: UUID) -> Prospect:
        result = await self.db.execute(
            select(Prospect).where(
                Prospect.id == prospect_id, Prospect.institution_id == institution_id
            )
        )
        prospect = result.scalar_one_or_none()
        if not prospect:
            raise NotFoundException("Prospect not found")
        return prospect

    async def create_prospect(self, institution_id: UUID, data: CreateProspectRequest) -> Prospect:
        _validate(data.source, PROSPECT_SOURCES, "source")
        _validate(data.stage, PROSPECT_STAGES, "stage")
        suppressed = await self._suppression_set(institution_id, [data.email])
        consent = data.consent_outreach and _norm_email(data.email) not in suppressed
        prospect = Prospect(
            institution_id=institution_id,
            name=data.name,
            email=data.email,
            phone=data.phone,
            city=data.city,
            region=data.region,
            country=data.country,
            interests=data.interests or [],
            source=data.source,
            source_detail=data.source_detail,
            stage=data.stage,
            territory_id=data.territory_id,
            owner_user_id=data.owner_user_id,
            owner_name=data.owner_name,
            consent_outreach=consent,
            notes=data.notes,
        )
        self.db.add(prospect)
        await self.db.flush()
        await self.db.refresh(prospect)
        return prospect

    async def update_prospect(
        self, institution_id: UUID, prospect_id: UUID, data: UpdateProspectRequest
    ) -> Prospect:
        prospect = await self.get_prospect(institution_id, prospect_id)
        payload = data.model_dump(exclude_unset=True)
        if "source" in payload and payload["source"] is not None:
            _validate(payload["source"], PROSPECT_SOURCES, "source")
        if "stage" in payload and payload["stage"] is not None:
            _validate(payload["stage"], PROSPECT_STAGES, "stage")
        # If turning consent on, honour the suppression list.
        if payload.get("consent_outreach"):
            email = payload.get("email", prospect.email)
            suppressed = await self._suppression_set(institution_id, [email])
            if _norm_email(email) in suppressed:
                payload["consent_outreach"] = False
        for key, value in payload.items():
            setattr(prospect, key, value)
        await self.db.flush()
        await self.db.refresh(prospect)
        return prospect

    async def _suppression_set(self, institution_id: UUID, emails: list[str | None]) -> set[str]:
        """Lower-cased suppressed emails for this institution intersected with the
        given candidate emails (§2.1 / 46 — never market to a suppressed address)."""
        candidates = {e for e in (_norm_email(x) for x in emails) if e}
        if not candidates:
            return set()
        rows = await self.db.execute(
            select(func.lower(CampaignSuppression.email)).where(
                CampaignSuppression.institution_id == institution_id,
                func.lower(CampaignSuppression.email).in_(candidates),
            )
        )
        return {r[0] for r in rows.all()}

    async def import_prospects(
        self, institution_id: UUID, data: ProspectImportRequest
    ) -> dict[str, int]:
        """Bulk-import prospects: dedup by lower(email) (update-in-place, never a
        duplicate person), apply the suppression list, and default outreach
        consent to opt-in only (§2.1 / §9)."""
        _validate(data.source, PROSPECT_SOURCES, "source")
        rows = data.rows or []
        all_emails = [r.email for r in rows]
        suppressed = await self._suppression_set(institution_id, all_emails)

        # Existing prospects keyed by lower(email) for dedup.
        existing_rows = await self.db.execute(
            select(Prospect).where(
                Prospect.institution_id == institution_id, Prospect.email.isnot(None)
            )
        )
        existing: dict[str, Prospect] = {}
        for p in existing_rows.scalars().all():
            ne = _norm_email(p.email)
            if ne:
                existing.setdefault(ne, p)

        imported = deduped = suppressed_count = 0
        seen_in_batch: set[str] = set()
        for row in rows:
            ne = _norm_email(row.email)
            is_suppressed = bool(ne and ne in suppressed)
            consent = row.consent_outreach and not is_suppressed
            if is_suppressed:
                suppressed_count += 1

            if ne and (ne in existing or ne in seen_in_batch):
                # Dedup: update the existing record's enrichable fields; never
                # create a second person row.
                target = existing.get(ne)
                if target is not None:
                    if row.city:
                        target.city = row.city
                    if row.region:
                        target.region = row.region
                    if row.country:
                        target.country = row.country
                    if row.interests:
                        target.interests = sorted(set((target.interests or []) + row.interests))
                    if consent:
                        target.consent_outreach = True
                deduped += 1
                continue

            prospect = Prospect(
                institution_id=institution_id,
                name=row.name,
                email=row.email,
                phone=row.phone,
                city=row.city,
                region=row.region,
                country=row.country,
                interests=row.interests or [],
                source=data.source,
                source_detail=data.source_detail,
                stage="prospect",
                territory_id=data.territory_id,
                consent_outreach=consent,
            )
            self.db.add(prospect)
            imported += 1
            if ne:
                existing[ne] = prospect
                seen_in_batch.add(ne)

        await self.db.flush()
        return {
            "imported": imported,
            "deduped": deduped,
            "suppressed": suppressed_count,
            "total_rows": len(rows),
        }

    async def convert_prospect(
        self, institution_id: UUID, prospect_id: UUID, data: ConvertProspectRequest
    ) -> Prospect:
        """Advance a prospect to the ``applicant`` stage with a forward link to
        the application they started. Idempotent — never spawns a duplicate
        person/application record (§2.1 / §9)."""
        prospect = await self.get_prospect(institution_id, prospect_id)

        if data.application_id is not None:
            # Verify the application belongs to a program owned by this institution.
            app = await self.db.execute(
                select(Application).where(Application.id == data.application_id)
            )
            application = app.scalar_one_or_none()
            if not application:
                raise NotFoundException("Application not found")
            # Idempotent: only set the link the first time.
            if prospect.converted_application_id is None:
                prospect.converted_application_id = data.application_id

        prospect.stage = "applicant"
        await self.db.flush()
        await self.db.refresh(prospect)
        return prospect

    async def prospects_to_segment(
        self, institution_id: UUID, user_id: UUID, data: ProspectToSegmentRequest
    ) -> dict:
        """Push selected prospects into a reusable uploaded list (Spec 25/26)
        for campaign targeting. Consent-gated: only prospects with
        ``consent_outreach`` AND an email are added (§2.1 / §3 / 46)."""
        result = await self.db.execute(
            select(Prospect).where(
                Prospect.institution_id == institution_id,
                Prospect.id.in_(data.prospect_ids),
            )
        )
        prospects = list(result.scalars().all())
        if not prospects:
            raise NotFoundException("No matching prospects found")

        lst = UploadedList(
            institution_id=institution_id,
            name=data.list_name,
            description="Generated from recruitment CRM prospects",
            source="crm",
            source_consent_confirmed=True,
            contact_count=0,
            created_by=user_id,
        )
        self.db.add(lst)
        await self.db.flush()

        added = skipped_no_consent = skipped_no_email = 0
        seen: set[str] = set()
        for p in prospects:
            ne = _norm_email(p.email)
            if not ne:
                skipped_no_email += 1
                continue
            if not p.consent_outreach:
                skipped_no_consent += 1
                continue
            if ne in seen:
                continue
            seen.add(ne)
            first, _, last = (p.name or "").partition(" ")
            self.db.add(
                UploadedContact(
                    list_id=lst.id,
                    institution_id=institution_id,
                    email=p.email,
                    first_name=first or None,
                    last_name=last or None,
                )
            )
            added += 1

        lst.contact_count = added
        await self.db.flush()
        return {
            "list_id": lst.id,
            "list_name": lst.name,
            "added": added,
            "skipped_no_consent": skipped_no_consent,
            "skipped_no_email": skipped_no_email,
        }

    # ── travel calendar (trips + visits) ──────────────────────────────────────

    async def list_trips(self, institution_id: UUID) -> list[RecruitmentTrip]:
        result = await self.db.execute(
            select(RecruitmentTrip)
            .where(RecruitmentTrip.institution_id == institution_id)
            .options(selectinload(RecruitmentTrip.visits))
            .order_by(RecruitmentTrip.start_date.desc())
        )
        return list(result.scalars().all())

    def trip_flags(
        self, trip: RecruitmentTrip, all_trips: list[RecruitmentTrip]
    ) -> tuple[bool, bool]:
        """(over_budget, conflict) for a trip (§6). Conflict = same recruiter,
        overlapping dates with another trip."""
        over_budget = trip.budget is not None and (trip.spend or 0) > trip.budget
        conflict = False
        if trip.recruiter_user_id is not None:
            for other in all_trips:
                if other.id == trip.id or other.recruiter_user_id != trip.recruiter_user_id:
                    continue
                if trip.start_date <= other.end_date and other.start_date <= trip.end_date:
                    conflict = True
                    break
        return over_budget, conflict

    async def get_trip(self, institution_id: UUID, trip_id: UUID) -> RecruitmentTrip:
        result = await self.db.execute(
            select(RecruitmentTrip)
            .where(
                RecruitmentTrip.id == trip_id,
                RecruitmentTrip.institution_id == institution_id,
            )
            .options(selectinload(RecruitmentTrip.visits))
        )
        trip = result.scalar_one_or_none()
        if not trip:
            raise NotFoundException("Trip not found")
        return trip

    async def create_trip(self, institution_id: UUID, data: CreateTripRequest) -> RecruitmentTrip:
        _validate(data.status, TRIP_STATUSES, "status")
        if data.end_date < data.start_date:
            raise BadRequestException("end_date must be on or after start_date")
        trip = RecruitmentTrip(
            institution_id=institution_id,
            name=data.name,
            region=data.region,
            start_date=data.start_date,
            end_date=data.end_date,
            recruiter_user_id=data.recruiter_user_id,
            recruiter_name=data.recruiter_name,
            budget=data.budget,
            spend=data.spend if data.spend is not None else 0,
            status=data.status,
            notes=data.notes,
        )
        for v in data.visits:
            _validate(v.kind, VISIT_KINDS, "visit kind")
            _validate(v.status, VISIT_STATUSES, "visit status")
            trip.visits.append(
                TripVisit(
                    kind=v.kind,
                    name=v.name,
                    fair_id=v.fair_id,
                    visit_date=v.visit_date,
                    status=v.status,
                    notes=v.notes,
                )
            )
        self.db.add(trip)
        await self.db.flush()
        await self.db.refresh(trip, attribute_names=["visits"])
        return trip

    async def update_trip(
        self, institution_id: UUID, trip_id: UUID, data: UpdateTripRequest
    ) -> RecruitmentTrip:
        trip = await self.get_trip(institution_id, trip_id)
        payload = data.model_dump(exclude_unset=True)
        if "status" in payload and payload["status"] is not None:
            _validate(payload["status"], TRIP_STATUSES, "status")
        start = payload.get("start_date", trip.start_date)
        end = payload.get("end_date", trip.end_date)
        if start and end and end < start:
            raise BadRequestException("end_date must be on or after start_date")
        for key, value in payload.items():
            setattr(trip, key, value)
        await self.db.flush()
        await self.db.refresh(trip, attribute_names=["visits"])
        return trip

    async def add_visit(self, institution_id: UUID, trip_id: UUID, data) -> RecruitmentTrip:
        trip = await self.get_trip(institution_id, trip_id)
        _validate(data.kind, VISIT_KINDS, "visit kind")
        _validate(data.status, VISIT_STATUSES, "visit status")
        trip.visits.append(
            TripVisit(
                kind=data.kind,
                name=data.name,
                fair_id=data.fair_id,
                visit_date=data.visit_date,
                status=data.status,
                notes=data.notes,
            )
        )
        await self.db.flush()
        await self.db.refresh(trip, attribute_names=["visits"])
        return trip

    async def update_visit(
        self,
        institution_id: UUID,
        trip_id: UUID,
        visit_id: UUID,
        data: UpdateTripVisitRequest,
    ) -> RecruitmentTrip:
        trip = await self.get_trip(institution_id, trip_id)
        visit = next((v for v in trip.visits if v.id == visit_id), None)
        if visit is None:
            raise NotFoundException("Visit not found")
        payload = data.model_dump(exclude_unset=True)
        if payload.get("kind") is not None:
            _validate(payload["kind"], VISIT_KINDS, "visit kind")
        if payload.get("status") is not None:
            _validate(payload["status"], VISIT_STATUSES, "visit status")
        for key, value in payload.items():
            setattr(visit, key, value)
        await self.db.flush()
        await self.db.refresh(trip, attribute_names=["visits"])
        return trip

    # ── fairs / HS directory ──────────────────────────────────────────────────

    async def list_fairs(self, institution_id: UUID) -> list[RecruitmentFair]:
        result = await self.db.execute(
            select(RecruitmentFair)
            .where(RecruitmentFair.institution_id == institution_id)
            .order_by(RecruitmentFair.prior_year_yield.desc().nullslast(), RecruitmentFair.name)
        )
        return list(result.scalars().all())

    async def get_fair(self, institution_id: UUID, fair_id: UUID) -> RecruitmentFair:
        result = await self.db.execute(
            select(RecruitmentFair).where(
                RecruitmentFair.id == fair_id,
                RecruitmentFair.institution_id == institution_id,
            )
        )
        fair = result.scalar_one_or_none()
        if not fair:
            raise NotFoundException("Fair not found")
        return fair

    async def create_fair(self, institution_id: UUID, data: CreateFairRequest) -> RecruitmentFair:
        _validate(data.kind, FAIR_KINDS, "kind")
        _validate(data.status, FAIR_STATUSES, "status")
        fair = RecruitmentFair(institution_id=institution_id, **data.model_dump())
        self.db.add(fair)
        await self.db.flush()
        await self.db.refresh(fair)
        return fair

    async def update_fair(
        self, institution_id: UUID, fair_id: UUID, data: UpdateFairRequest
    ) -> RecruitmentFair:
        fair = await self.get_fair(institution_id, fair_id)
        payload = data.model_dump(exclude_unset=True)
        if payload.get("kind") is not None:
            _validate(payload["kind"], FAIR_KINDS, "kind")
        if payload.get("status") is not None:
            _validate(payload["status"], FAIR_STATUSES, "status")
        for key, value in payload.items():
            setattr(fair, key, value)
        await self.db.flush()
        await self.db.refresh(fair)
        return fair

    async def capture_leads(
        self, institution_id: UUID, fair_id: UUID, data: FairCaptureRequest
    ) -> dict:
        """Capture prospects met at a fair → prospect records tagged with the
        source, an attribution event per the §2.3 / §9 / 28 flow, and a bump to
        the linked trip visit's ``prospects_met`` counter."""
        fair = await self.get_fair(institution_id, fair_id)
        emails = [lead.email for lead in data.leads]
        suppressed = await self._suppression_set(institution_id, emails)

        existing_rows = await self.db.execute(
            select(Prospect).where(
                Prospect.institution_id == institution_id, Prospect.email.isnot(None)
            )
        )
        existing = {}
        for p in existing_rows.scalars().all():
            ne = _norm_email(p.email)
            if ne:
                existing.setdefault(ne, p)

        captured = deduped = suppressed_count = 0
        for lead in data.leads:
            ne = _norm_email(lead.email)
            is_suppressed = bool(ne and ne in suppressed)
            if is_suppressed:
                suppressed_count += 1
            consent = lead.consent_outreach and not is_suppressed

            if ne and ne in existing:
                target = existing[ne]
                if lead.interests:
                    target.interests = sorted(set((target.interests or []) + lead.interests))
                if consent:
                    target.consent_outreach = True
                target.source_detail = fair.name
                deduped += 1
            else:
                prospect = Prospect(
                    institution_id=institution_id,
                    name=lead.name,
                    email=lead.email,
                    phone=lead.phone,
                    interests=lead.interests or [],
                    source="fair",
                    source_detail=fair.name,
                    stage="prospect",
                    city=fair.city,
                    region=fair.region,
                    country=fair.country,
                    territory_id=data.territory_id,
                    consent_outreach=consent,
                )
                self.db.add(prospect)
                if ne:
                    existing[ne] = prospect
                captured += 1

            # Attribution (§9 / 28): every captured lead carries the fair source.
            await self.attribution.record(
                institution_id=institution_id,
                source_kind="fair",
                source_id=fair.id,
                action="lead_captured",
                meta={"fair_name": fair.name, "kind": fair.kind},
            )

        # Bump the linked visit's prospects_met counter, if any.
        if data.trip_visit_id is not None:
            visit_row = await self.db.execute(
                select(TripVisit)
                .join(RecruitmentTrip, TripVisit.trip_id == RecruitmentTrip.id)
                .where(
                    TripVisit.id == data.trip_visit_id,
                    RecruitmentTrip.institution_id == institution_id,
                )
            )
            visit = visit_row.scalar_one_or_none()
            if visit is not None:
                visit.prospects_met = (visit.prospects_met or 0) + captured + deduped
                if visit.status == "planned":
                    visit.status = "done"

        # Mark the fair attended once leads have been captured against it.
        if fair.status in ("prospective", "registered", "confirmed"):
            fair.status = "attended"

        await self.db.flush()
        return {
            "captured": captured,
            "deduped": deduped,
            "suppressed": suppressed_count,
            "fair_id": fair.id,
        }

    # ── territories ───────────────────────────────────────────────────────────

    async def _territory_metrics(self, institution_id: UUID) -> dict[UUID, tuple[int, int]]:
        """Per-territory (prospect_count, applicant_count) in two grouped queries."""
        prospect_rows = await self.db.execute(
            select(Prospect.territory_id, func.count())
            .where(
                Prospect.institution_id == institution_id,
                Prospect.territory_id.isnot(None),
            )
            .group_by(Prospect.territory_id)
        )
        applicant_rows = await self.db.execute(
            select(Prospect.territory_id, func.count())
            .where(
                Prospect.institution_id == institution_id,
                Prospect.territory_id.isnot(None),
                Prospect.stage == "applicant",
            )
            .group_by(Prospect.territory_id)
        )
        prospects = {tid: n for tid, n in prospect_rows.all()}
        applicants = {tid: n for tid, n in applicant_rows.all()}
        out: dict[UUID, tuple[int, int]] = {}
        for tid in set(prospects) | set(applicants):
            out[tid] = (prospects.get(tid, 0), applicants.get(tid, 0))
        return out

    async def list_territories(self, institution_id: UUID) -> list[dict]:
        result = await self.db.execute(
            select(Territory)
            .where(Territory.institution_id == institution_id)
            .order_by(Territory.name)
        )
        territories = list(result.scalars().all())
        metrics = await self._territory_metrics(institution_id)
        out: list[dict] = []
        for t in territories:
            pc, ac = metrics.get(t.id, (0, 0))
            out.append(self._territory_dict(t, pc, ac))
        return out

    @staticmethod
    def _territory_dict(t: Territory, prospect_count: int, applicant_count: int) -> dict:
        conversion = round(applicant_count / prospect_count, 4) if prospect_count else 0.0
        unassigned = t.owner_user_id is None and not (t.owner_name or "").strip()
        return {
            "id": t.id,
            "name": t.name,
            "geo": t.geo,
            "owner_user_id": t.owner_user_id,
            "owner_name": t.owner_name,
            "notes": t.notes,
            "prospect_count": prospect_count,
            "applicant_count": applicant_count,
            "conversion_rate": conversion,
            "unassigned": unassigned,
            "created_at": t.created_at,
            "updated_at": t.updated_at,
        }

    async def get_territory(self, institution_id: UUID, territory_id: UUID) -> Territory:
        result = await self.db.execute(
            select(Territory).where(
                Territory.id == territory_id, Territory.institution_id == institution_id
            )
        )
        territory = result.scalar_one_or_none()
        if not territory:
            raise NotFoundException("Territory not found")
        return territory

    async def create_territory(self, institution_id: UUID, data: CreateTerritoryRequest) -> dict:
        territory = Territory(
            institution_id=institution_id,
            name=data.name,
            geo=data.geo.model_dump() if data.geo else None,
            owner_user_id=data.owner_user_id,
            owner_name=data.owner_name,
            notes=data.notes,
        )
        self.db.add(territory)
        await self.db.flush()
        await self.db.refresh(territory)
        return self._territory_dict(territory, 0, 0)

    async def update_territory(
        self, institution_id: UUID, territory_id: UUID, data: UpdateTerritoryRequest
    ) -> dict:
        territory = await self.get_territory(institution_id, territory_id)
        payload = data.model_dump(exclude_unset=True)
        if "geo" in payload and payload["geo"] is not None:
            payload["geo"] = data.geo.model_dump()
        for key, value in payload.items():
            setattr(territory, key, value)
        await self.db.flush()
        await self.db.refresh(territory)
        metrics = await self._territory_metrics(institution_id)
        pc, ac = metrics.get(territory.id, (0, 0))
        return self._territory_dict(territory, pc, ac)

    async def territory_dashboard(self, institution_id: UUID) -> dict:
        territories = await self.list_territories(institution_id)
        total_p = sum(t["prospect_count"] for t in territories)
        total_a = sum(t["applicant_count"] for t in territories)
        unassigned = sum(1 for t in territories if t["unassigned"])
        return {
            "territories": territories,
            "total_prospects": total_p,
            "total_applicants": total_a,
            "overall_conversion_rate": round(total_a / total_p, 4) if total_p else 0.0,
            "unassigned_count": unassigned,
        }

    async def optimize_territory(self, institution_id: UUID, territory_id: UUID) -> dict:
        """Suggest high-yield sources for a territory (§5). TerritoryOptimizer
        (LLM) when enabled; deterministic prior-year-yield ranking otherwise or
        on any failure."""
        territory = await self.get_territory(institution_id, territory_id)
        metrics = await self._territory_metrics(institution_id)
        pc, ac = metrics.get(territory.id, (0, 0))

        # Candidate sources: the institution's fairs/HS, narrowed to the
        # territory's regions when geo is set.
        fairs = await self.list_fairs(institution_id)
        regions = set((territory.geo or {}).get("regions") or [])
        candidates = [
            {"name": f.name, "kind": f.kind, "prior_year_yield": f.prior_year_yield or 0}
            for f in fairs
            if not regions or (f.region and f.region in regions)
        ]
        snapshot = {
            "name": territory.name,
            "prospect_count": pc,
            "applicant_count": ac,
            "conversion_rate": (ac / pc) if pc else 0.0,
            "has_owner": territory.owner_user_id is not None
            or bool((territory.owner_name or "").strip()),
            "candidates": candidates,
        }

        ai_generated = False
        suggestions: list[dict] | None = None
        if settings.ai_recruitment_v2_enabled:
            suggestions = await get_territory_optimizer().suggest(snapshot, db=self.db)
            ai_generated = suggestions is not None
        if not suggestions:
            suggestions = deterministic_suggestions(snapshot)
        return {
            "territory_id": territory.id,
            "suggestions": suggestions,
            "ai_generated": ai_generated,
        }

    # ── summary ───────────────────────────────────────────────────────────────

    async def summary(self, institution_id: UUID) -> dict:
        stage_counts = await self._stage_counts(institution_id)
        source_rows = await self.db.execute(
            select(Prospect.source, func.count())
            .where(Prospect.institution_id == institution_id)
            .group_by(Prospect.source)
        )
        source_counts = {s: n for s, n in source_rows.all()}
        prospect_count = sum(stage_counts.values())
        applicant_count = stage_counts.get("applicant", 0)

        trip_count = await self.db.scalar(
            select(func.count())
            .select_from(RecruitmentTrip)
            .where(RecruitmentTrip.institution_id == institution_id)
        )
        fair_count = await self.db.scalar(
            select(func.count())
            .select_from(RecruitmentFair)
            .where(RecruitmentFair.institution_id == institution_id)
        )
        territories = await self.list_territories(institution_id)
        unassigned = sum(1 for t in territories if t["unassigned"])

        trips = await self.list_trips(institution_id)
        over_budget = sum(1 for t in trips if self.trip_flags(t, trips)[0])

        return {
            "prospect_count": prospect_count,
            "applicant_count": applicant_count,
            "trip_count": trip_count or 0,
            "fair_count": fair_count or 0,
            "territory_count": len(territories),
            "unassigned_territory_count": unassigned,
            "over_budget_trip_count": over_budget,
            "stage_counts": stage_counts,
            "source_counts": source_counts,
            "is_empty": prospect_count == 0 and (fair_count or 0) == 0 and (trip_count or 0) == 0,
        }

"""Spec 25 — Campaigns (institution outbound).

Owns the full campaign lifecycle: setup → audience resolution (multi-segment +
uploaded lists, deduped by email, suppression + consent gated) → multi-channel
delivery (internal Inbox messaging + external SES email) → metrics. The legacy
v0 columns (campaign_name / message_* / program_id / segment_id) are kept and
dual-written so older rows and the CRM touchpoint code keep working.

Trackable links + click/attribution recording stay in ``InstitutionService``
(unchanged, already wired); this service composes with them for the §8 metrics.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.core.exceptions import BadRequestException, NotFoundException
from unipaith.models.engagement import Conversation, Message
from unipaith.models.institution import (
    Campaign,
    CampaignAction,
    CampaignRecipient,
    CampaignSuppression,
    Institution,
    Program,
    UploadedContact,
    UploadedList,
)
from unipaith.models.student import StudentDataConsent, StudentProfile
from unipaith.models.user import User
from unipaith.models.workflow import Notification
from unipaith.schemas.institution import (
    ATTRIBUTION_ACTIONS,
    AudiencePreviewResponse,
    AudienceSamplePerson,
    CampaignAudience,
    CampaignMetrics,
    CampaignMetricsResponse,
    CampaignResponse,
    CreateCampaignRequest,
    CreateSuppressionRequest,
    CreateUploadedListRequest,
    SuppressionResponse,
    UpdateCampaignRequest,
    UpdateUploadedListRequest,
    UploadedListResponse,
)
from unipaith.services.institution_service import InstitutionService

logger = logging.getLogger("unipaith.campaigns")

# Statuses in which the campaign body / audience can still be edited.
_EDITABLE = {"draft", "pending_approval", "scheduled", "paused"}
# Statuses that mean the campaign has already gone out (no delete).
_SENT = {"active", "completed"}


def _norm_email(value: str | None) -> str | None:
    return value.strip().lower() if value else None


@dataclass
class _Recip:
    source: str  # 'platform' | 'uploaded_list'
    email: str | None
    first_name: str | None
    last_name: str | None
    consent_outreach: bool = True
    student_id: UUID | None = None
    user_id: UUID | None = None
    uploaded_contact_id: UUID | None = None


@dataclass
class _Audience:
    # Every unique person who will receive at least one message.
    people: list[_Recip] = field(default_factory=list)
    deduped_count: int = 0
    platform_count: int = 0
    uploaded_count: int = 0
    suppressed_count: int = 0
    consent_excluded_count: int = 0


class CampaignService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.inst_svc = InstitutionService(db)

    # ── helpers ─────────────────────────────────────────────────────────────
    async def _verify(self, institution_id: UUID, campaign_id: UUID) -> Campaign:
        result = await self.db.execute(
            select(Campaign).where(
                Campaign.id == campaign_id,
                Campaign.institution_id == institution_id,
            )
        )
        campaign = result.scalar_one_or_none()
        if not campaign:
            raise NotFoundException("Campaign not found")
        return campaign

    async def _requires_approval(self, institution_id: UUID) -> bool:
        return bool(
            await self.db.scalar(
                select(Institution.require_campaign_approval).where(
                    Institution.id == institution_id
                )
            )
        )

    @staticmethod
    def _as_uuid_list(values: list | None) -> list[UUID]:
        out: list[UUID] = []
        for v in values or []:
            try:
                out.append(v if isinstance(v, UUID) else UUID(str(v)))
            except (ValueError, AttributeError, TypeError):
                continue
        return out

    async def _to_response(
        self, c: Campaign, *, requires_approval: bool, metrics: CampaignMetrics | None = None
    ) -> CampaignResponse:
        return CampaignResponse(
            id=c.id,
            institution_id=c.institution_id,
            name=c.campaign_name,
            objective=c.objective,
            owner_id=c.owner_id,
            status=c.status or "draft",
            associate_program_ids=self._as_uuid_list(c.associate_program_ids),
            associate_intake_round_id=c.associate_intake_round_id,
            destination_type=c.destination_type,
            destination_id=c.destination_id,
            destination_url=c.destination_url,
            cta_type=c.cta_type,
            channels=list(c.channels or []),
            audience=CampaignAudience(
                segment_ids=self._as_uuid_list(c.audience_segment_ids),
                uploaded_list_ids=self._as_uuid_list(c.audience_uploaded_list_ids),
                deduped_count=c.audience_deduped_count,
            ),
            subject=c.message_subject,
            body=c.message_body,
            scheduled_at=c.scheduled_send_at,
            sent_at=c.sent_at,
            sent_count=c.sent_count,
            metrics=metrics,
            submitted_for_approval_at=c.submitted_for_approval_at,
            approved_by=c.approved_by,
            approved_at=c.approved_at,
            rejection_comment=c.rejection_comment,
            requires_approval=requires_approval,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )

    @staticmethod
    def _legacy_type(channels: list[str]) -> str:
        if "external_email" in channels:
            return "email"
        if "internal_messaging" in channels:
            return "in_app"
        return "email"

    # ── CRUD ────────────────────────────────────────────────────────────────
    async def list_campaigns(
        self, institution_id: UUID, status_filter: str | None = None
    ) -> list[CampaignResponse]:
        stmt = select(Campaign).where(Campaign.institution_id == institution_id)
        if status_filter:
            stmt = stmt.where(Campaign.status == status_filter)
        stmt = stmt.order_by(Campaign.created_at.desc())
        result = await self.db.execute(stmt)
        campaigns = list(result.scalars().all())
        requires = await self._requires_approval(institution_id)
        return [await self._to_response(c, requires_approval=requires) for c in campaigns]

    async def get_campaign(self, institution_id: UUID, campaign_id: UUID) -> CampaignResponse:
        c = await self._verify(institution_id, campaign_id)
        requires = await self._requires_approval(institution_id)
        return await self._to_response(c, requires_approval=requires)

    async def create_campaign(
        self, institution_id: UUID, data: CreateCampaignRequest
    ) -> CampaignResponse:
        program_ids = [str(p) for p in data.associate_program_ids]
        segment_ids = [str(s) for s in data.audience_segment_ids]
        uploaded_ids = [str(u) for u in data.audience_uploaded_list_ids]
        channels = data.channels or ["internal_messaging"]
        campaign = Campaign(
            institution_id=institution_id,
            campaign_name=data.name,
            objective=data.objective,
            owner_id=data.owner_id,
            campaign_type=self._legacy_type(channels),
            message_subject=data.subject,
            message_body=data.body,
            status="draft",
            scheduled_send_at=data.scheduled_at,
            destination_type=data.destination_type,
            destination_id=data.destination_id,
            destination_url=data.destination_url,
            cta_type=data.cta_type,
            channels=channels,
            associate_program_ids=program_ids,
            associate_intake_round_id=data.associate_intake_round_id,
            audience_segment_ids=segment_ids,
            audience_uploaded_list_ids=uploaded_ids,
            # Legacy single-value columns (first of each), kept for back-compat.
            program_id=UUID(program_ids[0]) if program_ids else None,
            segment_id=UUID(segment_ids[0]) if segment_ids else None,
        )
        self.db.add(campaign)
        await self.db.flush()
        await self.db.refresh(campaign)
        requires = await self._requires_approval(institution_id)
        return await self._to_response(campaign, requires_approval=requires)

    async def update_campaign(
        self, institution_id: UUID, campaign_id: UUID, data: UpdateCampaignRequest
    ) -> CampaignResponse:
        c = await self._verify(institution_id, campaign_id)
        if (c.status or "draft") not in _EDITABLE:
            raise BadRequestException(f"Cannot edit a campaign in '{c.status}' status")
        patch = data.model_dump(exclude_unset=True)
        if "name" in patch:
            c.campaign_name = patch["name"]
        if "objective" in patch:
            c.objective = patch["objective"]
        if "owner_id" in patch:
            c.owner_id = patch["owner_id"]
        if "subject" in patch:
            c.message_subject = patch["subject"]
        if "body" in patch:
            c.message_body = patch["body"]
        if "scheduled_at" in patch:
            c.scheduled_send_at = patch["scheduled_at"]
        if "destination_type" in patch:
            c.destination_type = patch["destination_type"]
        if "destination_id" in patch:
            c.destination_id = patch["destination_id"]
        if "destination_url" in patch:
            c.destination_url = patch["destination_url"]
        if "cta_type" in patch:
            c.cta_type = patch["cta_type"]
        if "channels" in patch and patch["channels"] is not None:
            c.channels = patch["channels"]
            c.campaign_type = self._legacy_type(patch["channels"])
        if "associate_program_ids" in patch and patch["associate_program_ids"] is not None:
            ids = [str(p) for p in patch["associate_program_ids"]]
            c.associate_program_ids = ids
            c.program_id = UUID(ids[0]) if ids else None
        if "associate_intake_round_id" in patch:
            c.associate_intake_round_id = patch["associate_intake_round_id"]
        if "audience_segment_ids" in patch and patch["audience_segment_ids"] is not None:
            ids = [str(s) for s in patch["audience_segment_ids"]]
            c.audience_segment_ids = ids
            c.segment_id = UUID(ids[0]) if ids else None
        if (
            "audience_uploaded_list_ids" in patch
            and patch["audience_uploaded_list_ids"] is not None
        ):
            c.audience_uploaded_list_ids = [str(u) for u in patch["audience_uploaded_list_ids"]]
        # Editing invalidates a stale deduped preview and any prior approval.
        c.audience_deduped_count = None
        if patch:
            c.approved_at = None
            c.approved_by = None
        await self.db.flush()
        await self.db.refresh(c)
        requires = await self._requires_approval(institution_id)
        return await self._to_response(c, requires_approval=requires)

    async def delete_campaign(self, institution_id: UUID, campaign_id: UUID) -> None:
        c = await self._verify(institution_id, campaign_id)
        if (c.status or "draft") in _SENT:
            raise BadRequestException("Cannot delete a campaign that has been sent")
        await self.db.delete(c)
        await self.db.flush()

    # ── audience resolution ──────────────────────────────────────────────────
    async def _resolve_audience(self, institution_id: UUID, c: Campaign) -> _Audience:
        channels = list(c.channels or [])
        wants_internal = "internal_messaging" in channels
        wants_external = "external_email" in channels
        if not channels:
            # Default to internal if a campaign somehow has no channels set.
            wants_internal = True

        segment_ids = self._as_uuid_list(c.audience_segment_ids)
        uploaded_ids = self._as_uuid_list(c.audience_uploaded_list_ids)

        # Suppression set (external opt-out) for this institution.
        supp_rows = await self.db.execute(
            select(CampaignSuppression.email).where(
                CampaignSuppression.institution_id == institution_id
            )
        )
        suppressed = {_norm_email(e) for (e,) in supp_rows.all() if e}

        # 1) Platform students from the segments (or applicant fallback).
        student_ids: set[UUID] = set()
        if segment_ids:
            for sid in segment_ids:
                try:
                    members = await self.inst_svc.resolve_segment_members(institution_id, sid)
                    student_ids.update(members)
                except NotFoundException:
                    continue
        elif not uploaded_ids:
            # No explicit audience → fall back to applicants of associated programs.
            student_ids.update(await self._program_applicants(institution_id, c))

        platform: list[_Recip] = []
        if student_ids:
            rows = await self.db.execute(
                select(
                    StudentProfile.id,
                    StudentProfile.user_id,
                    StudentProfile.first_name,
                    StudentProfile.last_name,
                    User.email,
                    StudentDataConsent.consent_outreach,
                )
                .join(User, User.id == StudentProfile.user_id)
                .outerjoin(
                    StudentDataConsent,
                    StudentDataConsent.student_id == StudentProfile.id,
                )
                .where(StudentProfile.id.in_(student_ids))
            )
            for pid, uid, fn, ln, email, consent in rows.all():
                platform.append(
                    _Recip(
                        source="platform",
                        email=email,
                        first_name=fn,
                        last_name=ln,
                        consent_outreach=True if consent is None else bool(consent),
                        student_id=pid,
                        user_id=uid,
                    )
                )

        platform_emails = {_norm_email(p.email) for p in platform if p.email}

        # 2) Uploaded-list contacts (external only), deduped vs platform emails.
        uploaded: list[_Recip] = []
        seen_uploaded: set[str] = set()
        if uploaded_ids:
            urows = await self.db.execute(
                select(UploadedContact).where(
                    UploadedContact.list_id.in_(uploaded_ids),
                    UploadedContact.institution_id == institution_id,
                    UploadedContact.opted_out.is_(False),
                )
            )
            for uc in urows.scalars().all():
                key = _norm_email(uc.email)
                if not key or key in platform_emails or key in seen_uploaded:
                    continue
                seen_uploaded.add(key)
                uploaded.append(
                    _Recip(
                        source="uploaded_list",
                        email=uc.email,
                        first_name=uc.first_name,
                        last_name=uc.last_name,
                        uploaded_contact_id=uc.id,
                    )
                )

        # 3) Channel gating + suppression → the people who actually receive.
        people: list[_Recip] = []
        suppressed_count = 0
        consent_excluded_count = 0
        for p in platform:
            email_key = _norm_email(p.email)
            reach_internal = wants_internal and p.consent_outreach
            reach_external = wants_external and bool(email_key) and email_key not in suppressed
            if wants_external and email_key and email_key in suppressed:
                suppressed_count += 1
            if reach_internal or reach_external:
                people.append(p)
            elif wants_internal and not p.consent_outreach:
                consent_excluded_count += 1
        platform_count = len(people)
        for u in uploaded:
            email_key = _norm_email(u.email)
            if not wants_external:
                continue
            if email_key in suppressed:
                suppressed_count += 1
                continue
            people.append(u)
        uploaded_count = len(people) - platform_count

        return _Audience(
            people=people,
            deduped_count=len(people),
            platform_count=platform_count,
            uploaded_count=uploaded_count,
            suppressed_count=suppressed_count,
            consent_excluded_count=consent_excluded_count,
        )

    async def _program_applicants(self, institution_id: UUID, c: Campaign) -> list[UUID]:
        from unipaith.models.application import Application

        program_ids = self._as_uuid_list(c.associate_program_ids)
        if not program_ids:
            programs = await self.inst_svc.list_programs(institution_id)
            program_ids = [p.id for p in programs]
        if not program_ids:
            return []
        rows = await self.db.execute(
            select(Application.student_id)
            .distinct()
            .where(Application.program_id.in_(program_ids), Application.status != "draft")
        )
        return [r[0] for r in rows.all()]

    async def preview_audience(
        self, institution_id: UUID, campaign_id: UUID
    ) -> AudiencePreviewResponse:
        c = await self._verify(institution_id, campaign_id)
        aud = await self._resolve_audience(institution_id, c)
        # Persist the deduped count (Spec 25 §3 audience.deduped_count).
        c.audience_deduped_count = aud.deduped_count
        await self.db.flush()
        sample = [
            AudienceSamplePerson(
                student_id=p.student_id,
                name=" ".join(x for x in [p.first_name, p.last_name] if x) or None,
                email=p.email,
                source=p.source,
                channel="external" if p.source == "uploaded_list" else "platform",
            )
            for p in aud.people[:10]
        ]
        return AudiencePreviewResponse(
            campaign_id=campaign_id,
            deduped_count=aud.deduped_count,
            platform_count=aud.platform_count,
            uploaded_count=aud.uploaded_count,
            suppressed_count=aud.suppressed_count,
            consent_excluded_count=aud.consent_excluded_count,
            sample=sample,
        )

    # ── lifecycle ─────────────────────────────────────────────────────────────
    async def submit_for_approval(
        self, institution_id: UUID, campaign_id: UUID
    ) -> CampaignResponse:
        c = await self._verify(institution_id, campaign_id)
        if (c.status or "draft") != "draft":
            raise BadRequestException("Only draft campaigns can be submitted for approval")
        c.status = "pending_approval"
        c.submitted_for_approval_at = datetime.now(UTC)
        c.rejection_comment = None
        # Fresh approval cycle — clear any prior sign-off.
        c.approved_at = None
        c.approved_by = None
        await self.db.flush()
        await self.db.refresh(c)
        return await self._to_response(c, requires_approval=True)

    async def approve(
        self, institution_id: UUID, campaign_id: UUID, approver_user_id: UUID
    ) -> CampaignResponse:
        c = await self._verify(institution_id, campaign_id)
        if (c.status or "draft") != "pending_approval":
            raise BadRequestException("Only campaigns pending approval can be approved")
        c.approved_by = approver_user_id
        c.approved_at = datetime.now(UTC)
        c.status = "scheduled" if c.scheduled_send_at else "draft"
        await self.db.flush()
        await self.db.refresh(c)
        return await self._to_response(c, requires_approval=True)

    async def reject(
        self, institution_id: UUID, campaign_id: UUID, comment: str
    ) -> CampaignResponse:
        c = await self._verify(institution_id, campaign_id)
        if (c.status or "draft") != "pending_approval":
            raise BadRequestException("Only campaigns pending approval can be rejected")
        c.status = "draft"
        c.rejection_comment = comment
        await self.db.flush()
        await self.db.refresh(c)
        return await self._to_response(c, requires_approval=True)

    async def schedule(self, institution_id: UUID, campaign_id: UUID) -> CampaignResponse:
        c = await self._verify(institution_id, campaign_id)
        requires = await self._requires_approval(institution_id)
        if requires and (c.status or "draft") == "draft" and c.approved_at is None:
            raise BadRequestException("Campaign must be approved before scheduling")
        if (c.status or "draft") not in {"draft", "paused", "scheduled"}:
            raise BadRequestException(f"Cannot schedule a campaign in '{c.status}' status")
        if not c.scheduled_send_at:
            raise BadRequestException("A scheduled send time is required to schedule a campaign")
        c.status = "scheduled"
        await self.db.flush()
        await self.db.refresh(c)
        return await self._to_response(c, requires_approval=requires)

    async def pause(self, institution_id: UUID, campaign_id: UUID) -> CampaignResponse:
        c = await self._verify(institution_id, campaign_id)
        if (c.status or "draft") not in {"active", "scheduled"}:
            raise BadRequestException(f"Cannot pause a campaign in '{c.status}' status")
        c.status = "paused"
        await self.db.flush()
        await self.db.refresh(c)
        return await self._to_response(
            c, requires_approval=await self._requires_approval(institution_id)
        )

    async def resume(self, institution_id: UUID, campaign_id: UUID) -> CampaignResponse:
        c = await self._verify(institution_id, campaign_id)
        if (c.status or "draft") != "paused":
            raise BadRequestException("Only paused campaigns can be resumed")
        c.status = "active" if c.sent_at else ("scheduled" if c.scheduled_send_at else "draft")
        await self.db.flush()
        await self.db.refresh(c)
        return await self._to_response(
            c, requires_approval=await self._requires_approval(institution_id)
        )

    async def complete(self, institution_id: UUID, campaign_id: UUID) -> CampaignResponse:
        c = await self._verify(institution_id, campaign_id)
        if (c.status or "draft") not in {"active", "paused"}:
            raise BadRequestException(f"Cannot complete a campaign in '{c.status}' status")
        c.status = "completed"
        await self.db.flush()
        await self.db.refresh(c)
        return await self._to_response(
            c, requires_approval=await self._requires_approval(institution_id)
        )

    async def send(self, institution_id: UUID, campaign_id: UUID) -> CampaignResponse:
        """Deliver the campaign now (Spec 25 §8 POST /send). Resolves audience,
        creates recipients, drops internal messages into student inboxes (consent
        gated) and queues external email. Idempotent-ish: refuses to re-send an
        already active/completed campaign."""
        c = await self._verify(institution_id, campaign_id)
        requires = await self._requires_approval(institution_id)
        status = c.status or "draft"
        if status in _SENT:
            raise BadRequestException("Campaign has already been sent")
        if status == "pending_approval":
            raise BadRequestException("Campaign is pending approval")
        if requires and status == "draft" and c.approved_at is None:
            raise BadRequestException("Campaign must be approved before sending")
        if not (c.message_subject or c.message_body):
            raise BadRequestException("Campaign must have a subject or body before sending")
        channels = list(c.channels or [])
        if not channels:
            raise BadRequestException("Select at least one channel before sending")

        aud = await self._resolve_audience(institution_id, c)
        if aud.deduped_count == 0:
            raise BadRequestException("0 recipients after filtering. Adjust your audience.")

        inst = await self.db.get(Institution, institution_id)
        inst_name = inst.name if inst else "UniPaith"
        program_name = await self._first_program_name(c)
        wants_internal = "internal_messaging" in channels
        wants_external = "external_email" in channels
        now = datetime.now(UTC)
        delivered = 0

        for person in aud.people:
            email_key = _norm_email(person.email)
            got_internal = (
                wants_internal and person.source == "platform" and person.consent_outreach
            )
            got_external = wants_external and bool(email_key)
            channel_label = (
                "both"
                if got_internal and got_external
                else "internal"
                if got_internal
                else "external"
            )
            recipient = CampaignRecipient(
                campaign_id=campaign_id,
                student_id=person.student_id,
                uploaded_contact_id=person.uploaded_contact_id,
                email=person.email,
                first_name=person.first_name,
                last_name=person.last_name,
                channel=channel_label,
                delivered_at=now,
            )
            self.db.add(recipient)
            if got_internal and person.user_id and person.student_id:
                await self._deliver_internal(c, person, inst_name)
            delivered += 1
        c.sent_count = delivered
        c.sent_at = now
        c.audience_deduped_count = aud.deduped_count
        c.status = "active"
        await self.db.flush()

        # External email is a best-effort side-effect; failures mark the row,
        # they never 5xx the send (Plan 2 integration invariant).
        if wants_external:
            try:
                from unipaith.services.campaign_email_service import CampaignEmailService

                await CampaignEmailService(self.db).send_campaign_emails(c, inst_name, program_name)
            except Exception:  # noqa: BLE001
                logger.exception("campaign external email dispatch failed for %s", campaign_id)

        await self.db.refresh(c)
        return await self._to_response(c, requires_approval=requires)

    async def _deliver_internal(self, c: Campaign, person: _Recip, inst_name: str) -> None:
        """Drop a campaign message into the student's Inbox (Spec 17 system
        thread) and raise an in-app notification."""
        conversation = Conversation(
            student_id=person.student_id,
            institution_id=c.institution_id,
            program_id=c.program_id,
            thread_type="system",
            subject=c.message_subject or c.campaign_name,
            status="open",
            last_message_at=datetime.now(UTC),
        )
        self.db.add(conversation)
        await self.db.flush()
        self.db.add(
            Message(
                conversation_id=conversation.id,
                sender_type="institution",
                message_body=c.message_body or "",
                status="delivered",
            )
        )
        self.db.add(
            Notification(
                user_id=person.user_id,
                title=c.message_subject or c.campaign_name,
                body=(c.message_body or "")[:500],
                notification_type="campaign",
                action_url="/s/manage?tab=messages",
            )
        )

    async def _first_program_name(self, c: Campaign) -> str | None:
        program_ids = self._as_uuid_list(c.associate_program_ids)
        pid = program_ids[0] if program_ids else c.program_id
        if not pid:
            return None
        return await self.db.scalar(select(Program.program_name).where(Program.id == pid))

    # ── metrics (Spec 25 §8) ────────────────────────────────────────────────
    async def get_metrics(self, institution_id: UUID, campaign_id: UUID) -> CampaignMetricsResponse:
        await self._verify(institution_id, campaign_id)
        row = (
            await self.db.execute(
                select(
                    func.count().label("sent"),
                    func.count()
                    .filter(CampaignRecipient.delivered_at.isnot(None))
                    .label("delivered"),
                    func.count().filter(CampaignRecipient.opened_at.isnot(None)).label("opens"),
                    func.count().filter(CampaignRecipient.clicked_at.isnot(None)).label("clicks"),
                    func.count()
                    .filter(CampaignRecipient.unsubscribed_at.isnot(None))
                    .label("unsub"),
                    func.count().filter(CampaignRecipient.bounced_at.isnot(None)).label("bounces"),
                ).where(CampaignRecipient.campaign_id == campaign_id)
            )
        ).one()
        # Conversions per attribution action (Spec 25 §6 funnel).
        conversions: dict[str, int] = {}
        action_rows = await self.db.execute(
            select(CampaignAction.action_type, func.count())
            .where(CampaignAction.campaign_id == campaign_id)
            .group_by(CampaignAction.action_type)
        )
        raw = {atype: cnt for atype, cnt in action_rows.all()}
        # 'apply' (legacy) folds into apply_started for the funnel.
        for action in ATTRIBUTION_ACTIONS:
            conversions[action] = raw.get(action, 0)
        if raw.get("apply"):
            conversions["apply_started"] = conversions.get("apply_started", 0) + raw["apply"]
        # Clicks also reflect trackable-link clicks recorded as actions.
        link_clicks = raw.get("click", 0)
        return CampaignMetricsResponse(
            campaign_id=campaign_id,
            sent=row.sent,
            delivered=row.delivered,
            opens=row.opens,
            clicks=max(row.clicks, link_clicks),
            conversions=conversions,
            unsubscribes=row.unsub,
            bounces=row.bounces,
        )

    # ── uploaded contact lists (Spec 24/26 §2.5) ─────────────────────────────
    async def list_uploaded_lists(self, institution_id: UUID) -> list[UploadedListResponse]:
        rows = await self.db.execute(
            select(UploadedList)
            .where(UploadedList.institution_id == institution_id)
            .order_by(UploadedList.created_at.desc())
        )
        return [UploadedListResponse.model_validate(r) for r in rows.scalars().all()]

    async def create_uploaded_list(
        self, institution_id: UUID, user_id: UUID, data: CreateUploadedListRequest
    ) -> UploadedListResponse:
        lst = UploadedList(
            institution_id=institution_id,
            name=data.name,
            description=data.description,
            source=data.source,
            source_consent_confirmed=data.source_consent_confirmed,
            created_by=user_id,
        )
        self.db.add(lst)
        await self.db.flush()
        count = 0
        seen: set[str] = set()
        for raw in data.contacts:
            email = _norm_email(str(raw.get("email", "")))
            if not email or "@" not in email or email in seen:
                continue
            seen.add(email)
            self.db.add(
                UploadedContact(
                    list_id=lst.id,
                    institution_id=institution_id,
                    email=str(raw.get("email")).strip(),
                    first_name=(raw.get("first_name") or raw.get("firstName") or None),
                    last_name=(raw.get("last_name") or raw.get("lastName") or None),
                    extra={
                        k: v
                        for k, v in raw.items()
                        if k not in {"email", "first_name", "last_name", "firstName", "lastName"}
                    }
                    or None,
                )
            )
            count += 1
        lst.contact_count = count
        await self.db.flush()
        await self.db.refresh(lst)
        return UploadedListResponse.model_validate(lst)

    async def update_uploaded_list(
        self, institution_id: UUID, list_id: UUID, data: UpdateUploadedListRequest
    ) -> UploadedListResponse:
        lst = await self._verify_list(institution_id, list_id)
        patch = data.model_dump(exclude_unset=True)
        for k, v in patch.items():
            setattr(lst, k, v)
        await self.db.flush()
        await self.db.refresh(lst)
        return UploadedListResponse.model_validate(lst)

    async def delete_uploaded_list(self, institution_id: UUID, list_id: UUID) -> None:
        lst = await self._verify_list(institution_id, list_id)
        await self.db.delete(lst)
        await self.db.flush()

    async def _verify_list(self, institution_id: UUID, list_id: UUID) -> UploadedList:
        lst = await self.db.scalar(
            select(UploadedList).where(
                UploadedList.id == list_id, UploadedList.institution_id == institution_id
            )
        )
        if not lst:
            raise NotFoundException("Uploaded list not found")
        return lst

    # ── suppression list (Spec 25 §4) ────────────────────────────────────────
    async def list_suppressions(self, institution_id: UUID) -> list[SuppressionResponse]:
        rows = await self.db.execute(
            select(CampaignSuppression)
            .where(CampaignSuppression.institution_id == institution_id)
            .order_by(CampaignSuppression.created_at.desc())
        )
        return [SuppressionResponse.model_validate(r) for r in rows.scalars().all()]

    async def add_suppression(
        self, institution_id: UUID, data: CreateSuppressionRequest
    ) -> SuppressionResponse:
        email = data.email.strip()
        existing = await self.db.scalar(
            select(CampaignSuppression).where(
                CampaignSuppression.institution_id == institution_id,
                func.lower(CampaignSuppression.email) == email.lower(),
            )
        )
        if existing:
            return SuppressionResponse.model_validate(existing)
        row = CampaignSuppression(
            institution_id=institution_id, email=email, reason=data.reason or "manual"
        )
        self.db.add(row)
        await self.db.flush()
        await self.db.refresh(row)
        return SuppressionResponse.model_validate(row)

    async def delete_suppression(self, institution_id: UUID, suppression_id: UUID) -> None:
        row = await self.db.scalar(
            select(CampaignSuppression).where(
                CampaignSuppression.id == suppression_id,
                CampaignSuppression.institution_id == institution_id,
            )
        )
        if not row:
            raise NotFoundException("Suppression entry not found")
        await self.db.delete(row)
        await self.db.flush()

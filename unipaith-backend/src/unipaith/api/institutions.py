from datetime import date, datetime, time
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.dependencies import require_institution_admin, require_student
from unipaith.models.user import User
from unipaith.schemas.application import (
    WaitlistBulkOfferRequest,
    WaitlistOfferNextRequest,
)
from unipaith.schemas.checklist import (
    BulkChecklistRequest,
    CreateProgramChecklistItemRequest,
    ProgramChecklistItemResponse,
    UpdateProgramChecklistItemRequest,
)
from unipaith.schemas.communication import (
    CreateTemplateRequest,
    SendFromTemplateRequest,
    SendResult,
    TemplatePreviewResponse,
    TemplateResponse,
    UpdateTemplateRequest,
)
from unipaith.schemas.institution import (
    AnalyticsResponse,
    AudiencePreviewResponse,
    CampaignAttributionDetail,
    CampaignLinkResponse,
    CampaignMetricsResponse,
    CampaignResponse,
    ConfirmDatasetReplaceRequest,
    ConfirmDatasetRequest,
    CreateCampaignLinkRequest,
    CreateCampaignRequest,
    CreateDatasetRequest,
    CreateInstitutionRequest,
    CreatePostRequest,
    CreateProgramRequest,
    CreatePromotionRequest,
    CreateSegmentRequest,
    CreateSuppressionRequest,
    CreateUploadedListRequest,
    DashboardSummaryResponse,
    DatasetMappingTemplateResponse,
    DatasetPreviewResponse,
    DatasetReplaceRequest,
    DatasetResponse,
    DatasetUploadResponse,
    DatasetVersionResponse,
    DraftCampaignCopyRequest,
    DraftCampaignCopyResponse,
    InquiryResponse,
    InstitutionResponse,
    NLBridgeRequest,
    NLBridgeResponse,
    PostMediaUploadResponse,
    PostResponse,
    ProgramResponse,
    PromotionResponse,
    RecordActionRequest,
    RecordEngagementRequest,
    RejectCampaignRequest,
    SaveMappingTemplateRequest,
    SegmentPreviewRequest,
    SegmentPreviewResponse,
    SegmentResponse,
    SignalDictionaryResponse,
    SubmitInquiryRequest,
    SuppressionResponse,
    UpdateCampaignRequest,
    UpdateDatasetRequest,
    UpdateInquiryRequest,
    UpdateInstitutionRequest,
    UpdatePostRequest,
    UpdateProgramRequest,
    UpdatePromotionRequest,
    UpdateSegmentRequest,
    UpdateUploadedListRequest,
    UploadedListResponse,
)
from unipaith.schemas.intake import (
    CreateIntakeRoundRequest,
    IntakeRoundResponse,
    UpdateIntakeRoundRequest,
)
from unipaith.schemas.international import EnglishPolicyRequest
from unipaith.services.campaign_service import CampaignService
from unipaith.services.institution_service import InstitutionService
from unipaith.services.international_service import InternationalService
from unipaith.services.segment_service import SegmentService
from unipaith.services.segment_signals import signal_dictionary_json

router = APIRouter(prefix="/institutions", tags=["institutions"])


class InstitutionAssistantChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    context_program_id: UUID | None = None


class InstitutionAssistantChatResponse(BaseModel):
    reply: str
    model: str
    provider: str = "openai"


def _svc(db: AsyncSession) -> InstitutionService:
    return InstitutionService(db)


def _csvc(db: AsyncSession) -> CampaignService:
    return CampaignService(db)


# --- Institution Profile ---


@router.get("/me", response_model=InstitutionResponse)
async def get_institution(
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    count = await svc.get_program_count(inst.id)
    resp = InstitutionResponse.model_validate(inst)
    resp.program_count = count
    return resp


@router.post("/me", response_model=InstitutionResponse, status_code=status.HTTP_201_CREATED)
async def create_institution(
    body: CreateInstitutionRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.create_institution(user.id, body)
    count = await svc.get_program_count(inst.id)
    resp = InstitutionResponse.model_validate(inst)
    resp.program_count = count
    return resp


@router.put("/me", response_model=InstitutionResponse)
async def update_institution(
    body: UpdateInstitutionRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.update_institution(user.id, body)
    count = await svc.get_program_count(inst.id)
    resp = InstitutionResponse.model_validate(inst)
    resp.program_count = count
    return resp


# --- Setup wizard (Spec 30) ---


class SetupStepsComplete(BaseModel):
    profile: bool
    program: bool
    data: bool
    team: bool


class SetupSkipped(BaseModel):
    data: bool = False
    team: bool = False


class SetupStateResponse(BaseModel):
    institution_id: UUID | None = None
    step: int | str  # 1..4 while in progress, "done" once finished
    steps_complete: SetupStepsComplete
    skipped: SetupSkipped
    first_program_id: str | None = None
    setup_complete: bool = False
    published_program_count: int = 0


class SetupStepPatch(BaseModel):
    step: int | None = Field(None, ge=1, le=4)
    skip_data: bool | None = None
    skip_team: bool | None = None
    mark_complete: dict[str, bool] | None = None


@router.get("/me/setup", response_model=SetupStateResponse)
async def get_setup_state(
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).get_setup_state(user.id)


@router.patch("/me/setup/step", response_model=SetupStateResponse)
async def patch_setup_step(
    body: SetupStepPatch,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).patch_setup_step(
        user.id,
        step=body.step,
        skip_data=body.skip_data,
        skip_team=body.skip_team,
        mark_complete=body.mark_complete,
    )


@router.post("/me/setup/complete", response_model=SetupStateResponse)
async def complete_setup(
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).complete_setup(user.id)


# --- Programs (institution admin) ---


@router.get("/me/programs", response_model=list[ProgramResponse])
async def list_programs(
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    return await svc.list_programs(inst.id)


@router.post(
    "/me/programs",
    response_model=ProgramResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_program(
    body: CreateProgramRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    return await svc.create_program(inst.id, body)


@router.get("/me/programs/{program_id}", response_model=ProgramResponse)
async def get_program(
    program_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    return await svc.get_program(inst.id, program_id)


@router.put("/me/programs/{program_id}", response_model=ProgramResponse)
async def update_program(
    program_id: UUID,
    body: UpdateProgramRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    return await svc.update_program(inst.id, program_id, body)


@router.post("/me/programs/{program_id}/publish", response_model=ProgramResponse)
async def publish_program(
    program_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    return await svc.publish_program(inst.id, program_id)


@router.post("/me/programs/{program_id}/unpublish", response_model=ProgramResponse)
async def unpublish_program(
    program_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    return await svc.unpublish_program(inst.id, program_id)


@router.delete("/me/programs/{program_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_program(
    program_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    await svc.delete_program(inst.id, program_id)


@router.patch("/me/programs/{program_id}/english-policy", response_model=ProgramResponse)
async def update_program_english_policy(
    program_id: UUID,
    body: EnglishPolicyRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Spec 38 §2.2 — accepted English tests + minimum scores + waiver rules.
    Reuses the program-update path (optimistic lock + version bump)."""
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    payload = body.model_dump()
    expected_version = payload.pop("expected_version", None)
    return await svc.update_program(
        inst.id,
        program_id,
        UpdateProgramRequest(english_policy=payload, expected_version=expected_version),
    )


# --- Spec 38 · International Admissions ---


@router.get("/me/international/applicants")
async def list_international_applicants(
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """The institution-wide international queue for /i/admissions?tab=international
    — every international applicant with a compact processing summary (§0)."""
    inst = await InstitutionService(db).get_institution(user.id)
    return await InternationalService(db).list_applicants(inst.id)


@router.get("/me/international/country-requirements")
async def list_country_requirements(
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Platform-default country-requirement packs merged with this institution's
    overrides (§2.3)."""
    inst = await InstitutionService(db).get_institution(user.id)
    return await InternationalService(db).list_country_requirements(inst.id)


# --- Target Segments ---


@router.get("/me/segments", response_model=list[SegmentResponse])
async def list_segments(
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    return await svc.list_segments(inst.id)


@router.post(
    "/me/segments",
    response_model=SegmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_segment(
    body: CreateSegmentRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    return await svc.create_segment(inst.id, body, created_by=user.id)


@router.put("/me/segments/{segment_id}", response_model=SegmentResponse)
async def update_segment(
    segment_id: UUID,
    body: UpdateSegmentRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    return await svc.update_segment(inst.id, segment_id, body)


@router.delete("/me/segments/{segment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_segment(
    segment_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    await svc.delete_segment(inst.id, segment_id)


# --- Dashboard & Analytics ---


@router.get("/me/dashboard", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    return await svc.get_dashboard_summary(inst.id)


@router.get("/me/analytics", response_model=AnalyticsResponse)
async def get_analytics(
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    return await svc.get_analytics(inst.id)


# --- Campaigns (Spec 25) ---


@router.get("/me/campaigns", response_model=list[CampaignResponse])
async def list_campaigns(
    campaign_status: str | None = Query(None, alias="status"),
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst = await _svc(db).get_institution(user.id)
    return await _csvc(db).list_campaigns(inst.id, status_filter=campaign_status)


@router.post(
    "/me/campaigns",
    response_model=CampaignResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_campaign(
    body: CreateCampaignRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst = await _svc(db).get_institution(user.id)
    return await _csvc(db).create_campaign(inst.id, body)


@router.get("/me/campaigns/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst = await _svc(db).get_institution(user.id)
    return await _csvc(db).get_campaign(inst.id, campaign_id)


@router.put("/me/campaigns/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: UUID,
    body: UpdateCampaignRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst = await _svc(db).get_institution(user.id)
    return await _csvc(db).update_campaign(inst.id, campaign_id, body)


@router.delete("/me/campaigns/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign(
    campaign_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst = await _svc(db).get_institution(user.id)
    await _csvc(db).delete_campaign(inst.id, campaign_id)


@router.get("/me/segments/{segment_id}/preview")
async def preview_segment_audience(
    segment_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Preview how many students match this segment's criteria (legacy count-only)."""
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    student_ids = await svc.resolve_segment_members(inst.id, segment_id)
    return {"segment_id": str(segment_id), "audience_count": len(student_ids)}


@router.get("/me/segments/signal-dictionary", response_model=SignalDictionaryResponse)
async def get_segment_signal_dictionary(
    user: User = Depends(require_institution_admin),
):
    """Spec 26 §2 — the signal vocabulary the rule builder + AI assist draw on."""
    return signal_dictionary_json()


@router.post("/me/segments/preview", response_model=SegmentPreviewResponse)
async def preview_segment_rules(
    body: SegmentPreviewRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Spec 26 §3 — preview an unsaved rule tree: count + 10-row sample +
    composition + fairness skew warning. Suppression is applied before the
    count."""
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    seg_svc = SegmentService(db)
    return await seg_svc.preview(
        inst.id,
        body.rules,
        uploaded_list_ids=body.uploaded_list_ids,
        program_id=body.program_id,
    )


@router.post("/me/segments/{segment_id}/preview", response_model=SegmentPreviewResponse)
async def preview_saved_segment(
    segment_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Spec 26 §3 — preview a saved segment and cache its audience count."""
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    segment = await svc.get_segment(inst.id, segment_id)
    seg_svc = SegmentService(db)
    result = await seg_svc.preview(
        inst.id,
        segment.rules if segment.rules else segment.criteria,
        uploaded_list_ids=list(segment.uploaded_list_ids or []),
        program_id=segment.program_id,
    )
    # cache the count on the segment (Spec 26 §7 preview_audience_count)
    await svc.cache_segment_preview(inst.id, segment_id, result["audience_count"])
    return result


@router.post("/me/segments/nl-bridge", response_model=NLBridgeResponse)
async def segment_nl_bridge(
    body: NLBridgeRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Spec 26 §6 / 45 §17 — convert a natural-language audience description to
    structured rules (Sonnet, keyword-parser fallback)."""
    svc = _svc(db)
    await svc.get_institution(user.id)  # ensure caller owns an institution
    seg_svc = SegmentService(db)
    return await seg_svc.nl_bridge(body.text)


@router.post(
    "/me/campaigns/{campaign_id}/preview-audience",
    response_model=AudiencePreviewResponse,
)
async def preview_campaign_audience(
    campaign_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Spec 25 §8 — deduped recipient count + 10-row sample after suppression
    and consent filtering."""
    inst = await _svc(db).get_institution(user.id)
    return await _csvc(db).preview_audience(inst.id, campaign_id)


@router.get("/me/campaigns/{campaign_id}/audience")
async def preview_campaign_audience_count(
    campaign_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Back-compat alias returning just the deduped count."""
    inst = await _svc(db).get_institution(user.id)
    preview = await _csvc(db).preview_audience(inst.id, campaign_id)
    return {"campaign_id": str(campaign_id), "audience_count": preview.deduped_count}


@router.post("/me/campaigns/{campaign_id}/send", response_model=CampaignResponse)
async def send_campaign(
    campaign_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst = await _svc(db).get_institution(user.id)
    return await _csvc(db).send(inst.id, campaign_id)


@router.post("/me/campaigns/{campaign_id}/schedule", response_model=CampaignResponse)
async def schedule_campaign(
    campaign_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst = await _svc(db).get_institution(user.id)
    return await _csvc(db).schedule(inst.id, campaign_id)


@router.post("/me/campaigns/{campaign_id}/pause", response_model=CampaignResponse)
async def pause_campaign(
    campaign_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst = await _svc(db).get_institution(user.id)
    return await _csvc(db).pause(inst.id, campaign_id)


@router.post("/me/campaigns/{campaign_id}/resume", response_model=CampaignResponse)
async def resume_campaign(
    campaign_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst = await _svc(db).get_institution(user.id)
    return await _csvc(db).resume(inst.id, campaign_id)


@router.post("/me/campaigns/{campaign_id}/complete", response_model=CampaignResponse)
async def complete_campaign(
    campaign_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst = await _svc(db).get_institution(user.id)
    return await _csvc(db).complete(inst.id, campaign_id)


# --- Campaign approval (Spec 25 §7) ---


@router.post("/me/campaigns/{campaign_id}/submit-approval", response_model=CampaignResponse)
async def submit_campaign_for_approval(
    campaign_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst = await _svc(db).get_institution(user.id)
    return await _csvc(db).submit_for_approval(inst.id, campaign_id)


@router.post("/me/campaigns/{campaign_id}/approve", response_model=CampaignResponse)
async def approve_campaign(
    campaign_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst = await _svc(db).get_institution(user.id)
    return await _csvc(db).approve(inst.id, campaign_id, user.id)


@router.post("/me/campaigns/{campaign_id}/reject", response_model=CampaignResponse)
async def reject_campaign(
    campaign_id: UUID,
    body: RejectCampaignRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst = await _svc(db).get_institution(user.id)
    return await _csvc(db).reject(inst.id, campaign_id, body.comment)


@router.get(
    "/me/campaigns/{campaign_id}/metrics",
    response_model=CampaignMetricsResponse,
)
async def get_campaign_metrics(
    campaign_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst = await _svc(db).get_institution(user.id)
    return await _csvc(db).get_metrics(inst.id, campaign_id)


# --- Uploaded contact lists (Spec 24/26 §2.5) ---


@router.get("/me/uploaded-lists", response_model=list[UploadedListResponse])
async def list_uploaded_lists(
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst = await _svc(db).get_institution(user.id)
    return await _csvc(db).list_uploaded_lists(inst.id)


@router.post(
    "/me/uploaded-lists",
    response_model=UploadedListResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_uploaded_list(
    body: CreateUploadedListRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst = await _svc(db).get_institution(user.id)
    return await _csvc(db).create_uploaded_list(inst.id, user.id, body)


@router.put("/me/uploaded-lists/{list_id}", response_model=UploadedListResponse)
async def update_uploaded_list(
    list_id: UUID,
    body: UpdateUploadedListRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst = await _svc(db).get_institution(user.id)
    return await _csvc(db).update_uploaded_list(inst.id, list_id, body)


@router.delete("/me/uploaded-lists/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_uploaded_list(
    list_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst = await _svc(db).get_institution(user.id)
    await _csvc(db).delete_uploaded_list(inst.id, list_id)


# --- Suppression list (Spec 25 §4 / 46) ---


@router.get("/me/suppressions", response_model=list[SuppressionResponse])
async def list_suppressions(
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst = await _svc(db).get_institution(user.id)
    return await _csvc(db).list_suppressions(inst.id)


@router.post(
    "/me/suppressions",
    response_model=SuppressionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_suppression(
    body: CreateSuppressionRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst = await _svc(db).get_institution(user.id)
    return await _csvc(db).add_suppression(inst.id, body)


@router.delete("/me/suppressions/{suppression_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_suppression(
    suppression_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst = await _svc(db).get_institution(user.id)
    await _csvc(db).delete_suppression(inst.id, suppression_id)


# --- AI: CampaignAudienceCopySuggester (Spec 45 §16) ---


@router.post("/me/campaigns/draft-copy", response_model=DraftCampaignCopyResponse)
async def draft_campaign_copy(
    body: DraftCampaignCopyRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Spec 25 §10 "Draft with AI" — subject + body draft for the campaign editor.
    Falls back to an objective-keyed template stub when the LLM path is disabled
    or fails (never 5xxes)."""
    inst = await _svc(db).get_institution(user.id)
    from unipaith.services.ai_config_service import AIConfigService
    from unipaith.services.ai_surface_service import AISurfaceService
    from unipaith.services.campaign_copy_service import draft_campaign_copy as _draft

    cfgsvc = AIConfigService(db)
    if not await cfgsvc.is_surface_enabled(inst.id, "campaign_copy"):
        return DraftCampaignCopyResponse(subject="", body="", source="fallback", disabled=True)
    result = await _draft(db, inst, body)
    # Spec 37 §3 — record the AI-generated campaign copy; token lets the save
    # action capture the human edit diff.
    no_training = await cfgsvc.is_no_training(inst.id)
    token = await AISurfaceService(db).record_generated(
        institution_id=inst.id,
        actor_user_id=user.id,
        surface="campaign_copy",
        agent="campaign_copy",
        ai_output={"subject": result.subject, "body": result.body},
        model=result.source,
        no_training=no_training,
    )
    result.draft_token = str(token)
    return result


# --- Campaign Links & Attribution ---


@router.post(
    "/me/campaigns/{campaign_id}/links",
    response_model=CampaignLinkResponse,
)
async def create_campaign_link(
    campaign_id: UUID,
    body: CreateCampaignLinkRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    return await svc.create_campaign_link(inst.id, campaign_id, body)


@router.get(
    "/me/campaigns/{campaign_id}/links",
    response_model=list[CampaignLinkResponse],
)
async def get_campaign_links(
    campaign_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    return await svc.get_campaign_links(inst.id, campaign_id)


@router.delete(
    "/me/campaigns/{campaign_id}/links/{link_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_campaign_link(
    campaign_id: UUID,
    link_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    await svc.delete_campaign_link(inst.id, campaign_id, link_id)


@router.get(
    "/me/campaigns/{campaign_id}/attribution",
    response_model=CampaignAttributionDetail,
)
async def get_campaign_attribution(
    campaign_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    return await svc.get_campaign_attribution(inst.id, campaign_id)


@router.post("/me/assistant/chat", response_model=InstitutionAssistantChatResponse)
async def institution_assistant_chat(
    body: InstitutionAssistantChatRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """OpenAI assistant for institution admins."""
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    programs = await svc.list_programs(inst.id)
    context_program = None
    if body.context_program_id:
        for program in programs:
            if program.id == body.context_program_id:
                context_program = program
                break

    (
        f"Institution: {inst.name}\n"
        f"Country: {inst.country}\n"
        f"Program count: {len(programs)}\n"
        f"Context program: {context_program.program_name if context_program else 'N/A'}\n\n"
        f"User message:\n{body.message}"
    )

    return InstitutionAssistantChatResponse(
        reply="The AI assistant is currently being rebuilt. Please check back soon.",
        model="unavailable",
    )


# --- Datasets ---


@router.post("/me/datasets/upload", response_model=DatasetUploadResponse)
async def request_dataset_upload(
    body: CreateDatasetRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    return await svc.request_dataset_upload(inst.id, user.id, body)


def _dataset_response(dataset, download_url: str | None = None) -> DatasetResponse:
    from unipaith.services.dataset_upload_service import dataset_used_by

    resp = DatasetResponse.model_validate(dataset)
    resp.download_url = download_url
    resp.used_by = dataset_used_by(dataset.usage_scope)
    if dataset.status == "pending":
        resp.status = "uploaded"
    elif dataset.status == "active":
        resp.status = "processed"
    return resp


@router.post("/me/datasets/{dataset_id}/confirm", response_model=DatasetResponse)
async def confirm_dataset_upload(
    dataset_id: UUID,
    body: ConfirmDatasetRequest | None = None,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    from fastapi import HTTPException

    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    req = body or ConfirmDatasetRequest()
    dataset, report = await svc.confirm_dataset_upload(
        inst.id,
        dataset_id,
        user.id,
        column_mapping=req.column_mapping,
        skip_invalid_rows=req.skip_invalid_rows,
        save_template=req.save_template,
        template_name=req.template_name,
    )
    if report.get("error_count", 0) > 0 and not req.skip_invalid_rows:
        raise HTTPException(
            status_code=422,
            detail={"message": "Validation failed", "validation_report": report},
        )
    return _dataset_response(dataset)


@router.get("/me/datasets", response_model=list[DatasetResponse])
async def list_datasets(
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    datasets = await svc.list_datasets(inst.id)
    return [_dataset_response(d) for d in datasets]


@router.get("/me/datasets/mapping-templates", response_model=list[DatasetMappingTemplateResponse])
async def list_dataset_mapping_templates(
    dataset_type: str | None = None,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    from unipaith.services.dataset_upload_service import DatasetUploadService

    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    templates = await DatasetUploadService(db).list_mapping_templates(inst.id, dataset_type)
    return [DatasetMappingTemplateResponse.model_validate(t) for t in templates]


@router.post("/me/datasets/mapping-templates", response_model=DatasetMappingTemplateResponse)
async def save_dataset_mapping_template(
    body: SaveMappingTemplateRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    from unipaith.services.dataset_upload_service import DatasetUploadService

    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    tpl = await DatasetUploadService(db).save_mapping_template(
        inst.id,
        template_name=body.template_name,
        dataset_type=body.dataset_type,
        column_mapping=body.column_mapping,
    )
    return DatasetMappingTemplateResponse.model_validate(tpl)


@router.get("/me/datasets/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    return await svc.get_dataset(inst.id, dataset_id)


@router.get("/me/datasets/{dataset_id}/preview", response_model=DatasetPreviewResponse)
async def get_dataset_preview(
    dataset_id: UUID,
    limit: int = 100,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    return await svc.get_dataset_preview(inst.id, dataset_id, limit=min(limit, 100))


@router.post("/me/datasets/{dataset_id}/replace/upload", response_model=DatasetUploadResponse)
async def request_dataset_replace_upload(
    dataset_id: UUID,
    body: DatasetReplaceRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    return await svc.request_dataset_replace_upload(inst.id, dataset_id, body)


@router.post("/me/datasets/{dataset_id}/replace", response_model=DatasetResponse)
async def confirm_dataset_replace(
    dataset_id: UUID,
    body: ConfirmDatasetReplaceRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    from fastapi import HTTPException

    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    dataset, report = await svc.confirm_dataset_replace(
        inst.id,
        dataset_id,
        user.id,
        staging_s3_key=body.staging_s3_key,
        file_name=body.file_name,
        update_mode=body.update_mode,
        column_mapping=body.column_mapping,
        skip_invalid_rows=body.skip_invalid_rows,
    )
    if report.get("error_count", 0) > 0 and not body.skip_invalid_rows:
        raise HTTPException(
            status_code=422,
            detail={"message": "Validation failed", "validation_report": report},
        )
    return _dataset_response(dataset)


@router.post("/me/datasets/{dataset_id}/append", response_model=DatasetResponse)
async def confirm_dataset_append(
    dataset_id: UUID,
    body: ConfirmDatasetReplaceRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    from fastapi import HTTPException

    body = body.model_copy(update={"update_mode": "append"})
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    dataset, report = await svc.confirm_dataset_replace(
        inst.id,
        dataset_id,
        user.id,
        staging_s3_key=body.staging_s3_key,
        file_name=body.file_name,
        update_mode="append",
        column_mapping=body.column_mapping,
        skip_invalid_rows=body.skip_invalid_rows,
    )
    if report.get("error_count", 0) > 0 and not body.skip_invalid_rows:
        raise HTTPException(
            status_code=422,
            detail={"message": "Validation failed", "validation_report": report},
        )
    return _dataset_response(dataset)


@router.get("/me/datasets/{dataset_id}/versions", response_model=list[DatasetVersionResponse])
async def list_dataset_versions(
    dataset_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    from unipaith.services.dataset_upload_service import DatasetUploadService

    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    versions = await DatasetUploadService(db).list_versions(inst.id, dataset_id)
    return [DatasetVersionResponse.model_validate(v) for v in versions]


@router.post(
    "/me/datasets/{dataset_id}/versions/{version_id}/rollback", response_model=DatasetResponse
)
async def rollback_dataset_version(
    dataset_id: UUID,
    version_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    from unipaith.services.dataset_upload_service import DatasetUploadService

    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    dataset = await DatasetUploadService(db).rollback_version(
        inst.id, dataset_id, version_id, user.id
    )
    return _dataset_response(dataset)


@router.put("/me/datasets/{dataset_id}", response_model=DatasetResponse)
async def update_dataset(
    dataset_id: UUID,
    body: UpdateDatasetRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    dataset = await svc.update_dataset(inst.id, dataset_id, body)
    return _dataset_response(dataset)


@router.delete("/me/datasets/{dataset_id}", status_code=204)
async def delete_dataset(
    dataset_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    await svc.delete_dataset(inst.id, dataset_id, user.id)


# --- Posts ---


@router.get("/me/posts", response_model=list[PostResponse])
async def list_posts(
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    return await svc.list_posts(inst.id)


@router.post(
    "/me/posts",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_post(
    body: CreatePostRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    return await svc.create_post(inst.id, user.id, body)


@router.put("/me/posts/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: UUID,
    body: UpdatePostRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    return await svc.update_post(inst.id, post_id, body)


@router.delete("/me/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    await svc.delete_post(inst.id, post_id)


@router.post("/me/posts/{post_id}/publish", response_model=PostResponse)
async def publish_post(
    post_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    return await svc.publish_post(inst.id, post_id)


@router.post("/me/posts/{post_id}/pin", response_model=PostResponse)
async def pin_post(
    post_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    return await svc.pin_post(inst.id, post_id)


class MediaUploadRequest(BaseModel):
    content_type: str = "image/jpeg"


@router.post("/me/media/upload", response_model=PostMediaUploadResponse)
async def request_institution_media_upload(
    body: MediaUploadRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Spec 22 §9 — profile/gallery media presign (alias of post media key layout)."""
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    return await svc.request_post_media_upload(inst.id, body.content_type)


@router.post("/me/posts/media/upload", response_model=PostMediaUploadResponse)
async def request_post_media_upload(
    body: MediaUploadRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    return await svc.request_post_media_upload(inst.id, body.content_type)


@router.get("/me/posts/templates", response_model=list[PostResponse])
async def list_post_templates(
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    return await svc.list_post_templates(inst.id)


# --- Public Profile ---


@router.get("/search")
async def search_institutions(
    q: str | None = Query(None),
    country: str | None = Query(None),
    inst_type: str | None = Query(None, alias="type"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Public — search/browse institutions."""
    import math

    from sqlalchemy import func, select

    from unipaith.models.institution import Institution, Program

    stmt = select(Institution)

    if q:
        escaped_q = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        stmt = stmt.where(Institution.name.ilike(f"%{escaped_q}%"))
    if country:
        stmt = stmt.where(Institution.country == country)
    if inst_type:
        stmt = stmt.where(Institution.type == inst_type)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = stmt.order_by(Institution.name).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    institutions = result.scalars().all()

    # Get program counts and school counts
    from unipaith.models.institution import School as SchoolModel

    inst_ids = [i.id for i in institutions]
    if inst_ids:
        pc_result = await db.execute(
            select(
                Program.institution_id,
                func.count().label("cnt"),
            )
            .where(
                Program.institution_id.in_(inst_ids),
                Program.is_published.is_(True),
            )
            .group_by(Program.institution_id)
        )
        pc_map = {r[0]: r[1] for r in pc_result.all()}

        sc_result = await db.execute(
            select(
                SchoolModel.institution_id,
                func.count().label("cnt"),
            )
            .where(SchoolModel.institution_id.in_(inst_ids))
            .group_by(SchoolModel.institution_id)
        )
        sc_map = {r[0]: r[1] for r in sc_result.all()}

        # Aggregate the distinct set of program names, degree types, and
        # delivery formats per institution so the frontend can power
        # Subjects / Degree level / Delivery format filters without fetching
        # every program. Also collect intake_rounds + highlights for the
        # application-open + honors/study-abroad flags.
        prog_result = await db.execute(
            select(
                Program.institution_id,
                Program.program_name,
                Program.degree_type,
                Program.delivery_format,
                Program.application_deadline,
                Program.intake_rounds,
                Program.highlights,
            ).where(
                Program.institution_id.in_(inst_ids),
                Program.is_published.is_(True),
            )
        )
        subjects_map: dict = {}
        degree_map: dict = {}
        delivery_map: dict = {}
        next_deadline_map: dict = {}
        program_highlights_map: dict = {}

        today = date.today()

        def _collect_program_deadlines(dl, ir):
            """Yield date objects for every known future deadline for a program."""
            out = []
            if dl:
                try:
                    out.append(dl if isinstance(dl, date) else date.fromisoformat(str(dl)))
                except Exception:
                    pass
            if isinstance(ir, dict):
                # intake_rounds is usually { fall_2026: { regular_decision: { deadline }}}
                for term_val in ir.values():
                    if not isinstance(term_val, dict):
                        continue
                    for round_key in (
                        "regular_decision",
                        "early_decision_1",
                        "early_decision_2",
                        "early_action",
                        "rolling",
                    ):
                        r = term_val.get(round_key)
                        if isinstance(r, dict) and r.get("deadline"):
                            try:
                                out.append(date.fromisoformat(str(r["deadline"])))
                            except Exception:
                                pass
            return out

        for inst_id, name, deg, fmt, dl, ir, highlights in prog_result.all():
            if name:
                subjects_map.setdefault(inst_id, set()).add(name)
            if deg:
                degree_map.setdefault(inst_id, set()).add(deg)
            if fmt:
                delivery_map.setdefault(inst_id, set()).add(fmt)
            if isinstance(highlights, list):
                program_highlights_map.setdefault(inst_id, []).extend(highlights)
            # Track the earliest future deadline across all of the institution's programs
            for d in _collect_program_deadlines(dl, ir):
                if d >= today:
                    cur = next_deadline_map.get(inst_id)
                    if cur is None or d < cur:
                        next_deadline_map[inst_id] = d

        # Convert sets to sorted lists for stable UI
        subjects_map = {k: sorted(v) for k, v in subjects_map.items()}
        degree_map = {k: sorted(v) for k, v in degree_map.items()}
        delivery_map = {k: sorted(v) for k, v in delivery_map.items()}
    else:
        pc_map = {}
        sc_map = {}
        subjects_map = {}
        degree_map = {}
        delivery_map = {}
        next_deadline_map = {}
        program_highlights_map = {}

    items = []
    import re

    for inst in institutions:
        rd = inst.ranking_data or {}
        intl = inst.international_info or {}

        # "has_honors" / "has_study_abroad" are True when either the institution's
        # description mentions it or any of its published programs' highlights do.
        search_blob = (
            (inst.description_text or "")
            + " "
            + (inst.campus_description or "")
            + " "
            + " ".join(program_highlights_map.get(inst.id, []) or [])
        )
        has_honors = bool(re.search(r"\bhonors?\b|\bthesis\b", search_blob, re.IGNORECASE))
        study_abroad_pat = r"\bstudy abroad\b|\bexchange program\b|\bglobal campuses?\b"
        has_study_abroad = bool(re.search(study_abroad_pat, search_blob, re.IGNORECASE))

        # Tuition: in-state and out-of-state are usually the same for privates.
        # Prefer out-of-state as the universal published price.
        tuition_annual = rd.get("tuition_out_of_state") or rd.get("tuition_in_state")

        next_dl = next_deadline_map.get(inst.id)

        items.append(
            {
                "id": str(inst.id),
                "name": inst.name,
                "country": inst.country,
                "city": inst.city,
                "type": inst.type,
                # Structured classification hints so the explore-card eyebrow
                # ("Private/Public Research") works without relying on the
                # description prose. ownership_type lives in ranking_data;
                # school_outcomes.ownership is the federal-data fallback.
                "ownership": (
                    rd.get("ownership_type") or (inst.school_outcomes or {}).get("ownership")
                ),
                "carnegie_classification": (
                    rd.get("carnegie_classification")
                    or (inst.school_outcomes or {}).get("carnegie_classification")
                ),
                "campus_setting": inst.campus_setting,
                "student_body_size": inst.student_body_size,
                # Geo for the "near me" distance sort (from school_outcomes.location).
                "latitude": ((inst.school_outcomes or {}).get("location") or {}).get("lat"),
                "longitude": ((inst.school_outcomes or {}).get("location") or {}).get("lng"),
                "logo_url": inst.logo_url,
                "image_url": ((inst.media_gallery or [None])[0] if inst.media_gallery else None),
                "program_count": pc_map.get(inst.id, 0),
                "school_count": sc_map.get(inst.id, 0),
                "description_text": ((inst.description_text or "")[:200]),
                "acceptance_rate": rd.get("acceptance_rate"),
                "sat_avg": rd.get("sat_avg"),
                "us_news_rank": rd.get("us_news_2025"),
                "median_earnings": rd.get("earnings_10yr_median"),
                "graduation_rate": rd.get("graduation_rate"),
                "region": inst.region,
                "subjects_offered": subjects_map.get(inst.id, []),
                "top_industries": (inst.school_outcomes or {}).get("top_employer_industries", []),
                # New filter fields:
                "degree_types_offered": degree_map.get(inst.id, []),
                "delivery_formats_offered": delivery_map.get(inst.id, []),
                "next_deadline": next_dl.isoformat() if next_dl else None,
                "supports_international": bool(intl.get("supported_visas")),
                "has_study_abroad": has_study_abroad,
                "has_honors": has_honors,
                "tuition_annual": tuition_annual,
            }
        )

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, math.ceil(total / page_size)),
    }


@router.get("/{institution_id}", response_model=InstitutionResponse)
async def get_public_institution(
    institution_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Public endpoint — no auth required. Returns institution profile."""
    svc = _svc(db)
    inst = await svc.get_public_institution(institution_id)
    count = await svc.get_program_count(inst.id)
    resp = InstitutionResponse.model_validate(inst)
    resp.program_count = count
    return resp


@router.get("/{institution_id}/schools")
async def get_institution_schools(
    institution_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Public — returns schools within an institution, each with program count and names."""
    from sqlalchemy import func, select

    from unipaith.models.institution import Program, School

    result = await db.execute(
        select(School)
        .where(School.institution_id == institution_id)
        .order_by(School.sort_order, School.name)
    )
    schools = result.scalars().all()

    if not schools:
        return []

    school_ids = [s.id for s in schools]
    pc_result = await db.execute(
        select(
            Program.school_id,
            func.count().label("cnt"),
            func.array_agg(Program.program_name).label("names"),
        )
        .where(Program.school_id.in_(school_ids), Program.is_published.is_(True))
        .group_by(Program.school_id)
    )
    pc_map = {r[0]: (r[1], r[2]) for r in pc_result.all()}

    return [
        {
            "id": str(s.id),
            "institution_id": str(s.institution_id),
            "name": s.name,
            "description_text": s.description_text,
            "media_urls": s.media_urls,
            "logo_url": s.logo_url,
            "website_url": s.website_url,
            "content_sources": s.content_sources,
            "about_detail": s.about_detail,
            "program_count": pc_map.get(s.id, (0, []))[0],
            "program_names": sorted(pc_map.get(s.id, (0, []))[1] or []),
        }
        for s in schools
    ]


@router.get("/{institution_id}/schools/{school_id}/programs")
async def get_school_programs(
    institution_id: UUID,
    school_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Public — returns programs within a specific school."""

    from sqlalchemy import select

    from unipaith.models.institution import Institution, Program

    result = await db.execute(
        select(Program, Institution)
        .join(Institution, Program.institution_id == Institution.id)
        .where(
            Program.school_id == school_id,
            Program.institution_id == institution_id,
            Program.is_published.is_(True),
        )
        .order_by(Program.program_name)
    )
    rows = result.all()

    def _outcomes_int(prog: Program, key: str) -> int | None:
        v = (prog.outcomes_data or {}).get(key)
        return int(v) if v is not None else None

    def _outcomes_float(prog: Program, key: str) -> float | None:
        v = (prog.outcomes_data or {}).get(key)
        return float(v) if v is not None else None

    return [
        {
            "id": str(prog.id),
            "institution_id": str(prog.institution_id),
            "school_id": str(prog.school_id) if prog.school_id else None,
            "program_name": prog.program_name,
            "degree_type": prog.degree_type,
            "department": prog.department,
            "tuition": prog.tuition or (inst.ranking_data or {}).get("tuition_out_of_state"),
            "duration_months": prog.duration_months,
            "delivery_format": prog.delivery_format,
            "acceptance_rate": (
                float(prog.acceptance_rate)
                if prog.acceptance_rate is not None
                else (inst.ranking_data or {}).get("acceptance_rate")
            ),
            "application_deadline": (
                str(prog.application_deadline) if prog.application_deadline else None
            ),
            "institution_name": inst.name,
            "institution_country": inst.country,
            "institution_city": inst.city,
            "median_salary": (
                _outcomes_int(prog, "median_salary")
                or (inst.ranking_data or {}).get("earnings_10yr_median")
            ),
            "employment_rate": (
                _outcomes_float(prog, "employment_rate")
                or (inst.ranking_data or {}).get("graduation_rate")
            ),
            "description_text": prog.description_text,
            "media_urls": prog.media_urls,
            "highlights": prog.highlights,
        }
        for prog, inst in rows
    ]


@router.get("/posts/feed", response_model=list[PostResponse])
async def get_posts_feed(
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Public endpoint — returns latest published posts across all institutions."""
    from sqlalchemy import select

    from unipaith.models.institution import Institution, InstitutionPost

    result = await db.execute(
        select(InstitutionPost)
        .where(InstitutionPost.status == "published")
        .order_by(InstitutionPost.created_at.desc())
        .limit(limit)
    )
    posts = result.scalars().all()
    # Eagerly load institution names
    inst_ids = {p.institution_id for p in posts}
    if inst_ids:
        inst_result = await db.execute(select(Institution).where(Institution.id.in_(inst_ids)))
        inst_map = {i.id: i.name for i in inst_result.scalars().all()}
    else:
        inst_map = {}
    out = []
    for p in posts:
        d = PostResponse.model_validate(p)
        d.institution_name = inst_map.get(p.institution_id, "")  # type: ignore[attr-defined]
        out.append(d)
    return out


@router.get("/{institution_id}/posts", response_model=list[PostResponse])
async def get_public_posts(
    institution_id: UUID,
    school_id: UUID | None = Query(None),
    program_id: UUID | None = Query(None),
    institution_scope: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    """Public endpoint — returns published posts for an institution, optionally
    scoped to a school or program (channel-sourced Updates). institution_scope
    restricts to institution-wide items (no school/program copies)."""
    svc = _svc(db)
    return await svc.get_public_posts(
        institution_id,
        school_id=school_id,
        program_id=program_id,
        institution_scope=institution_scope,
    )


# --- Campaign Action Tracking (student-facing) ---


@router.post("/track/action", status_code=status.HTTP_204_NO_CONTENT)
async def record_campaign_action(
    body: RecordActionRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Record a downstream action attributed to a campaign (student auth)."""
    from sqlalchemy import select as sel

    from unipaith.models.student import StudentProfile

    r = await db.execute(sel(StudentProfile.id).where(StudentProfile.user_id == user.id))
    student_id = r.scalar_one_or_none()
    if not student_id:
        return

    svc = _svc(db)
    await svc.record_campaign_action(
        body.campaign_id,
        student_id,
        body.action_type,
        body.target_id,
        link_id=body.link_id,
    )


@router.post("/track/engagement", status_code=status.HTTP_204_NO_CONTENT)
async def record_engagement(
    body: RecordEngagementRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Spec 27 §5 — record a per-object engagement event (post/event/promotion).

    Spec 28 — resolve the acting student so the attribution funnel can attribute
    the engagement per-student / per-segment.
    """
    from sqlalchemy import select as sel

    from unipaith.models.student import StudentProfile

    r = await db.execute(sel(StudentProfile.id).where(StudentProfile.user_id == user.id))
    student_id = r.scalar_one_or_none()

    svc = _svc(db)
    await svc.record_engagement(body.object_type, body.object_id, body.action, student_id)


# --- Inquiries ---


@router.post("/inquiries", response_model=InquiryResponse)
async def submit_inquiry(
    body: SubmitInquiryRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Student submits a request-info inquiry to an institution."""
    from sqlalchemy import select as sel

    from unipaith.models.student import StudentProfile

    r = await db.execute(sel(StudentProfile).where(StudentProfile.user_id == user.id))
    profile = r.scalar_one_or_none()

    student_name = user.email
    if profile:
        parts = [profile.first_name or "", profile.last_name or ""]
        full = " ".join(p for p in parts if p).strip()
        if full:
            student_name = full

    svc = _svc(db)
    return await svc.submit_inquiry(
        data=body,
        student_id=profile.id if profile else None,
        student_name=student_name,
        student_email=user.email,
    )


@router.get("/me/inquiries", response_model=list[InquiryResponse])
async def list_inquiries(
    status: str | None = Query(None),
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    return await svc.list_inquiries(inst.id, status)


@router.put(
    "/me/inquiries/{inquiry_id}",
    response_model=InquiryResponse,
)
async def update_inquiry(
    inquiry_id: UUID,
    body: UpdateInquiryRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    return await svc.update_inquiry(inst.id, inquiry_id, body)


# --- Program Checklist ---


@router.get(
    "/me/programs/{program_id}/checklist",
    response_model=list[ProgramChecklistItemResponse],
)
async def list_checklist_items(
    program_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select

    from unipaith.models.institution import ProgramChecklistItem

    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    await svc.get_program(inst.id, program_id)
    result = await db.execute(
        select(ProgramChecklistItem)
        .where(ProgramChecklistItem.program_id == program_id)
        .order_by(
            ProgramChecklistItem.sort_order,
            ProgramChecklistItem.item_name,
        )
    )
    return list(result.scalars().all())


@router.post(
    "/me/programs/{program_id}/checklist",
    response_model=ProgramChecklistItemResponse,
)
async def create_checklist_item(
    program_id: UUID,
    body: CreateProgramChecklistItemRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    from unipaith.models.institution import ProgramChecklistItem

    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    await svc.get_program(inst.id, program_id)
    item = ProgramChecklistItem(
        program_id=program_id,
        item_name=body.item_name,
        category=body.category,
        requirement_level=body.requirement_level,
        description=body.description,
        instructions=body.instructions,
        sort_order=body.sort_order,
    )
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return item


@router.post(
    "/me/programs/{program_id}/checklist/bulk",
    response_model=list[ProgramChecklistItemResponse],
)
async def bulk_create_checklist(
    program_id: UUID,
    body: BulkChecklistRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    from unipaith.models.institution import ProgramChecklistItem

    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    await svc.get_program(inst.id, program_id)
    created = []
    for item_data in body.items:
        item = ProgramChecklistItem(
            program_id=program_id,
            item_name=item_data.item_name,
            category=item_data.category,
            requirement_level=item_data.requirement_level,
            description=item_data.description,
            instructions=item_data.instructions,
            sort_order=item_data.sort_order,
        )
        db.add(item)
        created.append(item)
    await db.flush()
    for item in created:
        await db.refresh(item)
    return created


@router.put(
    "/me/programs/{program_id}/checklist/{item_id}",
    response_model=ProgramChecklistItemResponse,
)
async def update_checklist_item(
    program_id: UUID,
    item_id: UUID,
    body: UpdateProgramChecklistItemRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select

    from unipaith.models.institution import ProgramChecklistItem

    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    await svc.get_program(inst.id, program_id)
    result = await db.execute(
        select(ProgramChecklistItem).where(
            ProgramChecklistItem.id == item_id,
            ProgramChecklistItem.program_id == program_id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        from unipaith.core.exceptions import NotFoundException

        raise NotFoundException("Checklist item not found")
    for key, val in body.model_dump(exclude_unset=True).items():
        setattr(item, key, val)
    await db.flush()
    await db.refresh(item)
    return item


@router.delete(
    "/me/programs/{program_id}/checklist/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_checklist_item(
    program_id: UUID,
    item_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select

    from unipaith.models.institution import ProgramChecklistItem

    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    await svc.get_program(inst.id, program_id)
    result = await db.execute(
        select(ProgramChecklistItem).where(
            ProgramChecklistItem.id == item_id,
            ProgramChecklistItem.program_id == program_id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        from unipaith.core.exceptions import NotFoundException

        raise NotFoundException("Checklist item not found")
    await db.delete(item)
    await db.flush()


# --- Intake Rounds ---


@router.get(
    "/me/programs/{program_id}/intakes",
    response_model=list[IntakeRoundResponse],
)
async def list_intake_rounds(
    program_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select

    from unipaith.models.institution import IntakeRound

    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    await svc.get_program(inst.id, program_id)
    result = await db.execute(
        select(IntakeRound)
        .where(IntakeRound.program_id == program_id)
        .order_by(IntakeRound.sort_order, IntakeRound.application_deadline)
    )
    rounds = list(result.scalars().all())
    return [_enrich_intake(r) for r in rounds]


@router.post(
    "/me/programs/{program_id}/intakes",
    response_model=IntakeRoundResponse,
)
async def create_intake_round(
    program_id: UUID,
    body: CreateIntakeRoundRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    from unipaith.models.institution import IntakeRound

    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    await svc.get_program(inst.id, program_id)
    intake = IntakeRound(
        program_id=program_id,
        round_name=body.round_name,
        intake_term=body.intake_term,
        application_open=body.application_open,
        application_deadline=body.application_deadline,
        decision_date=body.decision_date,
        program_start=body.program_start,
        capacity=body.capacity,
        requirements=body.requirements,
        sort_order=body.sort_order,
    )
    db.add(intake)
    await db.flush()
    await db.refresh(intake)
    return _enrich_intake(intake)


@router.put(
    "/me/programs/{program_id}/intakes/{intake_id}",
    response_model=IntakeRoundResponse,
)
async def update_intake_round(
    program_id: UUID,
    intake_id: UUID,
    body: UpdateIntakeRoundRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select

    from unipaith.models.institution import IntakeRound

    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    await svc.get_program(inst.id, program_id)
    result = await db.execute(
        select(IntakeRound).where(
            IntakeRound.id == intake_id,
            IntakeRound.program_id == program_id,
        )
    )
    intake = result.scalar_one_or_none()
    if not intake:
        from unipaith.core.exceptions import NotFoundException

        raise NotFoundException("Intake round not found")
    for key, val in body.model_dump(exclude_unset=True).items():
        setattr(intake, key, val)
    await db.flush()
    await db.refresh(intake)
    return _enrich_intake(intake)


@router.delete(
    "/me/programs/{program_id}/intakes/{intake_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_intake_round(
    program_id: UUID,
    intake_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select

    from unipaith.models.institution import IntakeRound

    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    await svc.get_program(inst.id, program_id)
    result = await db.execute(
        select(IntakeRound).where(
            IntakeRound.id == intake_id,
            IntakeRound.program_id == program_id,
        )
    )
    intake = result.scalar_one_or_none()
    if not intake:
        from unipaith.core.exceptions import NotFoundException

        raise NotFoundException("Intake round not found")
    await db.delete(intake)
    await db.flush()


@router.get(
    "/{institution_id}/programs/{program_id}/intakes",
    response_model=list[IntakeRoundResponse],
)
async def get_public_intake_rounds(
    institution_id: UUID,
    program_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Public — get active intake rounds for a program."""
    from sqlalchemy import select

    from unipaith.models.institution import IntakeRound

    result = await db.execute(
        select(IntakeRound)
        .where(
            IntakeRound.program_id == program_id,
            IntakeRound.is_active.is_(True),
        )
        .order_by(IntakeRound.sort_order, IntakeRound.application_deadline)
    )
    return [_enrich_intake(r) for r in result.scalars().all()]


def _enrich_intake(r):  # type: ignore[no-untyped-def]
    """Enrich an IntakeRound model instance to IntakeRoundResponse."""

    spots = None
    if r.capacity is not None:
        spots = max(0, r.capacity - (r.enrolled_count or 0))
    return IntakeRoundResponse(
        id=r.id,
        program_id=r.program_id,
        round_name=r.round_name,
        intake_term=r.intake_term,
        application_open=r.application_open,
        application_deadline=r.application_deadline,
        decision_date=r.decision_date,
        program_start=r.program_start,
        capacity=r.capacity,
        enrolled_count=r.enrolled_count or 0,
        requirements=r.requirements,
        status=r.status,
        is_active=r.is_active,
        sort_order=r.sort_order,
        created_at=r.created_at,
        updated_at=r.updated_at,
        spots_remaining=spots,
    )


# --- Communication Templates ---


@router.get("/me/templates", response_model=list[TemplateResponse])
async def list_templates(
    template_type: str | None = Query(None),
    program_id: UUID | None = Query(None),
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    from unipaith.services.communication_service import CommunicationService

    inst = await _svc(db).get_institution(user.id)
    svc = CommunicationService(db)
    return await svc.list_templates(inst.id, template_type, program_id)


@router.post("/me/templates", response_model=TemplateResponse)
async def create_template(
    body: CreateTemplateRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    from unipaith.services.communication_service import CommunicationService

    inst = await _svc(db).get_institution(user.id)
    return await CommunicationService(db).create_template(inst.id, body)


@router.put("/me/templates/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: UUID,
    body: UpdateTemplateRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    from unipaith.services.communication_service import CommunicationService

    inst = await _svc(db).get_institution(user.id)
    return await CommunicationService(db).update_template(
        inst.id,
        template_id,
        body,
    )


@router.delete(
    "/me/templates/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_template(
    template_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    from unipaith.services.communication_service import CommunicationService

    inst = await _svc(db).get_institution(user.id)
    await CommunicationService(db).delete_template(inst.id, template_id)


@router.post(
    "/me/templates/{template_id}/send",
    response_model=SendResult,
)
async def send_from_template(
    template_id: UUID,
    body: SendFromTemplateRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    from unipaith.services.communication_service import CommunicationService

    inst = await _svc(db).get_institution(user.id)
    return await CommunicationService(db).send_from_template(
        inst.id,
        user.id,
        template_id,
        body.application_ids,
        body.variable_overrides,
    )


@router.post(
    "/me/templates/{template_id}/preview",
    response_model=TemplatePreviewResponse,
)
async def preview_template(
    template_id: UUID,
    application_id: UUID | None = Query(None),
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    from unipaith.services.communication_service import CommunicationService

    inst = await _svc(db).get_institution(user.id)
    return await CommunicationService(db).preview_template(
        inst.id,
        template_id,
        application_id,
    )


@router.post("/me/templates/ai-draft")
async def generate_ai_communication_draft(
    application_id: UUID = Query(...),
    message_type: str = Query(...),
    context_notes: str | None = Query(None),
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """AI-generate a context-aware message draft for an applicant (Spec 37
    §2.1). Staff edit before sending; the human edit diff is captured when the
    message is sent (frontend → /institutions/me/ai-surface/commit)."""
    from unipaith.services.ai_config_service import AIConfigService
    from unipaith.services.ai_surface_service import AISurfaceService
    from unipaith.services.communication_service import CommunicationService

    inst = await _svc(db).get_institution(user.id)
    cfgsvc = AIConfigService(db)
    if not await cfgsvc.is_surface_enabled(inst.id, "message_draft"):
        return {"disabled": True, "message_type": message_type}
    draft = await CommunicationService(db).generate_ai_draft(
        inst.id,
        application_id,
        message_type,
        context_notes,
    )
    # Spec 37 §3 — record the AI-generated draft; return its token so the send
    # action can capture the human edit diff.
    no_training = await cfgsvc.is_no_training(inst.id)
    token = await AISurfaceService(db).record_generated(
        institution_id=inst.id,
        actor_user_id=user.id,
        surface="message_draft",
        agent="institution_reply_drafter",
        ai_output={"subject": draft.get("subject", ""), "body": draft.get("body", "")},
        application_id=application_id,
        model=draft.get("source"),
        no_training=no_training,
    )
    draft["draft_token"] = str(token)
    return draft


# --- Audit Log ---


def _audit_date_bounds(
    date_from: date | None, date_to: date | None
) -> tuple[datetime | None, datetime | None]:
    """Inclusive day bounds: from start-of-day to end-of-day."""
    df = datetime.combine(date_from, time.min) if date_from else None
    dt = datetime.combine(date_to, time.max) if date_to else None
    return df, dt


@router.get("/me/audit-log")
async def get_audit_log(
    application_id: UUID | None = Query(None),
    action: str | None = Query(None),
    entity_type: str | None = Query(None),
    category: str | None = Query(None),
    actor_id: UUID | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    format: str = Query("json", pattern="^(json|csv)$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Spec 36 §4/§5 — filterable, paginated institution audit log.

    Filters: action · entity · actor · category · date range. ``format=csv``
    streams the filtered range as a download (§13)."""
    from unipaith.schemas.audit import AuditLogListResponse, AuditLogResponse
    from unipaith.services.audit_service import AuditService

    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    audit = AuditService(db)
    df, dt = _audit_date_bounds(date_from, date_to)
    common = dict(
        application_id=application_id,
        action=action,
        entity_type=entity_type,
        category=category,
        actor_user_id=actor_id,
        date_from=df,
        date_to=dt,
    )

    if format == "csv":
        rows = await audit.list_logs(inst.id, **common, limit=10000, offset=0)
        csv_str = AuditService.to_csv(rows)
        stamp = datetime.now().strftime("%Y%m%d")  # noqa: DTZ005 — filename only
        return Response(
            content=csv_str,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="audit-log-{stamp}.csv"'},
        )

    logs = await audit.list_logs(inst.id, **common, limit=limit, offset=offset)
    total = await audit.count_logs(inst.id, **common)
    items = [AuditLogResponse.model_validate(entry) for entry in logs]
    return AuditLogListResponse(items=items, total=total)


@router.get("/me/audit-log/{event_id}")
async def get_audit_event(
    event_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Spec 36 §5 `GET /audit-log/:id` — single event with full before/after
    diff + reason. Scoped to the caller's institution (tenant-isolated)."""
    from fastapi import HTTPException

    from unipaith.schemas.audit import AuditEventDetailResponse
    from unipaith.services.audit_service import AuditService

    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    entry = await AuditService(db).get_event(inst.id, event_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Audit event not found")
    return AuditEventDetailResponse.model_validate(entry)


class FairnessOverrideRequest(BaseModel):
    signal_key: str = Field(..., min_length=1, max_length=128)
    action: str = Field("override", pattern="^(acknowledge|override)$")
    reason: str = Field(..., min_length=3, max_length=2000)


@router.post("/me/intelligence/fairness/override")
async def override_fairness_signal(
    body: FairnessOverrideRequest,
    request: Request,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Spec 36 §2 (`fairness_signal_override`, per 46 §6) — an institution admin
    acknowledges or overrides a flagged fairness signal. A free-text reason is
    required; the action is audit-logged."""
    from unipaith.schemas.audit import AuditEventDetailResponse
    from unipaith.services.audit_service import AuditService

    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    entry = await AuditService(db).log(
        institution_id=inst.id,
        actor_user_id=user.id,
        action=f"fairness_signal_{body.action}",
        category="fairness_signal_override",
        entity_type="review",
        entity_id=body.signal_key,
        reason=body.reason,
        new_value={"signal_key": body.signal_key, "action": body.action},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return AuditEventDetailResponse.model_validate(entry)


# --- Fairness governance (Spec 46 §6 — disparate-impact auto-halt) ---


class FairnessOverrideApplyRequest(BaseModel):
    program_id: UUID
    # §6.3 — a written rationale (≥100 chars) is required to resume scoring.
    rationale: str = Field(..., min_length=100, max_length=2000)
    # §6.3 — override window: default 1 week, max 4.
    weeks: int = Field(1, ge=1, le=4)
    signal_id: UUID | None = None


class FairnessProgramRequest(BaseModel):
    program_id: UUID


class FairnessThresholdRequest(BaseModel):
    program_id: UUID
    # §9 — per-program Δ ceiling, range 0.05–0.40.
    threshold: float = Field(..., ge=0.05, le=0.40)


class FairnessRecomputeRequest(BaseModel):
    weeks_back: int = Field(4, ge=1, le=12)


async def _owned_program_or_404(db: AsyncSession, institution_id: UUID, program_id: UUID):
    from fastapi import HTTPException

    from unipaith.models.institution import Program

    program = await db.get(Program, program_id)
    if program is None or program.institution_id != institution_id:
        raise HTTPException(status_code=404, detail="Program not found")
    return program


@router.get("/me/fairness/overview")
async def fairness_overview(
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Spec 46 §6.4 — compact panel payload for the dashboard fairness card."""
    from unipaith.services.fairness_service import FairnessService

    inst = await _svc(db).get_institution(user.id)
    return await FairnessService(db).get_overview(inst.id)


@router.get("/me/fairness/cohorts")
async def fairness_cohorts(
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Spec 46 §6.4 — full-page payload: per program×attribute 4-week trend,
    halt status, override history, and threshold config."""
    from unipaith.services.fairness_service import FairnessService

    inst = await _svc(db).get_institution(user.id)
    return await FairnessService(db).get_cohorts(inst.id)


@router.post("/me/fairness/override")
async def fairness_apply_override(
    body: FairnessOverrideApplyRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Spec 46 §6.3 — resume scoring for a halted program (audit-logged)."""
    from fastapi import HTTPException

    from unipaith.services.fairness_service import FairnessService

    inst = await _svc(db).get_institution(user.id)
    await _owned_program_or_404(db, inst.id, body.program_id)
    try:
        override = await FairnessService(db).apply_override(
            body.program_id,
            admin_user_id=user.id,
            rationale=body.rationale,
            weeks=body.weeks,
            signal_id=body.signal_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        "program_id": str(body.program_id),
        "matching_halted": False,
        "fairness_override_active": True,
        "override_expires_at": override.override_expires_at.isoformat(),
    }


@router.post("/me/fairness/revoke")
async def fairness_revoke_override(
    body: FairnessProgramRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Cancel an active override and re-halt the program (Spec 46 §6.3)."""
    from unipaith.services.fairness_service import FairnessService

    inst = await _svc(db).get_institution(user.id)
    await _owned_program_or_404(db, inst.id, body.program_id)
    await FairnessService(db).revoke_override(body.program_id, admin_user_id=user.id)
    return {"program_id": str(body.program_id), "matching_halted": True}


@router.patch("/me/fairness/threshold")
async def fairness_set_threshold(
    body: FairnessThresholdRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Spec 46 §9 — set the per-program disparate-impact threshold."""
    from fastapi import HTTPException

    from unipaith.services.fairness_service import FairnessService

    inst = await _svc(db).get_institution(user.id)
    await _owned_program_or_404(db, inst.id, body.program_id)
    try:
        program = await FairnessService(db).set_threshold(
            body.program_id, threshold=body.threshold, admin_user_id=user.id
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        "program_id": str(body.program_id),
        "fairness_threshold": float(program.fairness_threshold),
    }


@router.post("/me/fairness/recompute")
async def fairness_recompute(
    body: FairnessRecomputeRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """On-demand recompute of the last N completed weeks for this institution's
    programs (the standing Monday-00:00-UTC scheduler is a deferred infra item)."""
    from unipaith.services.fairness_service import FairnessService

    inst = await _svc(db).get_institution(user.id)
    count = await FairnessService(db).run_weekly_compute(
        institution_id=inst.id, weeks_back=body.weeks_back
    )
    return {"computations": count}


# --- Promotions ---


@router.get("/me/promotions", response_model=list[PromotionResponse])
async def list_promotions(
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    return await svc.list_promotions(inst.id)


@router.post("/me/promotions", response_model=PromotionResponse)
async def create_promotion(
    body: CreatePromotionRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    return await svc.create_promotion(inst.id, body)


@router.put(
    "/me/promotions/{promotion_id}",
    response_model=PromotionResponse,
)
async def update_promotion(
    promotion_id: UUID,
    body: UpdatePromotionRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    return await svc.update_promotion(inst.id, promotion_id, body)


@router.delete(
    "/me/promotions/{promotion_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_promotion(
    promotion_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    await svc.delete_promotion(inst.id, promotion_id)


@router.get("/promotions/featured", response_model=list[PromotionResponse])
async def get_featured_promotions(
    region: str | None = Query(None),
    country: str | None = Query(None),
    degree_type: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Public — get currently active featured promotions."""
    svc = _svc(db)
    return await svc.get_active_promotions(region, country, degree_type)


# --- Institution Intelligence ---


@router.get("/me/intelligence/digest")
async def institution_narrative_digest(
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Spec 31 §9 — plain-English daily digest of the institution's applicant
    landscape. Claude narrator when flagged; deterministic fallback otherwise."""
    from unipaith.services.dashboard_intelligence_service import DashboardIntelligenceService

    inst = await _svc(db).get_institution(user.id)
    return await DashboardIntelligenceService(db).generate_digest(inst.id)


@router.get("/me/intelligence/applicant/{student_id}")
async def institution_applicant_context(
    student_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Generate deep applicant context card for admissions review."""
    return {"status": "unavailable"}


@router.get("/me/intelligence/demand")
async def institution_demand_forecast(
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Forecast application demand based on interest signals."""
    return {"status": "unavailable"}


@router.get("/me/intelligence/yield-risks")
async def institution_yield_risks(
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admitted students with an unanswered offer near/past deadline (spec 34
    §6 / spec 31 §2 yield-risk alerts). Owned by the offers domain (Spec 34);
    Spec 31's dashboard yield card consumes this same endpoint."""
    from unipaith.services.application_service import ApplicationService

    inst = await InstitutionService(db).get_institution(user.id)
    return await ApplicationService(db).get_yield_risk_alerts(inst.id)


# --- Spec 35 · Yield analytics + waitlist movement (institution) ---


@router.get("/me/yield")
async def institution_yield(
    program_id: UUID | None = Query(None),
    intake_id: UUID | None = Query(None),
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Yield analytics — rate, funnel tail, melt, time-to-confirm, waitlist
    conversion, predicted-vs-target, cohort fairness lens, next-best-action
    (spec 35 §4). Falls back to deterministic counts when AI is off/fails."""
    from unipaith.services.yield_service import YieldService

    inst = await InstitutionService(db).get_institution(user.id)
    return await YieldService(db).get_yield(inst.id, program_id=program_id, intake_id=intake_id)


@router.get("/me/waitlist")
async def institution_waitlist(
    program_id: UUID | None = Query(None),
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Ranked waitlist + "N seats open, M on waitlist" headline (spec 35 §3.3)."""
    from unipaith.services.enrollment_service import EnrollmentService

    inst = await InstitutionService(db).get_institution(user.id)
    return await EnrollmentService(db).get_waitlist(inst.id, program_id)


@router.post("/me/waitlist/offer-next")
async def institution_waitlist_offer_next(
    body: WaitlistOfferNextRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Promote the top-ranked waitlisted applicant → admit + offer, notified +
    audited (spec 35 §3.3)."""
    from unipaith.services.enrollment_service import EnrollmentService

    inst = await InstitutionService(db).get_institution(user.id)
    return await EnrollmentService(db).offer_to_next(
        inst.id, body.program_id, offer_terms=body.offer, actor_user_id=user.id
    )


@router.post("/me/waitlist/bulk-offer")
async def institution_waitlist_bulk_offer(
    body: WaitlistBulkOfferRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Release places to the next N waitlisted applicants, each audited (§3.3)."""
    from unipaith.services.enrollment_service import EnrollmentService

    inst = await InstitutionService(db).get_institution(user.id)
    return await EnrollmentService(db).bulk_offer(
        inst.id, body.program_id, body.count, actor_user_id=user.id
    )

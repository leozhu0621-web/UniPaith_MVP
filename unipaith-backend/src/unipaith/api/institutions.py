from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai.llm_client import get_llm_client
from unipaith.config import settings
from unipaith.database import get_db
from unipaith.dependencies import require_institution_admin, require_student
from unipaith.models.user import User
from unipaith.schemas.institution import (
    AnalyticsResponse,
    CampaignAttributionDetail,
    CampaignLinkResponse,
    CampaignMetricsResponse,
    CampaignResponse,
    CreateCampaignLinkRequest,
    CreateCampaignRequest,
    CreateDatasetRequest,
    CreateInstitutionRequest,
    CreatePostRequest,
    CreateProgramRequest,
    CreateSegmentRequest,
    DashboardSummaryResponse,
    DatasetResponse,
    DatasetUploadResponse,
    InquiryResponse,
    InstitutionResponse,
    PostMediaUploadResponse,
    PostResponse,
    ProgramResponse,
    RecordActionRequest,
    SegmentResponse,
    SubmitInquiryRequest,
    UpdateCampaignRequest,
    UpdateDatasetRequest,
    UpdateInquiryRequest,
    UpdateInstitutionRequest,
    UpdatePostRequest,
    UpdateProgramRequest,
    UpdateSegmentRequest,
)
from unipaith.services.institution_service import InstitutionService

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
    return InstitutionResponse.model_validate(inst)


@router.put("/me", response_model=InstitutionResponse)
async def update_institution(
    body: UpdateInstitutionRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.update_institution(user.id, body)
    return InstitutionResponse.model_validate(inst)


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
    return await svc.create_segment(inst.id, body)


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


# --- Campaigns ---


@router.get("/me/campaigns", response_model=list[CampaignResponse])
async def list_campaigns(
    campaign_status: str | None = Query(None, alias="status"),
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    return await svc.list_campaigns(inst.id, status_filter=campaign_status)


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
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    return await svc.create_campaign(inst.id, body)


@router.put("/me/campaigns/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: UUID,
    body: UpdateCampaignRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    return await svc.update_campaign(inst.id, campaign_id, body)


@router.delete("/me/campaigns/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign(
    campaign_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    await svc.delete_campaign(inst.id, campaign_id)


@router.get("/me/segments/{segment_id}/preview")
async def preview_segment_audience(
    segment_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Preview how many students match this segment's criteria."""
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    student_ids = await svc.resolve_segment_members(inst.id, segment_id)
    return {"segment_id": str(segment_id), "audience_count": len(student_ids)}


@router.get("/me/campaigns/{campaign_id}/audience")
async def preview_campaign_audience(
    campaign_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Preview the audience that will receive this campaign when sent."""
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    count = await svc.preview_campaign_audience(inst.id, campaign_id)
    return {"campaign_id": str(campaign_id), "audience_count": count}


@router.post("/me/campaigns/{campaign_id}/send", response_model=CampaignResponse)
async def send_campaign(
    campaign_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    return await svc.send_campaign(inst.id, campaign_id)


@router.get(
    "/me/campaigns/{campaign_id}/metrics",
    response_model=CampaignMetricsResponse,
)
async def get_campaign_metrics(
    campaign_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    return await svc.get_campaign_metrics(inst.id, campaign_id)


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

    system_prompt = (
        "You are UniPaith's institutional admissions assistant. "
        "Give practical, concise guidance on applicant triage, pipeline operations, "
        "and program positioning. Avoid fabricating facts."
    )
    user_prompt = (
        f"Institution: {inst.name}\n"
        f"Country: {inst.country}\n"
        f"Program count: {len(programs)}\n"
        f"Context program: {context_program.program_name if context_program else 'N/A'}\n\n"
        f"User message:\n{body.message}"
    )

    llm = get_llm_client()
    reply = await llm.generate_reasoning(system_prompt=system_prompt, user_content=user_prompt)
    return InstitutionAssistantChatResponse(reply=reply, model=settings.llm_reasoning_model)


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


@router.post("/me/datasets/{dataset_id}/confirm", response_model=DatasetResponse)
async def confirm_dataset_upload(
    dataset_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    dataset = await svc.confirm_dataset_upload(inst.id, dataset_id)
    return DatasetResponse.model_validate(dataset)


@router.get("/me/datasets", response_model=list[DatasetResponse])
async def list_datasets(
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    datasets = await svc.list_datasets(inst.id)
    return [DatasetResponse.model_validate(d) for d in datasets]


@router.get("/me/datasets/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    return await svc.get_dataset(inst.id, dataset_id)


@router.get("/me/datasets/{dataset_id}/preview")
async def get_dataset_preview(
    dataset_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    return await svc.get_dataset_preview(inst.id, dataset_id)


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
    return DatasetResponse.model_validate(dataset)


@router.delete("/me/datasets/{dataset_id}", status_code=204)
async def delete_dataset(
    dataset_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    await svc.delete_dataset(inst.id, dataset_id)


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


@router.get("/{institution_id}/posts", response_model=list[PostResponse])
async def get_public_posts(
    institution_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Public endpoint — returns published posts for an institution."""
    svc = _svc(db)
    return await svc.get_public_posts(institution_id)


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

    r = await db.execute(
        sel(StudentProfile.id).where(StudentProfile.user_id == user.id)
    )
    student_id = r.scalar_one_or_none()
    if not student_id:
        return

    svc = _svc(db)
    await svc.record_campaign_action(
        body.campaign_id, student_id, body.action_type, body.target_id,
    )


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

    r = await db.execute(
        sel(StudentProfile).where(StudentProfile.user_id == user.id)
    )
    profile = r.scalar_one_or_none()

    svc = _svc(db)
    return await svc.submit_inquiry(
        data=body,
        student_id=profile.id if profile else None,
        student_name=user.name or user.email,
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


# --- Institution Intelligence ---


@router.get("/me/intelligence/digest")
async def institution_narrative_digest(
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Generate a narrative digest of the institution's applicant landscape."""
    from unipaith.services.institution_intelligence import InstitutionIntelligence

    inst = await _svc(db).get_institution(user.id)
    intelligence = InstitutionIntelligence(db)
    return await intelligence.generate_narrative_digest(inst.id)


@router.get("/me/intelligence/applicant/{student_id}")
async def institution_applicant_context(
    student_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Generate deep applicant context card for admissions review."""
    from unipaith.services.institution_intelligence import InstitutionIntelligence

    inst = await _svc(db).get_institution(user.id)
    intelligence = InstitutionIntelligence(db)
    return await intelligence.generate_applicant_context(inst.id, student_id)


@router.get("/me/intelligence/demand")
async def institution_demand_forecast(
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Forecast application demand based on interest signals."""
    from unipaith.services.institution_intelligence import InstitutionIntelligence

    inst = await _svc(db).get_institution(user.id)
    intelligence = InstitutionIntelligence(db)
    return await intelligence.generate_demand_forecast(inst.id)


@router.get("/me/intelligence/yield-risks")
async def institution_yield_risks(
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Identify admitted students showing signals of choosing elsewhere."""
    from unipaith.services.institution_intelligence import InstitutionIntelligence

    inst = await _svc(db).get_institution(user.id)
    intelligence = InstitutionIntelligence(db)
    return await intelligence.generate_yield_risk_alerts(inst.id)

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai.llm_client import get_llm_client
from unipaith.config import settings
from unipaith.database import get_db
from unipaith.dependencies import require_institution_admin, require_student
from unipaith.models.user import User
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
    CampaignAttributionDetail,
    CampaignLinkResponse,
    CampaignMetricsResponse,
    CampaignResponse,
    ClaimInstitutionRequest,
    CreateCampaignLinkRequest,
    CreateCampaignRequest,
    CreateDatasetRequest,
    CreateInstitutionRequest,
    CreatePostRequest,
    CreateProgramRequest,
    CreatePromotionRequest,
    CreateSegmentRequest,
    DashboardSummaryResponse,
    DatasetResponse,
    DatasetUploadResponse,
    InquiryResponse,
    InstitutionResponse,
    PostMediaUploadResponse,
    PostResponse,
    ProgramResponse,
    PromotionResponse,
    RecordActionRequest,
    SegmentResponse,
    SubmitInquiryRequest,
    UpdateCampaignRequest,
    UpdateDatasetRequest,
    UpdateInquiryRequest,
    UpdateInstitutionRequest,
    UpdatePostRequest,
    UpdateProgramRequest,
    UpdatePromotionRequest,
    UpdateSegmentRequest,
)
from unipaith.schemas.intake import (
    CreateIntakeRoundRequest,
    IntakeRoundResponse,
    UpdateIntakeRoundRequest,
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


# --- Institution Search & Claim ---


@router.get("/search-unclaimed")
async def search_unclaimed_institutions(
    q: str = Query("", min_length=2),
    db: AsyncSession = Depends(get_db),
):
    """Public — search crawled institutions available to claim."""
    svc = _svc(db)
    return await svc.search_unclaimed_institutions(q)


@router.post("/me/claim", response_model=InstitutionResponse)
async def claim_institution(
    body: ClaimInstitutionRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Claim an institution from crawled data, auto-populating profile + programs."""
    svc = _svc(db)
    inst = await svc.claim_institution(user.id, body.extracted_ids)
    return InstitutionResponse.model_validate(inst)


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
        stmt = stmt.where(Institution.name.ilike(f"%{q}%"))
    if country:
        stmt = stmt.where(Institution.country == country)
    if inst_type:
        stmt = stmt.where(Institution.type == inst_type)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = stmt.order_by(Institution.name).offset(
        (page - 1) * page_size
    ).limit(page_size)
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
    else:
        pc_map = {}
        sc_map = {}

    items = []
    for inst in institutions:
        rd = inst.ranking_data or {}
        items.append({
            "id": str(inst.id),
            "name": inst.name,
            "country": inst.country,
            "city": inst.city,
            "type": inst.type,
            "campus_setting": inst.campus_setting,
            "student_body_size": inst.student_body_size,
            "logo_url": inst.logo_url,
            "image_url": (
                (inst.media_gallery or [None])[0]
                if inst.media_gallery
                else None
            ),
            "program_count": pc_map.get(inst.id, 0),
            "school_count": sc_map.get(inst.id, 0),
            "description_text": (
                (inst.description_text or "")[:200]
            ),
            "acceptance_rate": rd.get("acceptance_rate"),
            "sat_avg": rd.get("sat_avg"),
            "us_news_rank": rd.get("us_news_2025"),
            "median_earnings": rd.get("earnings_10yr_median"),
            "graduation_rate": rd.get("graduation_rate"),
        })

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
        select(School).where(School.institution_id == institution_id).order_by(School.sort_order, School.name)
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
    import math

    from sqlalchemy import select

    from unipaith.models.institution import Institution, Program, School
    from unipaith.schemas.institution import ProgramSummaryResponse

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
                float(prog.acceptance_rate) if prog.acceptance_rate is not None
                else (inst.ranking_data or {}).get("acceptance_rate")
            ),
            "application_deadline": str(prog.application_deadline) if prog.application_deadline else None,
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
        inst_result = await db.execute(
            select(Institution).where(Institution.id.in_(inst_ids))
        )
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
        select(IntakeRound).where(
            IntakeRound.program_id == program_id,
            IntakeRound.is_active.is_(True),
        ).order_by(IntakeRound.sort_order, IntakeRound.application_deadline)
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
        inst.id, template_id, body,
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
        inst.id, user.id, template_id, body.application_ids,
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
        inst.id, template_id, application_id,
    )


@router.post("/me/templates/ai-draft")
async def generate_ai_communication_draft(
    application_id: UUID = Query(...),
    message_type: str = Query(...),
    context_notes: str | None = Query(None),
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """AI-generate a context-aware message draft for an applicant."""
    from unipaith.services.communication_service import CommunicationService

    inst = await _svc(db).get_institution(user.id)
    return await CommunicationService(db).generate_ai_draft(
        inst.id, application_id, message_type, context_notes,
    )


# --- Audit Log ---


@router.get("/me/audit-log")
async def get_audit_log(
    application_id: UUID | None = Query(None),
    action: str | None = Query(None),
    entity_type: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    from unipaith.schemas.audit import AuditLogListResponse, AuditLogResponse
    from unipaith.services.audit_service import AuditService

    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    audit = AuditService(db)
    logs = await audit.list_logs(
        inst.id,
        application_id=application_id,
        action=action,
        entity_type=entity_type,
        limit=limit,
        offset=offset,
    )
    total = await audit.count_logs(inst.id, application_id)

    items = []
    for entry in logs:
        actor_email = None
        if entry.actor_user and hasattr(entry.actor_user, "email"):
            actor_email = entry.actor_user.email
        items.append(AuditLogResponse(
            id=entry.id,
            institution_id=entry.institution_id,
            application_id=entry.application_id,
            actor_user_id=entry.actor_user_id,
            action=entry.action,
            entity_type=entry.entity_type,
            entity_id=entry.entity_id,
            description=entry.description,
            old_value=entry.old_value,
            new_value=entry.new_value,
            metadata_json=entry.metadata_json,
            created_at=entry.created_at,
            actor_email=actor_email,
        ))
    return AuditLogListResponse(items=items, total=total)


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

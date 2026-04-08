from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai.llm_client import get_llm_client
from unipaith.config import settings
from unipaith.database import get_db
from unipaith.dependencies import require_institution_admin
from unipaith.models.user import User
from unipaith.schemas.institution import (
    AnalyticsResponse,
    CampaignMetricsResponse,
    CampaignResponse,
    CreateCampaignRequest,
    CreateInstitutionRequest,
    CreateProgramRequest,
    CreateSegmentRequest,
    DashboardSummaryResponse,
    InstitutionResponse,
    ProgramResponse,
    SegmentResponse,
    UpdateCampaignRequest,
    UpdateInstitutionRequest,
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

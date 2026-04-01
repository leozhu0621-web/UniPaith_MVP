from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.dependencies import require_institution_admin, require_student
from unipaith.models.user import User
from unipaith.schemas.application import (
    ApplicationDetailResponse,
    ApplicationResponse,
    CreateApplicationRequest,
    CreateOfferRequest,
    DecisionRequest,
    OfferLetterResponse,
    OfferRespondRequest,
    UpdateApplicationRequest,
)
from unipaith.services.application_service import ApplicationService
from unipaith.services.institution_service import InstitutionService
from unipaith.services.student_service import StudentService

router = APIRouter(prefix="/applications", tags=["applications"])


# --- Student-facing ---

@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_application(
    body: CreateApplicationRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await StudentService(db)._get_student_profile(user.id)
    svc = ApplicationService(db)
    return await svc.create_application(profile.id, body.program_id)


@router.get("/me", response_model=list[ApplicationResponse])
async def list_my_applications(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await StudentService(db)._get_student_profile(user.id)
    svc = ApplicationService(db)
    return await svc.list_student_applications(profile.id)


@router.get("/me/{application_id}", response_model=ApplicationResponse)
async def get_my_application(
    application_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await StudentService(db)._get_student_profile(user.id)
    svc = ApplicationService(db)
    return await svc.get_student_application(profile.id, application_id)


@router.post("/me/{application_id}/submit", response_model=ApplicationResponse)
async def submit_application(
    application_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await StudentService(db)._get_student_profile(user.id)
    svc = ApplicationService(db)
    return await svc.submit_application(profile.id, application_id)


@router.delete("/me/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
async def withdraw_application(
    application_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await StudentService(db)._get_student_profile(user.id)
    svc = ApplicationService(db)
    await svc.withdraw_application(profile.id, application_id)


@router.post(
    "/me/{application_id}/offer/respond", response_model=OfferLetterResponse
)
async def respond_to_offer(
    application_id: UUID,
    body: OfferRespondRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await StudentService(db)._get_student_profile(user.id)
    svc = ApplicationService(db)
    return await svc.respond_to_offer(
        profile.id, application_id, body.response, body.decline_reason
    )


# --- Institution-facing ---

@router.get(
    "/programs/{program_id}",
    response_model=list[ApplicationDetailResponse],
)
async def list_program_applications(
    program_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst = await InstitutionService(db).get_institution(user.id)
    svc = ApplicationService(db)
    return await svc.list_program_applications(inst.id, program_id)


@router.patch(
    "/review/{application_id}/status",
    response_model=ApplicationDetailResponse,
)
async def update_application_status(
    application_id: UUID,
    body: UpdateApplicationRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst = await InstitutionService(db).get_institution(user.id)
    svc = ApplicationService(db)
    return await svc.update_status(inst.id, application_id, body.status)


@router.get(
    "/review/{application_id}", response_model=ApplicationDetailResponse
)
async def get_application_for_review(
    application_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst = await InstitutionService(db).get_institution(user.id)
    svc = ApplicationService(db)
    return await svc.get_application_detail(inst.id, application_id)


@router.post(
    "/review/{application_id}/decision",
    response_model=ApplicationDetailResponse,
)
async def make_decision(
    application_id: UUID,
    body: DecisionRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst = await InstitutionService(db).get_institution(user.id)
    svc = ApplicationService(db)
    return await svc.make_decision(
        inst.id, application_id, body.decision, body.decision_notes
    )


@router.post(
    "/review/{application_id}/offer",
    response_model=OfferLetterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_offer(
    application_id: UUID,
    body: CreateOfferRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst = await InstitutionService(db).get_institution(user.id)
    svc = ApplicationService(db)
    return await svc.create_offer(
        institution_id=inst.id,
        application_id=application_id,
        offer_type=body.offer_type,
        tuition_amount=body.tuition_amount,
        scholarship_amount=body.scholarship_amount,
        assistantship_details=body.assistantship_details,
        financial_package_total=body.financial_package_total,
        conditions=body.conditions,
        response_deadline=body.response_deadline,
    )

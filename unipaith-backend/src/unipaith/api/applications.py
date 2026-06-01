from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.dependencies import require_institution_admin, require_student
from unipaith.models.user import User
from unipaith.schemas.application import (
    ApplicationDetailResponse,
    ApplicationResponse,
    ApproveDeferralRequest,
    BatchReleaseDecisionRequest,
    BatchReleaseDecisionResponse,
    BulkWithdrawRequest,
    ChecklistToggleRequest,
    CreateApplicationRequest,
    CreateOfferRequest,
    DecisionRequest,
    EnrollmentChecklistItemRequest,
    EnrollmentDeclineRequest,
    EnrollmentDeferRequest,
    ExtendDeadlineRequest,
    GuardrailScanResponse,
    MarkEnrollmentConfirmedRequest,
    OfferDecisionResponse,
    OfferLetterResponse,
    OfferRespondRequest,
    OffersComparisonResponse,
    OfferStatusResponse,
    PatchApplicationRequest,
    RecordDepositRequest,
    RecordOfferRequest,
    ReleaseDecisionRequest,
    ReleaseDecisionResponse,
    UpdateApplicationRequest,
    WithdrawResult,
)
from unipaith.schemas.batch import (
    BatchDecisionRequest,
    BatchOperationResult,
    BatchRequestItemsRequest,
    BatchStatusRequest,
)
from unipaith.schemas.checklist import ApplicationChecklistResponse, ReadinessCheckResponse
from unipaith.services.application_service import ApplicationService
from unipaith.services.checklist_service import ChecklistService
from unipaith.services.enrollment_service import EnrollmentService
from unipaith.services.guardrail_service import GuardrailService
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


@router.post("/me/{application_id}/offer/respond", response_model=OfferLetterResponse)
async def respond_to_offer(
    application_id: UUID,
    body: OfferRespondRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Back-compat shim — accept/decline an offer (spec 18 §4)."""
    profile = await StudentService(db)._get_student_profile(user.id)
    svc = ApplicationService(db)
    return await svc.respond_to_offer(
        profile.id, application_id, body.response, body.decline_reason
    )


# --- Spec 18 · Decisions & Offers (student) ---


@router.get("/me/offers/comparison", response_model=OffersComparisonResponse)
async def offers_comparison(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Side-by-side comparison of all current offers (spec 18 §5)."""
    profile = await StudentService(db)._get_student_profile(user.id)
    return await ApplicationService(db).get_offers_comparison(profile.id)


@router.post(
    "/me/{application_id}/offers",
    response_model=OfferLetterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def record_offer(
    application_id: UUID,
    body: RecordOfferRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Record an offer received off-platform (spec 18 §3/§14)."""
    profile = await StudentService(db)._get_student_profile(user.id)
    svc = ApplicationService(db)
    return await svc.record_external_offer(profile.id, application_id, body.model_dump())


@router.patch(
    "/me/{application_id}/offers/{offer_id}",
    response_model=OfferDecisionResponse,
)
async def respond_offer(
    application_id: UUID,
    offer_id: UUID,
    body: OfferRespondRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Accept/decline an offer; returns the other pending apps now
    withdrawable in bulk (spec 18 §4/§6)."""
    profile = await StudentService(db)._get_student_profile(user.id)
    svc = ApplicationService(db)
    result = await svc.respond_to_offer_with_context(
        profile.id, application_id, body.response, body.decline_reason
    )
    return OfferDecisionResponse(
        offer=result["offer"], withdrawable_apps=result["withdrawable_apps"]
    )


@router.post("/me/{application_id}/withdraw", response_model=ApplicationResponse)
async def withdraw_decision(
    application_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Status-preserving withdraw — keeps the row as `withdrawn` (spec 18 §2)."""
    profile = await StudentService(db)._get_student_profile(user.id)
    return await ApplicationService(db).withdraw_from_decisions(profile.id, application_id)


@router.post("/me/withdraw-bulk", response_model=WithdrawResult)
async def withdraw_bulk(
    body: BulkWithdrawRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Withdraw the other pending apps after accepting elsewhere (spec 18 §6)."""
    profile = await StudentService(db)._get_student_profile(user.id)
    n = await ApplicationService(db).bulk_withdraw(profile.id, body.application_ids)
    return WithdrawResult(withdrawn_count=n)


@router.patch("/me/{application_id}", response_model=ApplicationResponse)
async def patch_application(
    application_id: UUID,
    body: PatchApplicationRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Partial update: submission_mode + guardrail intent/rationale (spec 15 §9)."""
    profile = await StudentService(db)._get_student_profile(user.id)
    svc = ApplicationService(db)
    return await svc.patch_application(
        profile.id, application_id, body.model_dump(exclude_unset=True)
    )


@router.post("/me/{application_id}/guardrail-scan", response_model=GuardrailScanResponse)
async def guardrail_scan(
    application_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Return fit band + recommended action + blockers (spec 15 §6.5, G-S4)."""
    profile = await StudentService(db)._get_student_profile(user.id)
    return await GuardrailService(db).scan(profile.id, application_id)


@router.post("/me/{application_id}/check-readiness", response_model=ReadinessCheckResponse)
async def check_readiness(
    application_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Re-evaluate readiness per the Adaptive Intake apply-ready check (spec 15 §5)."""
    profile = await StudentService(db)._get_student_profile(user.id)
    return await ChecklistService(db).readiness_check(profile.id, application_id)


@router.patch("/me/{application_id}/checklist", response_model=ApplicationChecklistResponse)
async def toggle_checklist_item(
    application_id: UUID,
    body: ChecklistToggleRequest,
    request: Request,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Manually mark a checklist item complete/incomplete (external mode, spec 15 §7)."""
    profile = await StudentService(db)._get_student_profile(user.id)
    result = await ChecklistService(db).toggle_item(
        profile.id, application_id, body.item_key, body.completed
    )
    # Spec 36 §2 — checklist_change is an audited event.
    from unipaith.services.audit_service import AuditService

    await AuditService(db).log(
        institution_id=None,
        actor_user_id=user.id,
        actor_role="student",
        action="checklist_completed" if body.completed else "checklist_uncompleted",
        category="checklist_change",
        entity_type="checklist_item",
        entity_id=body.item_key,
        application_id=application_id,
        new_value={"completed": body.completed},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return result


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
    # Get old status for audit
    old = await svc.get_application_detail(inst.id, application_id)
    result = await svc.update_status(inst.id, application_id, body.status)
    # Audit log
    from unipaith.services.audit_service import AuditService

    await AuditService(db).log(
        institution_id=inst.id,
        actor_user_id=user.id,
        action="status_change",
        entity_type="application",
        entity_id=str(application_id),
        application_id=application_id,
        description=f"Status changed from {old.status} to {body.status}",
        old_value={"status": old.status},
        new_value={"status": body.status},
    )
    return result


@router.get("/review/{application_id}", response_model=ApplicationDetailResponse)
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
    result = await svc.make_decision(inst.id, application_id, body.decision, body.decision_notes)
    from unipaith.services.audit_service import AuditService

    await AuditService(db).log(
        institution_id=inst.id,
        actor_user_id=user.id,
        action="decision_release",
        entity_type="application",
        entity_id=str(application_id),
        application_id=application_id,
        description=f"Decision: {body.decision}",
        new_value={"decision": body.decision, "notes": body.decision_notes},
    )
    return result


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
    start = body.start_term
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
        scholarship_currency=body.scholarship_currency,
        tuition_estimate=body.tuition_estimate,
        total_cost_estimate=body.total_cost_estimate,
        start_term_season=start.season if start else None,
        start_term_year=start.year if start else None,
        next_step_actions=body.next_step_actions,
    )


# --- Spec 34 · Decision release + offer + yield ---


@router.post("/review/{application_id}/release", response_model=ReleaseDecisionResponse)
async def release_decision(
    application_id: UUID,
    body: ReleaseDecisionRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Release a decision (and offer for accepts/conditionals) in one audited,
    notified action (spec 34 §3). Replaces the decision-then-offer two-step."""
    inst = await InstitutionService(db).get_institution(user.id)
    svc = ApplicationService(db)
    app, offer = await svc.release_decision(
        inst.id,
        application_id,
        body.decision,
        decision_notes=body.decision_notes,
        actor_user_id=user.id,
        offer=body.offer.model_dump() if body.offer else None,
        custom_message=body.message,
        notify=body.notify,
    )
    detail = await svc.get_application_detail(inst.id, application_id)
    return ReleaseDecisionResponse(application=detail, offer=offer)


@router.get("/review/{application_id}/offer-status", response_model=OfferStatusResponse)
async def get_offer_status(
    application_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Current student-response state for an applicant's offer (spec 34 §7)."""
    inst = await InstitutionService(db).get_institution(user.id)
    return await ApplicationService(db).get_offer_status(inst.id, application_id)


@router.post("/offers/{offer_id}/extend-deadline", response_model=OfferLetterResponse)
async def extend_offer_deadline(
    offer_id: UUID,
    body: ExtendDeadlineRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Push an offer's response deadline out and re-notify the student (§7)."""
    inst = await InstitutionService(db).get_institution(user.id)
    return await ApplicationService(db).extend_offer_deadline(
        inst.id, offer_id, body.response_deadline
    )


@router.post("/offers/{offer_id}/rescind", response_model=OfferLetterResponse)
async def rescind_offer(
    offer_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Rescind an unanswered offer past its deadline (spec 34 §8)."""
    inst = await InstitutionService(db).get_institution(user.id)
    return await ApplicationService(db).rescind_offer(inst.id, offer_id)


@router.post("/batch-release-decision", response_model=BatchReleaseDecisionResponse)
async def batch_release_decision_v2(
    body: BatchReleaseDecisionRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Per-applicant batch release with per-item decision + offer (spec 34 §5).
    Each applicant is audited individually."""
    inst = await InstitutionService(db).get_institution(user.id)
    svc = ApplicationService(db)
    items = [
        {
            "application_id": it.application_id,
            "decision": it.decision,
            "decision_notes": it.decision_notes,
            "offer": it.offer.model_dump() if it.offer else None,
            "message": it.message,
        }
        for it in body.items
    ]
    return await svc.batch_release_decisions(
        inst.id, items, actor_user_id=user.id, notify=body.notify
    )


# --- Batch Operations ---


@router.post("/batch/request-items", response_model=BatchOperationResult)
async def batch_request_missing_items(
    body: BatchRequestItemsRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select

    from unipaith.models.application import Application
    from unipaith.services.audit_service import AuditService

    inst = await InstitutionService(db).get_institution(user.id)  # auth check
    audit = AuditService(db)
    result = BatchOperationResult(
        success_count=0,
        failed_ids=[],
        errors=[],
    )
    for app_id in body.application_ids:
        try:
            r = await db.execute(select(Application).where(Application.id == app_id))
            app = r.scalar_one_or_none()
            if not app:
                result.failed_ids.append(app_id)
                result.errors.append(f"{app_id}: not found")
                continue
            app.missing_items = {"items": body.items}
            app.completeness_status = "incomplete"
            # Spec 31 §5 — audit-log per application in a batch action.
            await audit.log(
                institution_id=inst.id,
                actor_user_id=user.id,
                action="batch_request_missing_items",
                entity_type="application",
                entity_id=str(app_id),
                application_id=app_id,
                description="Batch request for missing items.",
                new_value={"items": body.items},
            )
            result.success_count += 1
        except Exception as e:
            result.failed_ids.append(app_id)
            result.errors.append(str(e))
    await db.flush()
    return result


@router.post("/batch/status", response_model=BatchOperationResult)
async def batch_update_status(
    body: BatchStatusRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst = await InstitutionService(db).get_institution(user.id)
    svc = ApplicationService(db)
    from unipaith.services.audit_service import AuditService

    audit = AuditService(db)
    result = BatchOperationResult(
        success_count=0,
        failed_ids=[],
        errors=[],
    )
    for app_id in body.application_ids:
        try:
            await svc.update_status(inst.id, app_id, body.status)
            # Spec 31 §5 — audit-log per application in a batch action.
            await audit.log(
                institution_id=inst.id,
                actor_user_id=user.id,
                action="batch_update_status",
                entity_type="application",
                entity_id=str(app_id),
                application_id=app_id,
                description=f"Batch status update to '{body.status}'.",
                new_value={"status": body.status},
            )
            result.success_count += 1
        except Exception as e:
            result.failed_ids.append(app_id)
            result.errors.append(str(e))
    return result


@router.post("/batch/decision", response_model=BatchOperationResult)
async def batch_release_decision(
    body: BatchDecisionRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst = await InstitutionService(db).get_institution(user.id)
    svc = ApplicationService(db)
    from unipaith.services.audit_service import AuditService

    audit = AuditService(db)
    result = BatchOperationResult(
        success_count=0,
        failed_ids=[],
        errors=[],
    )
    for app_id in body.application_ids:
        try:
            await svc.make_decision(
                inst.id,
                app_id,
                body.decision,
                body.decision_notes,
            )
            # Spec 31 §5 — audit-log per application in a batch action.
            await audit.log(
                institution_id=inst.id,
                actor_user_id=user.id,
                action="batch_release_decision",
                entity_type="application",
                entity_id=str(app_id),
                application_id=app_id,
                description=f"Batch decision released: '{body.decision}'.",
                new_value={"decision": body.decision},
            )
            result.success_count += 1
        except Exception as e:
            result.failed_ids.append(app_id)
            result.errors.append(str(e))
    return result


# --- Spec 35 · Enrollment Confirmation & Yield (student) ---


@router.get("/me/{application_id}/enrollment")
async def get_my_enrollment(
    application_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """The student's enrollment window for an accepted offer (spec 35 §2).
    Returns ``{available: False}`` until an offer is accepted (§7)."""
    profile = await StudentService(db)._get_student_profile(user.id)
    return await EnrollmentService(db).get_student_enrollment(profile.id, application_id)


@router.post("/me/{application_id}/enrollment/confirm")
async def confirm_enrollment(
    application_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Confirm intent to enroll — the §2.2 celebratory moment (intent_confirmed)."""
    profile = await StudentService(db)._get_student_profile(user.id)
    return await EnrollmentService(db).confirm_intent(profile.id, application_id)


@router.post("/me/{application_id}/enrollment/decline")
async def decline_enrollment(
    application_id: UUID,
    body: EnrollmentDeclineRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Decline a place after accepting (§2.2) — frees the seat for the waitlist."""
    profile = await StudentService(db)._get_student_profile(user.id)
    return await EnrollmentService(db).decline_after_accept(profile.id, application_id, body.reason)


@router.post("/me/{application_id}/enrollment/defer")
async def defer_enrollment(
    application_id: UUID,
    body: EnrollmentDeferRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Request a deferral to a later start term (§2.2) — routes to the school."""
    profile = await StudentService(db)._get_student_profile(user.id)
    to_term = body.to_term.model_dump() if body.to_term else None
    return await EnrollmentService(db).request_deferral(profile.id, application_id, to_term)


@router.post("/me/{application_id}/enrollment/checklist-item")
async def toggle_enrollment_checklist_item(
    application_id: UUID,
    body: EnrollmentChecklistItemRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Mark a self-serve pre-arrival checklist item complete/incomplete (§2.1)."""
    profile = await StudentService(db)._get_student_profile(user.id)
    return await EnrollmentService(db).toggle_checklist_item(
        profile.id, application_id, body.key, body.complete
    )


# --- Spec 35 · Enrollment tracking (institution, per-applicant) ---


@router.get("/review/{application_id}/enrollment")
async def get_applicant_enrollment(
    application_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Per-applicant enrollment state, deposit, checklist + timeline (spec 35 §3.1)."""
    inst = await InstitutionService(db).get_institution(user.id)
    return await EnrollmentService(db).get_institution_enrollment(inst.id, application_id)


@router.post("/review/{application_id}/enrollment/record-deposit")
async def record_enrollment_deposit(
    application_id: UUID,
    body: RecordDepositRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Record deposit *status* — status-only in MVP, no money moves (§3.1)."""
    inst = await InstitutionService(db).get_institution(user.id)
    return await EnrollmentService(db).record_deposit(
        inst.id,
        application_id,
        body.deposit_status,
        deposit_amount=body.deposit_amount,
        actor_user_id=user.id,
    )


@router.post("/review/{application_id}/enrollment/confirm")
async def mark_enrollment_confirmed(
    application_id: UUID,
    body: MarkEnrollmentConfirmedRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Mark enrollment confirmed (or finalize as enrolled with ``final``) (§3.1)."""
    inst = await InstitutionService(db).get_institution(user.id)
    return await EnrollmentService(db).mark_enrollment_confirmed(
        inst.id, application_id, final=body.final, actor_user_id=user.id
    )


@router.post("/review/{application_id}/enrollment/approve-deferral")
async def approve_enrollment_deferral(
    application_id: UUID,
    body: ApproveDeferralRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Approve / decline a student's deferral request (§3.1)."""
    inst = await InstitutionService(db).get_institution(user.id)
    return await EnrollmentService(db).approve_deferral(
        inst.id, application_id, approved=body.approved, actor_user_id=user.id
    )

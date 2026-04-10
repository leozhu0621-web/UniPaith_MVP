from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.dependencies import require_institution_admin
from unipaith.models.user import User
from unipaith.schemas.batch import BatchAssignRequest, BatchOperationResult
from unipaith.schemas.review import (
    AIReviewSummaryResponse,
    ApplicationScoreResponse,
    CreateRubricRequest,
    PipelineResponse,
    ReviewAssignmentResponse,
    RubricResponse,
    ScoreApplicationRequest,
)
from unipaith.services.institution_service import InstitutionService
from unipaith.services.review_pipeline_service import ReviewPipelineService

router = APIRouter(prefix="/reviews", tags=["reviews"])


# --- Rubrics ---


@router.post("/rubrics", response_model=RubricResponse, status_code=status.HTTP_201_CREATED)
async def create_rubric(
    body: CreateRubricRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst = await InstitutionService(db).get_institution(user.id)
    svc = ReviewPipelineService(db)
    return await svc.create_rubric(
        institution_id=inst.id,
        rubric_name=body.rubric_name,
        criteria=body.criteria,
        program_id=body.program_id,
    )


@router.get("/rubrics", response_model=list[RubricResponse])
async def list_rubrics(
    program_id: UUID | None = Query(None),
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst = await InstitutionService(db).get_institution(user.id)
    svc = ReviewPipelineService(db)
    return await svc.list_rubrics(inst.id, program_id=program_id)


# --- Application Review ---


@router.post("/applications/{application_id}/assign", response_model=list[ReviewAssignmentResponse])
async def assign_reviewers(
    application_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst = await InstitutionService(db).get_institution(user.id)
    svc = ReviewPipelineService(db)
    result = await svc.assign_reviewers(application_id, inst.id)
    from unipaith.services.audit_service import AuditService
    await AuditService(db).log(
        institution_id=inst.id, actor_user_id=user.id,
        action="reviewer_assigned", entity_type="application",
        entity_id=str(application_id), application_id=application_id,
        description=f"Assigned {len(result)} reviewer(s)",
        new_value={"reviewer_count": len(result)},
    )
    return result


@router.post("/applications/{application_id}/score", response_model=ApplicationScoreResponse)
async def score_application(
    application_id: UUID,
    body: ScoreApplicationRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst = await InstitutionService(db).get_institution(user.id)
    svc = ReviewPipelineService(db)
    reviewer = await svc.get_reviewer_by_user(user.id, inst.id)
    return await svc.score_application(
        reviewer_id=reviewer.id,
        application_id=application_id,
        rubric_id=body.rubric_id,
        criterion_scores=body.criterion_scores,
        reviewer_notes=body.reviewer_notes,
    )


@router.get("/applications/{application_id}/scores", response_model=list[ApplicationScoreResponse])
async def get_scores(
    application_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    await InstitutionService(db).get_institution(user.id)
    svc = ReviewPipelineService(db)
    return await svc.get_application_scores(application_id)


@router.get("/applications/{application_id}/ai-summary", response_model=AIReviewSummaryResponse)
async def ai_review_summary(
    application_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    await InstitutionService(db).get_institution(user.id)
    svc = ReviewPipelineService(db)
    return await svc.generate_ai_review_summary(application_id)


@router.get("/applications/{application_id}/ai-packet")
async def get_ai_packet_summary(
    application_id: UUID,
    rubric_id: UUID | None = Query(None),
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get cached AI packet summary or generate a new one."""
    inst = await InstitutionService(db).get_institution(user.id)
    svc = ReviewPipelineService(db)
    return await svc.get_or_generate_packet_summary(
        inst.id, application_id, rubric_id,
    )


@router.post("/applications/{application_id}/ai-packet/regenerate")
async def regenerate_ai_packet_summary(
    application_id: UUID,
    rubric_id: UUID | None = Query(None),
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Force regenerate AI packet summary."""
    inst = await InstitutionService(db).get_institution(user.id)
    svc = ReviewPipelineService(db)
    return await svc.get_or_generate_packet_summary(
        inst.id, application_id, rubric_id, force_regenerate=True,
    )


@router.post("/applications/{application_id}/ai-prefill")
async def ai_rubric_prefill(
    application_id: UUID,
    rubric_id: UUID = Query(...),
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """AI pre-fill reviewer notes + scores per rubric criterion."""
    inst = await InstitutionService(db).get_institution(user.id)
    svc = ReviewPipelineService(db)

    # Get or generate packet summary with the rubric
    packet = await svc.get_or_generate_packet_summary(
        inst.id, application_id, rubric_id,
    )

    # Map criterion assessments to pre-fill format
    prefill: dict[str, dict] = {}
    assessments = packet.get("criterion_assessments") or []
    for ca in assessments:
        name = ca.get("criterion_name", "")
        if name:
            evidence_text = ""
            for ev in ca.get("evidence", []):
                evidence_text += (
                    f"{ev.get('field', '')}: {ev.get('value', '')}. "
                )
            prefill[name] = {
                "suggested_score": ca.get("score"),
                "suggested_note": (
                    f"{ca.get('assessment', '')} "
                    f"[Evidence: {evidence_text.strip()}]"
                ).strip() if evidence_text else ca.get(
                    "assessment", "",
                ),
            }

    return {
        "application_id": str(application_id),
        "rubric_id": str(rubric_id),
        "prefill": prefill,
        "overall_note": packet.get("overall_summary", ""),
        "recommended_score": packet.get("recommended_score"),
    }


# --- Integrity Signals ---


@router.post("/applications/{application_id}/integrity-scan")
async def scan_application_integrity(
    application_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Run AI integrity scan on an application."""
    inst = await InstitutionService(db).get_institution(user.id)
    svc = ReviewPipelineService(db)
    return await svc.scan_integrity(inst.id, application_id)


@router.get("/integrity-signals")
async def list_integrity_signals(
    application_id: UUID | None = Query(None),
    signal_status: str | None = Query(None),
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """List integrity signals for the institution."""
    inst = await InstitutionService(db).get_institution(user.id)
    svc = ReviewPipelineService(db)
    return await svc.list_integrity_signals(
        inst.id, application_id, signal_status,
    )


@router.post("/integrity-signals/{signal_id}/resolve")
async def resolve_integrity_signal(
    signal_id: UUID,
    notes: str | None = Query(None),
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Resolve an integrity signal."""
    inst = await InstitutionService(db).get_institution(user.id)
    svc = ReviewPipelineService(db)
    return await svc.resolve_integrity_signal(
        inst.id, signal_id, user.id, notes,
    )


@router.get("/priority-queue")
async def get_review_priority_queue(
    program_id: UUID | None = Query(None),
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """AI-ranked priority queue for application review."""
    inst = await InstitutionService(db).get_institution(user.id)
    svc = ReviewPipelineService(db)
    return await svc.calculate_review_priorities(
        inst.id, program_id,
    )


# --- Batch Operations ---


@router.post("/batch/assign", response_model=BatchOperationResult)
async def batch_assign_reviewers(
    body: BatchAssignRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst = await InstitutionService(db).get_institution(user.id)
    svc = ReviewPipelineService(db)
    result = BatchOperationResult(success_count=0, failed_ids=[], errors=[])
    for app_id in body.application_ids:
        try:
            await svc.assign_reviewers(app_id, inst.id)
            result.success_count += 1
        except Exception as e:
            result.failed_ids.append(app_id)
            result.errors.append(str(e))
    return result


# --- Cohort Comparison ---


@router.get("/cohort-compare")
async def cohort_comparison(
    application_ids: str = Query(
        ..., description="Comma-separated application UUIDs",
    ),
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Side-by-side comparison of multiple applicants on rubric scores."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    from unipaith.models.application import Application, ApplicationScore
    from unipaith.models.student import StudentProfile

    await InstitutionService(db).get_institution(user.id)  # auth check
    ids = [UUID(aid.strip()) for aid in application_ids.split(",") if aid.strip()]

    applicants = []
    for app_id in ids:
        try:
            # Get application detail
            ar = await db.execute(
                select(Application).where(Application.id == app_id)
            )
            app = ar.scalar_one_or_none()
            if not app:
                continue

            # Get student profile
            sr = await db.execute(
                select(StudentProfile)
                .options(selectinload(StudentProfile.academic_records))
                .where(
                    StudentProfile.id == app.student_id,
                )
            )
            student = sr.scalar_one_or_none()

            # Get scores
            scores_r = await db.execute(
                select(ApplicationScore)
                .where(ApplicationScore.application_id == app_id)
                .order_by(ApplicationScore.scored_at.desc())
            )
            scores = [
                {
                    "id": str(s.id),
                    "reviewer_id": str(s.reviewer_id),
                    "rubric_id": str(s.rubric_id),
                    "criterion_scores": s.criterion_scores,
                    "total_weighted_score": (
                        float(s.total_weighted_score)
                        if s.total_weighted_score
                        else None
                    ),
                    "reviewer_notes": s.reviewer_notes,
                    "scored_by_type": s.scored_by_type,
                    "scored_at": s.scored_at.isoformat()
                    if s.scored_at
                    else None,
                }
                for s in scores_r.scalars().all()
            ]

            applicants.append({
                "application_id": str(app.id),
                "student_id": str(app.student_id),
                "student_name": (
                    f"{student.first_name or ''} {student.last_name or ''}".strip()
                    if student
                    else "Unknown"
                ),
                "status": app.status,
                "match_score": (
                    float(app.match_score)
                    if app.match_score
                    else None
                ),
                "decision": app.decision,
                "completeness_status": app.completeness_status,
                "submitted_at": (
                    app.submitted_at.isoformat()
                    if app.submitted_at
                    else None
                ),
                "scores": scores,
                "avg_score": (
                    round(
                        sum(
                            float(s["total_weighted_score"])
                            for s in scores
                            if s["total_weighted_score"]
                        )
                        / len(
                            [
                                s
                                for s in scores
                                if s["total_weighted_score"]
                            ]
                        ),
                        2,
                    )
                    if any(s["total_weighted_score"] for s in scores)
                    else None
                ),
                "gpa": (
                    max(
                        (float(ar.gpa) for ar in student.academic_records if ar.gpa is not None),
                        default=None,
                    )
                    if student and student.academic_records
                    else None
                ),
                "nationality": (
                    student.nationality
                    if student and hasattr(student, "nationality")
                    else None
                ),
            })
        except Exception:
            continue

    return {"applicants": applicants, "count": len(applicants)}


# --- Pipeline ---


@router.get("/pipeline/{program_id}", response_model=PipelineResponse)
async def get_pipeline(
    program_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst = await InstitutionService(db).get_institution(user.id)
    svc = ReviewPipelineService(db)
    return await svc.get_program_pipeline(inst.id, program_id)

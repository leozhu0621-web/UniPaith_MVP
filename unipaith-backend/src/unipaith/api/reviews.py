from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.dependencies import require_institution_admin
from unipaith.models.user import User
from unipaith.schemas.batch import BatchAssignRequest, BatchOperationResult
from unipaith.schemas.matching import InstitutionMatchRationaleResponse
from unipaith.schemas.review import (
    AIReviewSummaryResponse,
    ApplicationScoreResponse,
    CreateRubricRequest,
    IntegrityActionRequest,
    PipelineResponse,
    RevealIdentityRequest,
    ReviewAssignmentResponse,
    ReviewAssistantChatRequest,
    RubricResponse,
    ScoreApplicationRequest,
)
from unipaith.services.ai_config_service import AIConfigService
from unipaith.services.ai_surface_service import AISurfaceService
from unipaith.services.institution_service import InstitutionService
from unipaith.services.review_pipeline_service import ReviewPipelineService

router = APIRouter(prefix="/reviews", tags=["reviews"])

# AI packet confidence is a band string; map it to a 0-100 number for the
# per-surface threshold comparison (Spec 37 §5).
_BAND_CONFIDENCE = {"low": 30, "medium": 65, "high": 90}


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
        institution_id=inst.id,
        actor_user_id=user.id,
        action="reviewer_assigned",
        entity_type="application",
        entity_id=str(application_id),
        application_id=application_id,
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
    result = await svc.score_application(
        reviewer_id=reviewer.id,
        application_id=application_id,
        rubric_id=body.rubric_id,
        criterion_scores=body.criterion_scores,
        reviewer_notes=body.reviewer_notes,
    )
    # Spec 37 §3 — if scoring started from an AI pre-fill, capture the
    # human<->AI edit diff (human_edit + decision_action) against the pre-fill.
    if body.ai_draft_token is not None:
        no_training = await AIConfigService(db).is_no_training(inst.id)
        await AISurfaceService(db).record_committed(
            institution_id=inst.id,
            actor_user_id=user.id,
            surface="rubric_prefill",
            final_output={
                "criterion_scores": body.criterion_scores,
                "reviewer_notes": body.reviewer_notes or "",
            },
            action="score_saved",
            draft_token=body.ai_draft_token,
            application_id=application_id,
            no_training=no_training,
        )
    return result


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
    if not await AIConfigService(db).is_surface_enabled(inst.id, "packet_summary"):
        return {"disabled": True}
    svc = ReviewPipelineService(db)
    return await svc.get_or_generate_packet_summary(
        inst.id,
        application_id,
        rubric_id,
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
    if not await AIConfigService(db).is_surface_enabled(inst.id, "packet_summary"):
        return {"disabled": True}
    svc = ReviewPipelineService(db)
    packet = await svc.get_or_generate_packet_summary(
        inst.id,
        application_id,
        rubric_id,
        force_regenerate=True,
    )
    # Spec 37 §3 — record the AI-generated packet summary (the join token lets a
    # later human edit/decision tie back to this artifact).
    no_training = await AIConfigService(db).is_no_training(inst.id)
    token = await AISurfaceService(db).record_generated(
        institution_id=inst.id,
        actor_user_id=user.id,
        surface="packet_summary",
        agent="review_summarizer",
        ai_output={"summary": packet.get("overall_summary") or packet.get("summary") or ""},
        application_id=application_id,
        confidence=_BAND_CONFIDENCE.get(str(packet.get("confidence_level", "")).lower()),
        no_training=no_training,
    )
    if isinstance(packet, dict):
        packet["draft_token"] = str(token)
    return packet


@router.get("/applications/{application_id}/review-packet")
async def get_review_packet(
    application_id: UUID,
    rubric_id: UUID | None = Query(None),
    reveal: bool = Query(False),
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Spec 32 §8 — the consolidated ApplicantReviewPacket (student summary,
    program, AI summary, per-criterion × per-reviewer scores + variance,
    integrity, documents, essays, decision, offer, holistic + test-optional
    context, blind-review + locked state)."""
    inst = await InstitutionService(db).get_institution(user.id)
    svc = ReviewPipelineService(db)
    return await svc.build_review_packet(
        inst.id, application_id, rubric_id=rubric_id, reveal=reveal
    )


@router.post("/applications/{application_id}/synthesize")
async def synthesize_reviews(
    application_id: UUID,
    rubric_id: UUID | None = Query(None),
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Spec 32 §4 — AI synthesis across reviewers (Sonnet, rule-based fallback)."""
    inst = await InstitutionService(db).get_institution(user.id)
    svc = ReviewPipelineService(db)
    return await svc.synthesize_reviews(inst.id, application_id, rubric_id)


@router.post("/applications/{application_id}/assistant-chat")
async def review_assistant_chat(
    application_id: UUID,
    body: ReviewAssistantChatRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Spec 32 §6 — grounded Q&A about one applicant (Sonnet, rule-based fallback)."""
    inst = await InstitutionService(db).get_institution(user.id)
    if not await AIConfigService(db).is_surface_enabled(inst.id, "assistant_chat"):
        return {
            "answer": "The AI applicant assistant is turned off for your institution.",
            "citations": [],
            "grounded": True,
            "disabled": True,
        }
    svc = ReviewPipelineService(db)
    result = await svc.answer_applicant_question(inst.id, application_id, body.question)
    # Spec 37 §3 — record the AI Q&A artifact (grounded answer + citations).
    answer = result.get("answer") if isinstance(result, dict) else str(result)
    no_training = await AIConfigService(db).is_no_training(inst.id)
    await AISurfaceService(db).record_generated(
        institution_id=inst.id,
        actor_user_id=user.id,
        surface="assistant_chat",
        agent="review_assistant",
        ai_output={"question": body.question, "answer": answer},
        application_id=application_id,
        no_training=no_training,
    )
    return result


@router.post("/applications/{application_id}/reveal-identity")
async def reveal_applicant_identity(
    application_id: UUID,
    body: RevealIdentityRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Spec 32 §7A.1 — audit-logged reveal of a blind-redacted applicant."""
    inst = await InstitutionService(db).get_institution(user.id)
    svc = ReviewPipelineService(db)
    return await svc.reveal_identity(inst.id, application_id, user.id, body.reason)


@router.get(
    "/applications/{application_id}/match-rationale",
    response_model=InstitutionMatchRationaleResponse,
)
async def get_match_rationale_full(
    application_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Spec 06 §3 / §5.5 — the FULL, evidence-linked match rationale for a
    reviewer. This is the institution projection of the same artifact the
    student sees redacted (spec 32 §6)."""
    inst = await InstitutionService(db).get_institution(user.id)
    svc = ReviewPipelineService(db)
    return await svc.get_match_rationale_for_review(inst.id, application_id)


@router.post("/applications/{application_id}/ai-prefill")
async def ai_rubric_prefill(
    application_id: UUID,
    rubric_id: UUID = Query(...),
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """AI pre-fill reviewer notes + scores per rubric criterion."""
    inst = await InstitutionService(db).get_institution(user.id)
    cfgsvc = AIConfigService(db)
    if not await cfgsvc.is_surface_enabled(inst.id, "rubric_prefill"):
        return {
            "application_id": str(application_id),
            "rubric_id": str(rubric_id),
            "prefill": {},
            "disabled": True,
        }
    svc = ReviewPipelineService(db)

    # Get or generate packet summary with the rubric
    packet = await svc.get_or_generate_packet_summary(
        inst.id,
        application_id,
        rubric_id,
    )

    # Spec 37 §5 — only surface the pre-fill when its confidence clears the
    # institution's per-surface floor (default 70); otherwise withhold it.
    min_conf = await cfgsvc.min_confidence(inst.id, "rubric_prefill")
    confidence = _BAND_CONFIDENCE.get(str(packet.get("confidence_level", "")).lower(), 30)
    withheld = confidence < min_conf

    # Map criterion assessments to pre-fill format
    prefill: dict[str, dict] = {}
    if not withheld:
        assessments = packet.get("criterion_assessments") or []
        for ca in assessments:
            name = ca.get("criterion_name", "")
            if name:
                evidence_text = ""
                for ev in ca.get("evidence", []):
                    evidence_text += f"{ev.get('field', '')}: {ev.get('value', '')}. "
                prefill[name] = {
                    "suggested_score": ca.get("score"),
                    "suggested_note": (
                        f"{ca.get('assessment', '')} [Evidence: {evidence_text.strip()}]"
                    ).strip()
                    if evidence_text
                    else ca.get(
                        "assessment",
                        "",
                    ),
                }

    response: dict = {
        "application_id": str(application_id),
        "rubric_id": str(rubric_id),
        "prefill": prefill,
        "overall_note": packet.get("overall_summary", ""),
        "recommended_score": packet.get("recommended_score"),
        "confidence": confidence,
        "min_confidence": min_conf,
        "withheld_low_confidence": withheld,
    }

    # Spec 37 §3 — record the AI-generated pre-fill (only when actually shown);
    # the returned token lets the score-save capture the human edit diff.
    if prefill:
        no_training = await cfgsvc.is_no_training(inst.id)
        token = await AISurfaceService(db).record_generated(
            institution_id=inst.id,
            actor_user_id=user.id,
            surface="rubric_prefill",
            agent="review_summarizer",
            ai_output={"prefill": prefill, "overall_note": response["overall_note"]},
            application_id=application_id,
            confidence=confidence,
            no_training=no_training,
        )
        response["draft_token"] = str(token)

    return response


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
        inst.id,
        application_id,
        signal_status,
    )


@router.post("/integrity-signals/{signal_id}/resolve")
async def resolve_integrity_signal(
    signal_id: UUID,
    notes: str | None = Query(None),
    resolution: str | None = Query(
        None,
        description="acceptable | requires_clarification | reject_application",
    ),
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Resolve an integrity signal (spec 31 §6). The resolution outcome is
    audit-logged; reject_application is advisory (never auto-rejects)."""
    inst = await InstitutionService(db).get_institution(user.id)
    svc = ReviewPipelineService(db)
    return await svc.resolve_integrity_signal(
        inst.id,
        signal_id,
        user.id,
        notes,
        resolution,
    )


@router.post("/integrity-signals/{signal_id}/action")
async def act_on_integrity_signal(
    signal_id: UUID,
    body: IntegrityActionRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Spec 32 §7 — reviewer acts on an integrity signal (acknowledge / clarify /
    reject_application). Each action is audit-logged; reject flips the
    application to a rejected decision."""
    inst = await InstitutionService(db).get_institution(user.id)
    svc = ReviewPipelineService(db)
    return await svc.act_on_integrity_signal(inst.id, signal_id, user.id, body.action, body.notes)


@router.get("/calibration")
async def get_reviewer_calibration(
    program_id: UUID | None = Query(None),
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Spec 32 §7A.2 — reader calibration: inter-rater reliability, per-reviewer
    drift, and test-optional cohort breakdown. Coaching signals only."""
    inst = await InstitutionService(db).get_institution(user.id)
    svc = ReviewPipelineService(db)
    return await svc.compute_calibration(inst.id, program_id)


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
        inst.id,
        program_id,
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
    from unipaith.services.audit_service import AuditService

    audit = AuditService(db)
    result = BatchOperationResult(success_count=0, failed_ids=[], errors=[])
    for app_id in body.application_ids:
        try:
            await svc.assign_reviewers(app_id, inst.id)
            # Spec 31 §5 — audit-log per application in a batch action.
            await audit.log(
                institution_id=inst.id,
                actor_user_id=user.id,
                action="batch_assign_reviewers",
                entity_type="application",
                entity_id=str(app_id),
                application_id=app_id,
                description="Batch reviewer assignment.",
            )
            result.success_count += 1
        except Exception as e:
            result.failed_ids.append(app_id)
            result.errors.append(str(e))
    return result


# --- Cohort Comparison ---


@router.get("/cohort-compare")
async def cohort_comparison(
    application_ids: str = Query(
        ...,
        description="Comma-separated application UUIDs",
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
            ar = await db.execute(select(Application).where(Application.id == app_id))
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
                        float(s.total_weighted_score) if s.total_weighted_score else None
                    ),
                    "reviewer_notes": s.reviewer_notes,
                    "scored_by_type": s.scored_by_type,
                    "scored_at": s.scored_at.isoformat() if s.scored_at else None,
                }
                for s in scores_r.scalars().all()
            ]

            applicants.append(
                {
                    "application_id": str(app.id),
                    "student_id": str(app.student_id),
                    "student_name": (
                        f"{student.first_name or ''} {student.last_name or ''}".strip()
                        if student
                        else "Unknown"
                    ),
                    "status": app.status,
                    "match_score": (float(app.match_score) if app.match_score else None),
                    "decision": app.decision,
                    "completeness_status": app.completeness_status,
                    "submitted_at": (app.submitted_at.isoformat() if app.submitted_at else None),
                    "scores": scores,
                    "avg_score": (
                        round(
                            sum(
                                float(s["total_weighted_score"])
                                for s in scores
                                if s["total_weighted_score"]
                            )
                            / len([s for s in scores if s["total_weighted_score"]]),
                            2,
                        )
                        if any(s["total_weighted_score"] for s in scores)
                        else None
                    ),
                    "gpa": (
                        max(
                            (
                                float(ar.gpa)
                                for ar in student.academic_records
                                if ar.gpa is not None
                            ),
                            default=None,
                        )
                        if student and student.academic_records
                        else None
                    ),
                    "nationality": (
                        student.nationality if student and hasattr(student, "nationality") else None
                    ),
                }
            )
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
